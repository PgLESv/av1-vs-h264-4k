"""
Geração dos gráficos em PNG (300 DPI) e PDF.
Suporta todos os codificadores (x264, x264 veryslow, h264_nvenc, svt-av1, nvenc-av1),
barras de erro estatísticas (média ± desvio padrão), curvas R-D e benchmark de decodificação.
"""
import os
import matplotlib.pyplot as plt
import numpy as np
from scipy.interpolate import pchip_interpolate
from scipy.ndimage import uniform_filter1d

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Segoe UI", "DejaVu Sans", "Helvetica", "Arial"],
    "font.size": 11,
    "axes.titlesize": 13,
    "axes.titleweight": "bold",
    "axes.labelsize": 11,
    "axes.labelweight": "semibold",
    "xtick.labelsize": 10,
    "ytick.labelsize": 10,
    "legend.fontsize": 9.5,
    "figure.titlesize": 14,
    "lines.linewidth": 2.0,
    "lines.markersize": 6.5,
    "figure.autolayout": True
})

COLOR_MAP = {
    "h264": "#E63946",            # Vermelho
    "h264-veryslow": "#9B2226",   # Vermelho escuro/bordeaux
    "h264-nvenc": "#F4A261",      # Laranja quente
    "svt-av1": "#1D3557",         # Azul escuro
    "nvenc-av1": "#2A9D8F",       # Verde-azulado
}

LABEL_MAP = {
    "h264": "H.264 medium (CPU)",
    "h264-veryslow": "H.264 veryslow (CPU)",
    "h264-nvenc": "H.264 NVENC p7 (GPU)",
    "svt-av1": "AV1 SVT-AV1 P6 (CPU)",
    "nvenc-av1": "AV1 NVENC p7 (GPU)",
}

MARKER_MAP = {
    "h264": "o",
    "h264-veryslow": "D",
    "h264-nvenc": "v",
    "svt-av1": "s",
    "nvenc-av1": "^",
}


def _sanitize_name(name: str) -> str:
    for ch in ["/", "\\", ":", "*", "?", '"', "<", ">", "|", "(", ")", "."]:
        name = name.replace(ch, "_")
    return name.lower().replace(" ", "_").strip("_")


def save_plot(fig, filename_base: str, output_dir: str, pad_inches: float = 0.03):
    os.makedirs(output_dir, exist_ok=True)
    png_path = os.path.join(output_dir, f"{filename_base}.png")
    pdf_path = os.path.join(output_dir, f"{filename_base}.pdf")
    with plt.rc_context({"figure.autolayout": False}):
        fig.savefig(png_path, dpi=300, bbox_inches="tight", pad_inches=pad_inches)
        fig.savefig(pdf_path, bbox_inches="tight", pad_inches=pad_inches)
    plt.close(fig)


