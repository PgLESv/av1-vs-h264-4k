"""
Geração dos relatórios (Markdown, Excel, CSV e JSON).
Tabelas geradas em output/relatorio_tcc.md (numeração interna do relatório, não a do texto do TCC):
- Tabela 1: Ambiente HW/SW real (incluindo versões de bibliotecas e controladores)
- Tabela 2: Caracterização das amostras (SI/TI, integridade sem perdas, SHA-256)
- Tabela 3: Matriz comparativa com repetições (média ± std), energia, VMAF/NEG, PSNR-YUV, MS-SSIM
- Tabela 4: Síntese Bjøntegaard Delta com verificação de sobreposição e comparações justas (CPU vs CPU, GPU vs GPU)
- Tabela 5: Projeção de armazenamento e tráfego baseada em iso-qualidade (VMAF alvo)
- Tabela 6: Custo de codificação (nuvem e energia) e análise de ponto de equilíbrio (break-even)
- Tabela 7: Desempenho de decodificação no cliente (dav1d vs. NVDEC)
"""
import csv
import json
import os
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

from .hardware import format_table_1_markdown
from .siti import format_table_2_markdown


def format_table_2_enriched_markdown(siti_results: list) -> str:
    lines = [
        "### Tabela 2 — Caracterização Espaço-Temporal dos Vídeos de Amostra (ITU-T P.910)",
        "",
        "| Identificador do Vídeo | Resolução / FPS | Duração (s) | SI Máx | TI Máx | Complexidade | Fonte Sem Perdas? | SHA-256 (primeiros 12 dígitos) |",
        "| :---- | :---- | :---- | :---- | :---- | :---- | :---- | :---- |"
    ]
    for s in siti_results:
        meta = s["metadata"]
        res_fps = f"{meta['width']}×{meta['height']} @ {int(round(meta['fps']))}"
        dur = f"{meta['duration']:.1f} s"
        si_str = f"{s['si_max']:.2f}"
        ti_str = f"{s['ti_max']:.2f}"
        name = s.get("nome", "Amostra")
        classif = (s.get("classificacao_override") or s["classificacao"])
        lossless = "Sim (Y4M/Raw)" if s.get("is_lossless") else "Não (Atenção: Comprimido!)"
        sha = s.get("sha256", "N/A")[:12]
        lines.append(f"| **{name}** | {res_fps} | {dur} | {si_str} | {ti_str} | {classif} | {lossless} | `{sha}` |")
    lines.append("")
    return "\n".join(lines)


def format_table_3_markdown(matrix_rows: list) -> str:
    lines = [
        "### Tabela 3 — Matriz Comparativa de Desempenho e Qualidade Visual",
        "",
        "| Vídeo / Cenário | Codificador | Parâmetro | Taxa Real (kbps) | Tempo (s) | FPS Médio | VMAF Médio | PSNR-YUV (dB) | SSIM | MS-SSIM | XPSNR (dB) | SSIMULACRA2 | Butteraugli (2-Norm) | CVVDP | Energia (Wh) |",
        "| :---- | :---- | :---- | :---- | :---- | :---- | :---- | :---- | :---- | :---- | :---- | :---- | :---- | :---- | :---- |"
    ]
    for r in matrix_rows:
        sample = r.get("sample", "Amostra")
        codec = r.get("codec_label", r.get("codec"))
        param = r.get("param_label", str(r.get("target_value")))
        real_br = f"{r.get('real_bitrate_kbps', 0.0):.1f}"
        t_m = r.get("encoding_time_s", 0.0)
        t_s = r.get("encoding_time_std_s", 0.0)
        time_str = f"{t_m:.2f} ± {t_s:.2f}" if t_s > 0 else f"{t_m:.2f}"
        fps_m = r.get("encoding_fps", 0.0)
        fps_s = r.get("encoding_fps_std", 0.0)
        fps_str = f"{fps_m:.1f} ± {fps_s:.1f}" if fps_s > 0 else f"{fps_m:.1f}"
        vmaf_m = f"{r.get('vmaf_mean', 0.0):.2f}"
        psnr_yuv = f"{r.get('psnr_yuv_mean', r.get('psnr_mean', 0.0)):.2f}"
        ssim_val = f"{r.get('ssim_mean', 0.0):.4f}" if r.get('ssim_mean') is not None else "n/d"
        ms_ssim = f"{r.get('ms_ssim_mean', 0.0):.4f}" if r.get('ms_ssim_mean') is not None else "n/d"
        xpsnr_val = f"{r.get('xpsnr_yuv_mean', 0.0):.2f}" if r.get('xpsnr_yuv_mean') else "n/d"
        s2_val = f"{r.get('ssimulacra2_mean', 0.0):.2f}" if r.get('ssimulacra2_mean') is not None else "n/d"
        ba_val = f"{r.get('butteraugli_2norm', 0.0):.2f}" if r.get('butteraugli_2norm') is not None else "n/d"
        cvvdp_val = f"{r.get('cvvdp_score', 0.0):.2f}" if r.get('cvvdp_score') is not None else "n/d"
        energy = f"{r.get('energy_wh', 0.0):.2f}"

        lines.append(f"| **{sample}** | {codec} | {param} | {real_br} | {time_str} | {fps_str} | {vmaf_m} | {psnr_yuv} | {ssim_val} | {ms_ssim} | {xpsnr_val} | {s2_val} | {ba_val} | {cvvdp_val} | {energy} |")

    lines.append("")
    return "\n".join(lines)


