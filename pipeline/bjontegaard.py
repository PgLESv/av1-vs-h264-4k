"""
Bjøntegaard Delta (BD-Rate e BD-Metric) e interpolação de iso-qualidade.

- Método padrão: interpolação PCHIP por partes (prática atual JVET/AOM CTC), mais estável
  que o ajuste cúbico com poucos pontos.
- Método clássico VCEG-M33 (polinômio cúbico) também é calculado para comparação.
- Reporta o percentual de sobreposição das curvas (validade do BD).
"""
import numpy as np
from scipy.interpolate import PchipInterpolator

MIN_OVERLAP_PCT = 50.0

# Compatibilidade entre versões do NumPy (< 2.0 usa trapz; >= 2.0 usa trapezoid)
_trapz = getattr(np, "trapezoid", None) or getattr(np, "trapz", None)


def _monotonic(x, y):
    """Ordena por x e remove x repetidos/não crescentes (ex.: VMAF saturado em 100)."""
    x, y = np.asarray(x, float), np.asarray(y, float)
    ok = np.isfinite(x) & np.isfinite(y)  # métrica que falhou vira NaN e sai da curva
    x, y = x[ok], y[ok]
    if x.size == 0:
        return x, y
    idx = np.argsort(x)
    x, y = x[idx], y[idx]
    keep = np.concatenate(([True], np.diff(x) > 1e-9))
    return x[keep], y[keep]


def _avg_diff(x1, y1, x2, y2, method: str):
    """Diferença média (y2 - y1) integrada no intervalo comum de x."""
    lo, hi = max(x1.min(), x2.min()), min(x1.max(), x2.max())
    if hi <= lo:
        return None, 0.0
    span_ref = x1.max() - x1.min()
    overlap = 100.0 * (hi - lo) / span_ref if span_ref > 0 else 0.0

    if method == "cubic" and len(x1) >= 4 and len(x2) >= 4:
        p1, p2 = np.polyint(np.polyfit(x1, y1, 3)), np.polyint(np.polyfit(x2, y2, 3))
        diff = (np.polyval(p2, hi) - np.polyval(p2, lo)) - (np.polyval(p1, hi) - np.polyval(p1, lo))
        return diff / (hi - lo), overlap

    xs = np.linspace(lo, hi, 1000)
    f1, f2 = PchipInterpolator(x1, y1), PchipInterpolator(x2, y2)
    diff_area = float(_trapz(f2(xs) - f1(xs), xs))
    return diff_area / (hi - lo), overlap


def bd_rate(rate_ref, dist_ref, rate_test, dist_test, method: str = "pchip") -> dict:
    """BD-Rate (%): negativo = economia de bitrate do 'test' frente ao 'ref' na mesma qualidade."""
    d1, lr1 = _monotonic(dist_ref, np.log10(rate_ref))
    d2, lr2 = _monotonic(dist_test, np.log10(rate_test))
    if len(d1) < 2 or len(d2) < 2:
        return {"value": None, "overlap_pct": 0.0, "valid": False}
    avg, overlap = _avg_diff(d1, lr1, d2, lr2, method)
    if avg is None:
        return {"value": None, "overlap_pct": 0.0, "valid": False}
    return {"value": float((10 ** avg - 1) * 100), "overlap_pct": float(overlap), "valid": bool(overlap >= MIN_OVERLAP_PCT)}


def bd_metric(rate_ref, dist_ref, rate_test, dist_test, method: str = "pchip") -> dict:
    """BD-Metric: ganho médio de qualidade (pts VMAF ou dB) no mesmo bitrate."""
    lr1, d1 = _monotonic(np.log10(rate_ref), dist_ref)
    lr2, d2 = _monotonic(np.log10(rate_test), dist_test)
    if len(lr1) < 2 or len(lr2) < 2:
        return {"value": None, "overlap_pct": 0.0, "valid": False}
    avg, overlap = _avg_diff(lr1, d1, lr2, d2, method)
    if avg is None:
        return {"value": None, "overlap_pct": 0.0, "valid": False}
    return {"value": float(avg), "overlap_pct": float(overlap), "valid": bool(overlap >= MIN_OVERLAP_PCT)}


