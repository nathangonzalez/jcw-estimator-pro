#!/usr/bin/env python3
"""
AI-Assisted PDF Takeoff (Starter Pipeline) — Auto Scale
-------------------------------------------------------
Dependencies:
  pip install pymupdf numpy pandas

What this adds (vs the base version):
- Attempts to READ the scale from the title block / page text:
    * Imperial architectural: e.g., 1/8" = 1'-0", 3/32"=1'-0"
    * Ratio scales: e.g., 1:100, 1:50 (metric)
- If no explicit scale text is found, it ESTIMATES an imperial scale by analyzing
  the gap between parallel line pairs (wall thickness heuristic) and matching to
  common architectural scales.

Notes:
- PDF units are points (1 pt = 1/72 inch).
- Imperial scales convert inches-on-paper to feet-in-reality.
- Ratio scales (metric) convert millimeters-on-paper to millimeters-in-reality,
  but since PDF units are points, we use: 1 pt = 25.4/72 mm.

Usage:
  1) Set PDF_PATH below.
  2) Optionally set PREFERRED_UNITS ("ft" or "m"). If omitted, inferred.
  3) Run: python ai_takeoff_pipeline.py
  4) Outputs CSVs and logs which scale was used (read vs estimated).
"""
import math
import re
import fitz  # PyMuPDF
import numpy as np
import pandas as pd
import logging
from dataclasses import dataclass
from typing import List, Tuple, Dict, Optional

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# -------------------------------
# Data models
# -------------------------------

@dataclass
class LineSeg:
    page_num: int
    p0: Tuple[float, float]
    p1: Tuple[float, float]
    length_pdf_units: float
    stroke: Optional[Tuple[int, int, int]]  # RGB
    width: Optional[float]  # stroke width in PDF units

@dataclass
class PolyPath:
    page_num: int
    points: List[Tuple[float, float]]
    closed: bool
    stroke: Optional[Tuple[int, int, int]]
    width: Optional[float]

# -------------------------------
# Geometry helpers
# -------------------------------

def dist(a: Tuple[float, float], b: Tuple[float, float]) -> float:
    return math.hypot(a[0]-b[0], a[1]-b[1])

def polygon_area(points: List[Tuple[float, float]]) -> float:
    """Shoelace formula. Expects closed ring (first!=last ok)."""
    if len(points) < 3:
        return 0.0
    x = [p[0] for p in points]
    y = [p[1] for p in points]
    s1 = sum(x[i]*y[(i+1) % len(points)] for i in range(len(points)))
    s2 = sum(y[i]*x[(i+1) % len(points)] for i in range(len(points)))
    return abs(s1 - s2) / 2.0

# -------------------------------
# PDF extraction
# -------------------------------

def extract_drawings(pdf_path: str) -> Tuple[List[LineSeg], List[PolyPath]]:
    """
    Uses PyMuPDF page.get_drawings() to retrieve vector graphics.
    Returns line segments and poly paths with styling.
    """
    doc = fitz.open(pdf_path)
    all_lines: List[LineSeg] = []
    all_polys: List[PolyPath] = []

    for page_index in range(len(doc)):
        page = doc[page_index]
        drawings = page.get_drawings()
        for d in drawings:
            stroke_rgb = None
            if d.get('stroke'):
                # PyMuPDF draws colors as floats 0..1
                try:
                    stroke_rgb = tuple(int(255*c) for c in d['stroke'])
                except Exception:
                    stroke_rgb = tuple(d['stroke']) if isinstance(d['stroke'], (list, tuple)) else None

            width = d.get('width')

            for p in d['items']:
                if p[0] == 'l':  # line
                    _, x1, y1, x2, y2 = p
                    length = dist((x1, y1), (x2, y2))
                    all_lines.append(LineSeg(
                        page_num=page_index+1,
                        p0=(x1, y1),
                        p1=(x2, y2),
                        length_pdf_units=length,
                        stroke=stroke_rgb,
                        width=width
                    ))
                elif p[0] == 're':  # rectangle
                    _, x, y, w, h = p
                    pts = [(x, y), (x+w, y), (x+w, y+h), (x, y+h)]
                    all_polys.append(PolyPath(
                        page_num=page_index+1,
                        points=pts,
                        closed=True,
                        stroke=stroke_rgb,
                        width=width
                    ))
                # Other path commands omitted in this starter.

    doc.close()
    return all_lines, all_polys

