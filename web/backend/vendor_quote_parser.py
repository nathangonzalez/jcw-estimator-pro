from __future__ import annotations
import json, re, csv
from pathlib import Path
from typing import List, Dict, Any

try:
    from pdfminer.high_level import extract_text  # pdfminer.six
except Exception:
    extract_text = None  # allow import without runtime deps during sync-only

CANON_HEADERS = ["vendor","trade","item","description","unit","qty","unit_cost","line_total","notes"]

def parse_pdf_to_rows(pdf_path: str, vendor_name: str) -> List[Dict[str, Any]]:
    """
    Heuristic stub: pulls text and emits guessed rows for manual cleanup.
    Intentionally conservative—aim is to produce a skeleton we can edit.
    """
    text = ""
    p = Path(pdf_path)
    if extract_text is not None and p.exists() and p.suffix.lower() == ".pdf":
        try:
            text = extract_text(str(p)) or ""
        except Exception:
            text = ""
    # naive split-by-lines and regex probes
    rows: List[Dict[str, Any]] = []
    for line in (text.splitlines() if text else []):
        # example heuristics; real patterns will evolve with real quotes
        if re.search(r'(?i)\b(toilet|water closet|wc)\b', line):
            rows.append({
                "vendor": vendor_name, "trade": "plumbing", "item": "toilet",
                "description": line.strip(), "unit": "ea", "qty": 1,
                "unit_cost": None, "line_total": None, "notes": ""
            })
        elif re.search(r'(?i)\b(sink|lav(?:atory)?)\b', line):
            rows.append({
                "vendor": vendor_name, "trade": "plumbing", "item": "lavatory_sink",
                "description": line.strip(), "unit": "ea", "qty": 1,
                "unit_cost": None, "line_total": None, "notes": ""
            })
    return rows

def write_rows_json(rows: List[Dict[str,Any]], out_json: Path) -> None:
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(rows, indent=2), encoding="utf-8")

def write_rows_csv(rows: List[Dict[str,Any]], out_csv: Path) -> None:
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    with out_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=CANON_HEADERS)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in CANON_HEADERS})

def append_to_canonical(project_dir: Path, vendor_csv: Path) -> None:
    canon = project_dir / "quotes.canonical.csv"
    existing = canon.exists()
    project_dir.mkdir(parents=True, exist_ok=True)
    with vendor_csv.open("r", encoding="utf-8") as src, canon.open("a", newline="", encoding="utf-8") as dst:
        if not existing:
            dst.write(",".join(CANON_HEADERS) + "\n")
        # skip header
        _ = src.readline()
        for line in src:
            dst.write(line)
