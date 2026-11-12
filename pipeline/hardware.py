"""
Detecção do ambiente experimental (CPU, GPU, RAM, armazenamento, SO, CUDA e versões das bibliotecas).
"""
import json
import os
import platform
import re
import shutil
import subprocess
import tempfile


def get_cpu_info() -> dict:
    info = {
        "modelo": platform.processor(),
        "cores": None,
        "threads": os.cpu_count(),
        "frequencia_mhz": None,
        "descricao": platform.processor()
    }
    try:
        cmd = [
            "powershell", "-NoProfile", "-Command",
            "Get-CimInstance Win32_Processor | Select-Object -First 1 Name, NumberOfCores, NumberOfLogicalProcessors, MaxClockSpeed | ConvertTo-Json"
        ]
        res = subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL)
        data = json.loads(res)
        name = data.get("Name", "").strip()
        cores = data.get("NumberOfCores")
        threads = data.get("NumberOfLogicalProcessors")
        freq = data.get("MaxClockSpeed")

        info["modelo"] = name
        info["cores"] = cores
        info["threads"] = threads
        info["frequencia_mhz"] = freq
        freq_str = f" @ {freq/1000:.1f} GHz base" if freq else ""
        info["descricao"] = f"{name} ({cores}C/{threads}T{freq_str})"
    except Exception:
        pass
    return info


def get_gpu_info() -> dict:
    info = {
        "modelo": "N/A",
        "vram_mb": 0,
        "driver": "N/A",
        "cuda": "N/A",
        "arquitetura": "N/A",
        "descricao": "N/A"
    }
    try:
        cmd = ["nvidia-smi", "--query-gpu=name,memory.total,driver_version", "--format=csv,noheader,nounits"]
        res = subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL).strip().split(",")
        name = res[0].strip()
        vram = int(float(res[1].strip()))
        driver = res[2].strip()

        header = subprocess.check_output(["nvidia-smi"], text=True, stderr=subprocess.DEVNULL)
        m = re.search(r"CUDA(?:\s+\w+)?\s+Version:\s*([\d.]+)", header, re.IGNORECASE)
        cuda = m.group(1) if m else "N/A"

        # Identificação da arquitetura NVENC
        if re.search(r"RTX\s*50", name):
            arch = "NVENC 9ª Geração (Blackwell com dual AV1)"
        elif re.search(r"RTX\s*40|L4|L40|RTX\s*\d+\s*Ada", name):
            arch = "NVENC 8ª Geração (Ada Lovelace com suporte AV1)"
        elif re.search(r"RTX\s*30|A\d{2,4}", name):
            arch = "NVENC 7ª Geração (Ampere, sem AV1 encode)"
        else:
            arch = "NVIDIA NVENC"

        vram_gb = round(vram / 1024)
        info.update({
            "modelo": name,
            "vram_mb": vram,
            "driver": driver,
            "cuda": cuda,
            "arquitetura": arch,
            "descricao": f"{name} ({vram_gb} GB VRAM, {arch})"
        })
    except Exception:
        pass
    return info


MEMORY_TYPES = {20: "DDR", 21: "DDR2", 24: "DDR3", 26: "DDR4", 34: "DDR5"}


def get_ram_info() -> dict:
    info = {
        "capacidade_gb": None,
        "descricao": "N/A"
    }
    try:
        cmd = [
            "powershell", "-NoProfile", "-Command",
            "Get-CimInstance Win32_PhysicalMemory | Select-Object Capacity, ConfiguredClockSpeed, SMBIOSMemoryType | ConvertTo-Json"
        ]
        res = subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL)
        data = json.loads(res)
        if isinstance(data, dict):
            data = [data]
        gb = round(sum(int(d.get("Capacity") or 0) for d in data) / (1024 ** 3))
        speed = data[0].get("ConfiguredClockSpeed")
        mtype = MEMORY_TYPES.get(data[0].get("SMBIOSMemoryType"), "DDR")
        info["capacidade_gb"] = gb
        info["descricao"] = f"{gb} GB {mtype} @ {speed} MT/s ({len(data)} módulos)"
    except Exception:
        pass
    return info


