"""
Benchmark de desempenho de decodificação no cliente (espectador).
Compara decodificação por software (dav1d CPU / libavcodec) e por hardware dedicado (NVDEC).
"""
from .monitor import run_monitored
from .utils import log_command, mean_std

DECODERS = {
    "h264": [
        ("H.264 SW (libavcodec)", ["-c:v", "h264"]),
        ("H.264 HW (NVDEC)", ["-hwaccel", "cuda", "-hwaccel_output_format", "cuda"]),
    ],
    "av1": [
        ("AV1 SW (dav1d)", ["-c:v", "libdav1d"]),
        ("AV1 HW (NVDEC)", ["-hwaccel", "cuda", "-hwaccel_output_format", "cuda"]),
    ],
}


def benchmark_decode(path: str, family: str, nb_frames: int, duration: float, repetitions: int = 3,
                     loops: int = 5) -> list:
    """
    Executa o teste de decodificação e mede FPS, tempo e consumo de CPU/GPU.
    loops: o vídeo é decodificado N vezes seguidas (-stream_loop) para que a inicialização do
    FFmpeg/CUDA não domine a medição de clipes curtos. Quadros no NVDEC ficam na GPU
    (-hwaccel_output_format cuda), como num player real, sem cópia de volta para a RAM.
    """
    rows = []
    nb_frames, duration = nb_frames * loops, duration * loops
    for label, args in DECODERS.get(family, []):
        cmd = ["ffmpeg", "-v", "error", *args, "-stream_loop", str(loops - 1), "-i", path, "-f", "null", "-"]
        log_command(cmd, f"decode {label}")
        times, cpu, gpu, gpu3d = [], [], [], []
        failed = None
        for _ in range(max(1, repetitions)):
            rc, stderr, elapsed, res = run_monitored(cmd)
            if rc != 0:
                failed = stderr.strip().splitlines()[-1] if stderr.strip() else "erro na decodificação"
                break
            times.append(elapsed)
            cpu.append(res.get("cpu_util_pct", 0.0))
            gpu.append(res.get("gpu_dec_util_pct", 0.0))  # motor NVDEC
            gpu3d.append(res.get("gpu_util_pct", 0.0))

        if failed:
            rows.append({"decoder": label, "error": failed})
            continue

        t_mean, t_std = mean_std(times)
        rows.append({
            "decoder": label,
            "file": path,
            "loops": loops,
            "decode_time_s": t_mean,
            "decode_time_std_s": t_std,
            "decode_fps": nb_frames / t_mean if t_mean > 0 else 0.0,
            "decode_rtf": duration / t_mean if t_mean > 0 else 0.0,
            "cpu_util_pct": sum(cpu) / len(cpu) if cpu else 0.0,
            "gpu_util_pct": sum(gpu) / len(gpu) if gpu else 0.0,  # utilização do NVDEC
            "gpu_3d_util_pct": sum(gpu3d) / len(gpu3d) if gpu3d else 0.0,
        })
    return rows
