import re
from typing import List, Optional, Dict, Any

SCALE_PATTERNS = [
    # Architectural inch-based scales like 1/8"=1'-0"
    r'(?i)\b(?:scale\s*)?(\d+)\s*/\s*(\d+)\s*"?\s*=\s*(\d+)\'\s*-\s*(\d+)"\b',
    r'(?i)\b(?:scale\s*)?(\d+)\s*/\s*(\d+)\s*"?\s*=\s*(\d+)\'\b',
    r'(?i)\b(?:scale\s*)?(\d+)\s*/\s*(\d+)\s*"?\s*=\s*(\d+)\s*feet\b',
    # Metric like 1:50 or 1:100
    r'(?i)\b(?:scale\s*)?(\d+)\s*:\s*(\d+)\b',
]

def find_scale_strings(text: str) -> List[str]:
    """Return a list of matched scale labels from arbitrary plan text."""
    matches: List[str] = []
    for pat in SCALE_PATTERNS:
        for m in re.finditer(pat, text or ""):
            label = m.group(0).strip()
            if label and label not in matches:
                matches.append(label)
    return matches

def normalize_scale(label: str) -> Dict[str, Any]:
    """
    Normalize a scale label to a real-world ratio (inches per drawing unit for imperial, or unitless for metric).
    Result:
      { "ratio": float|None, "label": str }
    Heuristics:
      - 1/8\"=1'-0\" -> 96.0 (i.e., 1 drawing inch equals 96 real inches)
      - 1:100 -> 100.0 (unitless metric scale)
    """
    if not label:
        return {"ratio": None, "label": None}

    lbl = label.strip()

    # Try inch-based like 1/8"=1'-0"
    m = re.search(r'(?i)(\d+)\s*/\s*(\d+)\s*"?\s*=\s*(\d+)\'(?:\s*-\s*(\d+)\")?', lbl)
    if m:
        num = float(m.group(1))
        den = float(m.group(2))
        feet = float(m.group(3))
        inches = float(m.group(4) or 0)
        # inches on paper vs real inches: (1/8)" = 12" -> ratio = (feet*12 + inches) / (num/den)
        try:
            paper_in = num / den
            real_in = feet * 12.0 + inches
            if paper_in > 0:
                ratio = real_in / paper_in  # real inches per drawing inch
                return {"ratio": float(ratio), "label": lbl}
        except Exception:
            pass

    # Try metric 1:100
    m2 = re.search(r'(?i)(\d+)\s*:\s*(\d+)', lbl)
    if m2:
        try:
            a = float(m2.group(1))
            b = float(m2.group(2))
            if a > 0:
                ratio = b / a
                return {"ratio": float(ratio), "label": lbl}
        except Exception:
            pass

    return {"ratio": None, "label": lbl}