def get_storage_info() -> dict:
    info = {
        "dispositivos": [],
        "descricao": "Armazenamento em disco SSD"
    }
    try:
        cmd = [
            "powershell", "-NoProfile", "-Command",
            "Get-PhysicalDisk | Select-Object -Property FriendlyName, MediaType, BusType | ConvertTo-Json"
        ]
        res = subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL)
        data = json.loads(res)
        if isinstance(data, dict):
            data = [data]
        disks = []
        for d in data:
            bus = d.get("BusType", "")
            name = d.get("FriendlyName", "")
            disks.append(f"{name} ({bus})")
        info["dispositivos"] = disks
        if disks:
            info["descricao"] = "; ".join(disks)
    except Exception:
        pass
    return info


def get_os_info() -> dict:
    info = {
        "sistema": platform.system(),
        "release": platform.release(),
        "build": platform.version(),
        "descricao": "Microsoft Windows"
    }
    try:
        cmd = [
            "powershell", "-NoProfile", "-Command",
            "(Get-CimInstance Win32_OperatingSystem).Caption + ' 64-bit (Build ' + (Get-CimInstance Win32_OperatingSystem).BuildNumber + ')'"
        ]
        res = subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL).strip()
        info["descricao"] = res
    except Exception:
        info["descricao"] = f"{platform.system()} {platform.release()} ({platform.version()})"
    return info


def get_library_versions() -> dict:
    """Detecta as versões reais compiladas de x264, SVT-AV1, dav1d e libvmaf."""
    versions = {"x264": "N/A", "SVT-AV1": "N/A", "dav1d": "N/A", "libvmaf": "N/A"}
    tmp = tempfile.mkdtemp(prefix="tcc_ver_")
    src = ["-f", "lavfi", "-i", "testsrc2=s=320x240:r=30", "-frames:v", "3"]
    try:
        # Detectar x264 core
        h264_p = os.path.join(tmp, "v.h264")
        subprocess.run(["ffmpeg", "-hide_banner", "-y", *src, "-c:v", "libx264", h264_p],
                       capture_output=True, text=True)
        if os.path.exists(h264_p):
            with open(h264_p, "rb") as f:
                content = f.read()
                m = re.search(rb"x264 - core (\d+)(?: r(\d+))?", content)
                if m:
                    core_str = m.group(1).decode()
                    rev_str = f" r{m.group(2).decode()}" if m.group(2) else ""
                    versions["x264"] = f"core {core_str}{rev_str}"

        # Detectar SVT-AV1 lib
        av1_p = os.path.join(tmp, "v.ivf")
        proc_svt = subprocess.run(["ffmpeg", "-hide_banner", "-y", "-v", "verbose", *src, "-c:v", "libsvtav1", av1_p],
                                  capture_output=True, text=True)
        m = re.search(r"Encoder Lib (v[\w.\-]+)", proc_svt.stderr)
        if m:
            versions["SVT-AV1"] = m.group(1)

        # Detectar dav1d
        if os.path.exists(av1_p):
            proc_dav = subprocess.run(["ffmpeg", "-hide_banner", "-y", "-v", "verbose", "-c:v", "libdav1d", "-i", av1_p, "-f", "null", "-"],
                                      capture_output=True, text=True)
            m = re.search(r"libdav1d\s+([\w.\-]+)", proc_dav.stderr)
            if m:
                versions["dav1d"] = m.group(1)

        # Detectar libvmaf
        vlog = "temp_probe_vmaf.json"
        subprocess.run(["ffmpeg", "-hide_banner", "-y", "-f", "lavfi", "-i", "testsrc2=s=320x240:r=30",
                        "-f", "lavfi", "-i", "testsrc2=s=320x240:r=30", "-frames:v", "2",
                        "-lavfi", f"libvmaf=log_fmt=json:log_path={vlog}", "-f", "null", "-"],
                       capture_output=True, text=True)
        if os.path.exists(vlog):
            try:
                with open(vlog, encoding="utf-8") as f:
                    v_str = json.load(f).get("version", "N/A")
                    versions["libvmaf"] = f"v3.x ({v_str})" if v_str != "N/A" else "Habilitado"
            finally:
                if os.path.exists(vlog):
                    os.remove(vlog)

        # Detectar xpsnr
        filters_out = subprocess.check_output(["ffmpeg", "-filters"], text=True, stderr=subprocess.DEVNULL)
        if re.search(r"\bxpsnr\b", filters_out):
            versions["xpsnr"] = "Habilitado"

        # Detectar FFVship (CUDA/libvship para SSIMULACRA2, Butteraugli e CVVDP)
        from .metrics import find_ffvship_binary
        ffv_path = find_ffvship_binary()
        if ffv_path:
            try:
                proc_ffv = subprocess.run([ffv_path, "--version"], capture_output=True, text=True)
                m_ver = re.search(r"FFVship\s+([\w.\-]+)", proc_ffv.stdout)
                versions["FFVship"] = m_ver.group(1) if m_ver else "Presente (CUDA)"
            except Exception:
                versions["FFVship"] = "Presente"
    except Exception:
        pass
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return versions


