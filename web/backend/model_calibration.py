from __future__ import annotations
import csv, json, math, hashlib
from collections import defaultdict
from pathlib import Path
from typing import Dict, Tuple

def _key(trade:str, item:str)->str:
    return f"{trade.strip().lower()}::{item.strip().lower()}"

def normalize_key(trade: str, item: str) -> str:
    return f"{(trade or '').strip().lower()}::{(item or '').strip().lower()}"

def load_raw_estimate_lines(csv_path: Path) -> Dict[str, float]:
    """
    Input: output/LYNN-001/raw_estimate/estimate_lines.csv OR data/lynn/working/estimate_lines.csv
    Returns summed line_total by (trade,item) key from engine:policy rows only.
    """
    totals = defaultdict(float)
    if not csv_path.exists():
        return {}
    with csv_path.open("r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            trade = (r.get("trade") or "").strip()
            item  = (r.get("item") or "").strip()
            if not trade or not item: 
                continue
            try:
                lt = float(r.get("line_total", 0) or 0)
            except:
                lt = 0.0
            if lt > 0.0:
                totals[normalize_key(trade,item)] += lt
    return totals

def load_vendor_canonical(csv_path: Path) -> Dict[str, float]:
    """
    Input: data/lynn/working/vendor_quotes.canonical.csv (trade,item,quoted_total)
    Returns summed quoted_total by (trade,item).
    """
    totals = defaultdict(float)
    if not csv_path.exists():
        return {}
    with csv_path.open("r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            trade = (r.get("trade") or "").strip()
            item  = (r.get("item") or "").strip()
            # prefer quoted_total, fallback to line_total if present
            raw_qt = r.get("quoted_total", None)
            if raw_qt is None:
                raw_qt = r.get("line_total", 0)
            try:
                qt = float((raw_qt or 0))
            except:
                try:
                    qt = float(str(raw_qt).replace(",", "").replace("$", ""))
                except:
                    qt = 0.0
            if trade and item and qt > 0.0:
                totals[normalize_key(trade,item)] += qt
    return totals

def compute_multipliers(estimate: Dict[str,float], vendor: Dict[str,float],
                        min_estimate: float = 1.0, clamp: Tuple[float,float]=(0.4, 2.5)) -> Dict[str,float]:
    """
    Simple per-(trade,item) multiplier = vendor_total / estimate_total
    - Ignores lines where estimate_total < min_estimate (avoid divide-by-near-zero)
    - Clamps to [0.4, 2.5] by default to avoid extreme swings on v0
    """
    lo, hi = clamp
    factors = {}
    for k, est in estimate.items():
        if est < min_estimate: 
            continue
        vend = vendor.get(k, 0.0)
        if vend <= 0: 
            continue
        m = vend / est
        m = max(lo, min(hi, m))
        factors[k] = round(m, 3)
    return factors

def digest_file(p: Path) -> str:
    if not p.exists(): return ""
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()

def save_calibration_json(out_path: Path, factors: Dict[str,float], meta: Dict[str, str]):
    out_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"type":"per_trade_item_multiplier","factors":factors,"meta":meta}
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
