from __future__ import annotations
import csv, json, hashlib
from pathlib import Path
from collections import defaultdict
from typing import List, Dict, Any

def _to_key(trade: str, item: str) -> str:
    return f"{(trade or '').strip().lower()}::{(item or '').strip().lower()}"

def load_vendor_canonical(canon_csv: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    if canon_csv.exists():
        with canon_csv.open("r", encoding="utf-8") as f:
            rdr = csv.DictReader(f)
            for r in rdr:
                # normalize numeric fields
                try:
                    r["qty"] = float(r.get("qty") or 0)
                except Exception:
                    r["qty"] = 0.0
                try:
                    r["unit_cost"] = float(r.get("unit_cost") or 0)
                except Exception:
                    r["unit_cost"] = 0.0
                try:
                    r["line_total"] = float(r.get("line_total") or 0)
                except Exception:
                    r["line_total"] = 0.0
                rows.append(r)
    return rows

def load_estimate_response(resp_json: Path) -> List[Dict[str, Any]]:
    """
    Expect a v0-like response where trades are listed and line items exist.
    This scaffolding will evolve as F1 normalizes its response contract.
    """
    items: List[Dict[str, Any]] = []
    if not resp_json.exists():
        return items
    obj = json.loads(resp_json.read_text(encoding="utf-8"))

    # Try common shapes
    # Shape A: {"trades":[{"trade":"plumbing","line_items":[{"item":...,"qty":...,"unit_cost":...,"line_total":...}, ...]}, ...]}
    for trade_block in obj.get("trades", []) or []:
        trade = trade_block.get("trade")
        for li in trade_block.get("line_items", []) or []:
            items.append({
                "trade": trade,
                "item": li.get("item"),
                "qty": float(li.get("qty") or 0),
                "unit_cost": float(li.get("unit_cost") or 0),
                "line_total": float(li.get("line_total") or 0),
            })

    # Shape B: a flat "line_items" at top-level with embedded trade
    if not items:
        for li in obj.get("line_items", []) or []:
            items.append({
                "trade": li.get("trade"),
                "item": li.get("item"),
                "qty": float(li.get("qty") or 0),
                "unit_cost": float(li.get("unit_cost") or 0),
                "line_total": float(li.get("line_total") or 0),
            })

    return items

def compare(estimate_items: List[Dict[str, Any]], vendor_rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    agg_est = defaultdict(lambda: {"qty": 0.0, "line_total": 0.0})
    agg_vdr = defaultdict(lambda: {"qty": 0.0, "line_total": 0.0})

    for e in estimate_items:
        k = _to_key(e.get("trade"), e.get("item"))
        agg_est[k]["qty"] += float(e.get("qty") or 0)
        agg_est[k]["line_total"] += float(e.get("line_total") or 0)

    for v in vendor_rows:
        k = _to_key(v.get("trade"), v.get("item"))
        agg_vdr[k]["qty"] += float(v.get("qty") or 0)
        agg_vdr[k]["line_total"] += float(v.get("line_total") or 0)

    # join & deltas
    keys = sorted(set(agg_est.keys()) | set(agg_vdr.keys()))
    rows: List[Dict[str, Any]] = []
    for k in keys:
        est = agg_est.get(k, {"qty": 0.0, "line_total": 0.0})
        vdr = agg_vdr.get(k, {"qty": 0.0, "line_total": 0.0})
        trade, item = (k.split("::", 1) + [""])[:2]
        rows.append({
            "trade": trade,
            "item": item,
            "est_qty": round(est["qty"], 4),
            "vdr_qty": round(vdr["qty"], 4),
            "delta_qty": round(est["qty"] - vdr["qty"], 4),
            "est_total": round(est["line_total"], 2),
            "vdr_total": round(vdr["line_total"], 2),
            "delta_total": round(est["line_total"] - vdr["line_total"], 2),
        })
    return rows

def write_report(rows: List[Dict[str, Any]], out_csv: Path, out_json: Path) -> None:
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    with out_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=[
            "trade", "item",
            "est_qty", "vdr_qty", "delta_qty",
            "est_total", "vdr_total", "delta_total"
        ])
        w.writeheader()
        for r in rows:
            w.writerow(r)
    out_json.write_text(json.dumps(rows, indent=2), encoding="utf-8")

def digest_path(p: Path) -> str:
    h = hashlib.sha256()
    h.update(p.read_bytes() if p.exists() else b"")
    return h.hexdigest()
