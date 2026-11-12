"""
Geração de sequências sintéticas em Y4M sem perdas, usadas apenas no teste rápido (--quick-test)
para validar o ambiente. Não fazem parte dos resultados do TCC.
"""
import os
import subprocess

from .utils import log_command


def generate_synthetic_samples(
    samples_dir: str = "samples",
    resolution: str = "1920x1080",
    fps: int = 60,
    duration: int = 5
) -> dict:
    """
    Gera sequências sintéticas Y4M calibradas (sem compressão):
    1. Amostra 1 (Baixo Movimento): Gradientes suaves com movimento lento (Baixo SI, Baixo TI).
    2. Amostra 2 (Médio Movimento): Formas geométricas e contadores em movimento regular (Médio SI, Médio TI).
    3. Amostra 3 (Alto Movimento): Dinâmica caótica de alta frequência e partículas (Alto SI, Alto TI).
    4. Amostra 4 (Textura/Grão): Ruído de alta frequência espacial estático/dinâmico.
    """
    os.makedirs(samples_dir, exist_ok=True)
    w, h = resolution.split("x")

    samples = {
        "Amostra 1 (Baixo Mov.)": {
            "path": os.path.join(samples_dir, "amostra1_baixo_mov.y4m"),
            "filter": f"testsrc=size={w}x{h}:rate={fps}",
            "classificacao": "Baixo SI / Baixo TI (Vídeo Estático / Paisagem)"
        },
        "Amostra 2 (Médio Mov.)": {
            "path": os.path.join(samples_dir, "amostra2_medio_mov.y4m"),
            "filter": f"testsrc2=size={w}x{h}:rate={fps}",
            "classificacao": "Médio SI / Médio TI (Movimento Moderado)"
        },
        "Amostra 3 (Alto Mov.)": {
            "path": os.path.join(samples_dir, "amostra3_alto_mov.y4m"),
            "filter": f"cellauto=s={w}x{h}:r={fps}:rule=30",
            "classificacao": "Alto SI / Alto TI (Ação Dinâmica / Partículas)"
        },
        "Amostra 4 (Textura/Grão)": {
            "path": os.path.join(samples_dir, "amostra4_textura_grao.y4m"),
            "filter": f"nullsrc=size={w}x{h}:rate={fps},noise=alls=80:allf=t+u",
            "classificacao": "Textura fina / ruído de película"
        }
    }

    for name, s_info in samples.items():
        out_p = s_info["path"]
        if os.path.exists(out_p):
            continue

        print(f"Gerando sequência sintética bruta Y4M: {name} ({resolution} @ {fps}fps, {duration}s)...")
        cmd = [
            "ffmpeg", "-y", "-v", "error",
            "-f", "lavfi", "-i", s_info["filter"],
            "-t", str(duration),
            "-c:v", "rawvideo",
            "-pix_fmt", "yuv420p",
            out_p
        ]
        log_command(cmd, f"generate_synthetic {name}")
        subprocess.check_call(cmd)

    return samples
