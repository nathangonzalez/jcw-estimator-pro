"""
Read-only benchmarking utilities for quick gut-check metrics.

Constraints:
- No servers, no installs.
- Reads existing artifacts only.
- Emits reports under output/BENCH/.
"""
from __future__ import annotations

import os
import csv
import json
import math
import random
from typing import List, Dict, Any, Tuple, Optional
from statistics import median
from datetime import datetime

# -----------------------------
# Loaders
# -----------------------------

EXPECTED_ESTIMATE_COLS = [
    "project_id", "trade", "item", "quantity", "unit", "unit_cost", "line_total", "source"
]


def _to_float(x: Any, default: float = 0.0) -> float:
    try:
        if x is None or x == "":
            return default
        return float(x)
    except Exception:
        return default


def load_estimate_lines(csv_path: str) -> List[Dict[str, Any]]:
    """
    Load flat estimate lines CSV:
    [project_id, trade, item, quantity, unit, unit_cost, line_total, source]
    Returns list of dict rows with numeric fields cast and non-negatives enforced.
    """
    rows: List[Dict[str, Any]] = []
    if not os.path.exists(csv_path):
        return rows

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        # Validate columns (best-effort)
        header = [h.strip() for h in reader.fieldnames or []]
        missing = [c for c in EXPECTED_ESTIMATE_COLS if c not in header]
        if missing:
            # Attempt to continue; just ensure we create keys
            pass

        for r in reader:
            row = {k.strip(): (v.strip() if isinstance(v, str) else v) for k, v in (r or {}).items()}
            row.setdefault("project_id", "")
            row.setdefault("trade", "")
            row.setdefault("item", "")
            row.setdefault("unit", "")
            # Coerce numerics
            q = max(0.0, _to_float(row.get("quantity"), 0.0))
            uc = max(0.0, _to_float(row.get("unit_cost"), 0.0))
            lt = max(0.0, _to_float(row.get("line_total"), 0.0))
            row["quantity"] = q
            row["unit_cost"] = uc
            row["line_total"] = lt
            row.setdefault("source", "")
            rows.append(row)
    return rows


def load_plan_features(json_path: str) -> Dict[str, Any]:
    """
    Load plan/takeoff response and extract minimal features we use:
      - area_sqft (from concrete slab_area or any 'sf' item if present)
      - fixture_counts (dict)
      - trades_in_plan (List[str])
      - project_id
      - warnings (notes)
    """
    if not os.path.exists(json_path):
        return {}
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return {}

    res: Dict[str, Any] = {}
    meta = data.get("meta") or {}
    res["project_id"] = meta.get("project_id") or ""
    trades = data.get("trades") or {}
    res["trades_in_plan"] = list(trades.keys())
    # Area heuristic
    area_sqft: Optional[float] = None
    conc = trades.get("concrete") or {}
    for it in (conc.get("items") or []):
        code = (it.get("code") or "").lower()
        unit = (it.get("unit") or "").lower()
        if code in ("slab_area", "area") or unit in ("sf", "sqft"):
            area_sqft = _to_float(it.get("quantity"), 0.0)
            break
    # Fallback: first item with sf unit across trades
    if area_sqft is None:
        found = False
        for tname, tdata in trades.items():
            for it in (tdata.get("items") or []):
                unit = (it.get("unit") or "").lower()
                if unit in ("sf", "sqft"):
                    area_sqft = _to_float(it.get("quantity"), 0.0)
                    found = True
                    break
            if found:
                break
    res["area_sqft"] = area_sqft or 0.0

    # Fixtures
    fixture_counts: Dict[str, float] = {}
    if "plumbing" in trades:
        for it in (trades["plumbing"].get("items") or []):
            code = (it.get("code") or "").lower()
            qty = _to_float(it.get("quantity"), 0.0)
            if code:
                fixture_counts[code] = fixture_counts.get(code, 0.0) + qty
    res["fixture_counts"] = fixture_counts

    # Notes and warnings
    notes = []
    nmeta = (meta.get("notes") or "")
    if nmeta:
        notes.append(nmeta)
    res["notes"] = notes

    return res


