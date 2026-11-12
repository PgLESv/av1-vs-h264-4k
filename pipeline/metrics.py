"""
Cálculo das métricas de qualidade visual.

1. VMAF e VMAF NEG (libvmaf: vmaf_4k_v0.6.1 ou vmaf_v0.6.1)
2. PSNR-Y e PSNR-YUV ponderado 6:1:1
3. SSIM e MS-SSIM (libvmaf float_ssim e float_ms_ssim)
4. XPSNR (filtro nativo do FFmpeg)
5. SSIMULACRA2 (FFVship, GPU)
6. Butteraugli (FFVship: 2-norma, 3-norma e norma infinita)
7. CVVDP (FFVship)
"""
import json
import os
import re
import shutil
import subprocess

import numpy as np

NAN = float("nan")  # métrica indisponível/falhou: nunca 0.0, que distorce médias e BD-Rate

from .utils import log_command


def _vmaf_model_for_height(height: int) -> str:
    return "vmaf_4k_v0.6.1" if height >= 1440 else "vmaf_v0.6.1"


def _filter_path(path: str) -> str:
    try:
        path = os.path.relpath(path)
    except ValueError:
        pass
    return path.replace("\\", "/")


def find_ffvship_binary() -> str | None:
    """Localiza o binário FFVship com suporte a GPU (CUDA/Vulkan)."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    candidates = [
        os.path.join(base_dir, "tools", "FFVship", "FFVship.exe"),
        os.path.join(base_dir, "tools", "FFVship", "FFVship_nvidia", "FFVship.exe"),
    ]
    for c in candidates:
        if os.path.exists(c):
            return os.path.abspath(c)
    which_p = shutil.which("FFVship")
    if which_p:
        return which_p
    return None


def check_ffmpeg_filter(filter_name: str) -> bool:
    """Verifica se o binário ffmpeg no PATH suporta o filtro solicitado."""
    try:
        res = subprocess.check_output(["ffmpeg", "-filters"], text=True, stderr=subprocess.DEVNULL)
        return bool(re.search(rf"\b{re.escape(filter_name)}\b", res))
    except Exception:
        return False


class QualityAssessor:
    def __init__(self, metrics_dir: str, n_threads: int = None):
        self.metrics_dir = metrics_dir
        self.n_threads = n_threads or os.cpu_count() or 4
        os.makedirs(self.metrics_dir, exist_ok=True)
        self.ffvship_path = find_ffvship_binary()
        self.has_xpsnr = check_ffmpeg_filter("xpsnr")

    def _calculate_vmaf_psnr_ssim(self, encoded_path: str, reference_path: str,
                                  width: int, height: int, pix_fmt: str,
                                  enc_name: str, max_frames: int = None,
                                  force: bool = False) -> dict:
        """Calcula VMAF, VMAF NEG, PSNR e SSIM via libvmaf em passagem única."""
        json_log = os.path.join(self.metrics_dir, f"{enc_name}_vmaf.json")
        model = _vmaf_model_for_height(height)

        data = None
        if not force and os.path.exists(json_log) and os.path.getsize(json_log) > 0:
            try:
                with open(json_log, "r", encoding="utf-8") as f:
                    cached = json.load(f)
                if cached.get("frames"):
                    data = cached
            except Exception:
                data = None

        if data is None:
            models = f"version={model}\\:name=vmaf|version=vmaf_v0.6.1neg\\:name=vmaf_neg"
            features = "name=psnr|name=float_ssim|name=float_ms_ssim"
            graph = (
                f"[0:v]setpts=PTS-STARTPTS,scale={width}:{height}:flags=bicubic,format={pix_fmt}[dist];"
                f"[1:v]setpts=PTS-STARTPTS,format={pix_fmt}[ref];"
                f"[dist][ref]libvmaf=model='{models}':feature='{features}':n_threads={self.n_threads}"
                f":log_fmt=json:log_path='{_filter_path(json_log)}'"
            )
            cmd = ["ffmpeg", "-y", "-v", "error", "-i", encoded_path, "-i", reference_path]
            if max_frames:
                cmd += ["-frames:v", str(max_frames)]
            cmd += ["-filter_complex", graph, "-f", "null", "-"]
            log_command(cmd, f"metrics vmaf {enc_name}")

            proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if proc.returncode != 0:
                raise RuntimeError(f"Erro ao calcular VMAF com FFmpeg:\n{proc.stderr}")
            if not os.path.exists(json_log):
                raise FileNotFoundError(f"Arquivo de log VMAF não foi gerado: {json_log}")

            with open(json_log, "r", encoding="utf-8") as f:
                data = json.load(f)

        frames = data.get("frames", [])
        col = lambda key: np.array([float(fr["metrics"][key]) for fr in frames if key in fr.get("metrics", {})])

        vmaf = col("vmaf")
        vmaf_neg = col("vmaf_neg")
        psnr_y, psnr_u, psnr_v = col("psnr_y"), col("psnr_cb"), col("psnr_cr")
        ssim = col("float_ssim")
        ms_ssim = col("float_ms_ssim")

        # PSNR-YUV ponderado 6:1:1 conforme padrão JVET/AOM
        if len(psnr_y) and len(psnr_y) == len(psnr_u) == len(psnr_v):
            psnr_yuv = (6.0 * psnr_y + psnr_u + psnr_v) / 8.0
        else:
            psnr_yuv = psnr_y

        safe = lambda a, fn: float(fn(a)) if len(a) else NAN
        return {
            "vmaf_model": model,
            "libvmaf_version": data.get("version", "N/A"),
            "vmaf_mean": safe(vmaf, np.mean),
            "vmaf_min": safe(vmaf, np.min),
            "vmaf_min_1pct": safe(vmaf, lambda a: np.percentile(a, 1)),
            "vmaf_min_5pct": safe(vmaf, lambda a: np.percentile(a, 5)),
            "vmaf_std": safe(vmaf, np.std),
            "vmaf_neg_mean": safe(vmaf_neg, np.mean),
            "psnr_mean": safe(psnr_y, np.mean),
            "psnr_yuv_mean": safe(psnr_yuv, np.mean),
            "ssim_mean": safe(ssim, np.mean),
            "ms_ssim_mean": safe(ms_ssim, np.mean),
            "vmaf_frames": [float(v) for v in vmaf],
            "total_frames_evaluated": int(len(vmaf)),
            "json_log_path": json_log,
        }

    def _calculate_xpsnr(self, encoded_path: str, reference_path: str,
                         width: int, height: int, pix_fmt: str,
                         enc_name: str, max_frames: int = None,
                         force: bool = False) -> dict:
        """Calcula XPSNR (extended peak signal-to-noise ratio) conforme recomendação ITU-T."""
        xpsnr_log = os.path.join(self.metrics_dir, f"{enc_name}_xpsnr.log")
        has_cache = not force and os.path.exists(xpsnr_log) and os.path.getsize(xpsnr_log) > 0

        if not has_cache:
            graph = (
                f"[0:v]setpts=PTS-STARTPTS,scale={width}:{height}:flags=bicubic,format={pix_fmt}[dist];"
                f"[1:v]setpts=PTS-STARTPTS,format={pix_fmt}[ref];"
                f"[dist][ref]xpsnr=stats_file='{_filter_path(xpsnr_log)}'"
            )
            cmd = ["ffmpeg", "-y", "-v", "error", "-i", encoded_path, "-i", reference_path]
            if max_frames:
                cmd += ["-frames:v", str(max_frames)]
            cmd += ["-filter_complex", graph, "-f", "null", "-"]
            log_command(cmd, f"metrics xpsnr {enc_name}")

            proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if proc.returncode != 0:
                raise RuntimeError(f"Erro ao calcular XPSNR com FFmpeg:\n{proc.stderr}")
            if not os.path.exists(xpsnr_log):
                raise FileNotFoundError(f"Arquivo de log XPSNR não foi gerado: {xpsnr_log}")

        y_list, u_list, v_list = [], [], []
        avg_y, avg_u, avg_v, avg_min = None, None, None, None

        with open(xpsnr_log, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                # Linha de frame: n: 1 XPSNR y: 41.0618 XPSNR u: 44.3225 XPSNR v: 45.7175
                m_frame = re.search(r"XPSNR\s+y:\s*([\d.]+)\s+XPSNR\s+u:\s*([\d.]+)\s+XPSNR\s+v:\s*([\d.]+)", line)
                if m_frame:
                    y_list.append(float(m_frame.group(1)))
                    u_list.append(float(m_frame.group(2)))
                    v_list.append(float(m_frame.group(3)))
                # Linha de média: XPSNR average, 300 frames y: 26.8664 u: 30.1964 v: 31.2645 (minimum: 26.8664)
                m_avg = re.search(r"XPSNR\s+average.*?y:\s*([\d.]+)\s+u:\s*([\d.]+)\s+v:\s*([\d.]+)(?:\s+\(minimum:\s*([\d.]+)\))?", line)
                if m_avg:
                    avg_y = float(m_avg.group(1))
                    avg_u = float(m_avg.group(2))
                    avg_v = float(m_avg.group(3))
                    if m_avg.group(4):
                        avg_min = float(m_avg.group(4))

        y_val = avg_y if avg_y is not None else (float(np.mean(y_list)) if y_list else NAN)
        u_val = avg_u if avg_u is not None else (float(np.mean(u_list)) if u_list else NAN)
        v_val = avg_v if avg_v is not None else (float(np.mean(v_list)) if v_list else NAN)
        min_val = avg_min if avg_min is not None else (float(np.min(y_list)) if y_list else NAN)

        # XPSNR-YUV ponderado padrão 6:1:1
        xpsnr_yuv = (6.0 * y_val + u_val + v_val) / 8.0

        return {
            "xpsnr_y_mean": y_val,
            "xpsnr_u_mean": u_val,
            "xpsnr_v_mean": v_val,
            "xpsnr_yuv_mean": xpsnr_yuv,
            "xpsnr_min": min_val,
            "xpsnr_frames": y_list,
            "xpsnr_log_path": xpsnr_log
        }

    def _calculate_ffvship_metric(self, metric: str, encoded_path: str, reference_path: str,
                                  enc_name: str, max_frames: int = None,
                                  force: bool = False) -> dict:
        """Executa FFVship para SSIMULACRA2, Butteraugli ou CVVDP."""
        tag = metric.lower()
        json_log = os.path.join(self.metrics_dir, f"{enc_name}_{tag}.json")
        has_cache = not force and os.path.exists(json_log) and os.path.getsize(json_log) > 0

        stdout_txt = ""
        if not has_cache:
            if not self.ffvship_path or not os.path.exists(self.ffvship_path):
                raise FileNotFoundError(f"Binário FFVship não encontrado para calcular {metric}")

            cmd = [
                self.ffvship_path,
                "-s", reference_path,
                "-e", encoded_path,
                "-m", metric,
                "--json", json_log
            ]
            if max_frames:
                cmd += ["--start", "0", "--end", str(max_frames)]

            log_command(cmd, f"metrics {tag} {enc_name}")
            proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

            if proc.returncode != 0:
                raise RuntimeError(f"Erro ao calcular {metric} com FFVship:\n{proc.stderr}")
            if not os.path.exists(json_log):
                raise FileNotFoundError(f"Arquivo de log {metric} não foi gerado: {json_log}")
            stdout_txt = proc.stdout

        with open(json_log, "r", encoding="utf-8") as f:
            data = json.load(f)

        if metric == "SSIMULACRA2":
            scores = [float(fr[0]) for fr in data if fr]
            safe = lambda a, fn: float(fn(a)) if len(a) else NAN
            return {
                "ssimulacra2_mean": safe(scores, np.mean),
                "ssimulacra2_min": safe(scores, np.min),
                "ssimulacra2_std": safe(scores, np.std),
                "ssimulacra2_frames": scores,
                "ssimulacra2_log_path": json_log
            }

        elif metric == "Butteraugli":
            norm2 = [float(fr[0]) for fr in data if len(fr) >= 1]
            norm3 = [float(fr[1]) for fr in data if len(fr) >= 2]
            norm_inf = [float(fr[2]) for fr in data if len(fr) >= 3]
            safe = lambda a, fn: float(fn(a)) if len(a) else NAN
            return {
                "butteraugli_2norm": safe(norm2, np.mean),
                "butteraugli_3norm": safe(norm3, np.mean),
                "butteraugli_inf": safe(norm_inf, np.mean),
                "butteraugli_min": safe(norm2, np.min),
                "butteraugli_frames": norm2,
                "butteraugli_log_path": json_log
            }

        elif metric == "CVVDP":
            scores = [float(fr[0]) for fr in data if fr]
            # O FFVship grava a nota CVVDP acumulada: o último valor == "Video Score" do stdout (conferido).
            # Assim cache e execução nova dão o mesmo número.
            video_score = scores[-1] if scores else NAN
            safe = lambda a, fn: float(fn(a)) if len(a) else NAN
            return {
                "cvvdp_score": video_score,
                "cvvdp_mean": safe(scores, np.mean),
                "cvvdp_min": safe(scores, np.min),
                "cvvdp_frames": scores,
                "cvvdp_log_path": json_log
            }

        return {}

    def calculate_metrics(self, encoded_path: str, reference_path: str, width: int, height: int,
                          pix_fmt: str = "yuv420p", metrics_to_run: list = None,
                          max_frames: int = None, force: bool = False) -> dict:
        """
        Executa e consolida todas as 7 métricas de qualidade visual:
        CVVDP, PSNR, SSIM, SSIMULACRA2, VMAF, XPSNR, butteraugli.
        """
        enc_name = os.path.splitext(os.path.basename(encoded_path))[0]
        results = {}

        if metrics_to_run is None:
            metrics_to_run = ["vmaf", "psnr", "ssim", "xpsnr", "ssimulacra2", "butteraugli", "cvvdp"]

        # 1. VMAF, PSNR e SSIM
        if any(m in metrics_to_run for m in ["vmaf", "psnr", "ssim"]):
            try:
                vmaf_data = self._calculate_vmaf_psnr_ssim(encoded_path, reference_path, width, height, pix_fmt, enc_name, max_frames, force=force)
                results.update(vmaf_data)
            except Exception as e:
                print(f"[Aviso] Falha no cálculo de VMAF/PSNR/SSIM para {enc_name}: {e}")
                results.update({
                    "vmaf_model": _vmaf_model_for_height(height),
                    "libvmaf_version": "N/A",
                    "vmaf_mean": NAN, "vmaf_min": NAN, "vmaf_min_1pct": NAN, "vmaf_min_5pct": NAN, "vmaf_std": NAN,
                    "vmaf_neg_mean": NAN, "psnr_mean": NAN, "psnr_yuv_mean": NAN, "ssim_mean": NAN, "ms_ssim_mean": NAN,
                    "vmaf_frames": [], "total_frames_evaluated": 0, "json_log_path": ""
                })

        # 2. XPSNR
        if "xpsnr" in metrics_to_run:
            if self.has_xpsnr:
                try:
                    xp_data = self._calculate_xpsnr(encoded_path, reference_path, width, height, pix_fmt, enc_name, max_frames, force=force)
                    results.update(xp_data)
                except Exception as e:
                    print(f"[Aviso] Falha no cálculo de XPSNR para {enc_name}: {e}")
                    results.update({
                        "xpsnr_y_mean": NAN, "xpsnr_u_mean": NAN, "xpsnr_v_mean": NAN,
                        "xpsnr_yuv_mean": NAN, "xpsnr_min": NAN, "xpsnr_frames": [], "xpsnr_log_path": ""
                    })
            else:
                results.update({
                    "xpsnr_y_mean": NAN, "xpsnr_u_mean": NAN, "xpsnr_v_mean": NAN,
                    "xpsnr_yuv_mean": NAN, "xpsnr_min": NAN, "xpsnr_frames": [], "xpsnr_log_path": ""
                })

        # 3. SSIMULACRA2
        if "ssimulacra2" in metrics_to_run:
            if self.ffvship_path:
                try:
                    s2_data = self._calculate_ffvship_metric("SSIMULACRA2", encoded_path, reference_path, enc_name, max_frames, force=force)
                    results.update(s2_data)
                except Exception as e:
                    print(f"[Aviso] Falha no cálculo de SSIMULACRA2 para {enc_name}: {e}")
                    results.update({"ssimulacra2_mean": NAN, "ssimulacra2_min": NAN, "ssimulacra2_std": NAN, "ssimulacra2_frames": [], "ssimulacra2_log_path": ""})
            else:
                results.update({"ssimulacra2_mean": NAN, "ssimulacra2_min": NAN, "ssimulacra2_std": NAN, "ssimulacra2_frames": [], "ssimulacra2_log_path": ""})

        # 4. Butteraugli
        if "butteraugli" in metrics_to_run:
            if self.ffvship_path:
                try:
                    ba_data = self._calculate_ffvship_metric("Butteraugli", encoded_path, reference_path, enc_name, max_frames, force=force)
                    results.update(ba_data)
                except Exception as e:
                    print(f"[Aviso] Falha no cálculo de Butteraugli para {enc_name}: {e}")
                    results.update({"butteraugli_2norm": NAN, "butteraugli_3norm": NAN, "butteraugli_inf": NAN, "butteraugli_min": NAN, "butteraugli_frames": [], "butteraugli_log_path": ""})
            else:
                results.update({"butteraugli_2norm": NAN, "butteraugli_3norm": NAN, "butteraugli_inf": NAN, "butteraugli_min": NAN, "butteraugli_frames": [], "butteraugli_log_path": ""})

        # 5. CVVDP
        if "cvvdp" in metrics_to_run:
            if self.ffvship_path:
                try:
                    cv_data = self._calculate_ffvship_metric("CVVDP", encoded_path, reference_path, enc_name, max_frames, force=force)
                    results.update(cv_data)
                except Exception as e:
                    print(f"[Aviso] Falha no cálculo de CVVDP para {enc_name}: {e}")
                    results.update({"cvvdp_score": NAN, "cvvdp_mean": NAN, "cvvdp_min": NAN, "cvvdp_frames": [], "cvvdp_log_path": ""})
            else:
                results.update({"cvvdp_score": NAN, "cvvdp_mean": NAN, "cvvdp_min": NAN, "cvvdp_frames": [], "cvvdp_log_path": ""})

        return results