def format_table_4_enriched_markdown(bd_results: list) -> str:
    lines = [
        "### Tabela 4 — Síntese Bjøntegaard Delta (BD-Rate e BD-Metric com interpolação PCHIP)",
        "",
        "| Sequência de Vídeo | Comparação de Codificadores | BD-Rate (VMAF) (%) | Sobreposição (%) | BD-Rate (PSNR-YUV) (%) | BD-Rate (XPSNR) (%) | BD-Rate (SSIMULACRA2) (%) | BD-Rate (CVVDP) (%) |",
        "| :---- | :---- | :---- | :---- | :---- | :---- | :---- | :---- |"
    ]
    for r in bd_results:
        seq = r["sequencia"]
        comp = r["comparacao"]
        bdr_v = f"{r['bd_rate_vmaf']:+.2f} %" if r.get("bd_rate_vmaf") is not None else "n/d"
        ov_v = f"{r.get('overlap_vmaf_pct', 0.0):.1f}%"
        bdr_p = f"{r['bd_rate_psnr']:+.2f} %" if r.get("bd_rate_psnr") is not None else "n/d"
        bdr_xp = f"{r['bd_rate_xpsnr']:+.2f} %" if r.get("bd_rate_xpsnr") is not None else "n/d"
        bdr_s2 = f"{r['bd_rate_ssimulacra2']:+.2f} %" if r.get("bd_rate_ssimulacra2") is not None else "n/d"
        bdr_cvvdp = f"{r['bd_rate_cvvdp']:+.2f} %" if r.get("bd_rate_cvvdp") is not None else "n/d"

        val_flag = "" if r.get("valid_vmaf", True) else " *"
        lines.append(f"| **{seq}** | {comp} | {bdr_v}{val_flag} | {ov_v} | {bdr_p} | {bdr_xp} | {bdr_s2} | {bdr_cvvdp} |")
    lines.append("")
    lines.append("> *Nota:* Valores negativos de BD-Rate indicam redução percentual de taxa de bits para o mesmo nível de qualidade. A recomendação ITU-T/JVET considera confiável sobreposição ≥ 50%.")
    lines.append("")
    return "\n".join(lines)


def format_table_5_iso_markdown(projections: dict, econ_cfg: dict) -> str:
    target_v = econ_cfg.get("target_vmaf", 93)
    lines = [
        f"### Tabela 5 — Projeção Econômica de Armazenamento e Banda (Iso-Qualidade: VMAF ~{target_v})",
        "",
        f"| Codificador | Bitrate Alvo p/ VMAF ~{target_v} (kbps) | GB / Hora | Volume Acervo (1.000 h) | Custo Armazenamento (R$/Mês) | Economia Armazenamento | Custo Tráfego Egress (R$/Mês) | Economia Tráfego | Custo Mensal Total (R$) |",
        "| :---- | :---- | :---- | :---- | :---- | :---- | :---- | :---- | :---- |"
    ]
    for codec, p in projections.items():
        kbps = f"{p['iso_bitrate_kbps']:.0f}"
        gb_h = f"{p['gb_per_hour']:.2f} GB"
        vol = f"{p['volume_tb']:.2f} TB"
        stor = f"R$ {p['storage_cost']:.2f}"
        egress = f"R$ {p['egress_cost']:.2f}"
        tot = f"R$ {p['total_monthly_cost']:.2f}"

        sav_st = p.get("storage_savings_pct", 0.0)
        sav_eg = p.get("egress_savings_pct", 0.0)
        if abs(sav_st) < 1e-6:
            st_label = "Base"
        elif sav_st > 0:
            st_label = f"-{sav_st:.1f}% (R$ {p.get('storage_savings_brl', 0.0):.2f})"
        else:
            st_label = f"+{abs(sav_st):.1f}% (R$ {abs(p.get('storage_savings_brl', 0.0)):.2f})"

        if abs(sav_eg) < 1e-6:
            eg_label = "Base"
        elif sav_eg > 0:
            eg_label = f"-{sav_eg:.1f}% (R$ {p.get('egress_savings_brl', 0.0):.2f})"
        else:
            eg_label = f"+{abs(sav_eg):.1f}% (R$ {abs(p.get('egress_savings_brl', 0.0)):.2f})"

        lines.append(f"| **{codec}** | {kbps} | {gb_h} | {vol} | {stor} | {st_label} | {egress} | {eg_label} | {tot} |")

    lines.append("")
    lines.append(f"> *Premissas:* Armazenamento a R$ {econ_cfg.get('cost_storage_per_gb_month', 0.12):.2f}/GB-mês; Egress a R$ {econ_cfg.get('cost_egress_per_gb', 0.35):.2f}/GB; 5.000 horas transmitidas/mês.")
    lines.append("")
    return "\n".join(lines)