def plot_rd_curve_vmaf(sample_data: dict, sample_name: str, output_dir: str, metric_key: str = "vmaf_mean", title_metric: str = "VMAF"):
    """
    Gráfico 1: Curvas de Taxa-Distorção (R-D Curves VMAF vs. Bitrate)
    """
    has_data = any(len(items) > 0 for items in sample_data.values()) if sample_data else False
    if not has_data:
        return

    fig, ax = plt.subplots(figsize=(8.5, 5.5))

    for codec, items in sample_data.items():
        if not items:
            continue
        rates = [it["real_bitrate_kbps"] / 1000.0 for it in items]  # em Mbps
        dists = [it.get(metric_key, 0.0) for it in items]
        pts = [(r, d) for r, d in zip(rates, dists) if np.isfinite(d)]
        if not pts:
            continue
        rates, dists = map(list, zip(*pts))

        idx = np.argsort(rates)
        r_sorted = np.array(rates)[idx]
        d_sorted = np.array(dists)[idx]

        color = COLOR_MAP.get(codec, "#444444")
        label = LABEL_MAP.get(codec, codec)
        marker = MARKER_MAP.get(codec, "o")

        ax.plot(r_sorted, d_sorted, marker=marker, color=color, label=label, linestyle="None", zorder=4)

        if len(r_sorted) >= 3:
            xs = np.linspace(r_sorted.min(), r_sorted.max(), 100)
            try:
                ys = pchip_interpolate(r_sorted, d_sorted, xs)
                ax.plot(xs, ys, color=color, alpha=0.85, zorder=3)
            except Exception:
                ax.plot(r_sorted, d_sorted, color=color, alpha=0.85, zorder=3)
        elif len(r_sorted) == 2:
            ax.plot(r_sorted, d_sorted, color=color, alpha=0.85, zorder=3)

    # Título removido no topo para normas ABNT (deve constar na legenda/texto do documento)
    ax.set_xlabel("Taxa de Bits Medida do Stream (Mbps)")
    ax.set_ylabel(f"Pontuação {title_metric}")
    ax.grid(True, linestyle="--", alpha=0.45)
    ax.legend(loc="lower right", framealpha=0.92, facecolor="#F8F9FA", edgecolor="#D3D3D3")

    fig.tight_layout()
    safe_name = _sanitize_name(sample_name)
    save_plot(fig, f"grafico1_rd_{title_metric.lower()}_{safe_name}", output_dir, pad_inches=0.03)


def plot_rd_curve_psnr(sample_data: dict, sample_name: str, output_dir: str):
    """
    Gráfico 2: Curvas de Taxa-Distorção Secundárias (PSNR-YUV vs. Bitrate)
    """
    has_data = any(len(items) > 0 for items in sample_data.values()) if sample_data else False
    if not has_data:
        return

    fig, ax = plt.subplots(figsize=(8.5, 5.5))

    for codec, items in sample_data.items():
        if not items:
            continue
        rates = [it["real_bitrate_kbps"] / 1000.0 for it in items]  # em Mbps
        psnrs = [it.get("psnr_yuv_mean", it.get("psnr_mean", 0.0)) for it in items]
        pts = [(r, d) for r, d in zip(rates, psnrs) if np.isfinite(d)]
        if not pts:
            continue
        rates, psnrs = map(list, zip(*pts))

        idx = np.argsort(rates)
        r_sorted = np.array(rates)[idx]
        p_sorted = np.array(psnrs)[idx]

        color = COLOR_MAP.get(codec, "#444444")
        label = LABEL_MAP.get(codec, codec)
        marker = MARKER_MAP.get(codec, "o")

        ax.plot(r_sorted, p_sorted, marker=marker, color=color, label=label, linestyle="None", zorder=4)

        if len(r_sorted) >= 3:
            xs = np.linspace(r_sorted.min(), r_sorted.max(), 100)
            try:
                ys = pchip_interpolate(r_sorted, p_sorted, xs)
                ax.plot(xs, ys, color=color, alpha=0.85, zorder=3)
            except Exception:
                ax.plot(r_sorted, p_sorted, color=color, alpha=0.85, zorder=3)
        elif len(r_sorted) == 2:
            ax.plot(r_sorted, p_sorted, color=color, alpha=0.85, zorder=3)

    # Título removido no topo para normas ABNT (deve constar na legenda/texto do documento)
    ax.set_xlabel("Taxa de Bits Medida do Stream (Mbps)")
    ax.set_ylabel("PSNR-YUV Médio (dB)")
    ax.grid(True, linestyle="--", alpha=0.45)
    ax.legend(loc="lower right", framealpha=0.92, facecolor="#F8F9FA", edgecolor="#D3D3D3")

    fig.tight_layout()
    safe_name = _sanitize_name(sample_name)
    save_plot(fig, f"grafico2_rd_psnr_{safe_name}", output_dir, pad_inches=0.03)


