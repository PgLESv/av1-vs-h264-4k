"""
Recortes visuais ampliados lado a lado.
Compara a mesma região e mesmo quadro entre a referência sem perdas e os vídeos codificados.
A região é detectada automaticamente maximizando a energia de gradiente de Sobel (maior nível de detalhe).
"""
import os
import shutil
import subprocess

import matplotlib.pyplot as plt
import numpy as np
from scipy import ndimage

from .utils import log_command


def _read_gray_frame(path: str, frame_idx: int, width: int, height: int) -> np.ndarray:
    cmd = [
        "ffmpeg", "-v", "error", "-i", path,
        "-vf", f"select=eq(n\\,{frame_idx})",
        "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "gray", "pipe:1"
    ]
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    buf = proc.stdout
    if len(buf) < width * height:
        raise RuntimeError(f"Não foi possível ler o quadro {frame_idx} de {path}")
    return np.frombuffer(buf[: width * height], dtype=np.uint8).reshape(height, width).astype(np.float32)


def auto_crop_region(reference: str, frame_idx: int, width: int, height: int, cw: int, ch: int) -> tuple:
    """Localiza a coordenada (x, y) de dimensão cw x ch com maior variância e bordas."""
    try:
        frame = _read_gray_frame(reference, frame_idx, width, height)
        sh = ndimage.sobel(frame, axis=1)
        sv = ndimage.sobel(frame, axis=0)
        mag = np.hypot(sh, sv)
        integral = mag.cumsum(0).cumsum(1)

        best_score = -1.0
        best_xy = (0, 0)
        step_y = max(ch // 4, 1)
        step_x = max(cw // 4, 1)

        for y in range(0, height - ch + 1, step_y):
            for x in range(0, width - cw + 1, step_x):
                y2, x2 = y + ch - 1, x + cw - 1
                s = integral[y2, x2]
                if y > 0:
                    s -= integral[y - 1, x2]
                if x > 0:
                    s -= integral[y2, x - 1]
                if x > 0 and y > 0:
                    s += integral[y - 1, x - 1]
                if s > best_score:
                    best_score = s
                    best_xy = (x, y)
        return best_xy
    except Exception:
        # Fallback: recorte central
        return (max(0, (width - cw) // 2), max(0, (height - ch) // 2))


def _extract_crop_png(path: str, frame_idx: int, x: int, y: int, cw: int, ch: int, scale: int, out_png: str):
    vf = f"select=eq(n\\,{frame_idx}),crop={cw}:{ch}:{x}:{y},scale=iw*{scale}:ih*{scale}:flags=neighbor"
    cmd = [
        "ffmpeg", "-y", "-v", "error", "-i", path,
        "-vf", vf, "-frames:v", "1",
        "-pix_fmt", "rgb24", "-update", "1", out_png
    ]
    log_command(cmd, "crop_extract")
    subprocess.run(cmd, check=True)


def make_crop_comparison(reference: str, items: list, frame_idx: int, meta: dict, crop_cfg: dict,
                         out_dir: str, base_name: str, title: str, region: tuple = None) -> str:
    """
    Gera imagem lado a lado comparando a referência sem perdas e os codificados.
    items: [(rótulo, caminho_arquivo)]
    """
    os.makedirs(out_dir, exist_ok=True)
    w, h = meta["width"], meta["height"]
    cw = min(crop_cfg.get("width", 480), w)
    ch = min(crop_cfg.get("height", 270), h)
    scale = crop_cfg.get("upscale", 2)

    x, y = region or auto_crop_region(reference, frame_idx, w, h, cw, ch)

    panels = [("Referência (Sem Perdas)", reference)] + list(items)
    tmp_dir = os.path.join(out_dir, "_tmp")
    os.makedirs(tmp_dir, exist_ok=True)

    images = []
    for i, (label, p) in enumerate(panels):
        out_png = os.path.join(tmp_dir, f"{base_name}_{i}.png")
        try:
            _extract_crop_png(p, frame_idx, x, y, cw, ch, scale, out_png)
            images.append((label, plt.imread(out_png)))
        except Exception:
            pass

    if not images:
        return ""

    cols = min(3, len(images))
    rows = (len(images) + cols - 1) // cols
    fig, axes = plt.subplots(rows, cols, figsize=(5.2 * cols, 3.4 * rows))
    axes = np.atleast_1d(axes).ravel()

    for ax in axes:
        ax.axis("off")

    for ax, (label, img) in zip(axes, images):
        ax.imshow(img, interpolation="nearest")
        ax.set_title(label, fontsize=10.5, fontweight="bold")

    fig.suptitle(f"{title}\nQuadro {frame_idx}, Região {cw}×{ch} em ({x},{y}), Ampliação {scale}× (Pixel Peeping)",
                 fontsize=11.5)

    out_base = os.path.join(out_dir, base_name)
    fig.savefig(out_base + ".png", dpi=300, bbox_inches="tight")
    fig.savefig(out_base + ".pdf", bbox_inches="tight")
    plt.close(fig)
    shutil.rmtree(tmp_dir, ignore_errors=True)
    return out_base + ".png"
