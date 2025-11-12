from __future__ import annotations
import base64
import io
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from .blueprint_parsers.pdf_titleblock import find_scale_strings, normalize_scale
from .blueprint_parsers.layout_stage import detect_regions, extract_text, parse_titleblock, parse_legend
from pathlib import Path
import re
try:
    import yaml
    _HAVE_YAML = True
except Exception:
    _HAVE_YAML = False

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
        self.rules_path = Path("data/fixtures.rules.yaml")

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

# -------------------- FIXTURE DETECTION (rules + keywords) --------------------

    def _load_rules(self) -> List[Dict[str, Any]]:
        if _HAVE_YAML and self.rules_path.exists():
            try:
                with open(self.rules_path, "r", encoding="utf-8") as f:
                    doc = yaml.safe_load(f) or {}
                    rules = doc.get("rules", [])
                    if isinstance(rules, list):
                        return rules
            except Exception:
                pass
        return []

    def detect_fixture_rules(self, text_blob: str) -> List[Dict[str, Any]]:
        """
        Very simple regex-driven detection → list of {trade,item,unit,qty}.
        First-match-wins per rule; multiple rules may match.
        """
        results: List[Dict[str, Any]] = []
        rules = self._load_rules()
        src = text_blob or ""
        for rule in rules:
            pat = rule.get("pattern")
            if not pat:
                continue
            try:
                if re.search(pat, src, flags=re.IGNORECASE):
                    results.append({
                        "trade": rule.get("trade", "misc"),
                        "item": rule.get("item", "unknown"),
                        "unit": str(rule.get("unit", "ea")).lower(),
                        "qty": float(rule.get("qty", 1) or 0)
                    })
            except Exception:
                # ignore bad patterns
                continue
        return results

# -------------------- FIXTURE KEYWORDS --------------------

    def detect_fixtures(self, pages_text: List[str]) -> Dict[str, Any]:
        blob = "\n".join(pages_text or [])
        text = blob.lower()
        keywords = ["fixtures", "toilet", "sink", "lav", "lavatory", "shower", "bath", "wh", "hose bibb"]
        total = 0
        for kw in keywords:
            total += text.count(kw)
        rule_hits = self.detect_fixture_rules(blob)
        signals = []
        if total > 0:
            signals.append("legend:fixtures:found")
        if rule_hits:
            signals.append("fixtures:rules:matched")
        _log(f"[F2] detect_fixtures: count={total}; rules={len(rule_hits)}")
        return {"fixtures": int(total), "signals": signals, "rule_hits": rule_hits}

    # -------------------- LAYOUT STAGE (R2.1) --------------------

    def detect_layout(self, pdf_path: str) -> Dict[str, Any]:
        """
        Run layout analysis to detect title block, legend, and notes regions.
        Returns enriched metadata dict.
        """
        result = {
            "layout_detected": False,
            "scale": None,
            "sheet": None,
            "project": None,
            "legend_terms": [],
            "signals": []
        }

        try:
            # Detect regions
            regions_result = detect_regions(pdf_path)
            regions = regions_result.get("regions", {})

            if regions_result.get("error"):
                _log(f"[R2.1] detect_layout: error {regions_result['error']}")
                result["signals"].append("layout:error")
                return result

            # Extract and parse title block
            if "title_block" in regions:
                bbox = regions["title_block"]
                text = extract_text(pdf_path, bbox)
                if text.strip():
                    parsed = parse_titleblock(text)
                    result.update({
                        "scale": parsed.get("scale"),
                        "sheet": parsed.get("sheet"),
                        "project": parsed.get("project"),
                    })
                    result["signals"].append("layout:titleblock:parsed")

            # Extract and parse legend
            if "legend" in regions:
                bbox = regions["legend"]
                text = extract_text(pdf_path, bbox)
                if text.strip():
                    legend_items = parse_legend(text)
                    result["legend_terms"] = [item["desc"] for item in legend_items if item.get("desc")]
                    result["signals"].append("layout:legend:parsed")

                    # Add provisional quantity items from legend
                    for item in legend_items:
                        desc = item.get("desc", "").lower()
                        if "hose bibb" in desc:
                            # Add to fixtures rule_hits style
                            result.setdefault("legend_rule_hits", []).append({
                                "trade": "plumbing",
                                "item": "hose_bibb",
                                "unit": "ea",
                                "qty": 1,  # unknown quantity
                                "source": "legend"
                            })

            if regions:
                result["layout_detected"] = True
                _log(f"[R2.1] detect_layout: found regions {list(regions.keys())}")

        except Exception as e:
            _log(f"[R2.1] detect_layout: exception {e}")
            result["signals"].append("layout:exception")

        return result

    # -------------------- QUANTITIES BUILDER --------------------

    def to_quantities(self,
                      project_id: str,
                      pdf_meta: PdfMeta,
                      geom: Dict[str, Any],
                      fixtures: Dict[str, Any],
                      scale: Dict[str, Any],
                      layout: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
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
        # Add rule-driven fixture items (if any)
        for hit in (fixtures.get("rule_hits") or []):
            try:
                items_plumbing.append({
                    "code": str(hit.get("item", "fixture")),
                    "description": "Fixture (rule match)",
                    "unit": str(hit.get("unit", "ea")).lower(),
                    "quantity": float(hit.get("qty", 1) or 0),
                    "notes": f"Detected by fixtures.rules: {hit.get('trade','plumbing')}/{hit.get('item','')}"
                })
            except Exception:
                continue

        # Add legend-driven items (if any)
        if layout and layout.get("legend_rule_hits"):
            for hit in layout["legend_rule_hits"]:
                try:
                    items_plumbing.append({
                        "code": str(hit.get("item", "fixture")),
                        "description": "Fixture (legend)",
                        "unit": str(hit.get("unit", "ea")).lower(),
                        "quantity": float(hit.get("qty", 1) or 0),
                        "notes": f"Detected by layout.legend: {hit.get('trade','plumbing')}/{hit.get('item','')}"
                    })
                except Exception:
                    continue

        meta_notes = ["Derived via F2 heuristics"]
        signals = []
        signals.extend(scale.get("signals", []))
        signals.extend(geom.get("signals", []))
        signals.extend(fixtures.get("signals", []))
        if layout:
            signals.extend(layout.get("signals", []))
        if "scale:assumed" in signals:
            meta_notes.append("scale:assumed")

        # Enrich meta with layout data
        meta_dict = {
            "project_id": project_id,
            "source": "ai_takeoff",
            "plan_path": pdf_meta.source_pdf,
            "notes": "; ".join(meta_notes)
        }
        if layout:
            if layout.get("layout_detected"):
                meta_dict["layout_detected"] = True
            if layout.get("scale"):
                meta_dict["scale"] = layout["scale"]
            if layout.get("sheet"):
                meta_dict["sheet"] = layout["sheet"]
            if layout.get("project"):
                meta_dict["project"] = layout["project"]
            if layout.get("legend_terms"):
                meta_dict["legend_terms"] = layout["legend_terms"]

        quantities_v0 = {
            "version": "v0",
            "meta": meta_dict,
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
