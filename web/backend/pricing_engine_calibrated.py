from __future__ import annotations
from pathlib import Path
import json
from .pricing_engine import price_quantities

def load_calibration(path: Path) -> dict:
    if not path or not path.exists(): 
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    return data.get("factors", {})

def apply_calibration(unit_cost: float, trade:str, item:str, factors:dict) -> float:
    key = f"{trade.strip().lower()}::{item.strip().lower()}"
    m = float(factors.get(key, 1.0))
    return max(0.0, unit_cost * m)

# Note: price_quantities already resolves cost sources; the caller may inject
# calibrated unit costs by pre-mapping before calling price_quantities, or
# extend price_quantities later. For v0, we leave pricing_engine untouched and
# do a pre-pass in the runner script to apply factors to unit_costs CSV.
