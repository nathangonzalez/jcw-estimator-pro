from __future__ import annotations
import os
import re
from typing import Any, Dict, List, Optional, Tuple

# Prefer PyMuPDF for page-wise text and size if available
try:
    import fitz  # PyMuPDF
    _HAVE_FITZ = True
except Exception:
    _HAVE_FITZ = False

# Fallback text extractor (whole doc) if PyMuPDF isn't present
try:
    from pdfminer.high_level import extract_text as pdfminer_extract_text
    _HAVE_PDFMINER = True
except Exception:
    _HAVE_PDFMINER = False


# --------------------------- Utilities ---------------------------

def _inches_str(points: float) -> str:
    try:
        inches = points / 72.0
        return f"{inches:.2f} in"
    except Exception:
        return "Unknown"

def _page_size_label(width_pt: float, height_pt: float) -> str:
    try:
        return f"{int(round(width_pt))}x{int(round(height_pt))} pt ({_inches_str(width_pt)} x {_inches_str(height_pt)})"
    except Exception:
        return "Unknown"

def _split_text_equal(text: str, parts: int) -> List[str]:
    if not text:
        return [""]
    if parts <= 1:
        return [text]
    n = max(len(text) // parts, 1)
    chunks = [text[i:i+n] for i in range(0, len(text), n)]
    return chunks[:parts]


# --------------------------- Scale detection ---------------------------

# Patterns for scale strings like 'Scale 1/8"=1'-0"' or '1:100'
SCALE_PATTERNS = [
    r'(?i)\bscale\s*[:\s]*\d+\s*/\s*\d+\s*"?\s*=\s*\d+\'(?:\s*-\s*\d+")?',
    r'(?i)\bscale\s*[:\s]*\d+\s*:\s*\d+\b',
    r'(?i)\b\d+\s*/\s*\d+\s*"?\s*=\s*\d+\'(?:\s*-\s*\d+")?',
    r'(?i)\b\d+\s*:\s*\d+\b',
]

def _find_scales_in_text(text: str) -> List[str]:
    found: List[str] = []
    src = text or ""
    for pat in SCALE_PATTERNS:
        for m in re.finditer(pat, src):
            lab = m.group(0).strip()
            if lab not in found:
                found.append(lab)
    return found

def _normalize_scale_label(raw: str) -> Optional[str]:
    """
    Normalize to e.g.:
      - 1/8"=1'-0"  -> 1_8in_per_ft
      - 3/16"=1'-0" -> 3_16in_per_ft
      - 1:100       -> 1_to_100
    Returns None if not recognized.
    """
    if not raw:
        return None
    lbl = raw.strip()

    # inch-based  a/b" = c'-d"
    m = re.search(r'(?i)(\d+)\s*/\s*(\d+)\s*"?\s*=\s*(\d+)\s*\'(?:\s*-\s*\d+\s*")?', lbl)
    if m:
        a = m.group(1)
        b = m.group(2)
        # normalize to a_bin_per_ft
        return f"{a}_{b}in_per_ft"

    # metric a:b
    m2 = re.search(r'(?i)(\d+)\s*:\s*(\d+)', lbl)
    if m2:
        return f"{m2.group(1)}_to_{m2.group(2)}"

    return None


# --------------------------- Sheet index heuristics ---------------------------

# Heuristic: first non-empty uppercase-ish token that looks like "A1.01" or "S2", etc.
SHEET_ID_LINE = re.compile(r'(?m)^\s*([A-Z][A0-9\.]+)\b(?:[ \t\-–—:]+(.*))?$')

def _guess_sheet_info(page_text: str, page_no: int) -> Dict[str, Optional[str]]:
    """
    Return {'page_no': page_no, 'sheet_id': str|None, 'sheet_name': str|None}
    Strategy:
      - Scan lines; take first match of SHEET_ID_LINE.
      - If trailing text exists on same line -> name.
      - Else try next line as name.
    """
    sheet_id: Optional[str] = None
    sheet_name: Optional[str] = None
    if not page_text:
        return {"page_no": page_no, "sheet_id": None, "sheet_name": None}

    lines = [ln.strip() for ln in page_text.splitlines()]
    for idx, ln in enumerate(lines):
        m = SHEET_ID_LINE.match(ln)
        if m:
            sheet_id = m.group(1)
            rest = (m.group(2) or "").strip()
            if rest:
                sheet_name = rest
            else:
                # try next non-empty line as name (title-like)
                for j in range(idx+1, min(idx+6, len(lines))):
                    if lines[j]:
                        sheet_name = lines[j]
                        break
            break

    # clamp overly long names
    if sheet_name and len(sheet_name) > 200:
        sheet_name = sheet_name[:200] + "…"
    return {"page_no": page_no, "sheet_id": sheet_id, "sheet_name": sheet_name}


# --------------------------- Main extractor ---------------------------

def extract_plan_features(pdf_path: str) -> Dict[str, Any]:
    """
    Extract doc meta, per-page scales (raw + normalized), and sheet index (sheet_id/name)
    Returns PlanFeaturesV0 dict conforming to schemas/plan_features.schema.json.
    """
    if not pdf_path or not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    doc_meta_file_name = os.path.basename(pdf_path)
    page_count: int = 0
    page_sizes: List[str] = []
    pages_text: List[str] = []

    if _HAVE_FITZ:
        with fitz.open(pdf_path) as doc:
            page_count = len(doc)
            for i in range(page_count):
                page = doc.load_page(i)
                # size in points (72 pt/inch)
                w, h = page.rect.width, page.rect.height
                page_sizes.append(_page_size_label(w, h))
                pages_text.append(page.get_text("text") or "")
    else:
        # Without fitz, we can't reliably get page sizes; return "Unknown"
        if _HAVE_PDFMINER:
            text_all = pdfminer_extract_text(pdf_path) or ""
            # Heuristic split into up to 3 pages of text to keep deterministic
            pages_text = _split_text_equal(text_all, 3)
            page_count = max(len(pages_text), 1)
            page_sizes = ["Unknown"] * page_count
        else:
            # Last resort: minimal placeholders
            pages_text = [""]
            page_count = 1
            page_sizes = ["Unknown"]

    # Build scales
    scales: List[Dict[str, Any]] = []
    for idx, pt in enumerate(pages_text, start=1):
        labels = _find_scales_in_text(pt or "")
        for raw in labels:
            scales.append({
                "page_no": idx,
                "raw": raw,
                "normalized": _normalize_scale_label(raw)
            })

    # Build sheets
    sheets: List[Dict[str, Any]] = []
    for idx, pt in enumerate(pages_text, start=1):
        sheets.append(_guess_sheet_info(pt or "", idx))

    result: Dict[str, Any] = {
        "doc": {
            "file_name": doc_meta_file_name,
            "page_count": page_count,
            "page_sizes": page_sizes,
        },
        "sheets": sheets,
        "scales": scales,
    }
    return result
