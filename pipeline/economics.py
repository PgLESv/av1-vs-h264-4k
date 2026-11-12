"""
Projeção econômica de armazenamento e tráfego (Tabela 5) e custos de produção/break-even (Tabela 6).

As taxas de bits usadas são as necessárias para atingir o mesmo VMAF alvo (93 ou 95),
obtidas por interpolação PCHIP na curva taxa-distorção de cada sequência.
"""
GIB = 1024 ** 3


def gb_per_hour(kbps: float) -> float:
    """Converte kbps em Gigabytes por hora de vídeo."""
    return (kbps * 1000.0 * 3600.0) / (8.0 * GIB)


def _break_even(extra_cost: float, saving: float):
    if extra_cost <= 0:
        return 0.0
    if saving <= 0:
        return None
    return extra_cost / saving


def calculate_economic_projections(iso_bitrates: dict, encode_inputs: dict, econ: dict, baseline: str) -> dict:
    """
    iso_bitrates: {codec: kbps na qualidade alvo (VMAF ~93)}
    encode_inputs: {codec: {"encode_s_per_content_s", "energy_wh_per_content_s", "device"}}
    """
    storage_price = econ.get("cost_storage_per_gb_month", 0.12)
    egress_price = econ.get("cost_egress_per_gb", 0.35)
    catalog_h = econ.get("catalog_hours", 1000.0)
    streamed_h = econ.get("monthly_streamed_hours", 5000.0)
    kwh_price = econ.get("energy_per_kwh", 0.85)
    instance_price = {
        "cpu": econ.get("cpu_instance_per_hour", 2.50),
        "gpu": econ.get("gpu_instance_per_hour", 6.00)
    }

    out = {}
    for codec, kbps in iso_bitrates.items():
        if kbps is None or kbps <= 0:
            continue
        gbh = gb_per_hour(kbps)
        enc = encode_inputs.get(codec, {})
        enc_h_per_h = enc.get("encode_s_per_content_s", 0.0)
        energy_kwh_per_h = (enc.get("energy_wh_per_content_s", 0.0) * 3600.0) / 1000.0
        device = enc.get("device", "cpu")

        out[codec] = {
            "iso_bitrate_kbps": kbps,
            "gb_per_hour": gbh,
            "volume_tb": (gbh * catalog_h) / 1024.0,
            "storage_cost": gbh * catalog_h * storage_price,
            "egress_cost": gbh * streamed_h * egress_price,
            "egress_cost_per_watched_hour": gbh * egress_price,
            "device": device,
            "encode_hours_per_content_hour": enc_h_per_h,
            "encode_cost_cloud_per_content_hour": enc_h_per_h * instance_price.get(device, 2.5),
            "energy_kwh_per_content_hour": energy_kwh_per_h,
            "encode_cost_energy_per_content_hour": energy_kwh_per_h * kwh_price,
        }
        o = out[codec]
        o["total_monthly_cost"] = o["storage_cost"] + o["egress_cost"]
        o["catalog_encode_cost_cloud"] = o["encode_cost_cloud_per_content_hour"] * catalog_h
        o["catalog_encode_cost_energy"] = o["encode_cost_energy_per_content_hour"] * catalog_h

    base = out.get(baseline)
    if not base:
        # Se o baseline especificado não estiver presente, usa o primeiro codec disponível
        first_key = next(iter(out.keys())) if out else None
        base = out.get(first_key)
        if not base:
            return out

    for codec, o in out.items():
        o["storage_savings_brl"] = base["storage_cost"] - o["storage_cost"]
        o["storage_savings_pct"] = (100.0 * o["storage_savings_brl"] / base["storage_cost"]) if base["storage_cost"] > 0 else 0.0
        o["egress_savings_brl"] = base["egress_cost"] - o["egress_cost"]
        o["egress_savings_pct"] = (100.0 * o["egress_savings_brl"] / base["egress_cost"]) if base["egress_cost"] > 0 else 0.0
        o["monthly_savings_brl"] = base["total_monthly_cost"] - o["total_monthly_cost"]

        extra_cloud = o["catalog_encode_cost_cloud"] - base["catalog_encode_cost_cloud"]
        o["extra_encode_cost_cloud"] = extra_cloud
        o["break_even_months"] = _break_even(extra_cloud, o["monthly_savings_brl"])

        # Ponto de equilíbrio por conteúdo (número de visualizações de cada hora de vídeo)
        extra_per_h = o["encode_cost_cloud_per_content_hour"] - base["encode_cost_cloud_per_content_hour"]
        saving_per_view = base["egress_cost_per_watched_hour"] - o["egress_cost_per_watched_hour"]
        o["break_even_views_per_content_hour"] = _break_even(extra_per_h, saving_per_view)

    return out


def sensitivity_analysis(projections: dict, econ: dict, baseline: str) -> list:
    """Análise de sensibilidade frente a diferentes volumes de audiência."""
    base = projections.get(baseline)
    if not base:
        return []
    storage_price = econ.get("cost_storage_per_gb_month", 0.12)
    egress_price = econ.get("cost_egress_per_gb", 0.35)
    catalog_h = econ.get("catalog_hours", 1000.0)
    rows = []
    for hours in econ.get("sensitivity_streamed_hours", [1000, 10000, 100000, 1000000]):
        base_cost = base["gb_per_hour"] * (catalog_h * storage_price + hours * egress_price)
        for codec, o in projections.items():
            if codec == baseline:
                continue
            cost = o["gb_per_hour"] * (catalog_h * storage_price + hours * egress_price)
            saving = base_cost - cost
            rows.append({
                "streamed_hours": hours,
                "codec": codec,
                "monthly_cost": cost,
                "monthly_savings": saving,
                "break_even_months": _break_even(o.get("extra_encode_cost_cloud", 0.0), saving),
            })
    return rows
