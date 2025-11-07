from __future__ import annotations
import csv
import hashlib
import io
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Any

import math
import json
import yaml

# ---- Data structures ---------------------------------------------------------

@dataclass
class Policy:
    id: str
    region: str
    markups: Dict[str, float]  # e.g., {"overhead_pct": 0.1, "profit_pct": 0.05}
    waste_defaults: Dict[str, float]  # by trade or global: {"global_pct": 0.03, "concrete": 0.05}
    tax_pct: float  # e.g., 0.0625
    escalation_pct: float  # e.g., 0.02
    resolution_order: List[str]  # ["vendor_quotes","unit_costs","policy_defaults"]

@dataclass
class QuantityItem:
    trade: str           # e.g., "concrete"
    code: str            # item code or CSI
    description: str
    uom: str             # "LF","SF","EA","CY", etc
    qty: float
    notes: Optional[str] = None

@dataclass
class PricedItem:
    trade: str
    code: str
    description: str
    uom: str
    qty: float
    unit_cost: float
    waste_pct: float
    extended_base: float
    extended_with_waste: float
    markup_overhead: float
    markup_profit: float
    subtotal_before_tax: float
    tax: float
    total: float
    source: str  # "vendor_quotes" | "unit_costs" | "policy_defaults"

# ---- Helpers ----------------------------------------------------------------

def _sha256_hex(blob: bytes) -> str:
    return hashlib.sha256(blob).hexdigest()

def _digests(
    quantities: List[dict],
    policy_yaml: str,
    unit_costs_csv: Optional[str],
    vendor_quotes_csv: Optional[str],
) -> Dict[str, str]:
    q_bytes = json.dumps(quantities, sort_keys=True).encode("utf-8")
    d = {
        "quantities_json_sha256": _sha256_hex(q_bytes),
        "policy_yaml_sha256": _sha256_hex(policy_yaml.encode("utf-8")),
    }
    if unit_costs_csv is not None:
        d["unit_costs_csv_sha256"] = _sha256_hex(unit_costs_csv.encode("utf-8"))
    if vendor_quotes_csv is not None:
        d["vendor_quotes_csv_sha256"] = _sha256_hex(vendor_quotes_csv.encode("utf-8"))
    return d

def _load_policy(policy_yaml: Optional[str], region: Optional[str]) -> Policy:
    if not policy_yaml:
        with open("schemas/pricing_policy.v0.yaml", "r", encoding="utf-8") as f:
            policy_yaml = f.read()
    raw = yaml.safe_load(policy_yaml)

    # If multi-region is present, pick requested region or default
    if "regions" in raw:
        key = region or raw.get("default_region") or next(iter(raw["regions"].keys()))
        raw = raw["regions"][key]

    return Policy(
        id=str(raw.get("policy_id", "pricing_policy.v0")),
        region=str(raw.get("region", region or "unspecified")),
        markups=dict(raw.get("markups", {})),
        waste_defaults=dict(raw.get("waste_defaults", {})),
        tax_pct=float(raw.get("tax_pct", 0.0)),
        escalation_pct=float(raw.get("escalation_pct", 0.0)),
        resolution_order=list(raw.get("resolution_order", ["vendor_quotes","unit_costs","policy_defaults"]))
    )

def _parse_csv_kv(csv_text: Optional[str]) -> Dict[Tuple[str, str], float]:
    """
    Returns {(trade, code): unit_cost}
    CSV headers expected: trade,code,unit_cost
    """
    result: Dict[Tuple[str, str], float] = {}
    if not csv_text:
        return result
    rdr = csv.DictReader(io.StringIO(csv_text))
    for row in rdr:
        trade = row.get("trade","").strip().lower()
        code = row.get("code","").strip().lower()
        try:
            unit_cost = float(row.get("unit_cost","").strip())
        except Exception:
            continue
        if trade and code and unit_cost >= 0:
            result[(trade, code)] = unit_cost
    return result

def _waste_pct_for(trade: str, policy: Policy) -> float:
    t = trade.lower()
    if t in policy.waste_defaults:
        return float(policy.waste_defaults[t])
    return float(policy.waste_defaults.get("global_pct", 0.0))

