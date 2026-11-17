#!/usr/bin/env python3
"""
Análises complementares usadas no texto do TCC e não geradas pelo run_pipeline.py:

1. BD-Rate por métrica de qualidade (10 métricas), com a sobreposição verificada na própria métrica.
2. Correlação de Spearman entre o SI e o BD-Rate VMAF de cada comparação.
3. Mediana, por sequência, da variação de taxa de bits em iso-qualidade (VMAF 93 e 95).
4. Estabilidade temporal do VMAF por quadro (desvio padrão e percentis de 1% e 5%) em iso-qualidade.
5. Coeficiente de variação do tempo de codificação entre as repetições.
6. Sensibilidade da projeção econômica ao volume de horas assistidas.
7. Distribuição híbrida: cópia adicional em AV1 e transcodificação sob demanda para H.264.

Lê apenas output/resultados_completos.json e output/metrics/*_vmaf.json; não precisa dos vídeos.
Uso: python analise_complementar.py [--output-dir output]
"""
import argparse
import json
import os

import numpy as np
from scipy import stats

from pipeline.bjontegaard import bd_rate, value_at_quality
from pipeline.economics import sensitivity_analysis

# (campo em matrix_rows, nome, maior é melhor)
METRICS = [
    ("vmaf_mean", "VMAF", True),
    ("vmaf_neg_mean", "VMAF NEG", True),
    ("psnr_yuv_mean", "PSNR", True),
    ("xpsnr_yuv_mean", "XPSNR", True),
    ("ssim_mean", "SSIM", True),
    ("ms_ssim_mean", "MS-SSIM", True),
    ("ssimulacra2_mean", "SSIMULACRA2", True),
    ("butteraugli_2norm", "Butteraugli (2-norma)", False),
    ("butteraugli_3norm", "Butteraugli (3-norma)", False),
    ("cvvdp_score", "CVVDP", True),
]
TARGETS = (93.0, 95.0)


def fmt(v, f="{:.2f}"):
    return f.format(v) if v is not None and np.isfinite(v) else "n/d"


def table(header, rows):
    out = ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    out += ["| " + " | ".join(str(c) for c in r) + " |" for r in rows]
    return "\n".join(out)


def load(output_dir):
    with open(os.path.join(output_dir, "resultados_completos.json"), encoding="utf-8") as f:
        data = json.load(f)
    with open("config.json", encoding="utf-8") as f:
        config = json.load(f)
    # Curva R-D principal: exclui as linhas dos testes de presets e de síntese de grão
    rd = {}
    for r in data["matrix_rows"]:
        if r.get("mode") != "quality" or "Preset" in r["codec_label"] or "Grain" in r["codec_label"]:
            continue
        rd.setdefault(r["sample"], {}).setdefault(r["codec"], []).append(r)
    return data, config, rd