def format_table_6_production_cost_markdown(projections: dict, econ_cfg: dict) -> str:
    lines = [
        "### Tabela 6 — Custo de Produção (Codificação) e Ponto de Equilíbrio (Break-Even)",
        "",
        "| Codificador | Dispositivo | Tempo p/ Codificar 1h Conteúdo | Custo Nuvem p/ 1h Conteúdo | Custo Energia (R$/h) | Custo Total p/ Codificar Acervo (1.000 h) | Ponto de Equilíbrio (Meses a 5.000 h/mês) | Ponto de Equilíbrio (Visualizações / Conteúdo) |",
        "| :---- | :---- | :---- | :---- | :---- | :---- | :---- | :---- |"
    ]
    for codec, p in projections.items():
        dev = p.get("device", "cpu").upper()
        h_per_h = p.get("encode_hours_per_content_hour", 0.0)
        c_cloud = p.get("encode_cost_cloud_per_content_hour", 0.0)
        c_eng = p.get("encode_cost_energy_per_content_hour", 0.0)
        cat_c = p.get("catalog_encode_cost_cloud", 0.0)
        be_m = p.get("break_even_months")
        be_m_str = "Imediato / Base" if be_m == 0.0 else (f"{be_m:.1f} meses" if be_m is not None else "Inatingível")
        be_v = p.get("break_even_views_per_content_hour")
        be_v_str = "0" if be_v == 0.0 else (f"{be_v:.0f} views" if be_v is not None else "Inatingível")

        lines.append(f"| **{codec}** | {dev} | {h_per_h:.2f} h | R$ {c_cloud:.2f} | R$ {c_eng:.3f} | R$ {cat_c:.2f} | {be_m_str} | {be_v_str} |")

    lines.append("")
    lines.append("> *Interpretação do Ponto de Equilíbrio:* Quantas visualizações (ou meses de streaming) são necessárias para que a economia de banda de saída amortize o custo computacional mais elevado de codificação em AV1.")
    lines.append("")
    return "\n".join(lines)


def format_table_7_decode_markdown(decode_rows: list) -> str:
    lines = [
        "### Tabela 7 — Desempenho de Decodificação no Cliente (Software vs. Hardware NVDEC)",
        "",
        "| Família / Decodificador | FPS Médio de Decodificação | Fator de Tempo Real (RTF) | Utilização de CPU (%) | Utilização do NVDEC (%) | Viabilidade em Tempo Real (RTF ≥ 1) |",
        "| :---- | :---- | :---- | :---- | :---- | :---- |"
    ]
    for d in decode_rows:
        dec = d["decoder"]
        if "error" in d:
            lines.append(f"| **{dec}** | Erro | — | — | — | Não suportado |")
            continue
        fps = f"{d['decode_fps']:.1f}"
        rtf = f"{d['decode_rtf']:.2f}x"
        cpu = f"{d['cpu_util_pct']:.1f}%"
        gpu = f"{d['gpu_util_pct']:.1f}%"
        # RTF = duração do conteúdo / tempo de decodificação: independe da taxa de quadros da amostra
        viab = "Sim (Ampla margem)" if d["decode_rtf"] >= 2 else ("Sim" if d["decode_rtf"] >= 1 else "Gargalo (RTF < 1)")
        lines.append(f"| **{dec}** | {fps} | {rtf} | {cpu} | {gpu} | {viab} |")

    lines.append("")
    return "\n".join(lines)


STATS_HEADER = ["Comparação de Codificadores", "Papel", "Sequências válidas (excluídas)", "BD-Rate VMAF médio [IC 95%]",
                "Mediana (%)", "AV1 venceu (BD < 0)", "Abaixo do limiar", "p (Wilcoxon unilateral)",
                "p ajustado (Holm)", "Rejeita H₀?"]


def _stats_cells(r: dict) -> list:
    f = lambda v, fmt: (fmt.format(v) if v == v else "n/d")  # v != v -> NaN
    n = r["n"]
    return [
        r["comparacao"],
        r.get("papel", "Principal"),
        f"{n} ({r['n_excluidas']})",
        f"{f(r['media'], '{:+.2f} %')} [{f(r['ic95_inf'], '{:+.2f}')}; {f(r['ic95_sup'], '{:+.2f}')}]",
        f(r["mediana"], "{:+.2f}"),
        f"{r['vitorias']}/{n}",
        f"{r['abaixo_limiar']}/{n}",
        f(r["p"], "{:.4f}"),
        f(r["p_holm"], "{:.4f}"),
        "Sim" if r["rejeita_h0"] else "Não",
    ]


def format_table_4b_significance_markdown(stats_rows: list) -> str:
    if not stats_rows:
        return ""
    thr, alpha = stats_rows[0]["limiar_pct"], stats_rows[0]["alpha"]
    lines = [
        "### Tabela 4b — Teste de Hipótese sobre o BD-Rate VMAF (Wilcoxon + correção de Holm)",
        "",
        "| " + " | ".join(STATS_HEADER) + " |",
        "| " + " | ".join([":----"] * len(STATS_HEADER)) + " |",
    ]
    lines += ["| " + " | ".join(_stats_cells(r)) + " |" for r in stats_rows]
    lines += [
        "",
        f"> *H₀:* mediana do BD-Rate VMAF ≥ {thr:+.0f}%. *H₁:* mediana < {thr:+.0f}% (economia superior a {abs(thr):.0f}%). "
        f"Unidade amostral: sequência de vídeo. Teste de Wilcoxon de sinais com postos (exato, unilateral), "
        f"p ajustado por Holm-Bonferroni entre as comparações, α = {alpha:g}. IC 95% pela distribuição t. "
        "Teste e correção aplicados só às comparações principais, definidas antes da coleta; "
        "as exploratórias mostram apenas estatística descritiva. "
        "Excluídas: sequências com sobreposição R-D < 50%. Com n sequências, o menor p possível é 1/2ⁿ (n = 4 → 0,0625).",
        "",
    ]
    return "\n".join(lines)


