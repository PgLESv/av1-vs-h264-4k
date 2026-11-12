"""
Módulo de codificação de vídeo com FFmpeg.
Codificadores: libx264, h264_nvenc, libsvtav1, av1_nvenc.

Condições comuns a todos os codificadores:
- Mesma profundidade de bits (pix_fmt).
- GOP fixo (gop_seconds x fps) com detecção de corte de cena desabilitada.
- Modo 'quality' (CRF/CQ) para varredura R-D.
- Modo 'bitrate' (VBR restrito de 1 passagem) com mesmos maxrate e bufsize relativos.
- N repetições por ensaio (média amostral e desvio padrão para tempo e FPS).
"""
import os
import shutil

from .monitor import run_monitored, estimate_energy_wh
from .utils import log_command, stream_size_bytes, mean_std


class SkipEncode(Exception):
    """Combinação não suportada pelo hardware ou encoder."""


class VideoEncoder:
    def __init__(self, output_dir: str, encoding_cfg: dict, cpu_tdp_w: float = 120.0, gpu_idle_w: float = 0.0, cpu_idle_w: float = 0.0):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        self.bit_depth = int(encoding_cfg.get("bit_depth", 8))
        self.pix_fmt = "yuv420p10le" if self.bit_depth == 10 else "yuv420p"
        self.gop_seconds = float(encoding_cfg.get("gop_seconds", 2.0))
        self.repetitions = int(encoding_cfg.get("repetitions", 3))
        self.maxrate_factor = float(encoding_cfg.get("vbr_maxrate_factor", 1.5))
        self.bufsize_factor = float(encoding_cfg.get("vbr_bufsize_factor", 2.0))
        self.cpu_tdp_w = cpu_tdp_w
        self.gpu_idle_w = gpu_idle_w
        self.cpu_idle_w = cpu_idle_w

    def _build_codec_args(self, codec_cfg: dict, mode: str, value, fps: float, extra_svt_params: list = None) -> list:
        lib = codec_cfg["lib"]
        gop = str(max(1, int(round(self.gop_seconds * fps))))
        args = ["-c:v", lib]

        preset = codec_cfg.get("preset")
        if preset is not None:
            args += ["-preset", str(preset)]

        rate_args = []
        if mode == "bitrate":
            rate_args = [
                "-b:v", f"{int(value)}k",
                "-maxrate", f"{int(value * self.maxrate_factor)}k",
                "-bufsize", f"{int(value * self.bufsize_factor)}k"
            ]

        if lib == "libx264":
            args += ["-g", gop, "-keyint_min", gop, "-sc_threshold", "0"]
            if mode == "bitrate":
                args += rate_args
            else:
                args += ["-crf", str(value)]

        elif lib == "libsvtav1":
            args += ["-g", gop]
            if mode == "bitrate":
                args += rate_args
            else:
                args += ["-crf", str(value)]
            svt_params = ["scd=0"]
            if extra_svt_params:
                svt_params.extend(extra_svt_params)
            args += ["-svtav1-params", ":".join(svt_params)]

        elif lib in ("h264_nvenc", "av1_nvenc"):
            if lib == "h264_nvenc" and self.bit_depth == 10:
                raise SkipEncode("h264_nvenc não possui suporte a codificação em 10 bits")
            args += ["-g", gop, "-no-scenecut", "1", "-tune", "hq", "-rc", "vbr"]
            if mode == "bitrate":
                args += rate_args
            else:
                # Sem maxrate explícito o NVENC aplica um teto implícito (medido: ~130 Mbps; AV1 trava em ~43 Mbps a partir de cq 26)
                args += ["-cq", str(value), "-b:v", "0", "-maxrate", "800M", "-bufsize", "1600M"]
        else:
            raise ValueError(f"Biblioteca desconhecida: {lib}")

        if lib == "h264_nvenc":
            target_pix_fmt = "yuv420p"
        else:
            target_pix_fmt = self.pix_fmt

        args += ["-pix_fmt", target_pix_fmt]
        for extra in codec_cfg.get("extra_args", []):
            args.append(str(extra))

        return args

    def encode(self, input_path: str, codec_key: str, codec_cfg: dict, mode: str, value,
               video_meta: dict, tag: str = "", extra_svt_params: list = None) -> dict:
        fps = video_meta.get("fps", 60.0)
        duration = video_meta.get("duration") or 10.0
        nb_frames = video_meta.get("nb_frames") or int(round(duration * fps))

        video_name = os.path.splitext(os.path.basename(input_path))[0]
        val_tag = f"{value}k" if mode == "bitrate" else f"q{value}"
        preset_tag = f"p{codec_cfg.get('preset')}"
        out_name = f"{video_name}_{codec_key}_{preset_tag}_{val_tag}{tag}.mp4"
        out_path = os.path.join(self.output_dir, out_name)

        codec_args = self._build_codec_args(codec_cfg, mode, value, fps, extra_svt_params)
        cmd = ["ffmpeg", "-y", "-v", "error", "-i", input_path, *codec_args, "-an", out_path]
        log_command(cmd, f"encode {codec_key} ({mode}={value}{tag})")

        times = []
        energies = []
        res_list = []

        runs = max(1, self.repetitions)
        for r_idx in range(runs):
            rc, stderr, elapsed, res = run_monitored(cmd)
            if rc != 0:
                raise RuntimeError(f"Erro ao codificar com {codec_cfg['lib']} (tentativa {r_idx+1}/{runs}):\n{stderr}")
            times.append(elapsed)
            res_list.append(res)
            energies.append(estimate_energy_wh(res, elapsed, self.cpu_tdp_w, self.gpu_idle_w, self.cpu_idle_w))

        t_mean, t_std = mean_std(times)
        avg_k = lambda k: sum(r.get(k, 0.0) for r in res_list) / len(res_list) if res_list else 0.0

        stream_bytes = stream_size_bytes(out_path)
        real_kbps = (stream_bytes * 8.0) / (duration * 1000.0) if duration > 0 else 0.0
        divergence = ((real_kbps - value) / value) * 100.0 if mode == "bitrate" else 0.0

        fps_encoding = nb_frames / t_mean if t_mean > 0 else 0.0
        fps_std = (nb_frames / t_mean) * (t_std / t_mean) if t_mean > 0 else 0.0

        cpu_pwr_vals = [r.get("cpu_power_w") for r in res_list if r.get("cpu_power_w") is not None]
        avg_cpu_power = sum(cpu_pwr_vals) / len(cpu_pwr_vals) if cpu_pwr_vals else None
        cpu_pwr_src = res_list[0].get("cpu_power_source", "Estimativa TDP") if res_list else "Estimativa TDP"

        return {
            "codec": codec_key,
            "encoder_lib": codec_cfg["lib"],
            "preset": codec_cfg.get("preset"),
            "mode": mode,
            "target_value": value,
            "pix_fmt": self.pix_fmt,
            "output_path": out_path,
            "file_size_mb": os.path.getsize(out_path) / (1024 * 1024),
            "stream_size_mb": stream_bytes / (1024 * 1024),
            "real_bitrate_kbps": real_kbps,
            "bitrate_divergence_pct": divergence,
            "encoding_times_s": times,
            "encoding_time_s": t_mean,
            "encoding_time_std_s": t_std,
            "encoding_fps": fps_encoding,
            "encoding_fps_std": fps_std,
            "real_time_factor": duration / t_mean if t_mean > 0 else 0.0,
            "encode_s_per_content_s": t_mean / duration if duration > 0 else 0.0,
            "cpu_util_pct": avg_k("cpu_util_pct"),
            "cpu_power_w": avg_cpu_power,
            "cpu_power_source": cpu_pwr_src,
            "gpu_util_pct": avg_k("gpu_util_pct"),
            "gpu_power_w": avg_k("gpu_power_w"),
            "peak_rss_mb": max((r.get("peak_rss_mb", 0.0) for r in res_list), default=0.0),
            "energy_wh": sum(energies) / len(energies) if energies else 0.0,
            "repetitions": len(times),
        }
