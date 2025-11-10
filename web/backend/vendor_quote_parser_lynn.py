#!/usr/bin/env python3
"""
Lynn F3b — Vendor Quote Parser (DEV-FAST)
- Walks data/lynn/raw/vendor/** for PDFs
- Extracts text (pdfminer.six if available) and heuristically parses line items
- Classifies vendor/trade using data/lynn/vendor_rules.yaml (regex 'match')
- Emits per-vendor JSON/CSV and a combined canonical CSV under data/lynn/working

Canonical row shape (see schemas/vendor_quote_row.schema.json):
  {vendor, trade, item, description, unit, qty, unit_cost?, line_total?, notes?}

Outputs:
- data/lynn/working/vendor/rows/<vendor>.rows.json
- data/lynn/working/vendor/rows/<vendor>.rows.csv
- data/lynn/working/vendor_quotes.canonical.csv
- data/lynn/working/vendor_quotes.canonical.json  (container: {project_id, rows: [...]})
Guardrails:
- Only touches data/lynn; no deletion.
"""
from __future__ import annotations

import os
import re
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

# Optional deps (repo already carries pdfminer.six in requirements)
try:
    from pdfminer.high_level import extract_text
except Exception:
    extract_text = None

try:
    import yaml  # pyyaml
except Exception:
    yaml = None

REPO = Path(__file__).resolve().parents[2]
LYNN = REPO / "data" / "lynn"
RAW_VENDOR = LYNN / "raw" / "vendor"
WORKING = LYNN / "working"
OUT_ROWS_DIR = WORKING / "vendor" / "rows"
CANON_CSV = WORKING / "vendor_quotes.canonical.csv"
CANON_JSON = WORKING / "vendor_quotes.canonical.json"
RULES = LYNN / "vendor_rules.yaml"
TAXO_MAP = REPO / "data" / "taxonomy" / "vendor_map.yaml"

CANON_HEADERS = ["vendor","trade","item","description","unit","qty","unit_cost","line_total","quoted_total","notes"]

UNIT_NORMALIZE = {
    "ea": "EA", "each": "EA", "unit": "EA",
    "lf": "LF", "lnft": "LF", "ln ft": "LF",
    "sf": "SF", "sqft": "SF", "sq ft": "SF",
    "cy": "CY", "cuyd": "CY", "cu yd": "CY",
    "sy": "SY"
}

def _load_vendor_map() -> Dict[str, Any]:
    """
    Load optional vendor mapping config: normalizers, rules, unit_overrides
    """
    if yaml is None or not TAXO_MAP.exists():
        return {}
    try:
        return yaml.safe_load(TAXO_MAP.read_text(encoding="utf-8")) or {}
    except Exception:
        return {}

def _apply_normalizers(text: str, cfg: Dict[str, Any]) -> str:
    s = text or ""
    norms = (cfg or {}).get("normalizers") or []
    for n in norms:
        pat = str(n.get("pattern") or "").strip()
        repl = str(n.get("replace") or "")
        if not pat:
            continue
        try:
            s = re.sub(pat, repl, s, flags=re.IGNORECASE)
        except re.error:
            # fallback literal replace
            s = s.replace(pat, repl)
    return s.strip()

def _map_trade_item(desc: str, cfg: Dict[str, Any]) -> Dict[str, Optional[str]]:
    """
    Return {'trade':..., 'item':...} if a rule matches, else {}.
    """
    if not desc:
        return {}
    rules = (cfg or {}).get("rules") or []
    for r in rules:
        cond = str(r.get("if") or "").strip()
        to = r.get("to") or {}
        if not cond:
            continue
        try:
            if re.search(cond, desc, flags=re.IGNORECASE):
                t = (to.get("trade") or "").strip()
                i = (to.get("item") or "").strip()
                if t and i:
                    return {"trade": t, "item": i}
        except re.error:
            if cond.lower() in desc.lower():
                t = (to.get("trade") or "").strip()
                i = (to.get("item") or "").strip()
                if t and i:
                    return {"trade": t, "item": i}
    return {}


def _load_rules() -> Dict[str, Any]:
    rules: Dict[str, Any] = {"rules": [], "defaults": {"doc_type_by_ext": {}}}
    if yaml is None or not RULES.exists():
        return rules
    try:
        data = yaml.safe_load(RULES.read_text(encoding="utf-8")) or {}
        if isinstance(data, dict):
            rules.update(data)
    except Exception:
        pass
    return rules


def _classify_vendor_trade(pdf_path: Path, rules: Dict[str, Any]) -> Dict[str, Optional[str]]:
    text = str(pdf_path).lower()
    vendor = None
    trade = None
    for r in (rules.get("rules") or []):
        pat = (r.get("match") or "").strip()
        if not pat:
            continue
        try:
            if re.search(pat, text, flags=re.IGNORECASE):
                vendor = vendor or r.get("vendor")
                trade = trade or r.get("trade")
        except re.error:
            if pat.lower() in text:
                vendor = vendor or r.get("vendor")
                trade = trade or r.get("trade")
    return {"vendor": vendor or pdf_path.stem, "trade": trade or ""}


