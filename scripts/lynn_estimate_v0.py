#!/usr/bin/env python3
"""
Lynn v0 — RAW estimate (quote-free)
- Reads data/lynn/working/takeoff_quantities.json (M01 v0)
- Prices using schemas/pricing_policy.v0.yaml + data/unit_costs.sample.csv
- Ignores vendor quotes (CSV not used)
Outputs:
- data/lynn/working/PIPELINE_ESTIMATE_RESPONSE.json
- data/lynn/working/estimate_lines.csv
Guardrails:
- Only touches data/lynn paths. No deletion.
"""
from __future__ import annotations

import os
import json
from pathlib import Path
from typing import Any, Dict, List

REPO = Path(__file__).resolve().parents[1]
LYNN = REPO / "data" / "lynn"
WORKING = LYNN / "working"

POLICY_PATH = REPO / "schemas" / "pricing_policy.v0.yaml"
UNIT_COSTS_CSV = REPO / "data" / "unit_costs.sample.csv"

def _flatten_quantities(takeoff: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Convert M01 v0 quantities into pricing_engine list:
      {trade, code, description, uom, qty, notes?}
    Supports:
      - {"version":"v0","trades":{ trade: {items:[{code,description,unit,quantity,notes}]}}}
      - Already-flattened [{"trade","code","description","uom","qty","notes"}]
    """
    if isinstance(takeoff, list):
        # Assume already flattened (normalize keys)
        out: List[Dict[str, Any]] = []
        for it in takeoff:
            out.append({
                "trade": it.get("trade",""),
                "code": it.get("code",""),
                "description": it.get("description",""),
                "uom": (it.get("uom") or it.get("unit") or "EA").upper(),
                "qty": float(it.get("qty") or it.get("quantity") or 0.0),
                "notes": it.get("notes"),
            })
        return out

    if takeoff.get("version") == "v0" and isinstance(takeoff.get("trades"), dict):
        out: List[Dict[str, Any]] = []
        for trade, tdata in (takeoff.get("trades") or {}).items():
            for it in (tdata.get("items") or []):
                out.append({
                    "trade": trade,
                    "code": it.get("code",""),
                    "description": it.get("description",""),
                    "uom": (it.get("unit") or "EA").upper(),
                    "qty": float(it.get("quantity") or 0.0),
                    "notes": it.get("notes"),
                })
        return out

    # fallback: empty
    return []

def _read_text(p: Path) -> str:
    try:
        with open(p, "r", encoding="utf-8") as f:
            return f.read()
    except Exception:
        return ""

def _source_map(s: str) -> str:
    # Map engine sources for CSV output
    m = (s or "").lower()
    if m == "vendor_quotes":
        return "engine:vendor_override"
    if m == "unit_costs":
        return "engine:unit_costs"
    return "engine:policy"  # policy_defaults or unknown

def main() -> int:
    from web.backend.pricing_engine import price_quantities

    WORKING.mkdir(parents=True, exist_ok=True)

    # Load takeoff quantities
    tq_path = WORKING / "takeoff_quantities.json"
    if not tq_path.exists():
        print(f"Missing {tq_path}, cannot proceed.")
        return 0

    with open(tq_path, "r", encoding="utf-8") as f:
        takeoff = json.load(f)

    quantities = _flatten_quantities(takeoff)
    # Price
    policy_yaml = _read_text(POLICY_PATH)
    unit_csv = _read_text(UNIT_COSTS_CSV)

    resp = price_quantities(
        quantities=quantities,
        policy_yaml=policy_yaml,
        region="US-MA-Boston",
        unit_costs_csv=unit_csv,
        vendor_quotes_csv=None,
    )

    # Write response JSON
    out_resp = WORKING / "PIPELINE_ESTIMATE_RESPONSE.json"
    with open(out_resp, "w", encoding="utf-8") as f:
        json.dump(resp, f, indent=2)

    # Emit flat CSV for benchmarking
    csv_path = WORKING / "estimate_lines.csv"
    with open(csv_path, "w", encoding="utf-8") as f:
        f.write("project_id,trade,item,quantity,unit,unit_cost,line_total,source\n")
        project_id = "LYNN-001"
        for li in (resp.get("line_items") or []):
            trade = li.get("trade","")
            item = li.get("code") or li.get("description") or ""
            qty = float(li.get("qty") or 0.0)
            unit = li.get("uom") or li.get("unit") or "EA"
            unit_cost = float(li.get("unit_cost") or 0.0)
            line_total = float(li.get("total") or 0.0)
            source = _source_map(li.get("source"))
            # CSV-safe line
            def esc(s: str) -> str:
                return '"' + (s or "").replace('"','""') + '"'
            f.write(f'{esc(project_id)},{esc(trade)},{esc(item)},{qty},{esc(unit)},{unit_cost},{line_total},{esc(source)}\n')

    print(f"Wrote {out_resp} and {csv_path}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
