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

# Diagnostics outputs for calibration integrity
OUT_DIR = REPO / "output"
OUT_OUTLIERS = OUT_DIR / "CALIBRATION_OUTLIERS.csv"
OUT_DUPES = OUT_DIR / "CALIBRATION_DUPES.csv"

def _parsing_cfg(cfg: Dict[str, Any]) -> Dict[str, Any]:
    p = ((cfg or {}).get("parsing") or {})
    return {
        "max_line_amount": float(p.get("max_line_amount", 10_000_000)),
        "drop_total_keywords": list(p.get("drop_total_keywords", ["total", "total bid", "proposal total", "grand total"])),
        "dedupe_window": int(p.get("dedupe_window", 10)),
        "drop_line_keywords": list(p.get("drop_line_keywords", [])),
        "numeric_only_desc_min_len": int(p.get("numeric_only_desc_min_len", 5)),
        "accept_suffixes": [str(x).lower() for x in p.get("accept_suffixes", ["k","m"])],
        "prefer_latest_file": bool(p.get("prefer_latest_file", True)),
        "acceptable_ratio": float(p.get("acceptable_ratio", 3.0)),
    }

_money_tok = re.compile(r"[A-Za-z$€£\s]*([()\-+]?\s*(?:\d{1,3}([.,]\d{3})+|\d+)([.,]\d{1,2})?\s*(?:[kKmM])?)")
def parse_money(text: str, cfg: Optional[Dict[str, Any]] = None) -> (Optional[float], Optional[str]):
    """
    Canonical money normalizer:
      - Strips currency symbols and spaces
      - US: 12,345.67 -> 12345.67
      - EU: 12.345,67 -> 12345.67
      - Plain digits: 1234567 -> 1234567.00
      - K/M suffixes: 12.5k -> 12500 ; 1.2m -> 1200000
      - Parentheses => negative
      - Caps at max_line_amount (drop if exceeded)
    Returns (value, reason_if_dropped)
    """
    if not text:
        return (None, "empty")
    s = str(text).strip()
    m = _money_tok.search(s)
    if not m:
        return (None, "no-match")
    core = m.group(1).strip()

    neg = False
    if core.startswith("(") and core.endswith(")"):
        neg = True
        core = core[1:-1].strip()
    if core.startswith("+") or core.startswith("-"):
        neg = neg or core.startswith("-")
        core = core[1:].strip()

    # Handle suffixes
    suffix = None
    if core and core[-1].lower() in {"k","m"}:
        suffix = core[-1].lower()
        core = core[:-1]

    # Detect EU vs US separators
    # If both '.' and ',' present and comma is last separator => EU
    eu = ("," in core and "." in core and core.rfind(",") > core.rfind("."))
    if eu:
        # 12.345,67 -> remove dots, replace comma with dot
        core = core.replace(".", "").replace(",", ".")
    else:
        # US: remove commas
        core = core.replace(",", "")

    # Plain digits => decimal as-is
    try:
        val = float(core)
    except Exception:
        return (None, "parse-failed")

    if suffix == "k":
        val *= 1_000.0
    elif suffix == "m":
        val *= 1_000_000.0

    if neg:
        val = -val

    # Cap check
    p = _parsing_cfg(_load_vendor_map())
    mx = p["max_line_amount"]
    if abs(val) > mx:
        return (None, f"gt-max-{mx}")

    return (round(val, 2), None)

def _is_summary_or_duplicate_desc(desc: str, drop_keywords: List[str]) -> bool:
    d = (desc or "").strip().lower()
    for kw in drop_keywords:
        if kw.lower() in d:
            return True
    return False