def extract_page_text(pdf_path: str) -> str:
    """Concatenate text from all pages (blocks) for scale parsing."""
    doc = fitz.open(pdf_path)
    texts = []
    for i in range(len(doc)):
        page = doc[i]
        texts.append(page.get_text("text"))
    doc.close()
    return "\n".join(texts)

# -------------------------------
# Scaling
# -------------------------------

@dataclass
class Scale:
    real_per_pdf: float  # real-world units per 1 PDF point
    real_units_name: str # 'ft' or 'm' (or 'in' as internal helper)

PT_PER_IN = 72.0
MM_PER_IN = 25.4
MM_PER_PT = MM_PER_IN / PT_PER_IN  # ≈ 0.352777...

def parse_fraction(s: str) -> float:
    """Parse '3/32' or decimal '0.125' to float inches."""
    s = s.strip()
    if '/' in s:
        a,b = s.split('/', 1)
        return float(a) / float(b)
    return float(s)

def try_parse_scale_from_text(text: str) -> Optional[Scale]:
    """
    Look for common scale strings inside the PDF text.
    Returns a Scale in feet per point (imperial) or meters per point (metric).
    """
    # Normalize
    t = text.lower().replace("–", "-").replace("—", "-")

    # 1) Imperial patterns like: 1/8" = 1'-0"   or   3/32"=1'-0"
    imp = re.search(r'(\d+\s*/\s*\d+|\d*\.?\d+)\s*["in]?\s*=\s*1\s*[-\s]?\'\s*0*"?', t)
    if imp:
        x_in = parse_fraction(imp.group(1))  # inches on paper
        # 1 pt = 1/72 inch on paper.
        # Real inches per paper inch = 12/x_in feet? (No: inches)
        # For imperial,  x_in" on paper = 1'-0" (12 inches real).
        # So: real inches per paper inch = 12 / x_in inches.
        real_inches_per_paper_in = 12.0 / x_in
        real_inches_per_pt = real_inches_per_paper_in / PT_PER_IN  # inches real per pt
        real_feet_per_pt = real_inches_per_pt / 12.0
        return Scale(real_per_pdf=real_feet_per_pt, real_units_name='ft')

    # 2) Metric ratio patterns like: 1:100 or Scale 1:50
    ratio = re.search(r'(\bscale\b[:\s]*)?1\s*[:]\s*(\d{1,4})', t)
    if ratio:
        denom = float(ratio.group(2))  # e.g., 100
        # 1 unit on paper (mm) = denom units real (mm). Paper to real multiplier = denom.
        # Convert 1 pt to mm: MM_PER_PT.
        real_mm_per_pt = denom * MM_PER_PT
        real_m_per_pt = real_mm_per_pt / 1000.0
        return Scale(real_per_pdf=real_m_per_pt, real_units_name='m')

    return None

# --- Heuristic estimation by wall thickness (imperial only) ---

COMMON_IMPERIAL_SCALES_IN = [  # inches on paper that equal 1 foot real
    1/16, 3/32, 1/8, 3/16, 1/4, 3/8, 1/2, 3/4, 1.0
]

def line_direction(v: Tuple[float,float]) -> float:
    """Return angle in radians (0..pi) ignoring orientation."""
    ang = math.atan2(v[1], v[0])
    if ang < 0:
        ang += math.pi
    return ang