def load_vendor_quotes(csv_path: str) -> List[Dict[str, Any]]:
    """
    Load canonical vendor quotes CSV and aggregate to [trade,item,quoted_total].
    Returns list of dicts.
    """
    if not os.path.exists(csv_path):
        return []
    rows: List[Dict[str, Any]] = []
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        # If only header present (no data), return empty
        has_any = False
        agg: Dict[Tuple[str, str], float] = {}
        for r in reader:
            has_any = True
            trade = (r.get("trade") or "").strip()
            item = (r.get("item") or "").strip()
            line_total = _to_float(r.get("line_total"), None)
            if line_total is None:
                qty = _to_float(r.get("qty"), 0.0)
                uc = _to_float(r.get("unit_cost"), 0.0)
                line_total = qty * uc
            key = (trade, item)
            agg[key] = agg.get(key, 0.0) + max(0.0, line_total)
        if not has_any:
            return []
        for (trade, item), total in agg.items():
            rows.append({"trade": trade, "item": item, "quoted_total": max(0.0, total)})
    return rows


# -----------------------------
# Metrics
# -----------------------------

def _iqr(values: List[float]) -> Tuple[float, float, float]:
    """Return (q1, q3, iqr). Empty safe."""
    if not values:
        return (0.0, 0.0, 0.0)
    vs = sorted(values)
    n = len(vs)
    mid = n // 2
    if n % 2 == 0:
        lower = vs[:mid]
        upper = vs[mid:]
    else:
        lower = vs[:mid]
        upper = vs[mid+1:]
    q1 = median(lower) if lower else vs[0]
    q3 = median(upper) if upper else vs[-1]
    return (q1, q3, max(0.0, q3 - q1))


def _percentile(vs: List[float], pct: float) -> float:
    if not vs:
        return 0.0
    s = sorted(vs)
    k = (len(s) - 1) * pct
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return s[int(k)]
    d0 = s[f] * (c - k)
    d1 = s[c] * (k - f)
    return d0 + d1


def bands_from_history(dollars_per_sf: float) -> Dict[str, float]:
    """
    Provisional band around current $/SF with ±15% padding.
    """
    lower = max(0.0, dollars_per_sf * 0.85)
    upper = max(lower, dollars_per_sf * 1.15)
    return {"p25": lower, "p75": upper}