def _extra_table_markdown(t: dict) -> str:
    lines = [f"### {t['title']}", "", "| " + " | ".join(t["header"]) + " |",
             "| " + " | ".join([":----"] * len(t["header"])) + " |"]
    lines += ["| " + " | ".join(str(c) for c in r) + " |" for r in t["rows"]]
    lines += ["", f"> *Nota:* {t['note']}", "", "---", ""]
    return "\n".join(lines)


def generate_markdown_report(
    env_info: dict,
    siti_results: list,
    matrix_rows: list,
    bd_results: list,
    economics_data: dict,
    decode_rows: list,
    econ_cfg: dict,
    output_path: str = "output/relatorio_tcc.md",
    stats_rows: list = None,
    extra_tables: list = None
):
    md = [
        "# Relatório Experimental de Codificação de Vídeo — Resultados Completos para o TCC",
        "",
        "> Estudo comparativo experimental entre **H.264 (libx264 / NVENC)** e **AV1 (SVT-AV1 / NVENC AV1)**.",
        "> Avalia eficiência de compressão, qualidade percebida (VMAF, PSNR-YUV, MS-SSIM), rendimento computacional, impacto energético e viabilidade econômica.",
        "",
        "---",
        "",
        format_table_1_markdown(env_info),
        "---",
        "",
        format_table_2_enriched_markdown(siti_results),
        "---",
        "",
        format_table_3_markdown(matrix_rows),
        "---",
        "",
        format_table_4_enriched_markdown(bd_results),
        format_table_4b_significance_markdown(stats_rows),
        "---",
        "",
        format_table_5_iso_markdown(economics_data, econ_cfg),
        "---",
        "",
        format_table_6_production_cost_markdown(economics_data, econ_cfg),
        "---",
        "",
        format_table_7_decode_markdown(decode_rows),
        "---",
        "",
        *[_extra_table_markdown(t) for t in (extra_tables or [])],
        "",
        "### Galeria de Gráficos e Curvas R-D Geradas",
        "",
        "- **Gráfico 1:** [Curvas de Taxa-Distorção (VMAF vs. Bitrate)](graficos/)",
        "- **Gráfico 2:** [Curvas de Taxa-Distorção Secundárias (PSNR-YUV vs. Bitrate)](graficos/)",
        "- **Gráfico 3:** [Rendimento e Rendimento de Processamento com Desvio Padrão (FPS Médio)](graficos/grafico3_fps_rendimento.png)",
        "- **Gráfico 4:** [Estabilidade Temporal Quadro a Quadro com Distribuição Marginal e Detalhado](graficos/)",
        "- **Gráfico 5:** [Diagrama de Dispersão Espaço-Temporal (Espaço SI × TI)](graficos/grafico5_dispersao_siti.png)",
        "- **Gráfico 6:** [Desempenho de Decodificação no Cliente (Software vs. Hardware)](graficos/grafico6_decode_benchmark.png)",
        "- **Gráfico 7:** [Análise Econômica e Ponto de Equilíbrio / Break-Even](graficos/grafico7_economia_breakeven.png)",
        "- **Recortes Visuais:** [Comparações Lado a Lado de Texturas e Movimento](recortes/)",
        "- **Tabelas em CSV (GitHub):** [Conjunto de Dados Tabulares Brutos em CSV](csv/)",
        "",
        "---",
        "### Reprodutibilidade Experimental",
        "- O log completo de cada invocação do FFmpeg, com todos os argumentos exatos, encontra-se registrado em `output/comandos_executados.jsonl`.",
        "- Hashes SHA-256 das sequências de referência constam na Tabela 2 para verificação de integridade.",
        ""
    ]

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md))


def style_worksheet(ws, title: str):
    header_fill = PatternFill(start_color="1D3557", end_color="1D3557", fill_type="solid")
    header_font = Font(name="Segoe UI", size=11, bold=True, color="FFFFFF")
    border_thin = Border(
        left=Side(style='thin', color='DDDDDD'),
        right=Side(style='thin', color='DDDDDD'),
        top=Side(style='thin', color='DDDDDD'),
        bottom=Side(style='thin', color='DDDDDD')
    )

    for cell in ws[1]:
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

    ws.row_dimensions[1].height = 28

    for row in ws.iter_rows(min_row=2):
        for cell in row:
            cell.font = Font(name="Segoe UI", size=10)
            cell.border = border_thin
            if isinstance(cell.value, float):
                cell.alignment = Alignment(horizontal="right")
                cell.number_format = "0.00"
            elif isinstance(cell.value, int):
                cell.alignment = Alignment(horizontal="right")
            else:
                cell.alignment = Alignment(horizontal="left")

    for col in ws.columns:
        max_len = max(len(str(cell.value or '')) for cell in col)
        col_letter = get_column_letter(col[0].column)
        ws.column_dimensions[col_letter].width = max(max_len + 3, 12)