_date_token = re.compile(r"\b((?:20)?\d{2})[.\-_]([01]?\d)[.\-_]([0-3]?\d)\b")  # YYYY.MM.DD or YY.MM.DD
def choose_latest(paths: List[Path]) -> List[Path]:
    """
    Keep the most recent file(s) per vendor by date tokens in filename; fallback to mtime.
    """
    if not paths:
        return []
    buckets: Dict[str, List[Path]] = {}
    rules = _load_rules()
    for p in paths:
        vendor = _classify_vendor_trade(p, rules).get("vendor") or p.stem
        buckets.setdefault(vendor, []).append(p)
    chosen: List[Path] = []
    for vendor, lst in buckets.items():
        # pick latest by date token
        best = None
        best_key = None
        for p in lst:
            name = p.stem.lower()
            m = _date_token.search(name)
            if m:
                y, mo, d = m.groups()
                if len(y) == 2:
                    y = "20" + y
                key = (int(y), int(mo), int(d))
            else:
                ts = int(p.stat().st_mtime)
                key = (0,0,ts)
            if best_key is None or key > best_key:
                best_key = key
                best = p
        if best is not None:
            chosen.append(best)
    return chosen

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
# Require an explicit $ for a money token; limit to 2 decimals
_money_re = re.compile(r"^\s*\$\s*([-+]?\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?)\s*$")
# Find any $ amount anywhere in the line; prefer the last
_money_anywhere = re.compile(r"\$\s*([-+]?\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?)")
# Heuristic skip for metadata/noise lines (addresses, phones, headers)
_meta_skip_re = re.compile(r"(?i)\b(phone|fax|email|date|page\s*\d+|address|vero\s*beach|proposal|quote|bid|contract|terms|conditions|warranty|acceptance|pricing)\b")
# Price-ish cue words if we need to fall back to a plain number
_price_keywords_re = re.compile(r"(?i)\b(price|amount|total|labor|material|install|furnish|supply|provide|allowance|estimate)\b")
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

def _is_meta_line(line: str) -> bool:
    if not line:
        return True
    return bool(_meta_skip_re.search(line))


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

    # Try to find a money token (prefer any $ amount anywhere; else trailing $ token; else 'total/price' cue)
    tokens = original.split()
    line_total = None
    # $ anywhere in the line
    ma = _money_anywhere.findall(original)
    if ma:
        line_total = _to_float(ma[-1], None)
    else:
        # Trailing $ token
        if tokens:
            m = _money_re.match(tokens[-1])
            if m:
                line_total = _to_float(m.group(1), None)
                # remove last token from description construction
                tokens = tokens[:-1]
        # Cue words for totals without $, avoid obviously huge non-price tokens (phones/dates)
        if line_total is None and re.search(r"(?i)\b(total|price|amount)\b", original):
            nums = _num_re.findall(original)
            for n in reversed(nums):
                try:
                    v = float(str(n).replace(",", ""))
                    if 0 < v <= 200000:  # ignore absurd large metadata numbers
                        line_total = v
                        break
                except Exception:
                    pass
        # Final fallback: if we have price-ish keywords, take the last reasonable number as amount
        if line_total is None and _price_keywords_re.search(original):
            nums = _num_re.findall(original)
            for n in reversed(nums):
                try:
                    # reject very long integers (likely phones, ids)
                    if len(str(n).replace(".", "").replace(",", "")) >= 6 and "." not in str(n):
                        continue
                    v = float(str(n).replace(",", ""))
                    if 0 < v <= 200000:
                        line_total = v
                        break
                except Exception:
                    pass

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
        # Heuristic filter to avoid absurd EA quantities (phones/dates etc.)
        if qty is not None and (qty > 10000) and (unit == "EA"):
            qty = None

    # Reconstitute description (without trailing price token)
    description = " ".join(tokens).strip()

    return {
        "description": description,
        "unit": unit or "",
        "qty": qty,
        "line_total": line_total,
    }