def frame_stats(output_dir, row):
    stem = os.path.splitext(os.path.basename(row["output_path"].replace("\\", "/")))[0]
    path = os.path.join(output_dir, "metrics", f"{stem}_vmaf.json")
    with open(path, encoding="utf-8") as f:
        v = np.array([fr["metrics"]["vmaf"] for fr in json.load(f)["frames"] if "vmaf" in fr["metrics"]], float)
    return float(v.std(ddof=0)), float(np.percentile(v, 1)), float(np.percentile(v, 5))


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument("--output-dir", default="output")
    args = ap.parse_args()
    data, config, rd = load(args.output_dir)
    codecs = config["codecs"]
    label = lambda c: codecs[c]["label"]
    comps = config["comparisons"]
    baseline = config["baseline"]
    md = ["# Análises complementares", "",
          "Gerado por `analise_complementar.py` a partir de `resultados_completos.json` e dos arquivos de VMAF por quadro.", ""]

    # 1. BD-Rate por métrica
    per_seq = {}  # (métrica, teste, ref) -> [(sequência, valor, sobreposição, válido)]
    for s, by in rd.items():
        for t, r in comps:
            if t not in by or r not in by:
                continue
            for key, _, higher in METRICS:
                sign = 1 if higher else -1
                res = bd_rate([x["real_bitrate_kbps"] for x in by[r]], [sign * x[key] for x in by[r]],
                              [x["real_bitrate_kbps"] for x in by[t]], [sign * x[key] for x in by[t]])
                per_seq.setdefault((key, t, r), []).append((s, res["value"], res["overlap_pct"], res["valid"]))
    rows = []
    for key, name, _ in METRICS:
        line = [name]
        for t, r in comps:
            vals = [v for _, v, _, ok in per_seq.get((key, t, r), []) if ok and v is not None]
            line.append(f"{fmt(float(np.median(vals)), '{:+.1f}')} ({len(vals)})" if vals else "n/d (0)")
        rows.append(line)
    md += ["## 1. Mediana do BD-Rate (%) por métrica", "",
           table(["Métrica"] + [f"{label(t)} x {label(r)}" for t, r in comps], rows), "",
           "Entre parênteses: sequências com sobreposição mínima de 50% na própria métrica. "
           "Butteraugli com sinal invertido (medida de distorção).", ""]
    rows = [[s, name, f"{label(t)} x {label(r)}", fmt(v, "{:+.2f}"), fmt(o, "{:.1f}"), "sim" if ok else "não"]
            for (key, t, r), lst in per_seq.items() for name in [dict((k, n) for k, n, _ in METRICS)[key]]
            for s, v, o, ok in lst]
    md += ["### BD-Rate por sequência e métrica", "",
           table(["Sequência", "Métrica", "Comparação", "BD-Rate (%)", "Sobreposição (%)", "Válida"], rows), ""]

    # 2. Spearman SI x BD-Rate VMAF
    si = {s["nome"]: s["si_max"] for s in data["siti_samples"]}
    rows = []
    for t, r in comps:
        pts = [(si[s], v) for s, v, _, ok in per_seq.get(("vmaf_mean", t, r), []) if ok and v is not None]
        if len(pts) >= 3:
            rho, p = stats.spearmanr(*zip(*pts))
            rows.append([f"{label(t)} x {label(r)}", len(pts), fmt(rho), fmt(p, "{:.4f}")])
    md += ["## 2. Correlação de Spearman entre SI e BD-Rate VMAF", "",
           table(["Comparação", "n", "rho", "p (bilateral)"], rows), "",
           "Análise exploratória. rho positivo: quanto maior o SI, menor a economia.", ""]

    # 3 e 4. Iso-qualidade por sequência e estabilidade temporal
    keys = list(codecs)
    for target in TARGETS:
        iso, stab, used = {c: {} for c in keys}, {c: [] for c in keys}, []
        for s, by in rd.items():
            br = {c: value_at_quality([x["vmaf_mean"] for x in by[c]], [x["real_bitrate_kbps"] for x in by[c]], target)
                  for c in keys if c in by}
            if len(br) != len(keys) or any(v is None for v in br.values()):
                continue
            used.append(s)
            for c in keys:
                iso[c][s] = br[c]
                fs = [frame_stats(args.output_dir, x) for x in by[c]]
                vm = [x["vmaf_mean"] for x in by[c]]
                stab[c].append([value_at_quality(vm, [f[i] for f in fs], target, log_scale=False) for i in range(3)])
        rows = []
        for c in keys:
            var = [100 * (iso[c][s] / iso[baseline][s] - 1) for s in used]
            st = np.array(stab[c], float).mean(axis=0)
            rows.append([label(c), fmt(np.mean(list(iso[c].values())) / 1000),
                         "referência" if c == baseline else fmt(float(np.median(var)), "{:+.1f}%"),
                         fmt(st[0]), fmt(st[1]), fmt(st[2])])
        md += [f"## 3. Iso-qualidade em VMAF {target:g} ({len(used)} sequências)", "",
               table(["Codificador", "Taxa média (Mb/s)", "Mediana da variação por sequência",
                      "Desvio padrão do VMAF", "Percentil 1%", "Percentil 5%"], rows), "",
               "Desvio padrão e percentis do VMAF por quadro interpolados (PCHIP) no alvo e "
               "promediados entre as sequências. Sequências: " + ", ".join(used) + ".", ""]

    # 5. Coeficiente de variação do tempo
    rows = []
    for c in keys:
        cv = [100 * x["encoding_time_std_s"] / x["encoding_time_s"] for by in rd.values() for x in by.get(c, [])
              if x.get("encoding_time_s")]
        rows.append([label(c), fmt(np.mean(cv)), fmt(np.max(cv))])
    md += ["## 4. Coeficiente de variação do tempo de codificação (3 repetições)", "",
           table(["Codificador", "CV médio (%)", "CV máximo (%)"], rows), ""]

    # 6. Sensibilidade ao volume de audiência
    sens = sensitivity_analysis(data["economics"], config["economics"], baseline)
    rows = [[f"{x['streamed_hours']:,}".replace(",", "."), label(x["codec"]), fmt(x["monthly_cost"]),
             fmt(x["monthly_savings"]), fmt(x["break_even_months"], "{:.3f}")] for x in sens]
    md += [f"## 5. Sensibilidade ao volume de horas assistidas (VMAF {config['economics']['target_vmaf']})", "",
           table(["Horas assistidas/mês", "Codificador", "Custo mensal (R$)", "Economia mensal (R$)",
                  "Ponto de equilíbrio (meses)"], rows), ""]

    # 7. Distribuição híbrida (dispositivos com e sem suporte ao AV1)
    # a) Cópia adicional em AV1 mantida ao lado do acervo H.264: o custo extra é o armazenamento da cópia
    #    AV1; a economia é a diferença de tráfego em cada hora assistida em AV1. A cópia compensa quando a
    #    fração das horas assistidas em dispositivos compatíveis supera armazenamento / (horas * economia/h).
    # b) Acervo só em AV1, transcodificado sob demanda para H.264 via NVENC (GPU em nuvem) para dispositivos
    #    sem suporte: compensa enquanto o custo de transcodificação das horas assistidas nesses dispositivos
    #    for menor que o custo de armazenar a cópia H.264. Considera-se apenas o custo da instância.
    eco, econ_cfg = data["economics"], config["economics"]
    streamed_h = econ_cfg["monthly_streamed_hours"]
    rows = []
    for c in keys:
        if "av1" not in c or c not in eco:  # só cópias AV1; as variantes H.264 não exigem dispositivo novo
            continue
        saving_h = eco[baseline]["egress_cost_per_watched_hour"] - eco[c]["egress_cost_per_watched_hour"]
        frac = eco[c]["storage_cost"] / (streamed_h * saving_h) if saving_h > 0 else None
        rows.append([label(c), fmt(eco[c]["storage_cost"]), fmt(saving_h, "{:.3f}"),
                     fmt(100 * frac, "{:.1f}%") if frac is not None else "n/d"])
    md += [f"## 6. Distribuição híbrida (VMAF {econ_cfg['target_vmaf']}, {streamed_h:,} h assistidas/mês)".replace(",", "."), "",
           "### a) Cópia adicional mantida ao lado do acervo H.264", "",
           table(["Cópia adicional", "Armazenamento da cópia (R$/mês)", "Economia de tráfego por hora assistida (R$)",
                  "Fração mínima de horas em dispositivos compatíveis"], rows), "",
           "Fração mínima = armazenamento da cópia / (horas assistidas por mês x economia por hora). "
           "Não inclui o custo único de codificação da cópia.", ""]
    transc = "h264-nvenc"
    if transc in eco:
        cost_h = eco[transc]["encode_cost_cloud_per_content_hour"]
        limit = eco[baseline]["storage_cost"] / cost_h
        md += ["### b) Transcodificação sob demanda para H.264", "",
               table(["Item", "Valor"], [
                   [f"Armazenamento da cópia {label(baseline)} (R$/mês)", fmt(eco[baseline]["storage_cost"])],
                   [f"Custo de transcodificação por hora assistida, {label(transc)} em nuvem (R$)", fmt(cost_h, "{:.3f}")],
                   ["Limite de horas assistidas/mês em dispositivos sem AV1", fmt(limit, "{:.0f}")],
               ]), "",
               f"Abaixo do limite, transcodificar sob demanda custa menos que manter a cópia H.264. Usa-se o "
               f"{label(transc)} porque o x264 medium não codifica 4K a 50 quadros/s em tempo real. "
               "Considera apenas o custo da instância em nuvem.", ""]

    out = os.path.join(args.output_dir, "analise_complementar.md")
    with open(out, "w", encoding="utf-8") as f:
        f.write("\n".join(md))
    print(f"Gerado: {out}")


if __name__ == "__main__":
    main()