def metrics(
    est_rows: List[Dict[str, Any]],
    features: Optional[Dict[str, Any]] = None,
    vendor_rows: Optional[List[Dict[str, Any]]] = None,
    bootstrap_sigma: float = 0.075,
    bootstrap_samples: int = 500
) -> Dict[str, Any]:
    features = features or {}
    vendor_rows = vendor_rows or []

    # Totals
    estimate_total = sum(_to_float(r.get("line_total"), 0.0) for r in est_rows)
    # Fallback if zeros: try recompute as qty * unit_cost
    if estimate_total <= 0.0:
        estimate_total = sum(_to_float(r.get("quantity"), 0.0) * _to_float(r.get("unit_cost"), 0.0) for r in est_rows)

    area_sqft = _to_float(features.get("area_sqft"), 0.0)
    dollars_per_sf = (estimate_total / area_sqft) if (area_sqft > 0) else 0.0

    # Trade breakdown
    by_trade: Dict[str, float] = {}
    for r in est_rows:
        trade = (r.get("trade") or "").strip()
        by_trade[trade] = by_trade.get(trade, 0.0) + _to_float(r.get("line_total"), 0.0)
    # Fallback to qty*uc for trades with zero subtotal
    if estimate_total <= 0.0:
        by_trade = {}
        for r in est_rows:
            trade = (r.get("trade") or "").strip()
            by_trade[trade] = by_trade.get(trade, 0.0) + (_to_float(r.get("quantity"), 0.0) * _to_float(r.get("unit_cost"), 0.0))

    trade_breakdown = []
    for t, sub in by_trade.items():
        pct = (sub / estimate_total * 100.0) if estimate_total > 0 else 0.0
        trade_breakdown.append({"trade": t, "subtotal": round(sub, 2), "pct": round(pct, 2)})
    trade_breakdown.sort(key=lambda x: x["subtotal"], reverse=True)

    # Outliers on unit_cost via IQR
    unit_costs = [max(0.0, _to_float(r.get("unit_cost"), 0.0)) for r in est_rows if _to_float(r.get("unit_cost"), 0.0) > 0]
    q1, q3, iqr = _iqr(unit_costs)
    lo_cut = q1 - 1.5 * iqr
    hi_cut = q3 + 1.5 * iqr
    outliers = []
    if iqr > 0:
        for r in est_rows:
            uc = _to_float(r.get("unit_cost"), 0.0)
            if uc <= 0:
                continue
            flag = (uc < lo_cut) or (uc > hi_cut)
            if flag:
                outliers.append({
                    "trade": r.get("trade"),
                    "item": r.get("item"),
                    "unit_cost": round(uc, 4),
                    "iqr_flag": True
                })
    # Limit top 10 (largest unit_cost first)
    outliers.sort(key=lambda x: x["unit_cost"], reverse=True)
    outliers = outliers[:10]

    # Coverage: ensure all plan trades appear in estimate lines
    plan_trades = set((features.get("trades_in_plan") or []))
    est_trades = set([str(r.get("trade") or "").strip() for r in est_rows])
    missing_trades = sorted([t for t in plan_trades if t and t not in est_trades])
    expected_trades_present = sorted(list(plan_trades))
    coverage_pass = (len(missing_trades) == 0)

    # Sensitivity: +/-10% on unit_costs (recompute totals)
    def recompute_total(scale: float) -> float:
        tot = 0.0
        for r in est_rows:
            q = _to_float(r.get("quantity"), 0.0)
            uc = _to_float(r.get("unit_cost"), 0.0) * scale
            tot += q * uc
        return tot

    unit_costs_plus10 = recompute_total(1.10)
    unit_costs_minus10 = recompute_total(0.90)

    # Waste sensitivity (approximate as similar scaling, lacking explicit waste fields)
    waste_plus10 = estimate_total * 1.10 if estimate_total > 0 else unit_costs_plus10 * 1.10
    waste_minus10 = estimate_total * 0.90 if estimate_total > 0 else unit_costs_minus10 * 0.90

    sensitivity = {
        "unit_costs": {"plus10_pct": round(unit_costs_plus10, 2), "minus10_pct": round(unit_costs_minus10, 2)},
        "waste": {"plus10_pct": round(waste_plus10, 2), "minus10_pct": round(waste_minus10, 2)}
    }

    # Vendor metrics if present
    vendor_total = 0.0
    mape_project = None
    wape_by_trade: List[Dict[str, Any]] = []

    if vendor_rows:
        vendor_map: Dict[Tuple[str, str], float] = {}
        vendor_by_trade: Dict[str, float] = {}
        for v in vendor_rows:
            t = (v.get("trade") or "").strip()
            i = (v.get("item") or "").strip()
            vt = max(0.0, _to_float(v.get("quoted_total"), 0.0))
            vendor_map[(t, i)] = vendor_map.get((t, i), 0.0) + vt
            vendor_by_trade[t] = vendor_by_trade.get(t, 0.0) + vt
            vendor_total += vt

        est_map: Dict[Tuple[str, str], float] = {}
        for r in est_rows:
            t = (r.get("trade") or "").strip()
            i = (r.get("item") or "").strip()
            lt = max(0.0, _to_float(r.get("line_total"), 0.0))
            if lt <= 0.0:
                lt = max(0.0, _to_float(r.get("quantity"), 0.0) * _to_float(r.get("unit_cost"), 0.0))
            est_map[(t, i)] = est_map.get((t, i), 0.0) + lt

        # Project MAPE
        ape_sum = 0.0
        count = 0
        for key, vtot in vendor_map.items():
            if vtot <= 0:
                continue
            est_tot = est_map.get(key, 0.0)
            ape = abs(est_tot - vtot) / vtot
            ape_sum += ape
            count += 1
        if count > 0:
            mape_project = round(ape_sum / count * 100.0, 2)

        # WAPE by trade
        for t, v_sub in vendor_by_trade.items():
            if v_sub > 0:
                est_sub = 0.0
                for (tt, ii), vtot in vendor_map.items():
                    if tt == t:
                        est_sub += est_map.get((tt, ii), 0.0)
                wape = abs(est_sub - v_sub) / v_sub * 100.0
                wape_by_trade.append({"trade": t, "wape": round(wape, 2)})
        wape_by_trade.sort(key=lambda x: x["wape"], reverse=True)

    # Bootstrap P50/P90 on $/SF via unit cost sigma
    base_line_ext = []
    for r in est_rows:
        ext = _to_float(r.get("line_total"), 0.0)
        if ext <= 0.0:
            ext = _to_float(r.get("quantity"), 0.0) * _to_float(r.get("unit_cost"), 0.0)
        base_line_ext.append(max(0.0, ext))

    dpsf_samples: List[float] = []
    if area_sqft > 0 and base_line_ext:
        for _ in range(bootstrap_samples):
            tot = 0.0
            for ext in base_line_ext:
                # Random factor ~ N(1, sigma)
                factor = random.gauss(1.0, bootstrap_sigma)
                if factor < 0:
                    factor = 0.0
                tot += ext * factor
            dpsf_samples.append(tot / area_sqft if area_sqft > 0 else 0.0)

    p50 = _percentile(dpsf_samples, 0.50) if dpsf_samples else dollars_per_sf
    p90 = _percentile(dpsf_samples, 0.90) if dpsf_samples else dollars_per_sf

    # Bands
    band = bands_from_history(dollars_per_sf)
    band_pass = (band["p25"] <= dollars_per_sf <= band["p75"])

    # Warnings
    warnings: List[str] = []
    if estimate_total <= 0:
        warnings.append("estimate_total_is_zero")
    if not est_rows:
        warnings.append("no_estimate_lines_loaded")
    if area_sqft <= 0:
        warnings.append("area_sqft_missing_or_zero")
    if vendor_rows and vendor_total <= 0:
        warnings.append("vendor_rows_present_but_total_zero")

    return {
        "totals": {
            "estimate_total": round(estimate_total, 2),
            "area_sqft": round(area_sqft, 2),
            "dollars_per_sf": round(dollars_per_sf, 2),
        },
        "trade_breakdown": trade_breakdown,
        "outliers": outliers,
        "coverage": {
            "expected_trades_present": expected_trades_present,
            "missing_trades": missing_trades,
            "pass": coverage_pass
        },
        "sensitivity": sensitivity,
        "vendor": {
            "vendor_total": round(vendor_total, 2),
            "MAPE_project": mape_project,
            "WAPE_by_trade": wape_by_trade
        } if vendor_rows else None,
        "bootstrap": {
            "P50_dollars_per_sf": round(p50, 2),
            "P90_dollars_per_sf": round(p90, 2),
            "sigma": bootstrap_sigma,
            "samples": bootstrap_samples
        },
        "band_provisional": band,
        "band_pass": band_pass,
        "warnings": warnings
    }


