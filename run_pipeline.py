#!/usr/bin/env python3
"""
Pipeline experimental do TCC: H.264 (x264 / NVENC) x AV1 (SVT-AV1 / NVENC AV1).

Codifica as sequências, mede tempo, energia e qualidade, calcula BD-Rate, teste de hipótese
e projeção econômica, e gera tabelas (Markdown, Excel, CSV, JSON), gráficos e recortes visuais.
"""
import argparse
import json
import math
import os
import sys

# UTF-8 no console Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from rich.console import Console
from rich.panel import Panel
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn, TimeElapsedColumn

from pipeline.bjontegaard import bd_metric, bd_rate, significance_by_comparison, value_at_quality
from pipeline.crops import make_crop_comparison
from pipeline.decode import benchmark_decode
from pipeline.economics import calculate_economic_projections, sensitivity_analysis
from pipeline.encoder import SkipEncode, VideoEncoder
from pipeline.hardware import collect_all_environment_info
from pipeline.metrics import QualityAssessor
from pipeline.monitor import measure_idle_power
from pipeline.plots import (
    plot_decoding_benchmark,
    plot_economic_breakeven,
    plot_encoding_fps,
    plot_frame_vmaf_stability,
    plot_rd_curve_butteraugli,
    plot_rd_curve_cvvdp,
    plot_rd_curve_psnr,
    plot_rd_curve_ssimulacra2,
    plot_rd_curve_vmaf,
    plot_rd_curve_xpsnr,
    plot_siti_scatter,
)
from pipeline.reporter import (
    export_csv_tables,
    export_json_database,
    generate_excel_workbook,
    generate_markdown_report,
)
from pipeline.siti import calculate_siti
from pipeline.synthetic import generate_synthetic_samples
from pipeline.utils import is_lossless_source, set_command_log, sha256_file

console = Console()


def load_config(config_path: str) -> dict:
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    raise FileNotFoundError(f"Arquivo de configuração não encontrado: {config_path}")


def resolve_output_path(row: dict, sample_path: str, codecs_cfg: dict, encoded_dir: str) -> str:
    """Resolve com exatidão o caminho do arquivo codificado .mp4 para um ensaio."""
    out_p = row.get("output_path", "")
    if out_p and os.path.exists(out_p):
        return out_p
    val_tag = f"q{row['target_value']}" if row.get("mode") == "quality" else f"{row.get('target_value')}k"
    c_key = row.get("codec")
    s_base = os.path.splitext(os.path.basename(sample_path))[0]
    preset = codecs_cfg.get(c_key, {}).get("preset") if codecs_cfg else None
    if "Preset" in row.get("codec_label", ""):
        p_val = row["codec_label"].split("Preset ")[1].split(")")[0]
        fname = f"{s_base}_{c_key}_p{p_val}_{val_tag}_p{p_val}.mp4"
    elif preset is not None:
        fname = f"{s_base}_{c_key}_p{preset}_{val_tag}.mp4"
    else:
        fname = f"{s_base}_{c_key}_{val_tag}.mp4"
    candidate = os.path.join(encoded_dir, fname)
    if os.path.exists(candidate):
        return candidate

    if os.path.exists(encoded_dir):
        for f in os.listdir(encoded_dir):
            if f.startswith(s_base) and f"_{c_key}_" in f and (f"_{val_tag}." in f or f"_{val_tag}_" in f):
                cand = os.path.join(encoded_dir, f)
                if os.path.exists(cand):
                    return cand
    return ""


def closest_to_vmaf(rows: list, target: float):
    """Ponto R-D com VMAF mais próximo do alvo de iso-qualidade (comparações visuais justas)."""
    rows = [r for r in rows if r.get("mode", "quality") == "quality" and math.isfinite(r.get("vmaf_mean", float("nan")))]
    return min(rows, key=lambda r: abs(r["vmaf_mean"] - target)) if rows else None


def iso_projection(rd_data_by_sample: dict, codec_keys: list, codecs_cfg: dict, target: float,
                   econ_cfg: dict, baseline: str):
    """
    Projeção econômica em iso-qualidade (VMAF = target): bitrate, tempo e energia interpolados no MESMO
    ponto, sem extrapolar. Só entram amostras em que TODOS os codificadores atingem o alvo (mesmo conjunto).
    Retorna (projeções, amostras excluídas).
    """
    iso_br = {c: [] for c in codec_keys}
    enc_in = {c: {"encode_s_per_content_s": [], "energy_wh_per_content_s": []} for c in codec_keys}
    excluded = []
    for s_name, by_codec in rd_data_by_sample.items():
        iso_this = {}
        for c_k in codec_keys:
            rows = by_codec.get(c_k, [])
            if not rows:
                continue
            rates = [r["real_bitrate_kbps"] for r in rows]
            vmafs = [r["vmaf_mean"] for r in rows]
            t_ratios = [r["encode_s_per_content_s"] for r in rows]
            # energy_wh é do clipe inteiro: divide pela duração (tempo / razão tempo-por-segundo-de-conteúdo)
            e_ratios = [r["energy_wh"] * r["encode_s_per_content_s"] / r["encoding_time_s"] if r.get("encoding_time_s") else float("nan") for r in rows]
            iso_this[c_k] = (value_at_quality(vmafs, rates, target),
                             value_at_quality(vmafs, t_ratios, target, log_scale=False),
                             value_at_quality(vmafs, e_ratios, target, log_scale=False))
        if iso_this and all(v[0] is not None for v in iso_this.values()):
            for c_k, (br, t, e) in iso_this.items():
                iso_br[c_k].append(br)
                if t is not None:
                    enc_in[c_k]["encode_s_per_content_s"].append(t)
                if e is not None:
                    enc_in[c_k]["energy_wh_per_content_s"].append(e)
        elif iso_this:
            excluded.append(s_name)
            faltam = [c for c, v in iso_this.items() if v[0] is None]
            console.print(f"  [yellow]VMAF {target:g} — {s_name}: {', '.join(faltam)} não atinge(m) o alvo na faixa medida; amostra excluída desta projeção.[/yellow]")

    mean = lambda xs: sum(xs) / len(xs) if xs else None
    avg_br = {c: mean(iso_br[c]) for c in codec_keys}
    agg = {c: {"encode_s_per_content_s": mean(enc_in[c]["encode_s_per_content_s"]) or 0.0,
               "energy_wh_per_content_s": mean(enc_in[c]["energy_wh_per_content_s"]) or 0.0,
               "device": codecs_cfg.get(c, {}).get("device", "cpu")} for c in codec_keys}
    proj = calculate_economic_projections(iso_bitrates=avg_br, encode_inputs=agg, econ=econ_cfg, baseline=baseline)
    n_ok = len(rd_data_by_sample) - len(excluded)
    for p in proj.values():
        p["n_amostras"] = n_ok
    return proj, excluded


