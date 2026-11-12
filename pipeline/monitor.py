"""
Monitoramento em tempo real de recursos de hardware:
- Utilização de CPU e pico de memória RAM (via psutil).
- Telemetria de potência da CPU em Watts (via sensor físico LibreHardwareMonitor / AMD SMU ou estimativa TDP).
- Utilização e potência elétrica da GPU em Watts (via nvidia-smi).
- Estimativa de consumo de energia líquida em Watt-hora (Wh) com desconto de repouso (idle).
"""
import json
import shutil
import subprocess
import threading
import time
import urllib.request

import psutil

_HAS_NVIDIA_SMI = shutil.which("nvidia-smi") is not None


def _find_power_in_lhm_tree(node: dict):
    """Procura recursivamente o sensor de Package Power na árvore JSON do LibreHardwareMonitor."""
    text = node.get("Text", "")
    val = node.get("Value", "")
    if ("Package" in text or "CPU Package" in text) and "W" in val:
        try:
            return float(val.replace("W", "").replace(",", ".").strip())
        except (ValueError, AttributeError):
            pass
    for child in node.get("Children", []):
        res = _find_power_in_lhm_tree(child)
        if res is not None:
            return res
    return None


def get_cpu_power_reading() -> tuple:
    """
    Tenta ler a potência instantânea da CPU em Watts.
    Retorna (potencia_watts, "fonte") ou (None, "Estimativa TDP").
    """
    # 1. Tentar via Web Server do LibreHardwareMonitor (data.json na porta padrão 8085)
    try:
        req = urllib.request.Request("http://localhost:8085/data.json", headers={"User-Agent": "TCC-Pipeline"})
        with urllib.request.urlopen(req, timeout=0.15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            w = _find_power_in_lhm_tree(data)
            if w is not None and w > 0:
                return w, "LibreHardwareMonitor Web"
    except Exception:
        pass

    # 1.1 Tentar via endpoint /metrics (Prometheus) do LibreHardwareMonitor
    try:
        req = urllib.request.Request("http://localhost:8085/metrics", headers={"User-Agent": "TCC-Pipeline"})
        with urllib.request.urlopen(req, timeout=0.15) as resp:
            text = resp.read().decode("utf-8")
            for line in text.splitlines():
                if line.startswith("#"):
                    continue
                line_lower = line.lower()
                if "power" in line_lower and "package" in line_lower:
                    parts = line.split()
                    if len(parts) >= 2:
                        try:
                            val = float(parts[-1])
                            if val > 0:
                                return val, "LibreHardwareMonitor Metrics"
                        except ValueError:
                            pass
    except Exception:
        pass

    # 2. Tentar via WMI (namespace root/LibreHardwareMonitor) caso ativo
    try:
        import pythoncom
        import wmi
        pythoncom.CoInitialize()
        try:
            c = wmi.WMI(namespace="root/LibreHardwareMonitor")
            for s in c.Sensor():
                if getattr(s, "SensorType", "") == "Power" and ("Package" in getattr(s, "Name", "") or "CPU Package" in getattr(s, "Name", "")):
                    val = float(s.Value)
                    if val > 0:
                        return val, "LibreHardwareMonitor WMI"
        finally:
            pythoncom.CoUninitialize()
    except Exception:
        pass

    return None, "Estimativa TDP"


def detect_cpu_power_telemetry() -> str:
    """Detecta se há algum sensor físico de energia de CPU ativo no sistema."""
    w, source = get_cpu_power_reading()
    if w is not None:
        return source
    return "Estimativa TDP"


class ResourceMonitor:
    def __init__(self, interval_s: float = 0.25):
        self.interval_s = interval_s
        self.cpu_samples = []
        self.cpu_power_samples = []
        self.gpu_util_samples = []
        self.gpu_power_samples = []
        self.gpu_dec_samples = []
        self.gpu_enc_samples = []
        self.peak_rss_mb = 0.0
        self.cpu_power_source = "Estimativa TDP"
        self._stop = threading.Event()
        self._threads = []
        self._smi = None
        self._pid = None

    def start(self, pid: int = None):
        self._pid = pid
        psutil.cpu_percent(interval=None)

        # Thread de CPU e RAM
        t_cpu = threading.Thread(target=self._cpu_loop, daemon=True)
        self._threads.append(t_cpu)

        # Thread de potência da CPU (se sensor físico estiver ativo)
        _, detected_source = get_cpu_power_reading()
        if detected_source != "Estimativa TDP":
            self.cpu_power_source = detected_source
            t_cpu_pwr = threading.Thread(target=self._cpu_power_loop, daemon=True)
            self._threads.append(t_cpu_pwr)

        # Thread de GPU (nvidia-smi)
        if _HAS_NVIDIA_SMI:
            try:
                self._smi = subprocess.Popen(
                    ["nvidia-smi", "--query-gpu=utilization.gpu,power.draw,utilization.decoder,utilization.encoder",
                     "--format=csv,noheader,nounits", f"-lms={int(self.interval_s * 1000)}"],
                    stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True,
                )
                t_gpu = threading.Thread(target=self._gpu_loop, daemon=True)
                self._threads.append(t_gpu)
            except Exception:
                self._smi = None

        for t in self._threads:
            t.start()
        return self

    def _cpu_loop(self):
        proc = psutil.Process(self._pid) if self._pid else None
        while not self._stop.wait(self.interval_s):
            self.cpu_samples.append(psutil.cpu_percent(interval=None))
            if proc:
                try:
                    rss = proc.memory_info().rss / (1024 * 1024)
                    self.peak_rss_mb = max(self.peak_rss_mb, rss)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass

    def _cpu_power_loop(self):
        """Coleta amostras em tempo real de potência da CPU em Watts."""
        while not self._stop.wait(self.interval_s):
            w, _ = get_cpu_power_reading()
            if w is not None and w > 0:
                self.cpu_power_samples.append(w)

    def _gpu_loop(self):
        if not self._smi or not self._smi.stdout:
            return
        for line in self._smi.stdout:
            if self._stop.is_set():
                break
            parts = [p.strip() for p in line.split(",")]
            try:
                self.gpu_util_samples.append(float(parts[0]))
                self.gpu_power_samples.append(float(parts[1]))
                # motores dedicados NVDEC/NVENC: utilization.gpu mede só o 3D/CUDA
                self.gpu_dec_samples.append(float(parts[2]))
                self.gpu_enc_samples.append(float(parts[3]))
            except (ValueError, IndexError):
                continue

    def stop(self) -> dict:
        self._stop.set()
        if self._smi:
            self._smi.terminate()
            try:
                self._smi.wait(timeout=1.5)
            except subprocess.TimeoutExpired:
                self._smi.kill()
        for t in self._threads:
            t.join(timeout=1.5)
        return self.summary()

    def summary(self) -> dict:
        avg = lambda xs: sum(xs) / len(xs) if xs else 0.0
        cpu_pwr = avg(self.cpu_power_samples) if self.cpu_power_samples else None
        return {
            "cpu_util_pct": avg(self.cpu_samples),
            "cpu_power_w": cpu_pwr,
            "cpu_power_source": self.cpu_power_source if self.cpu_power_samples else "Estimativa TDP",
            "gpu_util_pct": avg(self.gpu_util_samples),
            "gpu_power_w": avg(self.gpu_power_samples),
            "gpu_dec_util_pct": avg(self.gpu_dec_samples),
            "gpu_enc_util_pct": avg(self.gpu_enc_samples),
            "peak_rss_mb": self.peak_rss_mb,
        }


def measure_idle_power(seconds: float = 2.0, cpu_tdp_w: float = 120.0) -> dict:
    """Mede a potência média de CPU e GPU em repouso para descontar o consumo de base."""
    mon = ResourceMonitor(interval_s=0.2).start()
    time.sleep(seconds)
    res = mon.stop()
    return {
        "cpu_idle_w": res.get("cpu_power_w") if res.get("cpu_power_source") != "Estimativa TDP" else 0.0,
        "gpu_idle_w": res.get("gpu_power_w", 0.0),
        "cpu_power_source": res.get("cpu_power_source", "Estimativa TDP"),
    }


def measure_gpu_idle_power(seconds: float = 2.0) -> float:
    """Compatibilidade reversa: mede potência da GPU em repouso."""
    idle = measure_idle_power(seconds)
    return idle.get("gpu_idle_w", 0.0)


def run_monitored(cmd: list) -> tuple:
    """Executa um comando de processo monitorando recursos. Retorna (returncode, stderr, elapsed_s, recursos)."""
    t0 = time.perf_counter()
    proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
    mon = ResourceMonitor().start(proc.pid)
    _, stderr = proc.communicate()
    elapsed = time.perf_counter() - t0
    res = mon.stop()
    return proc.returncode, stderr, elapsed, res


def estimate_energy_wh(resources: dict, elapsed_s: float, cpu_tdp_w: float, gpu_idle_w: float, cpu_idle_w: float = 0.0) -> float:
    """
    Energia líquida consumida (Wh):
    Se CPU tiver sensor físico de potência (W): usa max(CPU_W - cpu_idle_w, 0).
    Caso contrário: usa o modelo heurístico TDP x % utilização.
    GPU: Potência medida acima da potência de repouso (idle).
    """
    if resources.get("cpu_power_source") != "Estimativa TDP" and resources.get("cpu_power_w") is not None:
        cpu_w = max(resources.get("cpu_power_w", 0.0) - cpu_idle_w, 0.0)
    else:
        cpu_w = cpu_tdp_w * (resources.get("cpu_util_pct", 0.0) / 100.0)

    gpu_w = max(resources.get("gpu_power_w", 0.0) - gpu_idle_w, 0.0)
    total_w = cpu_w + gpu_w
    return (total_w * elapsed_s) / 3600.0