def _extract_rows_from_text(text: str, vendor: str, trade: str, map_cfg: Optional[Dict[str, Any]] = None,
                            accum: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """
    accum optional keys:
      - drop_keywords: list[str]
      - dedupe_window: int
      - recent: list[tuple]
      - seen: set()
      - drop_line_keywords: list[str]
      - out_outliers: csv writer
      - out_dupes: csv writer
    """
    rows: List[Dict[str, Any]] = []
    if not text:
        return rows
    pcfg = _parsing_cfg(map_cfg or {})
    drop_kws = (accum or {}).get("drop_keywords") or pcfg["drop_total_keywords"]
    dedupe_window = int((accum or {}).get("dedupe_window") or pcfg["dedupe_window"])
    recent = (accum or {}).get("recent")
    seen = (accum or {}).get("seen")
    out_outliers = (accum or {}).get("out_outliers")
    out_dupes = (accum or {}).get("out_dupes")
    line_kws = (accum or {}).get("drop_line_keywords") or pcfg.get("drop_line_keywords", [])
    num_min = int(pcfg.get("numeric_only_desc_min_len", 6))

    for raw_line in text.splitlines():
        if _is_meta_line(raw_line):
            continue
        # Normalize + parse
        norm_line = _apply_normalizers(raw_line, map_cfg or {})
        cand = _parse_line_candidate(norm_line or raw_line)
        if not cand or not cand.get("description"):
            continue

        # Non-scope keyword drop (tax/allowance/freight/alt/etc.)
        desc_lower = (cand["description"] or "").lower()
        if any((kw or "").lower() in desc_lower for kw in line_kws):
            if out_outliers:
                out_outliers.writerow({"reason":"non-scope-keyword", "vendor":vendor, "desc":cand["description"], "value":"", "unit":""})
            continue

        # Numeric-heavy description drop (guard against OCR/IDs like "360000" etc.)
        desc_raw = (cand["description"] or "")
        digits = sum(1 for ch in desc_raw if ch.isdigit())
        letters = sum(1 for ch in desc_raw if ch.isalpha())
        if letters == 0 and len(desc_raw.strip()) >= num_min:
            # If no letters and at least 50% digits, drop as likely non-scope numeric
            if digits >= max(num_min, int(0.5 * len(desc_raw))):
                if out_outliers:
                    out_outliers.writerow({"reason":"desc-numeric-heavy", "vendor":vendor, "desc":cand["description"], "value":"", "unit":""})
                continue

        # Summary/total-like headers drop
        if _is_summary_or_duplicate_desc(cand["description"], drop_kws):
            if out_outliers:
                out_outliers.writerow({"reason":"summary-header", "vendor":vendor, "desc":cand["description"], "value":"", "unit":""})
            continue

        # Money normalization
        val, reason = parse_money(raw_line, map_cfg or {})
        if (reason and reason.startswith("gt-max")) or (val is None and reason):
            if out_outliers:
                out_outliers.writerow({"reason":reason, "vendor":vendor, "desc":cand["description"], "value":"", "unit":""})
            continue
        # If parser found money, use it; else fallback to candidate
        if val is not None:
            cand["line_total"] = val

        # Require a usable total
        if cand.get("line_total") is None or float(cand.get("line_total") or 0) <= 0:
            continue

        # Attempt taxonomy mapping for trade/item
        mapped = _map_trade_item(cand["description"], map_cfg or {})
        trade_mapped = (mapped.get("trade") or trade or "").strip()
        item_mapped = (mapped.get("item") or (cand["description"][:40] or "")).strip()

        # Unit override
        unit_map = ((map_cfg or {}).get("unit_overrides") or {})
        unit_norm = (cand["unit"] or "EA").strip()
        unit_over = unit_map.get(unit_norm.lower(), None)
        final_unit = unit_over or UNIT_NORMALIZE.get(unit_norm.lower(), unit_norm.upper())

        # Dedup: global set + sliding window on (vendor, desc_norm, value, unit)
        desc_norm = re.sub(r"\s+", " ", (cand["description"] or "").strip().lower())
        key = (vendor, desc_norm, round(float(cand["line_total"]), 2), final_unit)
        if (seen is not None) and (key in seen):
            if out_dupes:
                out_dupes.writerow({"vendor":vendor, "desc":cand["description"], "value":cand["line_total"], "unit":final_unit})
            continue
        if seen is not None:
            try:
                seen.add(key)
            except Exception:
                pass
        if recent is not None and key in recent:
            if out_dupes:
                out_dupes.writerow({"vendor":vendor, "desc":cand["description"], "value":cand["line_total"], "unit":final_unit})
            continue
        if recent is not None:
            recent.append(key)
            if len(recent) > dedupe_window:
                recent.pop(0)

        rows.append({
            "vendor": vendor,
            "trade": trade_mapped,
            "item": item_mapped.lower().replace(" ", "_"),
            "description": cand["description"],
            "unit": final_unit or "EA",
            "qty": float(cand["qty"] if cand["qty"] is not None else 1.0),
            "unit_cost": None,
            "line_total": cand["line_total"],
            "quoted_total": cand["line_total"],
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
    pcfg = _parsing_cfg(map_cfg)
    OUT_ROWS_DIR.mkdir(parents=True, exist_ok=True)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    # Fresh run: remove previous canonical and per-vendor rows (write fresh files)
    try:
        if CANON_CSV.exists():
            CANON_CSV.unlink()
        if CANON_JSON.exists():
            CANON_JSON.unlink()
    except Exception:
        pass
    try:
        if OUT_ROWS_DIR.exists():
            for child in OUT_ROWS_DIR.glob("*"):
                try:
                    child.unlink()
                except Exception:
                    pass
    except Exception:
        pass

    # Prepare diagnostics CSVs
    import csv as _csv
    outliers_f = OUT_OUTLIERS.open("w", newline="", encoding="utf-8")
    dupes_f = OUT_DUPES.open("w", newline="", encoding="utf-8")
    outliers_w = _csv.DictWriter(outliers_f, fieldnames=["reason","vendor","desc","value","unit"])
    dupes_w = _csv.DictWriter(dupes_f, fieldnames=["vendor","desc","value","unit"])
    outliers_w.writeheader()
    dupes_w.writeheader()

    grand_rows: List[Dict[str, Any]] = []
    parsed_files = 0
    coverage = {"mapped": 0, "unmapped": 0, "by_vendor": {}}

    # Discover all PDFs and optionally reduce to latest per vendor
    all_pdfs: List[Path] = []
    for root, _, files in os.walk(RAW_VENDOR):
        for fn in files:
            p = Path(root) / fn
            if p.suffix.lower() == ".pdf":
                all_pdfs.append(p)
    if pcfg["prefer_latest_file"]:
        # group by vendor and select latest
        by_vendor: Dict[str, List[Path]] = {}
        for p in all_pdfs:
            vendor = _classify_vendor_trade(p, rules).get("vendor") or p.stem
            by_vendor.setdefault(vendor, []).append(p)
        use_paths: List[Path] = []
        for v, lst in by_vendor.items():
            use_paths.extend(choose_latest(lst))
    else:
        use_paths = list(all_pdfs)

    deduper_accum = {
        "drop_keywords": pcfg["drop_total_keywords"],
        "dedupe_window": pcfg["dedupe_window"],
        "recent": [],
        "drop_line_keywords": pcfg.get("drop_line_keywords", []),
        "seen": set(),
        "out_outliers": outliers_w,
        "out_dupes": dupes_w,
    }

    for p in use_paths:
        parsed_files += 1
        ctx = _classify_vendor_trade(p, rules)
        vendor = ctx["vendor"] or p.stem
        trade = (ctx["trade"] or "").lower()

        text = _extract_pdf_text(p)
        rows = _extract_rows_from_text(text, vendor, trade, map_cfg, accum=deduper_accum)

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

    # Close diagnostic CSVs
    outliers_f.close()
    dupes_f.close()

    # Write mapping coverage
    (WORKING / "vendor_mapping_coverage.json").write_text(json.dumps(coverage, indent=2), encoding="utf-8")

    return {"project_id": project_id, "files_parsed": parsed_files, "row_count": len(grand_rows)}


def cli_main() -> None:
    res = parse_all(project_id="LYNN-001")
    print(json.dumps(res, indent=2))


if __name__ == "__main__":
    cli_main()