# -----------------------------
# Reporting
# -----------------------------

def _format_markdown_report(project_id: str, m: Dict[str, Any]) -> str:
    tot = m.get("totals", {})
    dpsf = tot.get("dollars_per_sf", 0.0)
    band = m.get("band_provisional", {})
    band_pass = m.get("band_pass", False)
    coverage = m.get("coverage", {})
    coverage_pass = coverage.get("pass", False)
    vendor = m.get("vendor")

    # PASS/FAIL vendor (MAPE <= 15%)
    vendor_pass_text = "N/A"
    if vendor and vendor.get("MAPE_project") is not None:
        vendor_pass_text = "PASS" if vendor["MAPE_project"] <= 15.0 else "FAIL"

    lines = []
    lines.append("# LYNN Gut-Check")
    lines.append("")
    lines.append(f"- Project: {project_id or 'N/A'}")
    lines.append(f"- Generated: {datetime.now().isoformat()}")
    lines.append("")
    lines.append("## Totals")
    lines.append(f"- Estimate Total: ${tot.get('estimate_total', 0):,.2f}")
    lines.append(f"- Area (SF): {tot.get('area_sqft', 0):,.2f}")
    lines.append(f"- Dollars per SF: ${dpsf:,.2f}")
    lines.append("")
    lines.append("## Band Check (provisional)")
    lines.append(f"- Band (P25–P75): ${band.get('p25', 0):,.2f} – ${band.get('p75', 0):,.2f}")
    lines.append(f"- Within band: {'PASS' if band_pass else 'FAIL'}")
    lines.append("")
    lines.append("## Trade Subtotals (descending)")
    for tb in (m.get("trade_breakdown") or []):
        lines.append(f"- {tb['trade'] or 'unknown'}: ${tb['subtotal']:,.2f} ({tb['pct']:.2f}%)")
    lines.append("")
    lines.append("## Coverage")
    lines.append(f"- Present (from plan): {', '.join(coverage.get('expected_trades_present') or [])}")
    if coverage.get("missing_trades"):
        lines.append(f"- Missing: {', '.join(coverage.get('missing_trades'))}")
    lines.append(f"- Coverage check: {'PASS' if coverage_pass else 'FAIL'}")
    lines.append("")
    lines.append("## Outliers (top 10 by unit cost)")
    if m.get("outliers"):
        lines.append("| trade | item | unit_cost | IQR outlier |")
        lines.append("|---|---|---:|:---:|")
        for o in m["outliers"]:
            lines.append(f"| {o['trade']} | {o['item']} | {o['unit_cost']:.4f} | {'Y' if o['iqr_flag'] else ''} |")
    else:
        lines.append("- None")
    lines.append("")
    lines.append("## Sensitivity (totals)")
    sens = m.get("sensitivity") or {}
    uc = sens.get("unit_costs") or {}
    w = sens.get("waste") or {}
    lines.append(f"- Unit costs +10%: ${uc.get('plus10_pct', 0):,.2f} ; -10%: ${uc.get('minus10_pct', 0):,.2f}")
    lines.append(f"- Waste +10%: ${w.get('plus10_pct', 0):,.2f} ; -10%: ${w.get('minus10_pct', 0):,.2f}")
    lines.append("")
    if vendor is not None:
        lines.append("## Vendor Comparison")
        lines.append(f"- Vendor Total: ${vendor.get('vendor_total', 0):,.2f}")
        lines.append(f"- Project MAPE: {vendor.get('MAPE_project') if vendor.get('MAPE_project') is not None else 'N/A'}%")
        lines.append(f"- Vendor check (MAPE ≤ 15%): {vendor_pass_text}")
        if vendor.get("WAPE_by_trade"):
            lines.append("")
            lines.append("| trade | WAPE % |")
            lines.append("|---|---:|")
            for wape in vendor["WAPE_by_trade"]:
                lines.append(f"| {wape['trade']} | {wape['wape']:.2f} |")
    return "\n".join(lines) + "\n"