def plot_rd_curve_xpsnr(sample_data: dict, sample_name: str, output_dir: str):
    """Curvas de Taxa-Distorção XPSNR-YUV vs. Bitrate."""
    plot_rd_curve_vmaf(sample_data, sample_name, output_dir, metric_key="xpsnr_yuv_mean", title_metric="XPSNR")


def plot_rd_curve_ssimulacra2(sample_data: dict, sample_name: str, output_dir: str):
    """Curvas de Taxa-Distorção SSIMULACRA2 vs. Bitrate."""
    plot_rd_curve_vmaf(sample_data, sample_name, output_dir, metric_key="ssimulacra2_mean", title_metric="SSIMULACRA2")


def plot_rd_curve_butteraugli(sample_data: dict, sample_name: str, output_dir: str):
    """Curvas de Taxa-Distorção Butteraugli (2-Norm) vs. Bitrate."""
    plot_rd_curve_vmaf(sample_data, sample_name, output_dir, metric_key="butteraugli_2norm", title_metric="Butteraugli")


def plot_rd_curve_cvvdp(sample_data: dict, sample_name: str, output_dir: str):
    """Curvas de Taxa-Distorção CVVDP vs. Bitrate."""
    plot_rd_curve_vmaf(sample_data, sample_name, output_dir, metric_key="cvvdp_score", title_metric="CVVDP")


def plot_encoding_fps(comparison_data: dict, output_dir: str):
    """
    Gráfico 3: Desempenho de Codificação e Rendimento (FPS Médio com barras de erro std dev)
    """
    samples = list(comparison_data.keys())
    if not samples:
        return

    # Determinar codecs presentes
    codecs = []
    for s in samples:
        for c in comparison_data[s].keys():
            if c not in codecs:
                codecs.append(c)

    x = np.arange(len(samples))
    n_codecs = max(1, len(codecs))
    bar_width = min(0.18, 0.8 / n_codecs)

    fig, ax = plt.subplots(figsize=(max(8.5, 2.2 * len(samples)), 6.0))

    for i, codec in enumerate(codecs):
        fps_values = []
        fps_stds = []
        for s in samples:
            info = comparison_data[s].get(codec, {})
            fps_values.append(info.get("avg_fps", 0.0))
            fps_stds.append(info.get("avg_fps_std", 0.0))

        color = COLOR_MAP.get(codec, "#444444")
        label = LABEL_MAP.get(codec, codec)
        offset = (i - (n_codecs - 1) / 2) * bar_width

        rects = ax.bar(x + offset, fps_values, bar_width, yerr=fps_stds, capsize=3,
                       label=label, color=color, alpha=0.9, edgecolor="#222222", linewidth=0.8)

        for rect in rects:
            height = rect.get_height()
            if height > 0:
                ax.annotate(f"{height:.1f}",
                            xy=(rect.get_x() + rect.get_width() / 2, height),
                            xytext=(0, 4),
                            textcoords="offset points",
                            ha="center", va="bottom", fontsize=8.0, fontweight="bold")

    ax.set_title("Gráfico 3: Rendimento de Codificação — Velocidade Média (FPS ± desvio padrão)")
    ax.set_xlabel("Sequência de Teste")
    ax.set_ylabel("Taxa de Processamento (FPS de Codificação)")
    ax.set_xticks(x)
    ax.set_xticklabels(samples, rotation=10 if len(samples) > 3 else 0)
    ax.grid(True, linestyle="--", alpha=0.35, axis="y")
    ax.legend(loc="upper right", framealpha=0.92, facecolor="#F8F9FA", edgecolor="#D3D3D3")

    save_plot(fig, "grafico3_fps_rendimento", output_dir)


