"""
Módulo de cálculo de Informação Espacial (SI) e Temporal (TI) conforme a recomendação ITU-T P.910.
Preenche a Tabela 2 e gera os dados do Gráfico 5 (Diagrama de Dispersão SI x TI).
"""
import subprocess
import json
import os
import numpy as np
from scipy import ndimage

def get_video_metadata(video_path: str) -> dict:
    """Extrai resolução, taxa de quadros e duração do vídeo usando ffprobe."""
    cmd = [
        "ffprobe", "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=width,height,r_frame_rate,nb_frames,duration:format=duration",
        "-of", "json", video_path
    ]
    res = subprocess.check_output(cmd, text=True)
    data = json.loads(res)
    stream = data.get("streams", [{}])[0]
    fmt = data.get("format", {})
    
    width = int(stream.get("width", 1920))
    height = int(stream.get("height", 1080))
    
    fps_str = stream.get("r_frame_rate", "60/1")
    if "/" in fps_str:
        num, den = fps_str.split("/")
        fps = float(num) / float(den) if float(den) > 0 else 60.0
    else:
        fps = float(fps_str)
        
    duration = float(fmt.get("duration") or stream.get("duration") or 0.0)
    nb_frames = int(stream.get("nb_frames") or round(duration * fps) or 0)
    
    return {
        "width": width,
        "height": height,
        "fps": fps,
        "duration": duration,
        "nb_frames": nb_frames
    }

def calculate_siti(video_path: str, max_frames: int = None) -> dict:
    """
    Calcula os índices SI e TI de acordo com a recomendação ITU-T P.910:
    - SI = max_t ( std_space( Sobel( Y_t ) ) )
    - TI = max_t ( std_space( Y_t - Y_{t-1} ) )
    """
    meta = get_video_metadata(video_path)
    width, height = meta["width"], meta["height"]
    frame_size = width * height
    
    cmd = [
        "ffmpeg", "-v", "error",
        "-i", video_path,
        "-f", "rawvideo",
        "-pix_fmt", "gray",
        "pipe:1"
    ]
    
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    
    si_values = []
    ti_values = []
    prev_frame = None
    frame_count = 0
    
    while True:
        if max_frames and frame_count >= max_frames:
            break
        buf = proc.stdout.read(frame_size)
        if not buf or len(buf) < frame_size:
            break
        
        frame = np.frombuffer(buf, dtype=np.uint8).astype(np.float32).reshape((height, width))
        
        # Filtro de Sobel horizontal e vertical (ITU-T P.910)
        sh = ndimage.sobel(frame, axis=1)
        sv = ndimage.sobel(frame, axis=0)
        mag = np.hypot(sh, sv)
        si_values.append(float(np.std(mag)))
        
        # Diferença temporal de luminância
        if prev_frame is not None:
            diff = frame - prev_frame
            ti_values.append(float(np.std(diff)))
            
        prev_frame = frame
        frame_count += 1
        
    proc.stdout.close()
    proc.kill()
    proc.wait()
    
    if not si_values:
        si_max, si_mean = 0.0, 0.0
    else:
        si_max = float(np.max(si_values))
        si_mean = float(np.mean(si_values))
        
    if not ti_values:
        ti_max, ti_mean = 0.0, 0.0
    else:
        ti_max = float(np.max(ti_values))
        ti_mean = float(np.mean(ti_values))
        
    # Classificação ITU-T aproximada
    if si_max < 60 and ti_max < 15:
        classificacao = "Baixo SI / Baixo TI (Vídeo Estático / Paisagem)"
    elif si_max >= 100 or ti_max >= 30:
        classificacao = "Alto SI / Alto TI (Ação Dinâmica / Partículas)"
    else:
        classificacao = "Médio SI / Médio TI (Movimento Moderado)"
        
    return {
        "metadata": meta,
        "si_max": si_max,
        "si_mean": si_mean,
        "ti_max": ti_max,
        "ti_mean": ti_mean,
        "si_series": si_values,
        "ti_series": ti_values,
        "classificacao": classificacao
    }

def format_table_2_markdown(samples_results: list) -> str:
    """Gera a Tabela 2 em Markdown com os dados calculados de cada amostra."""
    lines = [
        "### Tabela 2 — Caracterização Espaço-Temporal dos Vídeos de Amostra (ITU-T P.910)",
        "",
        "| Identificador do Vídeo | Resolução / FPS | Duração (s) | Índice SI (Espacial) | Índice TI (Temporal) | Classificação de Complexidade |",
        "| :---- | :---- | :---- | :---- | :---- | :---- |"
    ]
    for s in samples_results:
        meta = s["metadata"]
        res_fps = f"{meta['width']}×{meta['height']} @ {int(round(meta['fps']))}"
        dur = f"{meta['duration']:.1f} s"
        si_str = f"{s['si_max']:.2f}"
        ti_str = f"{s['ti_max']:.2f}"
        name = s.get("nome", "Amostra")
        classif = s.get("classificacao_override", s["classificacao"])
        lines.append(f"| **{name}** | {res_fps} | {dur} | {si_str} | {ti_str} | {classif} |")
    lines.append("")
    return "\n".join(lines)
