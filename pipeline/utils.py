"""
Utilitários de integridade e reprodutibilidade:
- Log estruturado de cada invocação do FFmpeg (comandos_executados.jsonl).
- Cálculo de hash SHA-256 de cada sequência de entrada.
- Verificação de fonte sem perdas (lossless check).
- Extração de tamanho exato de pacotes de stream (ffprobe) excluindo container.
"""
import hashlib
import json
import os
import subprocess
import time

LOSSLESS_CODECS = {"rawvideo", "ffv1", "huffyuv", "utvideo", "wrapped_avframe"}

_command_log_path = None


def set_command_log(path: str):
    global _command_log_path
    _command_log_path = path
    os.makedirs(os.path.dirname(path), exist_ok=True)


def log_command(cmd: list, context: str = ""):
    """Registra cada comando FFmpeg executado no arquivo de log do TCC."""
    if not _command_log_path:
        return
    with open(_command_log_path, "a", encoding="utf-8") as f:
        entry = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "context": context,
            "cmd": " ".join(f'"{c}"' if " " in str(c) else str(c) for c in cmd)
        }
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def sha256_file(path: str, chunk: int = 8 * 1024 * 1024) -> str:
    """Calcula o hash SHA-256 de um arquivo."""
    if not os.path.exists(path):
        return "N/A"
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while block := f.read(chunk):
            h.update(block)
    return h.hexdigest()


def probe_source_codec(path: str) -> str:
    """Retorna o codec do primeiro stream de vídeo."""
    try:
        out = subprocess.check_output(
            ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=codec_name",
             "-of", "default=nw=1:nk=1", path], text=True
        )
        return out.strip().lower()
    except Exception:
        return "desconhecido"


def is_lossless_source(path: str) -> bool:
    """Verifica se o vídeo de entrada é um formato não comprimido ou sem perdas."""
    return probe_source_codec(path) in LOSSLESS_CODECS


def stream_size_bytes(path: str) -> int:
    """Retorna o tamanho em bytes estritamente dos pacotes de vídeo (sem container)."""
    try:
        out = subprocess.check_output(
            ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "packet=size",
             "-of", "csv=p=0", path], text=True
        )
        return sum(int(x) for x in out.split() if x.strip().isdigit())
    except Exception:
        return os.path.getsize(path) if os.path.exists(path) else 0


def mean_std(values: list) -> tuple:
    """Retorna a média e desvio padrão amostral."""
    if not values:
        return 0.0, 0.0
    m = sum(values) / len(values)
    if len(values) < 2:
        return m, 0.0
    var = sum((v - m) ** 2 for v in values) / (len(values) - 1)
    return m, var ** 0.5