def estimate_scale_from_walls(lines: List[LineSeg]) -> Optional[Scale]:
    """
    Try to guess the scale by finding pairs of parallel line segments that are close together
    (possible wall faces), collect gap distances, and see which common scale makes those gaps
    cluster around typical wall thickness (4-8 inches).
    """
    if len(lines) < 100:
        return None  # not enough signal

    # Preselect reasonably long segments to avoid noise
    min_len = 10.0  # pts
    segs = [ln for ln in lines if ln.length_pdf_units >= min_len]

    # Compute parallel pairs and perpendicular distances
    gaps = []
    for i in range(0, min(len(segs), 2000)):  # cap for speed
        a = segs[i]
        va = (a.p1[0]-a.p0[0], a.p1[1]-a.p0[1])
        ang_a = line_direction(va)

        # Find neighbors in a small window to reduce O(N^2)
        for j in range(i+1, min(i+80, len(segs))):
            b = segs[j]
            vb = (b.p1[0]-b.p0[0], b.p1[1]-b.p0[1])
            ang_b = line_direction(vb)

            # Parallel if angle difference small
            if abs(ang_a - ang_b) > (math.pi/180.0)*5.0:  # >5 degrees -> not parallel
                continue

            # Distance between lines: project vector from a.p0 to b.p0 onto normal of a
            ax, ay = va
            la = math.hypot(ax, ay)
            if la == 0:
                continue
            nx, ny = -ay/la, ax/la  # unit normal
            d = abs((b.p0[0]-a.p0[0])*nx + (b.p0[1]-a.p0[1])*ny)
            if 1.0 <= d <= 30.0:  # plausible wall face gap in points
                gaps.append(d)

    if not gaps:
        return None

    # For each candidate scale x_in (inches on paper = 1 ft real), compute how the point gap
    # converts to real inches: real_in_per_pt = (12/x_in)/72 = (1/6)/x_in inches per pt
    # We expect typical wall thickness 4-8 inches -> look for a mode near that.
    target_in = 6.0  # aim around 6" as a robust default
    best = None
    for x_in in COMMON_IMPERIAL_SCALES_IN:
        real_in_per_pt = (1.0/6.0) / x_in
        converted = [g * real_in_per_pt for g in gaps if g <= 30.0]
        if not converted:
            continue
        median_gap = float(np.median(converted))
        # score: closeness to 6", and ensure spread isn't insane
        mad = float(np.median([abs(v - median_gap) for v in converted]))
        score = abs(median_gap - target_in) + 0.25*mad
        if (best is None) or (score < best[0]):
            best = (score, x_in, median_gap, mad)

    if best is None:
        return None

    _, x_in, median_gap, mad = best
    # Build scale in ft/pt
    real_inches_per_paper_in = 12.0 / x_in
    real_inches_per_pt = real_inches_per_paper_in / 72.0
    real_feet_per_pt = real_inches_per_pt / 12.0
    return Scale(real_per_pdf=real_feet_per_pt, real_units_name='ft')

# -------------------------------
# Summaries
# -------------------------------

def summarize_lines(lines: List[LineSeg], scale: Scale) -> pd.DataFrame:
    """
    Summarize total lengths by page, stroke color, and width.
    """
    records = []
    for ln in lines:
        real_len = ln.length_pdf_units * scale.real_per_pdf
        color = ln.stroke if ln.stroke else (0,0,0)
        records.append({
            "page": ln.page_num,
            "stroke_rgb": str(color),
            "stroke_width_pdf": ln.width,
            f"length_{scale.real_units_name}": real_len
        })
    df = pd.DataFrame(records)
    if df.empty:
        return df
    grp = df.groupby(["page", "stroke_rgb", "stroke_width_pdf"], as_index=False)[f"length_{scale.real_units_name}"].sum()
    return grp.sort_values(["page", f"length_{scale.real_units_name}"], ascending=[True, False])

def summarize_polygons(polys: List[PolyPath], scale: Scale) -> pd.DataFrame:
    """
    Best-effort area estimation for rectangles (and simple closed paths, if added).
    """
    records = []
    for poly in polys:
        if not poly.closed:
            continue
        area_pdf = polygon_area(poly.points)
        area_real = area_pdf * (scale.real_per_pdf ** 2)
        color = poly.stroke if poly.stroke else (0,0,0)
        records.append({
            "page": poly.page_num,
            "stroke_rgb": str(color),
            f"area_{scale.real_units_name}^2": area_real
        })
    df = pd.DataFrame(records)
    if df.empty:
        return df
    grp = df.groupby(["page", "stroke_rgb"], as_index=False)[f"area_{scale.real_units_name}^2"].sum()
    return grp.sort_values(["page", f"area_{scale.real_units_name}^2"], ascending=[True, False])

# -------------------------------
# Optional: render preview images (PNG) per page for manual QA
# -------------------------------

def render_pages(pdf_path: str, dpi: int = 200, max_pages: Optional[int] = None) -> List[str]:
    """
    Render each page to a PNG for visual QA. Returns list of file paths.
    """
    doc = fitz.open(pdf_path)
    out_paths = []
    for page_index in range(len(doc)):
        if max_pages is not None and page_index >= max_pages:
            break
        page = doc[page_index]
        mat = fitz.Matrix(dpi/72, dpi/72)
        pix = page.get_pixmap(matrix=mat, alpha=False)
        out_path = f"page_{page_index+1:03d}.png"
        pix.save(out_path)
        out_paths.append(out_path)
    doc.close()
    return out_paths

# -------------------------------
# Main
# -------------------------------