def build_extra_tables(economics_by_target: dict, excluded_by_target: dict, baseline: str, codecs_cfg: dict,
                       matrix_rows: list, rd_data_by_sample: dict, config: dict) -> list:
    """Tabela 5b (economia por alvo de qualidade) e Tabela 8 (presets do SVT-AV1 com BD-Rate vs. preset principal)."""
    f = lambda v, fmt: fmt.format(v) if isinstance(v, (int, float)) and v == v else "n/d"
    tables = []

    rows5b = []
    for t, proj in sorted(economics_by_target.items()):
        for c_k, p in proj.items():
            rows5b.append([f"VMAF {t:g}", codecs_cfg.get(c_k, {}).get("label", c_k), f(p["iso_bitrate_kbps"] / 1000, "{:.2f}"),
                           "Base" if c_k == baseline else f(-p.get("egress_savings_pct", float("nan")), "{:+.1f} %"),
                           f"{p.get('n_amostras', 0)} ({len(excluded_by_target.get(t, []))} excl.)"])
    tables.append({
        "title": "Tabela 5b — Bitrate e Economia por Alvo de Qualidade (streaming VMAF 93 / premium-arquivamento VMAF 95)",
        "header": ["Alvo", "Codificador", "Bitrate médio em iso-qualidade (Mbps)", "Variação vs. base (banda e armazenamento)", "Amostras na média"],
        "rows": rows5b, "csv": "tabela5b_economia_por_alvo.csv",
        "note": "Banda e armazenamento escalam linearmente com o bitrate, então a variação percentual é a mesma para ambos. "
                "Só entram amostras em que todos os codificadores atingem o alvo (excluídas listadas no JSON).",
    })

    pcfg = config.get("preset_test", {})
    main_p = str(codecs_cfg.get("svt-av1", {}).get("preset"))
    sample = pcfg.get("sample")
    ref = rd_data_by_sample.get(sample, {}).get("svt-av1", [])
    if ref:
        rows8 = []
        for p in pcfg.get("presets", []):
            rows = ref if str(p) == main_p else [r for r in matrix_rows if r.get("sample") == sample and r.get("codec_label") == f"SVT-AV1 (Preset {p})"]
            if not rows:
                continue
            bd = bd_rate([r["real_bitrate_kbps"] for r in ref], [r["vmaf_mean"] for r in ref],
                         [r["real_bitrate_kbps"] for r in rows], [r["vmaf_mean"] for r in rows])
            fps = sum(r["encoding_fps"] for r in rows) / len(rows)
            ref_fps = sum(r["encoding_fps"] for r in ref) / len(ref)
            rows8.append([f"Preset {p}" + (" (principal)" if str(p) == main_p else ""), f(fps, "{:.1f}"),
                          f(fps / ref_fps, "{:.2f}x"),
                          "referência" if str(p) == main_p else f(bd["value"], "{:+.2f} %") + ("" if bd["valid"] else " *"),
                          f(bd["overlap_pct"], "{:.0f} %")])
        tables.append({
            "title": f"Tabela 8 — Variação de Presets do SVT-AV1 ({sample}, curva R-D completa)",
            "header": ["Preset", "FPS médio", "Velocidade relativa", f"BD-Rate VMAF vs. Preset {main_p}", "Sobreposição"],
            "rows": rows8, "csv": "tabela8_presets_svtav1.csv",
            "note": "BD-Rate positivo = o preset precisa de mais bitrate que o principal para a mesma qualidade.",
        })
    return tables


def get_sample_metadata(sample: dict, siti_results: list, s_idx: int = None) -> dict:
    """Retorna metadados do vídeo com segurança contra IndexError."""
    if s_idx is not None and 0 <= s_idx < len(siti_results):
        item = siti_results[s_idx]
        if isinstance(item, dict) and "metadata" in item:
            return item["metadata"]
    for s in siti_results:
        if isinstance(s, dict) and s.get("nome") == sample.get("nome") and "metadata" in s:
            return s["metadata"]
    from pipeline.siti import get_video_metadata
    return get_video_metadata(sample["path"])


def recompute_metrics_for_matrix_rows(matrix_rows: list, samples_to_process: list, siti_results: list,
                                     assessor: QualityAssessor, encoded_dir: str, metrics_mode: str = "all",
                                     codecs_cfg: dict = None, workers: int = 2):
    """Recalcula todas as 7 métricas (CVVDP, XPSNR, SSIMULACRA2, Butteraugli, etc.) para vídeos já codificados."""
    console.print("\n[bold cyan]Processando avaliação de qualidade visual (CVVDP, XPSNR, SSIMULACRA2, Butteraugli)...[/bold cyan]")
    sample_map = {s["nome"]: (s, get_sample_metadata(s, siti_results)) for s in samples_to_process}
    metrics_list = None
    if metrics_mode == "vmaf":
        metrics_list = ["vmaf", "psnr", "ssim"]
    elif metrics_mode == "fast":
        metrics_list = ["vmaf", "psnr", "ssim", "xpsnr"]

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TimeElapsedColumn(),
        console=console
    ) as progress:
        ALL_M = ["vmaf", "psnr", "ssim", "xpsnr", "ssimulacra2", "butteraugli", "cvvdp"]
        wanted = metrics_list or ALL_M
        if workers > 1:
            # Duas filas independentes: CPU (libvmaf/xpsnr) e GPU (FFVship). Cada uma anda no próprio ritmo,
            # então a GPU avalia um vídeo enquanto a CPU calcula o VMAF de outro. Resultado idêntico ao sequencial.
            jobs = [[m for m in wanted if m in ("vmaf", "psnr", "ssim", "xpsnr")],
                    [m for m in wanted if m in ("ssimulacra2", "butteraugli", "cvvdp")]]
            jobs = [j for j in jobs if j]
        else:
            jobs = [wanted]
        task = progress.add_task("[cyan]Calculando métricas...", total=len(matrix_rows) * len(jobs))

        def _one(r, metrics_to_run):
            s_name = r.get("sample")
            if s_name not in sample_map:
                progress.advance(task)
                return
            sample, s_meta = sample_map[s_name]

            out_p = resolve_output_path(r, sample["path"], codecs_cfg, encoded_dir)
            if out_p and os.path.exists(out_p):
                r["output_path"] = out_p
                progress.update(task, description=f"[cyan]{s_name}[/cyan] | {r.get('codec')} ({os.path.basename(out_p)})")
                met = assessor.calculate_metrics(
                    encoded_path=out_p,
                    reference_path=sample["path"],
                    width=s_meta["width"],
                    height=s_meta["height"],
                    metrics_to_run=metrics_to_run
                )
                for k in ["vmaf_mean", "vmaf_min_1pct", "vmaf_neg_mean", "psnr_mean", "psnr_yuv_mean",
                          "ssim_mean", "ms_ssim_mean", "xpsnr_yuv_mean", "ssimulacra2_mean",
                          "butteraugli_2norm", "butteraugli_3norm", "cvvdp_score"]:
                    if k in met:
                        r[k] = met[k]

            progress.advance(task)

        from concurrent.futures import ThreadPoolExecutor
        pools = [ThreadPoolExecutor(max_workers=1) for _ in jobs]
        try:
            futs = [pool.submit(_one, r, job) for pool, job in zip(pools, jobs) for r in matrix_rows]
            for f in futs:
                f.result()  # propaga exceções
        finally:
            for pool in pools:
                pool.shutdown()


