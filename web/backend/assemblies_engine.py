"""
Assemblies Engine (v0)
- Reads YAML assembly rule files and expands into line items based on simple plan features.
- No external calls; only local file reads.

YAML shape (example):
---
project_types:
  - SOD
assemblies:
  - trade: drywall
    item: drywall_board
    unit: SF
    formula: "area_sqft * 0.5"
    notes: "Walls approx. 0.5x area"
  - trade: paint
    item: interior_paint
    unit: SF
    formula: "area_sqft * 0.5"
    notes: "One coat typical"
variables:
  # optional variable aliases
  wall_sf: "area_sqft * 0.5"

Formulas:
- Python expressions evaluated with a restricted variable scope drawn from plan_features and 'variables' evaluated results.
- Allowed keys in scope: numbers, dicts, and precomputed variables.
- No builtins or modules exposed.
"""
from __future__ import annotations

import os
import yaml
from typing import Any, Dict, List, Tuple


def _safe_eval(expr: str, scope: Dict[str, Any]) -> float:
    """
    Evaluate a simple arithmetic expression with a restricted scope.
    This is intentionally minimal and should not expose builtins.
    """
    if not isinstance(expr, str):
        return 0.0
    # No builtins; only provided scope
    return float(eval(expr, {"__builtins__": {}}, dict(scope)))


def _load_yaml(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _matches_project_type(doc: Dict[str, Any], project_type: str) -> bool:
    pts = doc.get("project_types")
    if not pts:
        return True
    return str(project_type).strip().lower() in {str(x).strip().lower() for x in pts}


def expand_from_files(plan_features: Dict[str, Any], yaml_paths: List[str]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    plan_features expected keys (best-effort):
      - project_id: str
      - project_type: str
      - area_sqft: float
      - fixtures: dict

    Returns:
      (lines, applied_rules)
      lines: List[{trade,item,quantity,unit,notes}]
      applied_rules: List[rule_dict] of rules that contributed > 0 quantity
    """
    project_type = (plan_features or {}).get("project_type") or "SOD"
    area_sqft = float((plan_features or {}).get("area_sqft") or 0.0)
    fixtures = (plan_features or {}).get("fixtures") or {}
    scope_base = {
        "area_sqft": area_sqft,
        "fixtures": fixtures,
        # common fixture shortcuts
        "fixture_count": sum((fixtures or {}).values()) if isinstance(fixtures, dict) else 0.0,
    }

    lines: List[Dict[str, Any]] = []
    applied: List[Dict[str, Any]] = []

    for p in yaml_paths:
        if not os.path.exists(p):
            continue
        try:
            doc = _load_yaml(p)
        except Exception:
            continue

        if not _matches_project_type(doc, project_type):
            continue

        # Variables block (optional) can predefine aliases for expressions
        scope = dict(scope_base)
        for var_name, var_expr in (doc.get("variables") or {}).items():
            try:
                scope[var_name] = _safe_eval(str(var_expr), scope)
            except Exception:
                scope[var_name] = 0.0

        for rule in (doc.get("assemblies") or []):
            trade = str(rule.get("trade") or "").strip()
            item = str(rule.get("item") or "").strip()
            unit = str(rule.get("unit") or "EA").strip().upper()
            notes = str(rule.get("notes") or "")
            qty_expr = rule.get("formula") or rule.get("quantity") or "0"

            try:
                qty_val = _safe_eval(str(qty_expr), scope)
            except Exception:
                qty_val = 0.0

            # Enforce non-negative
            if qty_val < 0:
                qty_val = 0.0

            if trade and item and qty_val > 0:
                lines.append({
                    "trade": trade,
                    "item": item,
                    "quantity": float(qty_val),
                    "unit": unit,
                    "notes": notes,
                })
                r_copy = dict(rule)
                r_copy["computed_quantity"] = float(qty_val)
                applied.append(r_copy)

    return lines, applied