def run_pipeline(pdf_path: str, preferred_units: Optional[str] = None):
    """
    Main pipeline function to be called by the web backend.
    Returns a tuple: (df_lines, df_polys, scale_info, logs, error_message)
    """
    logs = []
    try:
        logging.info(f"[*] Starting AI takeoff for: {pdf_path}")
        logs.append(f"[*] Starting AI takeoff for: {pdf_path}")

        logging.info("[*] Extracting vector linework...")
        lines, polys = extract_drawings(pdf_path)
        logging.info(f"    Found {len(lines)} line segments and {len(polys)} polygonal paths.")
        logs.append(f"    Found {len(lines)} line segments and {len(polys)} polygonal paths.")

        logging.info("[*] Reading page text to detect scale...")
        text = extract_page_text(pdf_path)
        scale = try_parse_scale_from_text(text)

        scale_info = {}

        if scale:
            logging.info(f"    Parsed scale from text: units={scale.real_units_name}, real_per_pt={scale.real_per_pdf:.6f} {scale.real_units_name}/pt")
            logs.append(f"    Parsed scale from text: units={scale.real_units_name}, real_per_pt={scale.real_per_pdf:.6f} {scale.real_units_name}/pt")
        else:
            logging.info("    No explicit scale string found. Estimating from wall thickness...")
            logs.append("    No explicit scale string found. Estimating from wall thickness...")
            scale = estimate_scale_from_walls(lines)
            if scale:
                logging.info(f"    Estimated imperial scale by wall-gap heuristic: real_per_pt={scale.real_per_pdf:.6f} {scale.real_units_name}/pt")
                logs.append(f"    Estimated imperial scale by wall-gap heuristic: real_per_pt={scale.real_per_pdf:.6f} {scale.real_units_name}/pt")
            else:
                err_msg = "Could not determine scale automatically. Please check if the blueprint includes a scale notation (e.g., 1/8\" = 1'-0\") or has clear wall structures."
                logging.error(err_msg)
                logs.append(err_msg)
                return None, None, None, logs, err_msg

        # Respect preferred units if provided and convertible
        if preferred_units and preferred_units != scale.real_units_name:
            if scale.real_units_name == 'ft' and preferred_units == 'm':
                scale = Scale(real_per_pdf=scale.real_per_pdf * 0.3048, real_units_name='m')
            elif scale.real_units_name == 'm' and preferred_units == 'ft':
                scale = Scale(real_per_pdf=scale.real_per_pdf / 0.3048, real_units_name='ft')
        
        scale_info = {
            'units': scale.real_units_name,
            'real_per_pdf_point': scale.real_per_pdf
        }
        logging.info(f"[*] Using scale: 1 PDF pt = {scale.real_per_pdf:.6f} {scale.real_units_name}")
        logs.append(f"[*] Using scale: 1 PDF pt = {scale.real_per_pdf:.6f} {scale.real_units_name}")

        df_lines = summarize_lines(lines, scale)
        df_polys = summarize_polygons(polys, scale)

        if df_lines.empty:
            logs.append("    Warning: No linework was extracted. The PDF might be a scanned image.")
        if df_polys.empty:
            logs.append("    Info: No polygonal paths were found (this version only handles rectangles).")

        return df_lines, df_polys, scale_info, logs, None

    except Exception as e:
        logging.exception("An error occurred during the AI takeoff pipeline.")
        error_message = f"An unexpected error occurred: {str(e)}"
        logs.append(error_message)
        return None, None, None, logs, error_message


if __name__ == "__main__":
    # Example usage when running script directly
    PDF_PATH = "YOUR_BLUEPRINT.pdf"  # <-- put your file path here
    PREFERRED_UNITS = None  # 'ft' or 'm'

    df_lines, df_polys, scale_info, logs, error = run_pipeline(PDF_PATH, PREFERRED_UNITS)

    print("\n--- LOGS ---")
    for log_entry in logs:
        print(log_entry)

    if error:
        print(f"\n--- PIPELINE FAILED ---")
        print(error)
    else:
        print("\n--- RESULTS ---")
        print("Scale Info:", scale_info)
        if df_lines is not None and not df_lines.empty:
            print("\nLines Summary:")
            print(df_lines.head())
            df_lines.to_csv("lines_summary.csv", index=False)
            print("\n    Wrote lines_summary.csv")
        else:
            print("\nNo linework summary generated.")

        if df_polys is not None and not df_polys.empty:
            print("\nPolygons Summary:")
            print(df_polys.head())
            df_polys.to_csv("polygons_summary.csv", index=False)
            print("    Wrote polygons_summary.csv")
        else:
            print("No polygon summary generated.")