def value_at_quality(dists, values, target: float, log_scale: bool = True):
    """
    Interpola um valor (bitrate, tempo, energia) no ponto de qualidade 'target'.
    Retorna None se o alvo estiver fora da faixa medida (sem extrapolação).
    """
    d, v = _monotonic(dists, np.log10(values) if log_scale else values)
    if len(d) < 2 or not (d.min() <= target <= d.max()):
        return None
    y = float(PchipInterpolator(d, v)(target))
    return 10 ** y if log_scale else y


def fmt_bd(entry: dict, unit: str) -> str:
    if not entry or entry.get("value") is None:
        return "n/d (sem sobreposição)"
    s = f"{entry['value']:+.2f} {unit}"
    return s if entry.get("valid") else f"{s} * ({entry['overlap_pct']:.0f}% sobrep.)"


def significance_by_comparison(bd_results: list, threshold_pct: float = -30.0, alpha: float = 0.05,
                               primary: list = None) -> list:
    """
    Tabela 4b: H0: mediana do BD-Rate VMAF >= limiar; H1: mediana < limiar (economia maior que |limiar|).
    Unidade amostral = sequência (o BD-Rate é determinístico por clipe; repetições não geram variância).
    Wilcoxon de sinais com postos unilateral (exato) por comparação + correção de Holm-Bonferroni
    entre as comparações. Só entram sequências com sobreposição R-D válida (>= 50%).
    primary: pares [teste, referência] definidos a priori; só eles recebem teste e Holm (None = todos).
    As demais são exploratórias: apenas estatística descritiva.
    """
    from scipy import stats

    nan = float("nan")
    groups = {}
    for r in bd_results:
        g = groups.setdefault(r["comparacao"], {"vals": [], "excl": 0,
                                                "pair": [r.get("test_codec"), r.get("ref_codec")]})
        v = r.get("bd_rate_vmaf")
        if r.get("valid_vmaf") and v is not None and np.isfinite(v):
            g["vals"].append(float(v))
        else:
            g["excl"] += 1

    rows = []
    for comp, g in groups.items():
        x = np.array(g["vals"], float)
        n = len(x)
        principal = primary is None or g["pair"] in [list(p) for p in primary]
        row = {"comparacao": comp, "papel": "Principal" if principal else "Exploratória", "n": n, "n_excluidas": g["excl"], "limiar_pct": threshold_pct,
               "media": nan, "ic95_inf": nan, "ic95_sup": nan, "mediana": nan,
               "vitorias": int((x < 0).sum()), "abaixo_limiar": int((x < threshold_pct).sum()),
               "p": nan, "p_min_possivel": 0.5 ** n if n else nan}
        if n:
            row["media"], row["mediana"] = float(x.mean()), float(np.median(x))
        if n >= 2:
            half = float(stats.t.ppf(0.975, n - 1) * x.std(ddof=1) / np.sqrt(n))
            row["ic95_inf"], row["ic95_sup"] = row["media"] - half, row["media"] + half
            if principal and np.any(x != threshold_pct):
                row["p"] = float(stats.wilcoxon(x - threshold_pct, alternative="less").pvalue)
        rows.append(row)

    # Holm-Bonferroni (step-down) sobre as comparações com p calculado
    order = sorted((i for i, r in enumerate(rows) if np.isfinite(r["p"])), key=lambda i: rows[i]["p"])
    running = 0.0
    for k, i in enumerate(order):
        running = max(running, min(1.0, (len(order) - k) * rows[i]["p"]))
        rows[i]["p_holm"] = running
    for r in rows:
        r.setdefault("p_holm", nan)
        r["rejeita_h0"] = bool(np.isfinite(r["p_holm"]) and r["p_holm"] < alpha)
        r["alpha"] = alpha
    return rows