_num_re = re.compile(r"[-+]?\d{1,3}(?:,\d{3})*(?:\.\d+)?|\d+(?:\.\d+)?")
_money_re = re.compile(r"^\s*\$?\s*([-+]?\d{1,3}(?:,\d{3})*(?:\.\d+)?|\d+(?:\.\d+)?)\s*$")
_unit_token_re = re.compile(r"(?i)\b(ea|each|unit|lf|ln\s*ft|lnft|sf|sq\s*ft|sqft|cy|cu\s*yd|cuyd|sy)\b")


def _to_float(s: Any, default: Optional[float] = None) -> Optional[float]:
    if s is None:
        return default
    if isinstance(s, (int, float)):
        return float(s)
    try:
        ss = str(s).strip().replace(",", "").replace("$", "")
        return float(ss)
    except Exception:
        return default


def _norm_unit(tok: Optional[str]) -> str:
    if not tok:
        return ""
    t = tok.strip().lower()
    t = t.replace("ln ft", "lf").replace("lnft", "lf").replace("sq ft", "sf").replace("sqft", "sf").replace("cu yd", "cy")
    return UNIT_NORMALIZE.get(t, t.upper())


def _parse_line_candidate(line: str) -> Dict[str, Any]:
    """
    Heuristic parser for a single quote line:
    - looks for description, qty, unit, and a trailing money token (line total)
    - returns minimal dict; missing fields may be None; caller fills vendor/trade/item
    """
    original = line.strip()
    if not original:
        return {}

    # Pull a unit token if present
    unit_match = _unit_token_re.search(original)
    unit = _norm_unit(unit_match.group(1)) if unit_match else ""

    # Try to find a trailing money token (line total)
    tokens = original.split()
    line_total = None
    if tokens:
        m = _money_re.match(tokens[-1])
        if m:
            line_total = _to_float(m.group(1), None)
            # remove last token from description construction
            tokens = tokens[:-1]

    # Extract a qty number somewhere before unit (prefer the number nearest to unit)
    qty = None
    if tokens:
        # Look left of unit token index if we found a unit
        idx_unit = -1
        if unit_match:
            idx_unit = len(original[:unit_match.start()].split()) - 1
        # Scan tokens for a numeric candidate near idx_unit, else from right
        numeric_candidates: List[float] = []
        for t in tokens:
            if _num_re.fullmatch(t.replace(",", "")):
                v = _to_float(t, None)
                if v is not None:
                    numeric_candidates.append(v)
        if numeric_candidates:
            qty = numeric_candidates[0] if idx_unit < 0 else numeric_candidates[-1]

    # Reconstitute description (without trailing price token)
    description = " ".join(tokens).strip()

    return {
        "description": description,
        "unit": unit or "",
        "qty": qty,
        "line_total": line_total,
    }


def _extract_rows_from_text(text: str, vendor: str, trade: str, map_cfg: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    if not text:
        return rows
    for line in text.splitlines():
        # Skip obvious headers/footers
        if re.search(r"(?i)\b(subtotal|total|tax|quote|proposal|page\s+\d+|thank|balance)\b", line):
            # but keep lines where a total seems like a per-item line (has unit + qty)
            pass
        # Normalize + parse
        norm_line = _apply_normalizers(line, map_cfg or {})
        cand = _parse_line_candidate(norm_line or line)
        if not cand:
            continue
        # Accept if we have at least a description and either qty/line_total detected
        if cand.get("description") and (cand.get("qty") is not None or cand.get("line_total") is not None):
            # Attempt taxonomy mapping for trade/item
            mapped = _map_trade_item(cand["description"], map_cfg or {})
            trade_mapped = (mapped.get("trade") or trade or "").strip()
            item_mapped = (mapped.get("item") or (cand["description"][:40] or "")).strip()
            # Unit override from vendor map if present
            unit_map = ((map_cfg or {}).get("unit_overrides") or {})
            unit_norm = (cand["unit"] or "EA").strip()
            unit_over = unit_map.get(unit_norm.lower(), None)
            final_unit = unit_over or UNIT_NORMALIZE.get(unit_norm.lower(), unit_norm.upper())
            # Coerce totals
            q_total = cand["line_total"] if cand["line_total"] is not None else None
            rows.append({
                "vendor": vendor,
                "trade": trade_mapped,
                "item": item_mapped.lower().replace(" ", "_"),
                "description": cand["description"],
                "unit": final_unit or "EA",
                "qty": float(cand["qty"] if cand["qty"] is not None else 1.0),
                "unit_cost": None,
                "line_total": q_total,
                "quoted_total": q_total,
                "notes": ""
            })
    return rows


def _extract_pdf_text(p: Path) -> str:
    if extract_text is None:
        return ""
    try:
        return extract_text(str(p)) or ""
    except Exception:
        return ""


def _write_rows_csv(rows: List[Dict[str, Any]], out_csv: Path) -> None:
    import csv
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    with out_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=CANON_HEADERS)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in CANON_HEADERS})