def generate_excel_workbook(
    env_info: dict,
    siti_results: list,
    matrix_rows: list,
    bd_results: list,
    economics_data: dict,
    decode_rows: list,
    output_path: str = "output/resultados_tcc.xlsx",
    stats_rows: list = None,
    extra_tables: list = None
):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    wb = openpyxl.Workbook()
    wb.remove(wb.active)

    # Aba 1: T1 - Hardware e Software
    ws1 = wb.create_sheet(title="T1 - Hardware e Software")
    ws1.append(["Categoria", "Componente / Parâmetro", "Detalhes Técnicos"])
    ws1.append(["Processador (CPU)", "Modelo, núcleos/threads, frequência", env_info["cpu"]["descricao"]])
    ws1.append(["Placa Gráfica (GPU)", "Modelo, VRAM, arquitetura NVENC", env_info["gpu"]["descricao"]])
    ws1.append(["Memória RAM", "Capacidade, barramento, velocidade", env_info["ram"]["descricao"]])
    ws1.append(["Armazenamento", "Interface de disco dos arquivos", env_info["storage"]["descricao"]])
    ws1.append(["Sistema Operativo", "Versão e compilação do SO", env_info["os"]["descricao"]])
    ws1.append(["Compilação FFmpeg", "Versão e bibliotecas habilitadas", env_info["ffmpeg"]["detalhes"]])
    ws1.append(["Controlador Gráfico", "Driver NVIDIA / SDK CUDA", f"NVIDIA {env_info['gpu']['driver']} (CUDA {env_info['gpu'].get('cuda', 'N/A')})"])
    ws1.append(["Telemetria de Energia", "Método de medição elétrica", env_info.get("energia", {}).get("descricao", "CPU: Estimativa TDP / GPU: nvidia-smi")])
    style_worksheet(ws1, "Tabela 1")

    # Aba 2: T2 - Amostras SI-TI
    ws2 = wb.create_sheet(title="T2 - Amostras SI-TI")
    ws2.append(["Identificador do Vídeo", "Resolução / FPS", "Duração (s)", "SI Máx", "TI Máx", "Complexidade", "Fonte Sem Perdas", "Hash SHA-256"])
    for s in siti_results:
        meta = s["metadata"]
        res_fps = f"{meta['width']}x{meta['height']} @ {int(round(meta['fps']))}"
        ws2.append([
            s.get("nome", "Amostra"),
            res_fps,
            meta["duration"],
            s["si_max"],
            s["ti_max"],
            (s.get("classificacao_override") or s["classificacao"]),
            "Sim" if s.get("is_lossless") else "Não",
            s.get("sha256", "N/A")
        ])
    style_worksheet(ws2, "Tabela 2")

    # Aba 3: T3 - Matriz Comparativa
    ws3 = wb.create_sheet(title="T3 - Matriz Comparativa")
    ws3.append(["Amostra", "Codificador", "Parâmetro", "Taxa Real (kbps)", "Tempo Médio (s)", "Tempo Desvio (s)",
                "FPS Médio", "FPS Desvio", "VMAF Médio", "VMAF 1%", "VMAF NEG", "PSNR-YUV (dB)", "SSIM", "MS-SSIM",
                "XPSNR-YUV (dB)", "SSIMULACRA2", "Butteraugli 2-Norm", "Butteraugli 3-Norm", "CVVDP",
                "Energia (Wh)", "Potência CPU (W)", "Fonte CPU", "Potência GPU (W)", "CPU Média (%)", "GPU Média (%)"])
    for r in matrix_rows:
        cpu_pwr = r.get("cpu_power_w")
        gpu_pwr = r.get("gpu_power_w")
        ws3.append([
            r.get("sample", ""),
            r.get("codec_label", r.get("codec")),
            r.get("param_label", str(r.get("target_value"))),
            r.get("real_bitrate_kbps", 0.0),
            r.get("encoding_time_s", 0.0),
            r.get("encoding_time_std_s", 0.0),
            r.get("encoding_fps", 0.0),
            r.get("encoding_fps_std", 0.0),
            r.get("vmaf_mean", 0.0),
            r.get("vmaf_min_1pct", 0.0),
            r.get("vmaf_neg_mean", 0.0),
            r.get("psnr_yuv_mean", r.get("psnr_mean", 0.0)),
            r.get("ssim_mean", 0.0),
            r.get("ms_ssim_mean", 0.0),
            r.get("xpsnr_yuv_mean", 0.0),
            r.get("ssimulacra2_mean", 0.0),
            r.get("butteraugli_2norm", 0.0),
            r.get("butteraugli_3norm", 0.0),
            r.get("cvvdp_score", 0.0),
            r.get("energy_wh", 0.0),
            cpu_pwr if cpu_pwr is not None else "n/d",
            r.get("cpu_power_source", "Estimativa TDP"),
            gpu_pwr if gpu_pwr is not None else 0.0,
            r.get("cpu_util_pct", 0.0),
            r.get("gpu_util_pct", 0.0)
        ])
    style_worksheet(ws3, "Tabela 3")

    # Aba 4: T4 - BD-Rate e Métricas
    ws4 = wb.create_sheet(title="T4 - BD-Rate e Métricas")
    ws4.append(["Sequência de Vídeo", "Comparação de Codificadores", "BD-Rate VMAF (%)", "Sobreposição VMAF (%)", "Válido?",
                "BD-VMAF (pts)", "BD-Rate PSNR-YUV (%)", "BD-PSNR-YUV (dB)", "BD-Rate VMAF NEG (%)",
                "BD-Rate XPSNR (%)", "BD-Rate SSIMULACRA2 (%)", "BD-Rate CVVDP (%)"])
    for b in bd_results:
        ws4.append([
            b["sequencia"],
            b["comparacao"],
            b.get("bd_rate_vmaf"),
            b.get("overlap_vmaf_pct"),
            "Sim" if b.get("valid_vmaf") else "Não",
            b.get("bd_metric_vmaf"),
            b.get("bd_rate_psnr"),
            b.get("bd_metric_psnr"),
            b.get("bd_rate_vmaf_neg"),
            b.get("bd_rate_xpsnr"),
            b.get("bd_rate_ssimulacra2"),
            b.get("bd_rate_cvvdp")
        ])
    style_worksheet(ws4, "Tabela 4")

    if stats_rows:
        ws4b = wb.create_sheet(title="T4b - Teste de Hipótese")
        ws4b.append(STATS_HEADER)
        for r in stats_rows:
            ws4b.append(_stats_cells(r))
        style_worksheet(ws4b, "Tabela 4b")

    # Aba 5: T5 - Economia Iso-Qualidade
    ws5 = wb.create_sheet(title="T5 - Economia Iso-Qualidade")
    ws5.append(["Codificador", "Bitrate Alvo VMAF~93 (kbps)", "GB / Hora", "Volume Acervo (1.000 h em TB)",
                "Custo Armazenamento (R$/Mês)", "Economia Armaz. (%)", "Custo Egress (R$/Mês)", "Economia Egress (%)", "Custo Total Mensal (R$)"])
    for codec, data in economics_data.items():
        ws5.append([
            codec,
            data["iso_bitrate_kbps"],
            data["gb_per_hour"],
            data["volume_tb"],
            data["storage_cost"],
            data.get("storage_savings_pct", 0.0),
            data["egress_cost"],
            data.get("egress_savings_pct", 0.0),
            data["total_monthly_cost"]
        ])
    style_worksheet(ws5, "Tabela 5")

    # Aba 6: T6 - Custos e Break-Even
    ws6 = wb.create_sheet(title="T6 - Custos e Break-Even")
    ws6.append(["Codificador", "Dispositivo", "Tempo Codificação / Hora Conteúdo (h)", "Custo Nuvem / Hora Conteúdo (R$)",
                "Energia / Hora Conteúdo (R$)", "Custo Total Acervo 1.000h (R$)", "Break-Even (Meses)", "Break-Even (Visualizações/Conteúdo)"])
    for codec, data in economics_data.items():
        ws6.append([
            codec,
            data.get("device", "").upper(),
            data.get("encode_hours_per_content_hour", 0.0),
            data.get("encode_cost_cloud_per_content_hour", 0.0),
            data.get("encode_cost_energy_per_content_hour", 0.0),
            data.get("catalog_encode_cost_cloud", 0.0),
            data.get("break_even_months"),
            data.get("break_even_views_per_content_hour")
        ])
    style_worksheet(ws6, "Tabela 6")

    # Aba 7: T7 - Decodificação Cliente
    ws7 = wb.create_sheet(title="T7 - Decodificação Cliente")
    ws7.append(["Decodificador", "FPS Médio de Decodificação", "Tempo Decodificação (s)", "RTF (Fator de Tempo Real)", "Utilização CPU (%)", "Utilização GPU (%)"])
    for d in decode_rows:
        if "error" not in d:
            ws7.append([
                d["decoder"],
                d["decode_fps"],
                d["decode_time_s"],
                d["decode_rtf"],
                d["cpu_util_pct"],
                d["gpu_util_pct"]
            ])
    style_worksheet(ws7, "Tabela 7")

    for t in (extra_tables or []):
        wsx = wb.create_sheet(title=t["title"].split(" — ")[0].replace("Tabela ", "T")[:31])
        wsx.append(t["header"])
        for r in t["rows"]:
            wsx.append(r)
        style_worksheet(wsx, t["title"].split(" — ")[0])

    for ws in wb.worksheets:  # NaN corrompe o .xlsx; célula vazia = métrica indisponível
        for row in ws.iter_rows():
            for c in row:
                if isinstance(c.value, float) and c.value != c.value:
                    c.value = None
    wb.save(output_path)