def main():
    parser = argparse.ArgumentParser(description="Pipeline experimental do TCC (H.264 x AV1)")
    parser.add_argument("--config", default="config.json", help="Arquivo de configuração JSON")
    parser.add_argument("--samples-dir", default="samples", help="Diretório onde estão os vídeos brutos de amostra")
    parser.add_argument("--mode", choices=["quality", "bitrate", "all"], default="quality",
                        help="Modo de varredura: quality (CRF/CQ, usado no TCC) ou bitrate (VBR restrito)")
    parser.add_argument("--generate-synthetic", action="store_true", help="Gera as amostras sintéticas brutas Y4M")
    parser.add_argument("--quick-test", action="store_true", help="Modo rápido de validação do pipeline (~1-2 min)")
    parser.add_argument("--test-presets", action="store_true", help="Executa a variação de presets do SVT-AV1")
    parser.add_argument("--test-decode", action="store_true", help="Executa benchmark de decodificação no cliente (dav1d vs. NVDEC)")
    parser.add_argument("--test-grain", action="store_true", help="Executa o teste de síntese de grão do SVT-AV1")
    parser.add_argument("--generate-crops", action="store_true", help="Gera recortes visuais ampliados lado a lado")
    parser.add_argument("--skip-metrics", action="store_true", help="Pula cálculo de métricas (apenas testa codificação e velocidade)")
    parser.add_argument("--skip-encoding", action="store_true", help="Reutiliza dados já gerados para recriar tabelas e gráficos")
    parser.add_argument("--recompute-metrics", action="store_true", help="Recalcula as 7 métricas (CVVDP, XPSNR, SSIMULACRA2, etc.) nos vídeos já codificados")
    parser.add_argument("--metrics-workers", type=int, default=2,
                        help="--recompute-metrics: 2 = filas paralelas de CPU (VMAF/XPSNR) e GPU (FFVship); 1 = sequencial")
    parser.add_argument("--metrics-mode", choices=["all", "vmaf", "fast"], default="all",
                        help="Conjunto de métricas: all (todas as 7), vmaf (apenas VMAF/PSNR/SSIM), fast (VMAF + XPSNR)")
    args = parser.parse_args()

    console.print(Panel.fit(
        "[bold cyan]PIPELINE DE AVALIAÇÃO DE CODIFICADORES — TCC[/bold cyan]\n"
        "[dim]Comparativo Experimental: H.264 (libx264/NVENC) vs. AV1 (SVT-AV1/NVENC AV1)[/dim]",
        border_style="cyan"
    ))

    config = load_config(args.config)
    output_dir = config.get("output_dir", "output")
    if args.quick_test:
        output_dir += "_quick"  # nunca sobrescreve os resultados oficiais
    encoded_dir = os.path.join(output_dir, "encoded")
    metrics_dir = os.path.join(output_dir, "metrics")
    plots_dir = os.path.join(output_dir, "graficos")
    crops_dir = os.path.join(output_dir, "recortes")

    for d in [output_dir, encoded_dir, metrics_dir, plots_dir, crops_dir]:
        os.makedirs(d, exist_ok=True)

    # Iniciar registro de comandos para reprodutibilidade
    set_command_log(os.path.join(output_dir, "comandos_executados.jsonl"))

    # Medir potência de repouso de CPU e GPU para cálculo de energia líquida
    console.print("[dim]Medindo potência de repouso (idle) de CPU e GPU...[/dim]")
    cpu_tdp_w = float(config.get("energy", {}).get("cpu_tdp_watts", 120.0))
    idle_info = measure_idle_power(2.0, cpu_tdp_w)
    gpu_idle_w = idle_info["gpu_idle_w"]
    cpu_idle_w = idle_info["cpu_idle_w"]
    cpu_power_source = idle_info["cpu_power_source"]
    if cpu_power_source != "Estimativa TDP":
        console.print(f"  [bold green]Telemetria física da CPU ativa ({cpu_power_source})![/bold green] Idle CPU: [cyan]{cpu_idle_w:.2f} W[/cyan] | Idle GPU: [cyan]{gpu_idle_w:.2f} W[/cyan]")
    else:
        console.print(f"  [yellow]Sensor físico de CPU não detectado (usando modelo TDP {cpu_tdp_w:.0f}W). Idle GPU: [cyan]{gpu_idle_w:.2f} W[/cyan][/yellow]")

    # -------------------------------------------------------------
    # ETAPA 1: Hardware e Ambiente Experimental (Tabela 1)
    # -------------------------------------------------------------
    console.print("\n[bold green][1/8] Coletando especificações reais do ambiente experimental...[/bold green]")
    env_info = collect_all_environment_info()
    console.print(f"  [cyan]CPU:[/cyan] {env_info['cpu']['descricao']}")
    console.print(f"  [cyan]GPU:[/cyan] {env_info['gpu']['descricao']}")
    console.print(f"  [cyan]RAM:[/cyan] {env_info['ram']['descricao']}")
    console.print(f"  [cyan]SO:[/cyan]  {env_info['os']['descricao']}")
    console.print(f"  [cyan]FFmpeg:[/cyan] {env_info['ffmpeg']['versao']}")
    libs = env_info['ffmpeg'].get('bibliotecas', {})
    console.print(f"  [cyan]Libs:[/cyan] x264={libs.get('x264')} | SVT-AV1={libs.get('SVT-AV1')} | dav1d={libs.get('dav1d')} | libvmaf={libs.get('libvmaf')}")

    # -------------------------------------------------------------
    # ETAPA 2: Amostras de Vídeo e Caracterização SI/TI (Tabela 2)
    # -------------------------------------------------------------
    console.print("\n[bold green][2/8] Analisando vídeos de amostra, SI/TI (ITU-T P.910) e integridade...[/bold green]")
    samples_dir = args.samples_dir
    os.makedirs(samples_dir, exist_ok=True)

    existing_files = [f for f in os.listdir(samples_dir) if f.lower().endswith((".y4m", ".mp4", ".mkv", ".mov", ".yuv"))]
    if args.generate_synthetic or not existing_files:
        dur = 2 if args.quick_test else 5
        console.print(f"  [yellow]Gerando sequências brutas Y4M calibradas ({dur}s)...[/yellow]")
        generate_synthetic_samples(samples_dir, resolution="1920x1080", fps=60, duration=dur)
        existing_files = [f for f in os.listdir(samples_dir) if f.lower().endswith((".y4m", ".mp4", ".mkv", ".mov", ".yuv"))]

    configured_samples = config.get("samples", [])
    samples_to_process = []

    for s_def in configured_samples:
        fname = s_def.get("filename")
        fpath = os.path.join(samples_dir, fname)
        if not os.path.exists(fpath):
            # Tentar fallback com extensão alternativa caso o usuário tenha .mp4 ou .y4m
            base_fn = os.path.splitext(fname)[0]
            alt = [f for f in existing_files if os.path.splitext(f)[0] == base_fn]
            if alt:
                fpath = os.path.join(samples_dir, alt[0])
            else:
                # Tentar correspondência por palavras-chave (ex: grain/grao, baixo/low, medio/med, etc.)
                fname_l = fname.lower()
                for ef in existing_files:
                    ef_l = ef.lower()
                    if (("grain" in fname_l or "grao" in fname_l) and ("grain" in ef_l or "grao" in ef_l)) or \
                       (("baixo" in fname_l or "low" in fname_l) and ("baixo" in ef_l or "low" in ef_l)) or \
                       (("medio" in fname_l or "mid" in fname_l) and ("medio" in ef_l or "mid" in ef_l)) or \
                       (("alto" in fname_l or "high" in fname_l) and ("alto" in ef_l or "high" in ef_l)):
                        fpath = os.path.join(samples_dir, ef)
                        break

        if os.path.exists(fpath):
            samples_to_process.append({
                "nome": s_def.get("name", fname),
                "path": fpath,
                "classificacao_override": s_def.get("classificacao"),
                "bitrates_kbps": s_def.get("bitrates_kbps", [2000, 4000, 8000, 12000]),
                "grain_test": s_def.get("grain_test", False)
            })

    if not samples_to_process:
        for idx, f in enumerate(sorted(existing_files)):
            samples_to_process.append({
                "nome": f"Amostra {idx + 1} ({f})",
                "path": os.path.join(samples_dir, f),
                "classificacao_override": None,
                "bitrates_kbps": [2000, 4000, 8000, 12000],
                "grain_test": False
            })

    if args.quick_test:
        samples_to_process = samples_to_process[:1]

    siti_results = []
    has_compressed_warning = False

    json_path = os.path.join(output_dir, "resultados_completos.json")
    cached_data = None
    if (args.skip_encoding or args.recompute_metrics) and os.path.exists(json_path):
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                cached_data = json.load(f)
        except Exception:
            cached_data = None

    cached_siti = {}
    if cached_data and cached_data.get("siti_samples") and (args.skip_encoding or args.recompute_metrics):
        cached_siti = {s.get("nome"): s for s in cached_data["siti_samples"] if isinstance(s, dict)}

    for s in samples_to_process:
        s_name = s["nome"]
        if s_name in cached_siti and "metadata" in cached_siti[s_name]:
            siti_results.append(cached_siti[s_name])
            console.print(f"  [dim]Reutilizando caracterização SI/TI em cache para '{s_name}'.[/dim]")
        else:
            console.print(f"  Analisando complexidade SI e TI para [bold]{s_name}[/bold]...")
            s_data = calculate_siti(s["path"], max_frames=180 if args.quick_test else None)
            s_data["nome"] = s_name
            s_data["classificacao_override"] = s["classificacao_override"]

            # Checagem de lossless e hash
            is_lossless = is_lossless_source(s["path"])
            sha = sha256_file(s["path"])
            s_data["is_lossless"] = is_lossless
            s_data["sha256"] = sha

            if not is_lossless:
                has_compressed_warning = True
                console.print(f"    [bold red]ATENÇÃO:[/bold red] '{s_name}' é um arquivo já comprimido. Para dados finais do TCC, use Y4M/YUV sem perdas!")

            siti_results.append(s_data)
            console.print(f"    SI Máx: [cyan]{s_data['si_max']:.2f}[/cyan] | TI Máx: [cyan]{s_data['ti_max']:.2f}[/cyan] | SHA-256: {sha[:12]}...")

    # Gráfico 5: Diagrama SI x TI
    plot_siti_scatter(siti_results, plots_dir)

    # -------------------------------------------------------------
    # ETAPA 3: Codificação Experimental e Avaliação de Qualidade
    # -------------------------------------------------------------
    console.print("\n[bold green][3/8] Executando codificação com medições de tempo, recursos e qualidade...[/bold green]")
    encoding_cfg = config.get("encoding", {})
    if args.quick_test:
        encoding_cfg = dict(encoding_cfg)
        encoding_cfg["repetitions"] = 1

    encoder = VideoEncoder(output_dir=encoded_dir, encoding_cfg=encoding_cfg,
                           cpu_tdp_w=cpu_tdp_w, gpu_idle_w=gpu_idle_w, cpu_idle_w=cpu_idle_w)
    assessor = QualityAssessor(metrics_dir=metrics_dir)

    codecs_cfg = config.get("codecs", {})
    if args.quick_test:
        # No teste rápido, testa apenas o baseline e o SVT-AV1
        test_codec_keys = ["h264", "svt-av1"]
    else:
        test_codec_keys = list(codecs_cfg.keys())

    matrix_rows = []
    rd_data_by_sample = {}
    fps_by_sample = {}
    frame_vmaf_by_sample = {}
    encoded_paths_catalog = {}  # sample -> codec -> path

    # Planejar passos de execução
    test_plans = []
    for s_idx, sample in enumerate(samples_to_process):
        s_name = sample["nome"]
        rd_data_by_sample[s_name] = {c: [] for c in test_codec_keys}
        fps_by_sample[s_name] = {c: {"avg_fps": 0.0, "avg_fps_std": 0.0, "fps_list": [], "fps_std_list": []} for c in test_codec_keys}
        frame_vmaf_by_sample[s_name] = {}
        encoded_paths_catalog[s_name] = {}

        for c_key in test_codec_keys:
            c_cfg = codecs_cfg.get(c_key, {})
            if args.mode in ["quality", "all"]:
                points = c_cfg.get("rd_points", [22, 28, 34, 40])
                if args.quick_test:
                    points = points[:2]
                for pt in points:
                    test_plans.append((sample, s_idx, c_key, c_cfg, "quality", pt))

            if args.mode in ["bitrate", "all"]:
                br_points = sample.get("bitrates_kbps", [4000, 8000])
                if args.quick_test:
                    br_points = br_points[:2]
                for br in br_points:
                    test_plans.append((sample, s_idx, c_key, c_cfg, "bitrate", br))

    if args.recompute_metrics:
        args.skip_encoding = True

    json_path = os.path.join(output_dir, "resultados_completos.json")
    cached_data = None
    if args.skip_encoding and os.path.exists(json_path):
        console.print("[yellow]Modo --skip-encoding ativo: Reutilizando ensaios e medições existentes de resultados_completos.json.[/yellow]")
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                cached_data = json.load(f)
            matrix_rows = cached_data.get("matrix_rows", [])

            # Resolver caminhos dos arquivos codificados em cache
            for r in matrix_rows:
                s_name = r.get("sample")
                matched_s = next((s for s in samples_to_process if s["nome"] == s_name), None)
                if matched_s:
                    resolved_p = resolve_output_path(r, matched_s["path"], codecs_cfg, encoded_dir)
                    if resolved_p:
                        r["output_path"] = resolved_p

            if args.recompute_metrics:
                recompute_metrics_for_matrix_rows(
                    matrix_rows=matrix_rows,
                    samples_to_process=samples_to_process,
                    siti_results=siti_results,
                    assessor=assessor,
                    encoded_dir=encoded_dir,
                    metrics_mode=args.metrics_mode,
                    codecs_cfg=codecs_cfg,
                    workers=args.metrics_workers
                )

            for r in matrix_rows:
                s_name = r.get("sample")
                c_key = r.get("codec")
                # linhas do teste de presets/grão têm codec "svt-av1" mas NÃO pertencem à curva R-D principal
                if "Preset" in r.get("codec_label", "") or "Grain" in r.get("codec_label", ""):
                    continue
                if s_name in rd_data_by_sample and c_key in rd_data_by_sample[s_name]:
                    if r.get("mode") == "quality":
                        rd_data_by_sample[s_name][c_key].append(r)
                    fps_by_sample[s_name][c_key]["fps_list"].append(r.get("encoding_fps", 0.0))
                    fps_by_sample[s_name][c_key]["fps_std_list"].append(r.get("encoding_fps_std", 0.0))
                if s_name in encoded_paths_catalog and c_key:
                    out_p = r.get("output_path", "")
                    if out_p and os.path.exists(out_p):
                        encoded_paths_catalog[s_name][c_key] = out_p

            for s_idx, sample in enumerate(samples_to_process):
                s_name = sample["nome"]
                for c_k in test_codec_keys:
                    for r in rd_data_by_sample[s_name].get(c_k, []):
                        enc_name = os.path.splitext(os.path.basename(r.get("output_path", "")))[0]
                        vmaf_json = os.path.join(metrics_dir, f"{enc_name}_vmaf.json")
                        if os.path.exists(vmaf_json):
                            try:
                                with open(vmaf_json, "r", encoding="utf-8") as jf:
                                    fr_data = json.load(jf)
                                    v_frames = [float(fr["metrics"]["vmaf"]) for fr in fr_data.get("frames", []) if "vmaf" in fr.get("metrics", {})]
                                    if v_frames:
                                        frame_vmaf_by_sample[s_name][c_k] = v_frames
                                        break
                            except Exception:
                                pass
        except Exception as e:
            console.print(f"[bold red]Erro ao processar cache: {e}.[/bold red]")
            import traceback
            traceback.print_exc()
            if args.recompute_metrics or args.skip_encoding:
                sys.exit(1)
            cached_data = None

    if not (args.skip_encoding and cached_data):
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TimeElapsedColumn(),
            console=console
        ) as progress:
            task = progress.add_task("[cyan]Executando ensaios...", total=len(test_plans))

            metrics_list = None
            if args.metrics_mode == "vmaf":
                metrics_list = ["vmaf", "psnr", "ssim"]
            elif args.metrics_mode == "fast":
                metrics_list = ["vmaf", "psnr", "ssim", "xpsnr"]

            warmed = set()
            for sample, s_idx, c_key, c_cfg, mode, val in test_plans:
                s_name = sample["nome"]
                s_path = sample["path"]
                s_meta = get_sample_metadata(sample, siti_results, s_idx)
                if s_path not in warmed:
                    # Lê a amostra uma vez antes de cronometrar: sem isso a 1ª repetição da 1ª codificação
                    # inclui a leitura do disco (cache frio) e infla o tempo (observado: CV de até 33%).
                    progress.update(task, description=f"[cyan]{s_name}[/cyan] | aquecendo cache de leitura")
                    with open(s_path, "rb") as fh:
                        while fh.read(64 * 1024 * 1024):
                            pass
                    warmed.add(s_path)
                progress.update(task, description=f"[cyan]{s_name}[/cyan] | {c_key} ({mode}={val})")

                try:
                    enc_res = encoder.encode(
                        input_path=s_path,
                        codec_key=c_key,
                        codec_cfg=c_cfg,
                        mode=mode,
                        value=val,
                        video_meta=s_meta
                    )
                except SkipEncode as e:
                    console.print(f"[yellow]Pulando {c_key}: {e}[/yellow]")
                    progress.advance(task)
                    continue

                encoded_paths_catalog[s_name][c_key] = enc_res["output_path"]

                # Medição de qualidade (todas as 7 métricas)
                if not args.skip_metrics:
                    met_res = assessor.calculate_metrics(
                        encoded_path=enc_res["output_path"],
                        reference_path=s_path,
                        width=s_meta["width"],
                        height=s_meta["height"],
                        pix_fmt=enc_res["pix_fmt"],
                        metrics_to_run=metrics_list,
                        force=True
                    )
                else:
                    # vídeo novo: apaga métricas antigas de mesmo nome para o --recompute-metrics não reaproveitá-las
                    stem = os.path.splitext(os.path.basename(enc_res["output_path"]))[0]
                    for ext in ("_vmaf.json", "_xpsnr.log", "_ssimulacra2.json", "_butteraugli.json", "_cvvdp.json"):
                        old_m = os.path.join(metrics_dir, stem + ext)
                        if os.path.exists(old_m):
                            os.remove(old_m)
                    met_res = {
                        k: float("nan") for k in ["vmaf_mean", "vmaf_min_1pct", "vmaf_neg_mean", "psnr_mean",
                                                  "psnr_yuv_mean", "ssim_mean", "ms_ssim_mean", "xpsnr_yuv_mean",
                                                  "ssimulacra2_mean", "butteraugli_2norm", "butteraugli_3norm",
                                                  "cvvdp_score"]
                    }

                param_lbl = f"CRF/CQ {val}" if mode == "quality" else f"Target {val // 1000} Mbps"
                row = {
                    "sample": s_name,
                    "codec": c_key,
                    "codec_label": c_cfg.get("label", c_key),
                    "param_label": param_lbl,
                    "mode": mode,
                    "target_value": val,
                    "output_path": enc_res["output_path"],
                    "real_bitrate_kbps": enc_res["real_bitrate_kbps"],
                    "file_size_mb": enc_res["file_size_mb"],
                    "stream_size_mb": enc_res["stream_size_mb"],
                    "encoding_time_s": enc_res["encoding_time_s"],
                    "encoding_time_std_s": enc_res["encoding_time_std_s"],
                    "encoding_fps": enc_res["encoding_fps"],
                    "encoding_fps_std": enc_res["encoding_fps_std"],
                    "real_time_factor": enc_res["real_time_factor"],
                    "encode_s_per_content_s": enc_res["encode_s_per_content_s"],
                    "cpu_util_pct": enc_res["cpu_util_pct"],
                    "cpu_power_w": enc_res.get("cpu_power_w"),
                    "cpu_power_source": enc_res.get("cpu_power_source", "Estimativa TDP"),
                    "gpu_util_pct": enc_res["gpu_util_pct"],
                    "gpu_power_w": enc_res.get("gpu_power_w"),
                    "energy_wh": enc_res["energy_wh"],
                    "vmaf_mean": met_res.get("vmaf_mean", float("nan")),
                    "vmaf_min_1pct": met_res.get("vmaf_min_1pct", float("nan")),
                    "vmaf_neg_mean": met_res.get("vmaf_neg_mean", float("nan")),
                    "psnr_mean": met_res.get("psnr_mean", float("nan")),
                    "psnr_yuv_mean": met_res.get("psnr_yuv_mean", float("nan")),
                    "ssim_mean": met_res.get("ssim_mean", float("nan")),
                    "ms_ssim_mean": met_res.get("ms_ssim_mean", float("nan")),
                    "xpsnr_yuv_mean": met_res.get("xpsnr_yuv_mean", float("nan")),
                    "ssimulacra2_mean": met_res.get("ssimulacra2_mean", float("nan")),
                    "butteraugli_2norm": met_res.get("butteraugli_2norm", float("nan")),
                    "butteraugli_3norm": met_res.get("butteraugli_3norm", float("nan")),
                    "cvvdp_score": met_res.get("cvvdp_score", float("nan")),
                }
                matrix_rows.append(row)

                # Salvar ponto para curvas R-D
                rd_data_by_sample[s_name][c_key].append(row)
                fps_by_sample[s_name][c_key]["fps_list"].append(enc_res["encoding_fps"])
                fps_by_sample[s_name][c_key]["fps_std_list"].append(enc_res["encoding_fps_std"])

                # Estabilidade temporal para um ponto intermediário representativo
                if c_key not in frame_vmaf_by_sample[s_name] and met_res.get("vmaf_frames"):
                    frame_vmaf_by_sample[s_name][c_key] = met_res["vmaf_frames"]

                progress.advance(task)

    # Calcular médias de rendimento (FPS) com desvio padrão agrupado
    for s_name in fps_by_sample:
        for c_key in fps_by_sample[s_name]:
            lst = fps_by_sample[s_name][c_key]["fps_list"]
            if lst:
                fps_by_sample[s_name][c_key]["avg_fps"] = sum(lst) / len(lst)
                std_lst = fps_by_sample[s_name][c_key]["fps_std_list"]
                fps_by_sample[s_name][c_key]["avg_fps_std"] = sum(std_lst) / len(std_lst) if std_lst else 0.0

    if not (args.skip_encoding and cached_data):
        # -------------------------------------------------------------
        # ETAPA 4: Variação de Presets no SVT-AV1
        # -------------------------------------------------------------
        if args.test_presets and not args.quick_test:
            console.print("\n[bold green][4/8] Executando variação de Presets no SVT-AV1 (Presets 4, 6, 8, 10)...[/bold green]")
            preset_cfg = config.get("preset_test", {})
            presets_to_test = preset_cfg.get("presets", ["4", "6", "8", "10"])
            ref_sample = next((s for s in samples_to_process if s["nome"] == preset_cfg.get("sample")), samples_to_process[0])
            s_meta = get_sample_metadata(ref_sample, siti_results)
            main_preset = str(codecs_cfg.get("svt-av1", {}).get("preset"))
            # curva R-D completa por preset; o preset principal reutiliza a curva já codificada
            preset_plan = [(p, q) for p in presets_to_test if str(p) != main_preset
                           for q in codecs_cfg.get("svt-av1", {}).get("rd_points", [])]

            for p_val, q_val in preset_plan:
                console.print(f"  Testando SVT-AV1 com Preset [cyan]{p_val}[/cyan], CRF {q_val}...")
                c_cfg = dict(codecs_cfg.get("svt-av1", {}))
                c_cfg["preset"] = p_val
                enc_p = encoder.encode(ref_sample["path"], "svt-av1", c_cfg, "quality", q_val, s_meta, tag=f"_p{p_val}")
                met_p = assessor.calculate_metrics(enc_p["output_path"], ref_sample["path"], s_meta["width"], s_meta["height"], force=True)
                matrix_rows.append({
                    "sample": ref_sample["nome"],
                    "codec": "svt-av1",
                    "codec_label": f"SVT-AV1 (Preset {p_val})",
                    "param_label": f"CRF {q_val} (Variação Preset)",
                    "mode": "quality",
                    "target_value": q_val,
                    "output_path": enc_p["output_path"],
                    "real_bitrate_kbps": enc_p["real_bitrate_kbps"],
                    "file_size_mb": enc_p["file_size_mb"],
                    "stream_size_mb": enc_p["stream_size_mb"],
                    "encoding_time_s": enc_p["encoding_time_s"],
                    "encoding_time_std_s": enc_p["encoding_time_std_s"],
                    "encoding_fps": enc_p["encoding_fps"],
                    "encoding_fps_std": enc_p["encoding_fps_std"],
                    "real_time_factor": enc_p["real_time_factor"],
                    "encode_s_per_content_s": enc_p["encode_s_per_content_s"],
                    "cpu_util_pct": enc_p["cpu_util_pct"],
                    "cpu_power_w": enc_p.get("cpu_power_w"),
                    "cpu_power_source": enc_p.get("cpu_power_source", "Estimativa TDP"),
                    "gpu_util_pct": enc_p["gpu_util_pct"],
                    "gpu_power_w": enc_p.get("gpu_power_w"),
                    "energy_wh": enc_p["energy_wh"],
                    "vmaf_mean": met_p.get("vmaf_mean", float("nan")),
                    "vmaf_min_1pct": met_p.get("vmaf_min_1pct", float("nan")),
                    "vmaf_neg_mean": met_p.get("vmaf_neg_mean", float("nan")),
                    "psnr_mean": met_p.get("psnr_mean", float("nan")),
                    "psnr_yuv_mean": met_p.get("psnr_yuv_mean", float("nan")),
                    "ssim_mean": met_p.get("ssim_mean", float("nan")),
                    "ms_ssim_mean": met_p.get("ms_ssim_mean", float("nan")),
                    "xpsnr_yuv_mean": met_p.get("xpsnr_yuv_mean", float("nan")),
                    "ssimulacra2_mean": met_p.get("ssimulacra2_mean", float("nan")),
                    "butteraugli_2norm": met_p.get("butteraugli_2norm", float("nan")),
                    "butteraugli_3norm": met_p.get("butteraugli_3norm", float("nan")),
                    "cvvdp_score": met_p.get("cvvdp_score", float("nan")),
                })

        # -------------------------------------------------------------
        # ETAPA 5: Teste de Síntese de Grão
        # -------------------------------------------------------------
        if args.test_grain and not args.quick_test:
            console.print("\n[bold green][5/8] Executando teste de Film Grain Synthesis no SVT-AV1...[/bold green]")
            grain_samples = [s for s in samples_to_process if s.get("grain_test")] or [samples_to_process[-1]]
            target_s = grain_samples[0]
            s_meta = get_sample_metadata(target_s, siti_results)
            g_lvl = config.get("grain_test", {}).get("film_grain_level", 8)
            g_crf = int(config.get("grain_test", {}).get("crf", 35))  # deve pertencer à grade do SVT-AV1

            console.print(f"  Codificando {target_s['nome']} com film-grain={g_lvl}...")
            enc_g = encoder.encode(target_s["path"], "svt-av1", codecs_cfg.get("svt-av1", {}),
                                   "quality", g_crf, s_meta, tag="_grain",
                                   extra_svt_params=[f"film-grain={g_lvl}", "film-grain-denoise=1"])
            met_g = assessor.calculate_metrics(enc_g["output_path"], target_s["path"], s_meta["width"], s_meta["height"], force=True)
            matrix_rows.append({
                "sample": target_s["nome"],
                "codec": "svt-av1",
                "codec_label": f"SVT-AV1 (Film Grain {g_lvl})",
                "param_label": f"CRF {g_crf} (Grain Synth)",
                "mode": "quality",
                "target_value": g_crf,
                "output_path": enc_g["output_path"],
                "real_bitrate_kbps": enc_g["real_bitrate_kbps"],
                "file_size_mb": enc_g["file_size_mb"],
                "stream_size_mb": enc_g["stream_size_mb"],
                "encoding_time_s": enc_g["encoding_time_s"],
                "encoding_time_std_s": enc_g["encoding_time_std_s"],
                "encoding_fps": enc_g["encoding_fps"],
                "encoding_fps_std": enc_g["encoding_fps_std"],
                "real_time_factor": enc_g["real_time_factor"],
                "encode_s_per_content_s": enc_g["encode_s_per_content_s"],
                "cpu_util_pct": enc_g["cpu_util_pct"],
                "cpu_power_w": enc_g.get("cpu_power_w"),
                "cpu_power_source": enc_g.get("cpu_power_source", "Estimativa TDP"),
                "gpu_util_pct": enc_g["gpu_util_pct"],
                "gpu_power_w": enc_g.get("gpu_power_w"),
                "energy_wh": enc_g["energy_wh"],
                "vmaf_mean": met_g.get("vmaf_mean", float("nan")),
                "vmaf_min_1pct": met_g.get("vmaf_min_1pct", float("nan")),
                "vmaf_neg_mean": met_g.get("vmaf_neg_mean", float("nan")),
                "psnr_mean": met_g.get("psnr_mean", float("nan")),
                "psnr_yuv_mean": met_g.get("psnr_yuv_mean", float("nan")),
                "ssim_mean": met_g.get("ssim_mean", float("nan")),
                "ms_ssim_mean": met_g.get("ms_ssim_mean", float("nan")),
                "xpsnr_yuv_mean": met_g.get("xpsnr_yuv_mean", float("nan")),
                "ssimulacra2_mean": met_g.get("ssimulacra2_mean", float("nan")),
                "butteraugli_2norm": met_g.get("butteraugli_2norm", float("nan")),
                "butteraugli_3norm": met_g.get("butteraugli_3norm", float("nan")),
                "cvvdp_score": met_g.get("cvvdp_score", float("nan")),
            })

    # -------------------------------------------------------------
    # ETAPA 6: Recortes Visuais Ampliados
    # -------------------------------------------------------------
    if args.generate_crops:
        console.print("\n[bold green][6/8] Gerando recortes visuais ampliados lado a lado...[/bold green]")
        crop_cfg = config.get("crops", {})
        for s_idx, sample in enumerate(samples_to_process):
            s_name = sample["nome"]
            s_meta = get_sample_metadata(sample, siti_results, s_idx)
            candidates = []
            crop_target = float(config.get("economics", {}).get("target_vmaf", 93.0))
            for c_k in ["h264", "svt-av1", "nvenc-av1"]:
                r_best = closest_to_vmaf(rd_data_by_sample.get(s_name, {}).get(c_k, []), crop_target)
                if r_best and os.path.exists(r_best["output_path"]):
                    lbl = f"{codecs_cfg.get(c_k, {}).get('label', c_k)} ({r_best['real_bitrate_kbps'] / 1000:.1f} Mbps, VMAF {r_best['vmaf_mean']:.1f})"
                    candidates.append((lbl, r_best["output_path"]))

            if candidates:
                mid_frame = min(60, s_meta["nb_frames"] // 2)
                make_crop_comparison(
                    reference=sample["path"],
                    items=candidates,
                    frame_idx=mid_frame,
                    meta=s_meta,
                    crop_cfg=crop_cfg,
                    out_dir=crops_dir,
                    base_name=f"recorte_visual_amostra_{s_idx + 1}",
                    title=f"Comparação Visual — {s_name}"
                )
                console.print(f"  Recorte gerado para [cyan]{s_name}[/cyan] (Quadro {mid_frame}).")

    # -------------------------------------------------------------
    # ETAPA 7: Benchmark de Decodificação no Cliente (Tabela 7)
    # -------------------------------------------------------------
    decode_rows = []
    if args.test_decode:
        console.print("\n[bold green][7/8] Executando benchmark de decodificação no espectador (Software vs NVDEC)...[/bold green]")
        ref_sample = samples_to_process[0]
        s_meta = get_sample_metadata(ref_sample, siti_results, 0)
        s_name = ref_sample["nome"]

        dec_target = float(config.get("economics", {}).get("target_vmaf", 93.0))
        for c_k, fam in [("h264", "h264"), ("svt-av1", "av1")]:
            rows_c = sorted(rd_data_by_sample.get(s_name, {}).get(c_k, []), key=lambda r: r["target_value"])
            r_best = closest_to_vmaf(rows_c, dec_target) or (rows_c[len(rows_c) // 2] if rows_c else None)
            enc_p = r_best["output_path"] if r_best else encoded_paths_catalog.get(s_name, {}).get(c_k)
            if enc_p and os.path.exists(enc_p):
                console.print(f"  Testando decodificação de stream {fam.upper()}...")
                dec_results = benchmark_decode(enc_p, fam, s_meta["nb_frames"], s_meta["duration"],
                                               repetitions=1 if args.quick_test else 3)
                decode_rows.extend(dec_results)

        plot_decoding_benchmark(decode_rows, plots_dir)
    elif cached_data and cached_data.get("decoding"):
        decode_rows = cached_data["decoding"]

    # -------------------------------------------------------------
    # ETAPA 8: Síntese Bjøntegaard Delta e Interpolação Iso-Qualidade
    # -------------------------------------------------------------
    console.print("\n[bold green][8/8] Calculando BD-Rate, interpolação iso-qualidade e projeções econômicas...[/bold green]")
    bd_results = []

    configured_comparisons = config.get("comparisons", [["svt-av1", "h264"], ["nvenc-av1", "h264"]])
    target_iso_vmaf = float(config.get("economics", {}).get("target_vmaf", 93.0))

    for s_name in rd_data_by_sample:
        # Calcular BD-Rate para cada par comparativo
        for test_c, ref_c in configured_comparisons:
            if test_c not in rd_data_by_sample[s_name] or ref_c not in rd_data_by_sample[s_name]:
                continue
            t_rows = rd_data_by_sample[s_name][test_c]
            r_rows = rd_data_by_sample[s_name][ref_c]
            if len(t_rows) < 2 or len(r_rows) < 2:
                continue

            r_rates = [r["real_bitrate_kbps"] for r in r_rows]
            t_rates = [r["real_bitrate_kbps"] for r in t_rows]

            # VMAF
            bdr_v = bd_rate(r_rates, [r["vmaf_mean"] for r in r_rows], t_rates, [r["vmaf_mean"] for r in t_rows])
            bdm_v = bd_metric(r_rates, [r["vmaf_mean"] for r in r_rows], t_rates, [r["vmaf_mean"] for r in t_rows])

            # PSNR-YUV
            bdr_p = bd_rate(r_rates, [r["psnr_yuv_mean"] for r in r_rows], t_rates, [r["psnr_yuv_mean"] for r in t_rows])
            bdm_p = bd_metric(r_rates, [r["psnr_yuv_mean"] for r in r_rows], t_rates, [r["psnr_yuv_mean"] for r in t_rows])

            # VMAF NEG
            bdr_neg = bd_rate(r_rates, [r["vmaf_neg_mean"] for r in r_rows], t_rates, [r["vmaf_neg_mean"] for r in t_rows])

            # XPSNR
            bdr_xp = bd_rate(r_rates, [r.get("xpsnr_yuv_mean", float("nan")) for r in r_rows], t_rates, [r.get("xpsnr_yuv_mean", float("nan")) for r in t_rows])

            # SSIMULACRA2
            bdr_s2 = bd_rate(r_rates, [r.get("ssimulacra2_mean", float("nan")) for r in r_rows], t_rates, [r.get("ssimulacra2_mean", float("nan")) for r in t_rows])

            # CVVDP
            bdr_cvvdp = bd_rate(r_rates, [r.get("cvvdp_score", float("nan")) for r in r_rows], t_rates, [r.get("cvvdp_score", float("nan")) for r in t_rows])

            test_label = codecs_cfg.get(test_c, {}).get("label", test_c)
            ref_label = codecs_cfg.get(ref_c, {}).get("label", ref_c)

            bd_results.append({
                "sequencia": s_name,
                "comparacao": f"{test_label} vs. {ref_label}",
                "test_codec": test_c,
                "ref_codec": ref_c,
                "bd_rate_vmaf": bdr_v["value"],
                "overlap_vmaf_pct": float(bdr_v["overlap_pct"]),
                "valid_vmaf": bool(bdr_v["valid"]),
                "bd_metric_vmaf": bdm_v["value"],
                "bd_rate_psnr": bdr_p["value"],
                "bd_metric_psnr": bdm_p["value"],
                "bd_rate_vmaf_neg": bdr_neg["value"],
                "bd_rate_xpsnr": bdr_xp["value"],
                "bd_rate_ssimulacra2": bdr_s2["value"],
                "bd_rate_cvvdp": bdr_cvvdp["value"],
            })

            val_str = f"{bdr_v['value']:+.2f}%" if bdr_v['value'] is not None else "n/d (sem sobreposição)"
            console.print(f"  [cyan]{s_name}[/cyan] ({test_c} vs {ref_c}): BD-Rate VMAF = [bold]{val_str}[/bold] (Sobreposição: {bdr_v['overlap_pct']:.1f}%)")

    sig_cfg = config.get("significance", {})
    stats_rows = significance_by_comparison(bd_results, float(sig_cfg.get("bd_rate_threshold_pct", -30.0)),
                                            float(sig_cfg.get("alpha", 0.05)),
                                            primary=sig_cfg.get("primary_comparisons"))
    for st in stats_rows:
        console.print(f"  [cyan]{st['comparacao']}[/cyan]: n={st['n']} | média {st['media']:+.2f}% | "
                      f"p(Holm)={st['p_holm']:.4f} → {'rejeita' if st['rejeita_h0'] else 'não rejeita'} H0")

    econ_cfg = config.get("economics", {})
    baseline_codec = config.get("baseline", "h264")
    iso_targets = sorted({float(t) for t in config.get("iso_quality_targets_vmaf", [])} | {target_iso_vmaf})
    economics_by_target, iso_excluded_by_target = {}, {}
    for t in iso_targets:
        economics_by_target[t], iso_excluded_by_target[t] = iso_projection(
            rd_data_by_sample, test_codec_keys, codecs_cfg, t, econ_cfg, baseline_codec)
    economics_data = economics_by_target[target_iso_vmaf]
    iso_excluded_samples = iso_excluded_by_target[target_iso_vmaf]

    # -------------------------------------------------------------
    # GERAÇÃO DE GRÁFICOS E RELATÓRIOS FINAIS
    # -------------------------------------------------------------
    console.print("\n[bold green]Gerando gráficos e compilando relatórios...[/bold green]")
    # Gráfico 4: estabilidade temporal no ponto de cada codec mais próximo da iso-qualidade
    for s_name in rd_data_by_sample:
        frame_vmaf_by_sample[s_name] = {}
        for c_k, rows in rd_data_by_sample[s_name].items():
            r_best = closest_to_vmaf(rows, target_iso_vmaf)
            if not r_best:
                continue
            vj = os.path.join(metrics_dir, os.path.splitext(os.path.basename(r_best["output_path"]))[0] + "_vmaf.json")
            if os.path.exists(vj):
                with open(vj, "r", encoding="utf-8") as jf:
                    frame_vmaf_by_sample[s_name][c_k] = [float(fr["metrics"]["vmaf"]) for fr in json.load(jf).get("frames", []) if "vmaf" in fr.get("metrics", {})]
    for s_name in rd_data_by_sample:
        plot_rd_curve_vmaf(rd_data_by_sample[s_name], s_name, plots_dir)
        plot_rd_curve_psnr(rd_data_by_sample[s_name], s_name, plots_dir)
        plot_rd_curve_xpsnr(rd_data_by_sample[s_name], s_name, plots_dir)
        plot_rd_curve_ssimulacra2(rd_data_by_sample[s_name], s_name, plots_dir)
        plot_rd_curve_butteraugli(rd_data_by_sample[s_name], s_name, plots_dir)
        plot_rd_curve_cvvdp(rd_data_by_sample[s_name], s_name, plots_dir)
        if s_name in frame_vmaf_by_sample and frame_vmaf_by_sample[s_name]:
            plot_frame_vmaf_stability(frame_vmaf_by_sample[s_name], s_name, plots_dir)

    plot_encoding_fps(fps_by_sample, plots_dir)
    plot_economic_breakeven(economics_data, econ_cfg, plots_dir)

    extra_tables = build_extra_tables(economics_by_target, iso_excluded_by_target, baseline_codec, codecs_cfg,
                                      matrix_rows, rd_data_by_sample, config)

    md_path = os.path.join(output_dir, "relatorio_tcc.md")
    xlsx_path = os.path.join(output_dir, "resultados_tcc.xlsx")
    json_path = os.path.join(output_dir, "resultados_completos.json")
    csv_dir = os.path.join(output_dir, "csv")

    generate_markdown_report(env_info, siti_results, matrix_rows, bd_results, economics_data, decode_rows, econ_cfg, md_path, stats_rows=stats_rows, extra_tables=extra_tables)
    generate_excel_workbook(env_info, siti_results, matrix_rows, bd_results, economics_data, decode_rows, xlsx_path, stats_rows=stats_rows, extra_tables=extra_tables)
    export_csv_tables(env_info, siti_results, matrix_rows, bd_results, economics_data, decode_rows, csv_dir, stats_rows=stats_rows, extra_tables=extra_tables)
    export_json_database({
        "environment": env_info,
        "siti_samples": siti_results,
        "matrix_rows": matrix_rows,
        "bd_results": bd_results,
        "significance_tests": stats_rows,
        "economics": economics_data,
        "iso_excluded_samples": iso_excluded_samples,
        "economics_by_target": {f"vmaf_{t:g}": v for t, v in economics_by_target.items()},
        "iso_excluded_by_target": {f"vmaf_{t:g}": v for t, v in iso_excluded_by_target.items()},
        "decoding": decode_rows
    }, json_path)

    console.print(Panel.fit(
        f"[bold green]Pipeline concluído.[/bold green]\n\n"
        f"[white]1. Relatório:[/white]        [cyan]{md_path}[/cyan]\n"
        f"[white]2. Planilha Excel:[/white]   [cyan]{xlsx_path}[/cyan]\n"
        f"[white]3. Tabelas CSV:[/white]      [cyan]{csv_dir}[/cyan]\n"
        f"[white]4. Base JSON:[/white]        [cyan]{json_path}[/cyan]\n"
        f"[white]5. Gráficos:[/white]         [cyan]{plots_dir}[/cyan]\n"
        f"[white]6. Log de Comandos Executados:[/white]   [cyan]{output_dir}/comandos_executados.jsonl[/cyan]",
        border_style="green"
    ))


if __name__ == "__main__":
    main()