def _append_canonical(rows: List[Dict[str, Any]], project_id: str) -> None:
    # Append rows to combined canonical CSV and JSON container (overwrite JSON)
    import csv
    WORKING.mkdir(parents=True, exist_ok=True)

    # CSV append with header if missing
    write_header = not CANON_CSV.exists()
    with CANON_CSV.open("a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=CANON_HEADERS)
        if write_header:
            w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in CANON_HEADERS})

    # JSON container overwrite with all rows
    all_rows: List[Dict[str, Any]] = []
    try:
        import csv as _csv
        with CANON_CSV.open("r", encoding="utf-8") as f:
            reader = _csv.DictReader(f)
            for r in reader:
                # coerce numeric fields
                def _num_or_none(x: str) -> Optional[float]:
                    try:
                        if x is None or str(x).strip() == "":
                            return None
                        return float(str(x).replace(",", "").replace("$", ""))
                    except Exception:
                        return None
                all_rows.append({
                    "vendor": r.get("vendor",""),
                    "trade": r.get("trade",""),
                    "item": r.get("item",""),
                    "description": r.get("description",""),
                    "unit": r.get("unit",""),
                    "qty": _num_or_none(r.get("qty")),
                    "unit_cost": _num_or_none(r.get("unit_cost")),
                    "line_total": _num_or_none(r.get("line_total")),
                    "notes": r.get("notes",""),
                })
    except Exception:
        pass

    CANON_JSON.parent.mkdir(parents=True, exist_ok=True)
    CANON_JSON.write_text(json.dumps({"project_id": project_id, "rows": all_rows}, indent=2), encoding="utf-8")


def parse_all(project_id: str = "LYNN-001") -> Dict[str, Any]:
    """
    Walk vendor PDFs and emit per-vendor rows + canonical CSV/JSON.
    Returns summary dict with counts.
    """
    rules = _load_rules()
    map_cfg = _load_vendor_map()
    OUT_ROWS_DIR.mkdir(parents=True, exist_ok=True)
    # Reset canonical CSV if we want a fresh combined file
    if CANON_CSV.exists():
        # Non-destructive policy: keep a rotated copy in working/_archive if needed.
        # For simplicity, append fresh; callers can delete manually if desired.
        pass

    grand_rows: List[Dict[str, Any]] = []
    parsed_files = 0
    coverage = {"mapped": 0, "unmapped": 0, "by_vendor": {}}

    for root, _, files in os.walk(RAW_VENDOR):
        for fn in files:
            p = Path(root) / fn
            if p.suffix.lower() != ".pdf":
                continue
            parsed_files += 1
            ctx = _classify_vendor_trade(p, rules)
            vendor = ctx["vendor"] or p.stem
            trade = (ctx["trade"] or "").lower()

            text = _extract_pdf_text(p)
            rows = _extract_rows_from_text(text, vendor, trade, map_cfg)

            # Coverage tallies
            vkey = vendor
            if vkey not in coverage["by_vendor"]:
                coverage["by_vendor"][vkey] = {"mapped": 0, "unmapped": 0}
            for r in rows:
                qt = r.get("quoted_total") or r.get("line_total") or 0
                ok = bool(r.get("trade")) and bool(r.get("item")) and (qt or 0) and float(qt or 0) > 0
                if ok:
                    coverage["mapped"] += 1
                    coverage["by_vendor"][vkey]["mapped"] += 1
                else:
                    coverage["unmapped"] += 1
                    coverage["by_vendor"][vkey]["unmapped"] += 1

            # Persist per-vendor
            (OUT_ROWS_DIR / f"{vendor}.rows.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")
            _write_rows_csv(rows, OUT_ROWS_DIR / f"{vendor}.rows.csv")

            # Append canonical
            _append_canonical(rows, project_id=project_id)
            grand_rows.extend(rows)

    # Write mapping coverage
    (WORKING / "vendor_mapping_coverage.json").write_text(json.dumps(coverage, indent=2), encoding="utf-8")

    return {"project_id": project_id, "files_parsed": parsed_files, "row_count": len(grand_rows)}


def cli_main() -> None:
    res = parse_all(project_id="LYNN-001")
    print(json.dumps(res, indent=2))


if __name__ == "__main__":
    cli_main()
