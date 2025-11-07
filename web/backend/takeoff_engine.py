from __future__ import annotations
import base64
import io
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from .blueprint_parsers.pdf_titleblock import find_scale_strings, normalize_scale

# Optional imports guarded for determinism
try:
    import fitz  # PyMuPDF
    _HAVE_FITZ = True
except Exception:
    _HAVE_FITZ = False

# Fallback simple text extractor if fitz is unavailable
try:
    from pdfminer.high_level import extract_text as pdfminer_extract_text
    _HAVE_PDFMINER = True
except Exception:
    _HAVE_PDFMINER = False


LOG_PATH = os.path.join("output", "TAKEOFF_RUN.log")


def _log(msg: str) -> None:
    try:
        os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(msg.rstrip() + "\n")
    except Exception:
        pass


@dataclass
class PdfMeta:
    project_id: str
    source_pdf: str
    pages_scanned: int


class TakeoffEngine:
    def __init__(self, max_pages: int = 3) -> None:
        self.max_pages = max_pages

    # -------------------- LOADING --------------------

    def load_pdf(self, pdf_path: Optional[str] = None, pdf_base64: Optional[str] = None) -> Tuple[PdfMeta, List[Any], List[str]]:
        """
        Returns (pdf_meta, pages, pages_text_list).
        pages: engine-specific page objects if fitz available, else empty list
        pages_text_list: extracted text per page (first N pages)
        """
        _log("[F2] TakeoffEngine.load_pdf: start")
        source_pdf = "<inline-base64>" if pdf_base64 else (pdf_path or "<unknown-path>")

        if _HAVE_FITZ:
            _log("[F2] Using PyMuPDF for parsing")
            if pdf_base64:
                data = base64.b64decode(pdf_base64)
                doc = fitz.open(stream=data, filetype="pdf")
            else:
                if not (pdf_path and os.path.exists(pdf_path)):
                    raise FileNotFoundError(f"PDF not found at path: {pdf_path}")
                doc = fitz.open(pdf_path)

            scan_pages = min(len(doc), self.max_pages)
            pages = [doc.load_page(i) for i in range(scan_pages)]
            pages_text = [pages[i].get_text("text") or "" for i in range(scan_pages)]
            meta = PdfMeta(project_id="", source_pdf=source_pdf, pages_scanned=scan_pages)
            _log(f"[F2] Loaded {scan_pages} pages from {source_pdf}")
            return meta, pages, pages_text

        # Fallback: try pdfminer text only
        _log("[F2] PyMuPDF not available; falling back to text-only extraction with pdfminer (if present)")
        data_bytes: bytes
        if pdf_base64:
            data_bytes = base64.b64decode(pdf_base64)
        else:
            if not (pdf_path and os.path.exists(pdf_path)):
                raise FileNotFoundError(f"PDF not found at path: {pdf_path}")
            with open(pdf_path, "rb") as f:
                data_bytes = f.read()

        pages_text: List[str] = []
        if _HAVE_PDFMINER:
            # pdfminer doesn't easily split per-page with the simple API; for determinism, extract all
            text_all = pdfminer_extract_text(io.BytesIO(data_bytes))
            # Approximate per-page split: just take first N chunks of equal length
            chunks = self._split_text_equal(text_all or "", self.max_pages)
            pages_text = chunks
            scan_pages = len(chunks)
        else:
            pages_text = [""]
            scan_pages = 1

        meta = PdfMeta(project_id="", source_pdf=source_pdf, pages_scanned=scan_pages)
        _log(f"[F2] Fallback extracted text pages={scan_pages} from {source_pdf}")
        return meta, [], pages_text

    @staticmethod
    def _split_text_equal(text: str, parts: int) -> List[str]:
        if parts <= 1 or not text:
            return [text] if text else [""]
        n = max(len(text) // parts, 1)
        chunks = [text[i:i + n] for i in range(0, len(text), n)]
        return chunks[:parts]

    # -------------------- DETECT SCALE --------------------

    def detect_scale(self, pages_text: List[str]) -> Dict[str, Any]:
        combined = "\n".join(pages_text or [])
        labels = find_scale_strings(combined)
        signals: List[str] = []
        ratio: Optional[float] = None
        label: Optional[str] = None

        if labels:
            # Prefer the first one deterministically
            norm = normalize_scale(labels[0])
            ratio = norm.get("ratio")
            label = norm.get("label")
            signals.append("titleblock:scale:found")
            _log(f"[F2] detect_scale: found label={label} ratio={ratio}")
        else:
            # default to 1/8" = 1'-0" => 96.0 inches per drawing inch
            ratio = 96.0
            label = '1/8"=1\'-0" (assumed)'
            signals.append("scale:assumed")
            _log("[F2] detect_scale: no label found, assuming 1/8\"=1'-0\" (96.0)")

        return {"scale_label": label, "ratio": ratio, "signals": signals}

    # -------------------- GEOMETRY --------------------

    def extract_geometry(self, pages: List[Any]) -> Dict[str, Any]:
        """
        Returns wall_lf (linear feet), slab_sf (square feet), and signals (list).
        Deterministic heuristics; clamps to >= 0.
        """
        signals: List[str] = []
        wall_lf: float = 0.0
        slab_sf: float = 0.0

        if _HAVE_FITZ and pages:
            try:
                for p in pages:
                    # Approximate: sum lengths of stroke line segments as "walls"
                    drawings = p.get_drawings()
                    for d in drawings:
                        for item in d["items"]:
                            itype = item[0]
                            if itype == "l":  # line
                                _, p1, p2 = item
                                dx = float(p2.x - p1.x)
                                dy = float(p2.y - p1.y)
                                seg = (dx * dx + dy * dy) ** 0.5
                                wall_lf += seg / 12.0  # convert points->inches->feet approx; heuristic
                            elif itype == "re":  # rectangle path (proxy for slab regions)
                                _, rect = item
                                # approximate area in square feet
                                slab_sf += (float(rect.width) * float(rect.height)) / (12.0 * 12.0)
                signals.append("geometry:fitz:used")
                _log(f"[F2] extract_geometry: wall_lf~{wall_lf:.2f} LF, slab_sf~{slab_sf:.2f} SF")
            except Exception as e:
                _log(f"[F2] extract_geometry: error {e}; using deterministic fallback")
                wall_lf, slab_sf = self._fallback_geom(len(pages))
                signals.append("geometry:fallback")
        else:
            wall_lf, slab_sf = self._fallback_geom(len(pages))
            signals.append("geometry:fallback")
            _log(f"[F2] extract_geometry: fallback wall_lf~{wall_lf:.2f}, slab_sf~{slab_sf:.2f}")

        # clamp non-negatives
        wall_lf = max(0.0, wall_lf)
        slab_sf = max(0.0, slab_sf)
        return {"wall_lf": float(round(wall_lf, 2)), "slab_sf": float(round(slab_sf, 2)), "signals": signals}

    @staticmethod
    def _fallback_geom(page_count: int) -> Tuple[float, float]:
        # Deterministic simple heuristics by page count
        wall_lf = float(page_count) * 300.0
        slab_sf = float(page_count) * 1200.0
        return wall_lf, slab_sf

    # -------------------- FIXTURE KEYWORDS --------------------

    def detect_fixtures(self, pages_text: List[str]) -> Dict[str, Any]:
        text = ("\n".join(pages_text or [])).lower()
        keywords = ["fixtures", "toilet", "sink", "lav", "lavatory", "shower", "bath", "wh", "hose bibb"]
        total = 0
        for kw in keywords:
            total += text.count(kw)
        signals = ["legend:fixtures:found"] if total > 0 else []
        _log(f"[F2] detect_fixtures: count={total}")
        return {"fixtures": int(total), "signals": signals}

    # -------------------- QUANTITIES BUILDER --------------------

    def to_quantities(self,
                      project_id: str,
                      pdf_meta: PdfMeta,
                      geom: Dict[str, Any],
                      fixtures: Dict[str, Any],
                      scale: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build a v0-conformant trade quantities structure.
        Units must be lower-case to satisfy the v0 schema.
        """
        items_concrete = [{
            "code": "slab_area",
            "description": "Slab area (heuristic)",
            "unit": "sf",
            "quantity": float(geom.get("slab_sf", 0.0)),
            "notes": f"Derived via F2 heuristics; scale={scale.get('scale_label')}"
        }]
        items_framing = [{
            "code": "wall_linear",
            "description": "Wall linear (heuristic)",
            "unit": "lf",
            "quantity": float(geom.get("wall_lf", 0.0)),
            "notes": "Derived via F2 heuristics"
        }]
        items_plumbing = [{
            "code": "fixtures",
            "description": "Fixture count (keyword scan)",
            "unit": "ea",
            "quantity": max(0, int(fixtures.get("fixtures", 0))),
            "notes": "Derived via F2 keyword heuristics"
        }]

        meta_notes = ["Derived via F2 heuristics"]
        signals = []
        signals.extend(scale.get("signals", []))
        signals.extend(geom.get("signals", []))
        signals.extend(fixtures.get("signals", []))
        if "scale:assumed" in signals:
            meta_notes.append("scale:assumed")

        quantities_v0 = {
            "version": "v0",
            "meta": {
                "project_id": project_id,
                "source": "ai_takeoff",
                "plan_path": pdf_meta.source_pdf,
                "notes": "; ".join(meta_notes)
            },
            "trades": {
                "concrete": {
                    "scope_notes": "Derived via F2 heuristics",
                    "items": items_concrete
                },
                "framing": {
                    "scope_notes": "Derived via F2 heuristics",
                    "items": items_framing
                },
                "plumbing": {
                    "scope_notes": "Derived via F2 heuristics",
                    "items": items_plumbing
                }
            }
        }
        return quantities_v0