def get_ffmpeg_info() -> dict:
    info = {
        "versao": "N/A",
        "detalhes": "N/A",
        "bibliotecas": {}
    }
    try:
        res = subprocess.check_output(["ffmpeg", "-version"], text=True, stderr=subprocess.DEVNULL)
        info["versao"] = res.splitlines()[0]
    except Exception:
        return info

    libs = get_library_versions()
    info["bibliotecas"] = libs
    info["detalhes"] = f"{info['versao']} | " + ", ".join(f"{k}: {v}" for k, v in libs.items())
    return info


def get_energy_telemetry_info() -> dict:
    from .monitor import detect_cpu_power_telemetry, _HAS_NVIDIA_SMI
    cpu_src = detect_cpu_power_telemetry()
    gpu_src = "NVIDIA NVML (nvidia-smi)" if _HAS_NVIDIA_SMI else "N/A"
    if cpu_src != "Estimativa TDP":
        desc = f"CPU: Sensor de hardware Package Power ({cpu_src}) | GPU: {gpu_src}"
    else:
        desc = f"CPU: Estimativa por TDP nominal (120 W) | GPU: {gpu_src}"
    return {
        "cpu_fonte": cpu_src,
        "gpu_fonte": gpu_src,
        "descricao": desc
    }


def collect_all_environment_info() -> dict:
    """Coleta todas as informações necessárias para preencher a Tabela 1."""
    return {
        "cpu": get_cpu_info(),
        "gpu": get_gpu_info(),
        "ram": get_ram_info(),
        "storage": get_storage_info(),
        "os": get_os_info(),
        "ffmpeg": get_ffmpeg_info(),
        "energia": get_energy_telemetry_info()
    }


def format_table_1_markdown(env: dict) -> str:
    """Gera a Tabela 1 em Markdown."""
    cpu_desc = env["cpu"]["descricao"]
    gpu_desc = env["gpu"]["descricao"]
    ram_desc = env["ram"]["descricao"]
    storage_desc = env["storage"]["descricao"]
    os_desc = env["os"]["descricao"]
    ffmpeg_desc = env["ffmpeg"]["detalhes"]
    driver_desc = f"NVIDIA {env['gpu']['driver']} (CUDA {env['gpu'].get('cuda', 'N/A')})"
    energia_desc = env.get("energia", {}).get("descricao", "CPU: Estimativa TDP / GPU: nvidia-smi")

    lines = [
        "### Tabela 1 — Especificações do Ambiente Experimental de Hardware e Software",
        "",
        "| Categoria | Componente / Parâmetro | Detalhes Técnicos |",
        "| :---- | :---- | :---- |",
        f"| **Processador (CPU)** | Modelo, núcleos/threads, frequência base/boost | {cpu_desc} |",
        f"| **Placa Gráfica (GPU)** | Modelo, VRAM, versão da arquitetura NVENC | {gpu_desc} |",
        f"| **Memória RAM** | Capacidade (GB), tecnologia, velocidade | {ram_desc} |",
        f"| **Armazenamento** | Interface de disco dos ficheiros fonte | {storage_desc} |",
        f"| **Sistema Operativo** | Distribuição, versão de kernel / build | {os_desc} |",
        f"| **Compilação FFmpeg** | Versão exata do binário e bibliotecas | {ffmpeg_desc} |",
        f"| **Versão dos Drivers** | Versão do controlador NVIDIA / SDK | {driver_desc} |",
        f"| **Telemetria Energética** | Método de medição de potência e energia | {energia_desc} |",
        ""
    ]
    return "\n".join(lines)