def _json_default(obj):
    """Serializador de fallback para tipos do NumPy, conjuntos, caminhos e objetos."""
    if hasattr(obj, "tolist") and callable(obj.tolist):
        return obj.tolist()
    if hasattr(obj, "item") and callable(obj.item):
        return obj.item()
    if isinstance(obj, (set, tuple)):
        return list(obj)
    if hasattr(obj, "__dict__"):
        return obj.__dict__
    return str(obj)


def export_json_database(all_data: dict, output_path: str = "output/resultados_completos.json"):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_data, f, indent=2, ensure_ascii=False, default=_json_default)


def export_csv_tables(
    env_info: dict,
    siti_results: list,
    matrix_rows: list,
    bd_results: list,
    economics_data: dict,
    decode_rows: list,
    csv_dir: str = "output/csv",
    stats_rows: list = None,
    extra_tables: list = None
):
    """Exporta as tabelas em arquivos CSV individuais."""
    os.makedirs(csv_dir, exist_ok=True)

    # Tabela 1: HW/SW
    with open(os.path.join(csv_dir, "tabela1_hardware_software.csv"), "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Categoria", "Componente", "Detalhes_Tecnicos"])
        writer.writerow(["Processador (CPU)", "Modelo, nucleos, frequencia", env_info["cpu"]["descricao"]])
        writer.writerow(["Placa Grafica (GPU)", "Modelo, VRAM, arquitetura NVENC", env_info["gpu"]["descricao"]])
        writer.writerow(["Memoria RAM", "Capacidade, tecnologia, frequencia", env_info["ram"]["descricao"]])
        writer.writerow(["Armazenamento", "Interface de disco", env_info["storage"]["descricao"]])
        writer.writerow(["Sistema Operacional", "Versao e build", env_info["os"]["descricao"]])
        writer.writerow(["FFmpeg e Bibliotecas", "Compilacao e versoes", env_info["ffmpeg"]["detalhes"]])
        writer.writerow(["Driver GPU", "Controlador NVIDIA e CUDA", f"NVIDIA {env_info['gpu']['driver']} (CUDA {env_info['gpu'].get('cuda', 'N/A')})"])

    # Tabela 2: Amostras SI/TI
    with open(os.path.join(csv_dir, "tabela2_amostras_siti.csv"), "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Amostra", "Resolucao_FPS", "Duracao_s", "SI_Max", "TI_Max", "Complexidade", "Fonte_Lossless", "SHA256"])
        for s in siti_results:
            meta = s["metadata"]
            res_fps = f"{meta['width']}x{meta['height']}@{int(round(meta['fps']))}"
            writer.writerow([
                s.get("nome", "Amostra"),
                res_fps,
                f"{meta['duration']:.2f}",
                f"{s['si_max']:.2f}",
                f"{s['ti_max']:.2f}",
                (s.get("classificacao_override") or s.get("classificacao", "")),
                "Sim" if s.get("is_lossless") else "Nao",
                s.get("sha256", "N/A")
            ])

    # Tabela 3: Matriz de Desempenho e Qualidade
    with open(os.path.join(csv_dir, "tabela3_matriz_metricas.csv"), "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "Amostra", "Codificador", "Parametro", "Bitrate_Real_kbps",
            "Tempo_Medio_s", "Tempo_Std_s", "FPS_Medio", "FPS_Std",
            "VMAF_Medio", "VMAF_1pct", "VMAF_NEG_Medio", "PSNR_YUV_dB",
            "SSIM_Medio", "MS_SSIM_Medio", "XPSNR_YUV_dB", "SSIMULACRA2",
            "Butteraugli_2Norm", "Butteraugli_3Norm", "CVVDP", "Energia_Wh",
            "CPU_Util_pct", "GPU_Util_pct"
        ])
        for r in matrix_rows:
            writer.writerow([
                r.get("sample", ""),
                r.get("codec_label", r.get("codec")),
                r.get("param_label", str(r.get("target_value"))),
                f"{r.get('real_bitrate_kbps', 0.0):.2f}",
                f"{r.get('encoding_time_s', 0.0):.2f}",
                f"{r.get('encoding_time_std_s', 0.0):.2f}",
                f"{r.get('encoding_fps', 0.0):.2f}",
                f"{r.get('encoding_fps_std', 0.0):.2f}",
                f"{r.get('vmaf_mean', 0.0):.2f}",
                f"{r.get('vmaf_min_1pct', 0.0):.2f}",
                f"{r.get('vmaf_neg_mean', 0.0):.2f}",
                f"{r.get('psnr_yuv_mean', r.get('psnr_mean', 0.0)):.2f}",
                f"{r.get('ssim_mean', 0.0):.4f}",
                f"{r.get('ms_ssim_mean', 0.0):.4f}",
                f"{r.get('xpsnr_yuv_mean', 0.0):.2f}",
                f"{r.get('ssimulacra2_mean', 0.0):.2f}",
                f"{r.get('butteraugli_2norm', 0.0):.2f}",
                f"{r.get('butteraugli_3norm', 0.0):.2f}",
                f"{r.get('cvvdp_score', 0.0):.2f}",
                f"{r.get('energy_wh', 0.0):.3f}",
                f"{r.get('cpu_util_pct', 0.0):.1f}",
                f"{r.get('gpu_util_pct', 0.0):.1f}"
            ])

    # Tabela 4: BD-Rate
    with open(os.path.join(csv_dir, "tabela4_bd_rate.csv"), "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "Sequencia", "Comparacao", "BD_Rate_VMAF_pct", "Sobreposicao_VMAF_pct", "Valido",
            "BD_VMAF_pts", "BD_Rate_PSNR_pct", "BD_PSNR_dB", "BD_Rate_VMAF_NEG_pct",
            "BD_Rate_XPSNR_pct", "BD_Rate_SSIMULACRA2_pct", "BD_Rate_CVVDP_pct"
        ])
        for b in bd_results:
            writer.writerow([
                b.get("sequencia", ""),
                b.get("comparacao", ""),
                f"{b.get('bd_rate_vmaf', 0.0):.2f}" if b.get("bd_rate_vmaf") is not None else "",
                f"{b.get('overlap_vmaf_pct', 0.0):.1f}" if b.get("overlap_vmaf_pct") is not None else "",
                "Sim" if b.get("valid_vmaf") else "Nao",
                f"{b.get('bd_metric_vmaf', 0.0):.2f}" if b.get("bd_metric_vmaf") is not None else "",
                f"{b.get('bd_rate_psnr', 0.0):.2f}" if b.get("bd_rate_psnr") is not None else "",
                f"{b.get('bd_metric_psnr', 0.0):.2f}" if b.get("bd_metric_psnr") is not None else "",
                f"{b.get('bd_rate_vmaf_neg', 0.0):.2f}" if b.get("bd_rate_vmaf_neg") is not None else "",
                f"{b.get('bd_rate_xpsnr', 0.0):.2f}" if b.get("bd_rate_xpsnr") is not None else "",
                f"{b.get('bd_rate_ssimulacra2', 0.0):.2f}" if b.get("bd_rate_ssimulacra2") is not None else "",
                f"{b.get('bd_rate_cvvdp', 0.0):.2f}" if b.get("bd_rate_cvvdp") is not None else ""
            ])

    if stats_rows:
        keys = ["comparacao", "papel", "n", "n_excluidas", "limiar_pct", "media", "ic95_inf", "ic95_sup", "mediana",
                "vitorias", "abaixo_limiar", "p", "p_holm", "p_min_possivel", "alpha", "rejeita_h0"]
        with open(os.path.join(csv_dir, "tabela4b_teste_hipotese.csv"), "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(keys)
            for r in stats_rows:
                writer.writerow([r[k] for k in keys])

    for t in (extra_tables or []):
        with open(os.path.join(csv_dir, t["csv"]), "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(t["header"])
            writer.writerows(t["rows"])

    # Tabela 5: Economia Iso-Qualidade
    with open(os.path.join(csv_dir, "tabela5_economia_iso.csv"), "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "Codificador", "Bitrate_Iso_VMAF93_kbps", "GB_por_Hora", "Volume_Acervo_1000h_TB",
            "Custo_Armazenamento_BRL_Mes", "Economia_Armazenamento_pct",
            "Custo_Egress_BRL_Mes", "Economia_Egress_pct", "Custo_Total_Mensal_BRL"
        ])
        for codec, data in economics_data.items():
            writer.writerow([
                codec,
                f"{data.get('iso_bitrate_kbps', 0.0):.2f}",
                f"{data.get('gb_per_hour', 0.0):.3f}",
                f"{data.get('volume_tb', 0.0):.3f}",
                f"{data.get('storage_cost', 0.0):.2f}",
                f"{data.get('storage_savings_pct', 0.0):.2f}",
                f"{data.get('egress_cost', 0.0):.2f}",
                f"{data.get('egress_savings_pct', 0.0):.2f}",
                f"{data.get('total_monthly_cost', 0.0):.2f}"
            ])

    # Tabela 6: Custos de Produção e Break-Even
    with open(os.path.join(csv_dir, "tabela6_custos_breakeven.csv"), "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "Codificador", "Dispositivo", "Horas_Codificacao_por_Hora_Conteudo",
            "Custo_Nuvem_Hora_Conteudo_BRL", "Custo_Energia_Hora_Conteudo_BRL",
            "Custo_Total_Acervo_1000h_BRL", "Break_Even_Meses", "Break_Even_Views_por_Conteudo"
        ])
        for codec, data in economics_data.items():
            be_m = data.get("break_even_months")
            be_v = data.get("break_even_views_per_content_hour")
            writer.writerow([
                codec,
                data.get("device", "").upper(),
                f"{data.get('encode_hours_per_content_hour', 0.0):.3f}",
                f"{data.get('encode_cost_cloud_per_content_hour', 0.0):.3f}",
                f"{data.get('encode_cost_energy_per_content_hour', 0.0):.3f}",
                f"{data.get('catalog_encode_cost_cloud', 0.0):.2f}",
                f"{be_m:.2f}" if be_m is not None else "Inatingivel",
                f"{be_v:.1f}" if be_v is not None else "Inatingivel"
            ])

    # Tabela 7: Benchmark de Decodificação
    with open(os.path.join(csv_dir, "tabela7_decodificacao.csv"), "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Decodificador", "FPS_Medio", "Tempo_Decodificacao_s", "RTF_Tempo_Real", "CPU_Util_pct", "GPU_Util_pct"])
        for d in decode_rows:
            if "error" not in d:
                writer.writerow([
                    d.get("decoder", ""),
                    f"{d.get('decode_fps', 0.0):.1f}",
                    f"{d.get('decode_time_s', 0.0):.2f}",
                    f"{d.get('decode_rtf', 0.0):.2f}",
                    f"{d.get('cpu_util_pct', 0.0):.1f}",
                    f"{d.get('gpu_util_pct', 0.0):.1f}"
                ])