def plot_frame_vmaf_stability(frame_series_dict: dict, sample_name: str, output_dir: str):
    """
    Gráfico 4: Estabilidade Visual Quadro a Quadro (Frame-by-Frame VMAF Score)
    Gera gráfico composto com:
    1. Painel principal: Tendência com Média Móvel (elimina oscilação do GOP) + sinal bruto tênue
    2. Painel lateral: Boxplot com a distribuição estatística de estabilidade (mediana, quartis e quedas)
    Também salva versão facetada em subplots individuais para inspeção detalhada isolada.
    """
    valid_items = {k: v for k, v in frame_series_dict.items() if v and len(v) > 0}
    if not valid_items:
        return

    all_scores = [s for scores in valid_items.values() for s in scores]
    all_min = min(all_scores)
    all_max = max(all_scores)
    y_min = max(0.0, np.floor(all_min - 1.5))
    y_max = min(100.5, np.ceil(all_max + 1.2))

    # --- 1. Gráfico Composto: Curvas Suavizadas + Distribuição Marginal ---
    with plt.rc_context({"figure.autolayout": False}):
        fig = plt.figure(figsize=(13.5, 6.0))
        gs = fig.add_gridspec(1, 2, width_ratios=[3.6, 1.2], wspace=0.07)
        ax1 = fig.add_subplot(gs[0])
        ax2 = fig.add_subplot(gs[1], sharey=ax1)

    max_frames = 0
    box_data = []
    box_codecs = []

    for codec, scores in valid_items.items():
        arr = np.array(scores, dtype=float)
        frames = np.arange(len(arr))
        max_frames = max(max_frames, len(arr))
        color = COLOR_MAP.get(codec, "#444444")
        label = LABEL_MAP.get(codec, codec)

        win = min(15, max(3, len(arr) // 10))
        smoothed = uniform_filter1d(arr, size=win, mode="nearest")
        mean_val = float(np.mean(arr))
        p1_val = float(np.percentile(arr, 1))
        std_val = float(np.std(arr))

        # Sinal bruto translúcido em segundo plano (preserva dados de GOP sem poluir)
        ax1.plot(frames, arr, color=color, alpha=0.18, linewidth=0.75, zorder=2)
        # Tendência suavizada em primeiro plano
        ax1.plot(frames, smoothed, color=color, linewidth=2.3, alpha=0.95, zorder=4,
                 label=f"{label:22s} | Média: {mean_val:4.1f} | 1% Pior: {p1_val:4.1f} | σ: {std_val:4.2f}")

        box_data.append(arr)
        box_codecs.append(codec)

    ax1.set_title(f"Gráfico 4: Estabilidade Temporal Quadro a Quadro (VMAF) — {sample_name}", fontsize=12.5, fontweight="bold", pad=18)
    ax1.text(0.005, 1.02, "Linhas sólidas: Tendência (Média móvel centrada N=15)  |  Linhas translúcidas: Sinal bruto quadro a quadro (efeito GOP)",
             transform=ax1.transAxes, fontsize=8.6, color="#555555", fontstyle="italic")
    ax1.set_xlabel("Número Sequencial do Quadro (Frame)", fontsize=10.5, fontweight="bold")
    ax1.set_ylabel("Pontuação VMAF", fontsize=10.5, fontweight="bold")
    ax1.set_ylim(y_min, y_max)
    ax1.set_xlim(0, max_frames - 1)
    ax1.grid(True, linestyle="--", alpha=0.45, zorder=1)
    ax1.legend(loc="lower right", framealpha=0.94, facecolor="#F8F9FA", edgecolor="#D3D3D3",
               fontsize=8.5, prop={"family": "monospace", "size": 8.3})

    # Boxplot lateral com a distribuição e cauda de quedas
    bplot = ax2.boxplot(box_data, patch_artist=True, widths=0.55,
                        showmeans=True, meanline=True,
                        medianprops=dict(color="#111111", linewidth=1.5),
                        meanprops=dict(color="#D90429", linewidth=1.5, linestyle="--"),
                        flierprops=dict(marker="o", markersize=3, alpha=0.35, markerfacecolor="#555555", markeredgecolor="none"))

    for patch, c in zip(bplot["boxes"], box_codecs):
        col = COLOR_MAP.get(c, "#444444")
        patch.set_facecolor(col)
        patch.set_alpha(0.60)
        patch.set_edgecolor(col)
        patch.set_linewidth(1.3)

    short_labels = [LABEL_MAP.get(c, c).split(" (")[0].replace(" ", "\n") for c in box_codecs]
    ax2.set_xticklabels(short_labels, fontsize=8.0, fontweight="bold")
    ax2.set_title("Distribuição / Quedas", fontsize=11, fontweight="bold", pad=18)
    ax2.text(0.5, 1.02, "Traço preto: Mediana | Vermelho: Média", transform=ax2.transAxes,
             fontsize=7.8, color="#555555", ha="center", va="bottom", fontstyle="italic")
    ax2.grid(True, linestyle="--", alpha=0.45, axis="y")
    plt.setp(ax2.get_yticklabels(), visible=False)

    safe_name = _sanitize_name(sample_name)
    save_plot(fig, f"grafico4_vmaf_temporal_{safe_name}", output_dir)

    # --- 2. Gráfico Detalhado Facetado (Subplots Individuais por Codificador) ---
    fig_f, axes = plt.subplots(len(box_codecs), 1, figsize=(11.5, 2.0 * len(box_codecs) + 1.2), sharex=True, sharey=True)
    if len(box_codecs) == 1:
        axes = [axes]

    for i, c in enumerate(box_codecs):
        ax_i = axes[i]
        arr = np.array(valid_items[c], dtype=float)
        frames = np.arange(len(arr))
        color = COLOR_MAP.get(c, "#444444")
        label = LABEL_MAP.get(c, c)

        win = min(15, max(3, len(arr) // 10))
        smoothed = uniform_filter1d(arr, size=win, mode="nearest")
        mean_val = float(np.mean(arr))
        p1_val = float(np.percentile(arr, 1))
        std_val = float(np.std(arr))

        ax_i.plot(frames, arr, color=color, alpha=0.30, linewidth=0.85, label="Sinal bruto (quadros)")
        ax_i.plot(frames, smoothed, color=color, linewidth=2.0, label="Média móvel (N=15)")
        ax_i.axhline(mean_val, color="#222222", linestyle="--", linewidth=1.0, alpha=0.7, label=f"Média ({mean_val:.1f})")
        ax_i.axhline(p1_val, color="#D90429", linestyle=":", linewidth=1.2, alpha=0.85, label=f"Pior 1% ({p1_val:.1f})")

        ax_i.set_ylabel("VMAF", fontsize=9.0, fontweight="bold")
        ax_i.set_ylim(y_min, y_max)
        ax_i.grid(True, linestyle="--", alpha=0.4)
        ax_i.text(0.015, 0.82, f"{label}  |  Média = {mean_val:.2f}  |  Pior 1% = {p1_val:.2f}  |  σ = {std_val:.2f}",
                  transform=ax_i.transAxes, fontsize=9.2, fontweight="bold", color=color,
                  bbox=dict(boxstyle="round,pad=0.25", facecolor="#FFFFFF", edgecolor="#CCCCCC", alpha=0.92))
        if i == 0:
            ax_i.legend(loc="upper right", ncol=4, fontsize=8.0, framealpha=0.92)

    axes[-1].set_xlabel("Número Sequencial do Quadro (Frame)", fontsize=10.5, fontweight="bold")
    axes[0].set_title(f"Estabilidade Temporal por Codificador — {sample_name}", fontsize=12, fontweight="bold", pad=10)
    save_plot(fig_f, f"grafico4_vmaf_temporal_detalhado_{safe_name}", output_dir)


def plot_siti_scatter(samples_siti: list, output_dir: str):
    """
    Gráfico 5: Diagrama de Dispersão Espaço-Temporal (Espaço SI x TI)
    """
    fig, ax = plt.subplots(figsize=(8.5, 6))
    colors = ["#264653", "#E76F51", "#2A9D8F", "#F4A261", "#E63946", "#3D5A80"]

    max_si = max((s["si_max"] for s in samples_siti), default=25.0)
    max_ti = max((s["ti_max"] for s in samples_siti), default=45.0)

    for i, s in enumerate(samples_siti):
        name = s.get("nome", f"Amostra {i+1}")
        si = s["si_max"]
        ti = s["ti_max"]
        c = colors[i % len(colors)]

        ax.scatter(ti, si, s=170, color=c, edgecolors="black", linewidth=1.5, zorder=5,
                   label=f"{name} (SI={si:.1f}, TI={ti:.1f})")
        ax.annotate(name, (ti, si), xytext=(8, 5), textcoords="offset points", fontweight="bold", fontsize=9.5)

    # Limites dinâmicos adaptados aos valores reais com folga proporcional
    ax.set_xlim(0, max(max_ti * 1.25, 20.0))
    ax.set_ylim(0, max(max_si * 1.30, 20.0))

    # Linhas de referência para categorização de quadrantes
    ax.axhline(max_si / 2.0, color="gray", linestyle=":", alpha=0.55)
    ax.axvline(max_ti / 2.0, color="gray", linestyle=":", alpha=0.55)

    ax.set_title("Gráfico 5: Diagrama de Dispersão Espaço-Temporal (Espaço SI × TI — ITU-T P.910)")
    ax.set_xlabel("Índice de Informação Temporal (TI)")
    ax.set_ylabel("Índice de Informação Espacial (SI)")
    ax.grid(True, linestyle="--", alpha=0.45)
    ax.legend(loc="upper right", framealpha=0.92, facecolor="#F8F9FA", edgecolor="#D3D3D3")

    save_plot(fig, "grafico5_dispersao_siti", output_dir)


def plot_decoding_benchmark(decode_rows: list, output_dir: str):
    """
    Gráfico 6: Benchmark de Decodificação (FPS e Utilização de CPU/GPU no espectador)
    """
    if not decode_rows:
        return
    labels = [r["decoder"] for r in decode_rows if "decode_fps" in r]
    fps_vals = [r["decode_fps"] for r in decode_rows if "decode_fps" in r]
    cpu_vals = [r.get("cpu_util_pct", 0.0) for r in decode_rows if "decode_fps" in r]

    if not labels:
        return

    x = np.arange(len(labels))
    fig, ax1 = plt.subplots(figsize=(8.5, 5.0))

    color_fps = "#1D3557"
    color_cpu = "#E63946"

    rects = ax1.bar(x - 0.18, fps_vals, 0.35, label="FPS de Decodificação", color=color_fps, edgecolor="#222")
    ax1.set_ylabel("Velocidade de Decodificação (FPS)", color=color_fps, fontweight="bold")
    ax1.tick_params(axis="y", labelcolor=color_fps)

    ax2 = ax1.twinx()
    rects2 = ax2.bar(x + 0.18, cpu_vals, 0.35, label="Utilização da CPU (%)", color=color_cpu, alpha=0.85, edgecolor="#222")
    ax2.set_ylabel("Carga de CPU (%)", color=color_cpu, fontweight="bold")
    ax2.tick_params(axis="y", labelcolor=color_cpu)
    ax2.set_ylim(0, 105)

    ax1.set_xticks(x)
    ax1.set_xticklabels(labels, rotation=12)
    ax1.set_title("Gráfico 6: Desempenho de Decodificação — Software (dav1d) vs. Hardware (NVDEC)")
    ax1.grid(True, linestyle="--", alpha=0.35, axis="y")

    save_plot(fig, "grafico6_decode_benchmark", output_dir)


def plot_economic_breakeven(economics_data: dict, econ_cfg: dict, output_dir: str):
    """
    Gráfico 7: Análise Econômica de Sensibilidade e Ponto de Equilíbrio (Break-Even).
    Custo Mensal Total (Armazenamento + Egress de Rede) vs. Horas de Streaming Transmitidas.
    """
    if not economics_data:
        return

    storage_price = econ_cfg.get("cost_storage_per_gb_month", 0.12)
    egress_price = econ_cfg.get("cost_egress_per_gb", 0.35)
    catalog_h = econ_cfg.get("catalog_hours", 1000.0)

    stream_hours = np.linspace(500, 30000, 300)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14.0, 5.8), gridspec_kw={"width_ratios": [1.4, 1.0]})

    # Subgráfico 1: Curvas de Custo Mensal Total vs. Horas de Streaming
    for codec, data in economics_data.items():
        gb_h = data["gb_per_hour"]
        storage_c = gb_h * catalog_h * storage_price
        monthly_costs = storage_c + (stream_hours * gb_h * egress_price)

        color = COLOR_MAP.get(codec, "#555555")
        label = LABEL_MAP.get(codec, codec)
        ls = "-" if codec in ("h264", "svt-av1", "nvenc-av1") else "--"
        lw = 2.4 if codec in ("h264", "svt-av1") else 1.8

        ax1.plot(stream_hours, monthly_costs, label=label, color=color, linestyle=ls, linewidth=lw)

    ref_hours = econ_cfg.get("monthly_streamed_hours", 5000.0)
    ax1.axvline(ref_hours, color="#666666", linestyle=":", linewidth=1.5, alpha=0.8,
                label=f"Cenário TCC ({ref_hours:.0f} h/mês)")

    ax1.set_title("Custo Mensal Consolidado (Armazenamento + Banda) vs. Audiência", fontsize=11.5, fontweight="bold")
    ax1.set_xlabel("Horas de Vídeo Transmitidas por Mês (Audiência)", fontweight="semibold")
    ax1.set_ylabel("Custo Operacional Mensal (R$/mês)", fontweight="semibold")
    ax1.grid(True, linestyle="--", alpha=0.45)
    ax1.legend(loc="upper left", framealpha=0.92, facecolor="#F8F9FA", edgecolor="#D3D3D3", fontsize=9.0)

    # Subgráfico 2: Ponto de Equilíbrio (Break-Even) em Meses
    codecs_be = [c for c, d in economics_data.items() if d.get("break_even_months") is not None and d.get("break_even_months") > 0]
    if codecs_be:
        be_vals = [economics_data[c]["break_even_months"] for c in codecs_be]
        be_labels = [LABEL_MAP.get(c, c) for c in codecs_be]
        be_colors = [COLOR_MAP.get(c, "#555555") for c in codecs_be]

        bars = ax2.bar(range(len(codecs_be)), be_vals, color=be_colors, edgecolor="#222", width=0.55, alpha=0.9)
        ax2.set_xticks(range(len(codecs_be)))
        ax2.set_xticklabels(be_labels, rotation=15, ha="right", fontsize=9.0)
        ax2.set_ylabel("Tempo para Retorno / Break-Even (Meses a 5.000 h/mês)", fontweight="semibold")
        ax2.set_title("Tempo de Amortização do Custo de Codificação", fontsize=11.5, fontweight="bold")
        ax2.grid(True, linestyle="--", alpha=0.40, axis="y")

        for bar in bars:
            h = bar.get_height()
            ax2.annotate(f"{h:.1f} meses", xy=(bar.get_x() + bar.get_width() / 2, h),
                         xytext=(0, 4), textcoords="offset points", ha="center", va="bottom",
                         fontsize=9.5, fontweight="bold")
    else:
        ax2.axis("off")

    fig.suptitle("Gráfico 7: Viabilidade Econômica e Ponto de Equilíbrio (Iso-Qualidade VMAF ~93)",
                 fontsize=13.0, fontweight="bold")

    save_plot(fig, "grafico7_economia_breakeven", output_dir)
