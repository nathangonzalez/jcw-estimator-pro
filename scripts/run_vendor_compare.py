#!/usr/bin/env python3
"""
Lynn F3b — Vendor Calibration & Comparison (DEV-FAST)

Pipeline:
1) Parse vendor PDFs -> canonical rows
   - web.backend.vendor_quote_parser_lynn.parse_all()
   - Writes:
       data/lynn/working/vendor/rows/<vendor>.rows.json
       data/lynn/working/vendor/rows/<vendor>.rows.csv
       data/lynn/working/vendor_quotes.canonical.csv
       data/lynn/working/vendor_quotes.canonical.json

2) Compare canonical vendor totals against RAW estimate
   - Estimate response: data/lynn/working/PIPELINE_ESTIMATE_RESPONSE.json
   - Canonical CSV:     data/lynn/working/vendor_quotes.canonical.csv
   - Outputs:
       data/lynn/working/vendor_vs_estimate.csv
       data/lynn/working/vendor_vs_estimate.json
       data/lynn/working/VENDOR_COMPARE_SUMMARY.md

Guardrails:
- Only touches data/lynn and output files under working/. No deletion.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

# Ensure repo root is importable for `web.*` modules when launched from scripts
import sys as _sys
_repo_root = Path(__file__).resolve().parents[1]
if str(_repo_root) not in _sys.path:
    _sys.path.insert(0, str(_repo_root))

REPO = Path(__file__).resolve().parents[1]
LYNN = REPO / "data" / "lynn"
WORKING = LYNN / "working"

CANON_CSV = WORKING / "vendor_quotes.canonical.csv"
CANON_JSON = WORKING / "vendor_quotes.canonical.json"
ESTIMATE_RESPONSE = WORKING / "PIPELINE_ESTIMATE_RESPONSE.json"
OUT_CSV = WORKING / "vendor_vs_estimate.csv"
OUT_JSON = WORKING / "vendor_vs_estimate.json"
SUMMARY_MD = WORKING / "VENDOR_COMPARE_SUMMARY.md"


def _format_money(v: float) -> str:
    try:
        return f"${float(v):,.2f}"
    except Exception:
        return "$0.00"


def _totals(rows: List[Dict[str, Any]]) -> Dict[str, float]:
    t_est = sum(float(r.get("est_total") or 0.0) for r in rows)
    t_vdr = sum(float(r.get("vdr_total") or 0.0) for r in rows)
    return {"estimate_total": t_est, "vendor_total": t_vdr, "delta_total": t_est - t_vdr}


def _group_by_trade(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    from collections import defaultdict
    g = defaultdict(lambda: {"est": 0.0, "vdr": 0.0})
    for r in rows:
        t = (r.get("trade") or "").strip().lower()
        g[t]["est"] += float(r.get("est_total") or 0.0)
        g[t]["vdr"] += float(r.get("vdr_total") or 0.0)
    out = []
    for trade, v in sorted(g.items(), key=lambda kv: abs(kv[1]["est"] - kv[1]["vdr"]), reverse=True):
        out.append({
            "trade": trade,
            "est_total": round(v["est"], 2),
            "vdr_total": round(v["vdr"], 2),
            "delta_total": round(v["est"] - v["vdr"], 2),
        })
    return out


def _write_summary_md(rows: List[Dict[str, Any]]) -> None:
    WORKING.mkdir(parents=True, exist_ok=True)
    totals = _totals(rows)
    by_trade = _group_by_trade(rows)

    lines: List[str] = []
    lines.append("# Lynn F3b — Vendor vs RAW Estimate (Summary)")
    lines.append("")
    lines.append("## Totals")
    lines.append(f"- Estimate Total: {_format_money(totals['estimate_total'])}")
    lines.append(f"- Vendor Total:   {_format_money(totals['vendor_total'])}")
    lines.append(f"- Delta (Est - Vendor): {_format_money(totals['delta_total'])}")
    lines.append("")
    lines.append("## Largest Deltas (Top 15 lines)")
    top = sorted(rows, key=lambda r: abs(float(r.get("delta_total") or 0.0)), reverse=True)[:15]
    lines.append("| trade | item | est_total | vdr_total | delta_total |")
    lines.append("|---|---|---:|---:|---:|")
    for r in top:
        lines.append(
            f"| {r.get('trade','')}| {r.get('item','')} | "
            f"{_format_money(r.get('est_total') or 0)} | "
            f"{_format_money(r.get('vdr_total') or 0)} | "
            f"{_format_money(r.get('delta_total') or 0)} |"
        )
    lines.append("")
    lines.append("## Trade Rollup (by absolute delta)")
    lines.append("| trade | est_total | vdr_total | delta_total |")
    lines.append("|---|---:|---:|---:|")
    for r in by_trade[:20]:
        lines.append(
            f"| {r.get('trade','')} | "
            f"{_format_money(r.get('est_total') or 0)} | "
            f"{_format_money(r.get('vdr_total') or 0)} | "
            f"{_format_money(r.get('delta_total') or 0)} |"
        )
    SUMMARY_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    # Step 1: Parse vendor PDFs -> canonical
    from web.backend.vendor_quote_parser_lynn import parse_all
    parse_summary = parse_all(project_id="LYNN-001")

    # Step 2: Load canonical + RAW estimate and compare
    from web.backend.compare_estimate_vs_vendor import (
        load_vendor_canonical,
        load_estimate_response,
        compare,
        write_report,
    )

    vendor_rows = load_vendor_canonical(CANON_CSV)
    estimate_items = load_estimate_response(ESTIMATE_RESPONSE)

    rows = compare(estimate_items, vendor_rows)

    # Step 3: Write machine-readable deltas
    write_report(rows, OUT_CSV, OUT_JSON)

    # Step 4: Summary Markdown
    _write_summary_md(rows)

    # Also refresh combined JSON container to align with schema wrapper (if canonical exists)
    if CANON_CSV.exists():
        try:
            import csv as _csv
            all_rows: List[Dict[str, Any]] = []
            with CANON_CSV.open("r", encoding="utf-8") as f:
                reader = _csv.DictReader(f)
                for r in reader:
                    all_rows.append(r)
            CANON_JSON.write_text(json.dumps({"project_id": "LYNN-001", "rows": all_rows}, indent=2), encoding="utf-8")
        except Exception:
            pass

    print(json.dumps({
        "parsed": parse_summary,
        "out": {
            "compare_csv": str(OUT_CSV),
            "compare_json": str(OUT_JSON),
            "summary_md": str(SUMMARY_MD),
            "canonical_csv": str(CANON_CSV),
            "canonical_json": str(CANON_JSON),
        }
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