def _resolve_unit_cost(
    trade: str,
    code: str,
    policy: Policy,
    vendor: Dict[Tuple[str,str], float],
    unit: Dict[Tuple[str,str], float],
) -> Tuple[float, str]:
    key = (trade.lower(), code.lower())
    for source in policy.resolution_order:
        if source == "vendor_quotes" and key in vendor:
            return vendor[key], "vendor_quotes"
        if source == "unit_costs" and key in unit:
            return unit[key], "unit_costs"
        if source == "policy_defaults":
            # optional: embed policy defaults per trade/code in YAML; for now, not present
            continue
    # fallback: 0 with policy_defaults source
    return 0.0, "policy_defaults"

# ---- Core API ----------------------------------------------------------------

def price_quantities(
    *,
    quantities: List[dict],
    policy_yaml: Optional[str],
    region: Optional[str],
    unit_costs_csv: Optional[str],
    vendor_quotes_csv: Optional[str],
) -> Dict[str, Any]:
    """
    Returns an object conforming to schemas/estimate_response.schema.json (v0)
    """
    policy = _load_policy(policy_yaml, region)
    vendor = _parse_csv_kv(vendor_quotes_csv)
    unit = _parse_csv_kv(unit_costs_csv)

    priced: List[PricedItem] = []
    trade_totals: Dict[str, float] = {}
    warnings: List[str] = []

    for raw in quantities:
        qi = QuantityItem(
            trade=raw["trade"],
            code=raw["code"],
            description=raw.get("description",""),
            uom=raw.get("uom","EA"),
            qty=float(raw.get("qty", 0.0)),
            notes=raw.get("notes")
        )
        base_unit, source = _resolve_unit_cost(qi.trade, qi.code, policy, vendor, unit)
        waste_pct = _waste_pct_for(qi.trade, policy)
        extended_base = qi.qty * base_unit
        extended_with_waste = extended_base * (1.0 + waste_pct)

        overhead = extended_with_waste * float(policy.markups.get("overhead_pct", 0.0))
        profit = (extended_with_waste + overhead) * float(policy.markups.get("profit_pct", 0.0))
        subtotal_before_tax = extended_with_waste + overhead + profit
        tax = subtotal_before_tax * float(policy.tax_pct)
        escalated = subtotal_before_tax * float(policy.escalation_pct)
        total = subtotal_before_tax + tax + escalated

        pi = PricedItem(
            trade=qi.trade, code=qi.code, description=qi.description, uom=qi.uom, qty=qi.qty,
            unit_cost=base_unit, waste_pct=waste_pct, extended_base=extended_base,
            extended_with_waste=extended_with_waste, markup_overhead=overhead,
            markup_profit=profit, subtotal_before_tax=subtotal_before_tax,
            tax=tax, total=total, source=source
        )
        priced.append(pi)
        trade_totals[qi.trade] = trade_totals.get(qi.trade, 0.0) + total

        if base_unit == 0.0 and source == "policy_defaults":
            warnings.append(f"Missing cost for {qi.trade}/{qi.code}; defaulted to 0.0")

    # compose v0 response
    line_items = [
        {
            "trade": p.trade, "code": p.code, "description": p.description, "uom": p.uom, "qty": p.qty,
            "unit_cost": round(p.unit_cost, 4), "waste_pct": round(p.waste_pct, 4),
            "extended_base": round(p.extended_base, 2),
            "extended_with_waste": round(p.extended_with_waste, 2),
            "markup_overhead": round(p.markup_overhead, 2),
            "markup_profit": round(p.markup_profit, 2),
            "subtotal_before_tax": round(p.subtotal_before_tax, 2),
            "tax": round(p.tax, 2),
            "total": round(p.total, 2),
            "source": p.source
        } for p in priced
    ]
    trades = [
        {"trade": t, "subtotal": round(v, 2)} for t, v in sorted(trade_totals.items())
    ]
    grand_total = round(sum(trade_totals.values()), 2)

    response = {
        "version": "v0",
        "policy_id": policy.id,
        "region": policy.region,
        "trades": trades,
        "line_items": line_items,
        "grand_total": grand_total,
        "warnings": warnings,
        "digests": _digests(quantities, policy_yaml or open("schemas/pricing_policy.v0.yaml","r",encoding="utf-8").read(), unit_costs_csv, vendor_quotes_csv),
    }
    return response