def generate_reports(
    estimate_csv: str,
    plan_json: str,
    vendor_csv: Optional[str],
    out_dir: str = "output/BENCH",
    project_id_fallback: str = "LYNN-001"
) -> Dict[str, str]:
    os.makedirs(out_dir, exist_ok=True)
    json_out = os.path.join(out_dir, "LYNN_GUTCHECK.json")
    md_out = os.path.join(out_dir, "LYNN_GUTCHECK.md")

    missing: List[str] = []
    if not os.path.exists(estimate_csv):
        missing.append(estimate_csv)
    if not os.path.exists(plan_json):
        missing.append(plan_json)

    if missing:
        # Write minimal "Inputs Missing" report
        with open(md_out, "w", encoding="utf-8") as f:
            f.write("# LYNN Gut-Check\n\n")
            f.write("## Inputs Missing\n\n")
            for path in missing:
                f.write(f"- {path}\n")
        # Also emit minimal JSON
        with open(json_out, "w", encoding="utf-8") as f:
            json.dump({"error": "inputs_missing", "missing": missing}, f, indent=2)
        return {"json": json_out, "md": md_out}

    est_rows = load_estimate_lines(estimate_csv)
    features = load_plan_features(plan_json)
    vendor_rows = load_vendor_quotes(vendor_csv) if (vendor_csv and os.path.exists(vendor_csv)) else []

    # Fallback feature derivation from estimate lines if plan features are missing/empty
    if (not features) or (features.get("area_sqft") in (None, 0, 0.0)) or (not features.get("trades_in_plan")):
        # area from slab_area (preferred), else sum of SF quantities
        fallback_area = 0.0
        for r in est_rows:
            item = (str(r.get("item") or "")).lower()
            unit = (str(r.get("unit") or "")).upper()
            if item in ("slab_area", "area") and unit == "SF":
                fallback_area = _to_float(r.get("quantity"), 0.0)
                break
        if fallback_area == 0.0:
            fallback_area = sum(_to_float(r.get("quantity"), 0.0) for r in est_rows if (str(r.get("unit") or "")).upper() == "SF")

        est_trades = sorted({str(r.get("trade") or "").strip() for r in est_rows if r.get("trade")})
        proj_id = (features or {}).get("project_id") or (est_rows[0].get("project_id") if est_rows else project_id_fallback)

        features = {
            **(features or {}),
            "project_id": proj_id,
            "trades_in_plan": (features or {}).get("trades_in_plan") or est_trades,
            "area_sqft": (features or {}).get("area_sqft") or fallback_area
        }

    m = metrics(est_rows, features, vendor_rows)
    project_id = features.get("project_id") or (est_rows[0].get("project_id") if est_rows else project_id_fallback)

    # Write JSON
    with open(json_out, "w", encoding="utf-8") as f:
        json.dump(m, f, indent=2)

    # Write Markdown
    md = _format_markdown_report(project_id, m)
    with open(md_out, "w", encoding="utf-8") as f:
        f.write(md)

    return {"json": json_out, "md": md_out}


# -----------------------------
# CLI
# -----------------------------

def cli_main() -> None:
    """
    Default entrypoint for LYNN-001 read-only gut-check.
    """
    estimate_csv = "output/LYNN-001/raw_estimate/estimate_lines.csv"
    plan_json = "output/TAKEOFF_RESPONSE.json"
    vendor_csv = "data/vendor_quotes/LYNN-001/quotes.canonical.csv"  # optional; may be empty
    generate_reports(estimate_csv, plan_json, vendor_csv)


if __name__ == "__main__":
    cli_main()
