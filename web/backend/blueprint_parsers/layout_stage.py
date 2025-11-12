"""
Layout Stage for Blueprint Analysis (R2.1)
==========================================
Uses layoutparser + OCR to detect title blocks, legends, and notes regions.
Extracts and parses structured metadata for enhanced takeoff.
"""

import os
import re
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path

try:
    import numpy as np
    _HAVE_NUMPY = True
except ImportError:
    _HAVE_NUMPY = False

# Guarded imports for optional dependencies
try:
    import layoutparser as lp
    _HAVE_LAYOUTPARSER = True
except ImportError:
    _HAVE_LAYOUTPARSER = False

try:
    import cv2
    _HAVE_OPENCV = True
except ImportError:
    _HAVE_OPENCV = False

try:
    import pytesseract
    _HAVE_TESSERACT = True
except ImportError:
    _HAVE_TESSERACT = False

try:
    from paddleocr import PaddleOCR
    _HAVE_PADDLEOCR = True
except ImportError:
    _HAVE_PADDLEOCR = False

try:
    import fitz  # PyMuPDF
    _HAVE_FITZ = True
except ImportError:
    _HAVE_FITZ = False

try:
    from pdfminer.high_level import extract_text as pdfminer_extract_text
    from pdfminer.layout import LAParams, LTTextBox, LTTextLine
    from pdfminer.pdfpage import PDFPage
    from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
    from pdfminer.converter import PDFPageAggregator
    _HAVE_PDFMINER = True
except ImportError:
    _HAVE_PDFMINER = False

# Reuse existing scale patterns
from .pdf_titleblock import find_scale_strings, normalize_scale

# LayoutParser model path (will download on first use)
MODEL_PATH = "lp://efficientdet/PubLayNet"

def detect_regions(pdf_path: str) -> Dict[str, Any]:
    """
    Detect layout regions using LayoutParser.
    Returns: {"title_block": (x0,y0,x1,y1), "legend": (x0,y0,x1,y1), "notes": [(x0,y0,x1,y1), ...]}
    """
    if not _HAVE_LAYOUTPARSER or not _HAVE_OPENCV or not _HAVE_FITZ:
        return {"error": "layoutparser dependencies not available", "regions": {}}

    try:
        # Convert first page to image
        doc = fitz.open(pdf_path)
        page = doc.load_page(0)
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2x scaling for better detection
        img_path = pdf_path + ".png"
        pix.save(img_path)

        # Load LayoutParser model
        model = lp.EfficientDetLayoutModel(MODEL_PATH)
        image = cv2.imread(img_path)
        layout = model.detect(image)

        regions = {}
        notes_regions = []

        # Classify detected blocks
        for block in layout:
            x0, y0, x1, y1 = block.block.x_1, block.block.y_1, block.block.x_2, block.block.y_2
            text = block.text if hasattr(block, 'text') else ""

            # Heuristic classification based on position and content
            if y0 < image.shape[0] * 0.2:  # Top 20% likely title block
                if "title_block" not in regions:
                    regions["title_block"] = (x0, y0, x1, y1)
            elif x1 > image.shape[1] * 0.7:  # Right side likely legend
                if "legend" not in regions:
                    regions["legend"] = (x0, y0, x1, y1)
            else:
                # Collect potential notes regions
                notes_regions.append((x0, y0, x1, y1))

        regions["notes"] = notes_regions[:3]  # Limit to 3 notes regions

        # Cleanup
        os.unlink(img_path)
        doc.close()

        return {"regions": regions}

    except Exception as e:
        return {"error": str(e), "regions": {}}

def extract_text(pdf_path: str, bbox: Tuple[float, float, float, float]) -> str:
    """
    Extract text from PDF bbox using pdfminer first, OCR fallback.
    """
    if not bbox or len(bbox) != 4:
        return ""

    x0, y0, x1, y1 = bbox

    # Try pdfminer first
    if _HAVE_PDFMINER and _HAVE_FITZ:
        try:
            # Get page dimensions
            doc = fitz.open(pdf_path)
            page = doc.load_page(0)
            page_width = page.rect.width
            page_height = page.rect.height

            # Convert bbox to pdfminer coordinates (bottom-left origin)
            # fitz uses top-left, pdfminer uses bottom-left
            miner_bbox = (x0, page_height - y1, x1, page_height - y0)

            laparams = LAParams()
            rsrcmgr = PDFResourceManager()
            device = PDFPageAggregator(rsrcmgr, laparams=laparams)
            interpreter = PDFPageInterpreter(rsrcmgr, device)

            with open(pdf_path, 'rb') as fp:
                pages = PDFPage.get_pages(fp)
                for page in pages:
                    interpreter.process_page(page)
                    layout = device.get_result()

                    text_boxes = []
                    for lt_obj in layout:
                        if isinstance(lt_obj, LTTextBox) or isinstance(lt_obj, LTTextLine):
                            if _bbox_overlap(lt_obj.bbox, miner_bbox):
                                text_boxes.append(lt_obj.get_text())

                    if text_boxes:
                        doc.close()
                        return "\n".join(text_boxes)

            doc.close()

        except Exception:
            pass

    # Fallback to OCR
    return _extract_text_ocr(pdf_path, bbox)

def _bbox_overlap(bbox1: Tuple[float, ...], bbox2: Tuple[float, ...]) -> bool:
    """Check if two bboxes overlap."""
    x0_1, y0_1, x1_1, y1_1 = bbox1
    x0_2, y0_2, x1_2, y1_2 = bbox2
    return not (x1_1 < x0_2 or x1_2 < x0_1 or y1_1 < y0_2 or y1_2 < y0_1)

def _extract_text_ocr(pdf_path: str, bbox: Tuple[float, float, float, float]) -> str:
    """Extract text using OCR from bbox."""
    if not _HAVE_FITZ or not _HAVE_OPENCV:
        return ""

    try:
        doc = fitz.open(pdf_path)
        page = doc.load_page(0)
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))

        # Convert to PIL Image
        img_data = pix.tobytes("png")
        nparr = np.frombuffer(img_data, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        # Crop to bbox (scale coordinates)
        scale = 2.0
        x0, y0, x1, y1 = [int(coord * scale) for coord in bbox]
        cropped = img[y0:y1, x0:x1]

        if _HAVE_TESSERACT:
            text = pytesseract.image_to_string(cropped)
            doc.close()
            return text

        elif _HAVE_PADDLEOCR:
            ocr = PaddleOCR(use_angle_cls=True, lang='en')
            result = ocr.ocr(cropped, cls=True)
            text = ""
            if result and result[0]:
                for line in result[0]:
                    if line and len(line) > 1:
                        text += line[1][0] + "\n"
            doc.close()
            return text

        doc.close()

    except Exception:
        pass

    return ""

def parse_titleblock(text: str) -> Dict[str, Any]:
    """
    Parse titleblock text using regex patterns.
    Returns: {"scale": "...", "sheet": "...", "project": "...", ...}
    """
    result = {}

    # Extract scale
    scales = find_scale_strings(text)
    if scales:
        norm = normalize_scale(scales[0])
        result["scale"] = norm.get("label")

    # Extract sheet info
    sheet_match = re.search(r'(?i)\b(sheet|drawing)\s*[:\-]?\s*([^\n\r]+)', text)
    if sheet_match:
        result["sheet"] = sheet_match.group(2).strip()

    # Extract project
    project_match = re.search(r'(?i)\b(project|job)\s*[:\-]?\s*([^\n\r]+)', text)
    if project_match:
        result["project"] = project_match.group(2).strip()

    # Extract date
    date_match = re.search(r'(?i)\b(date|drawn)\s*[:\-]?\s*([^\n\r]+)', text)
    if date_match:
        result["date"] = date_match.group(2).strip()

    return result

def parse_legend(text: str) -> List[Dict[str, str]]:
    """
    Parse legend text into symbol-description pairs.
    Returns: [{"symbol": "...", "desc": "..."}, ...]
    """
    items = []

    # Split into lines
    lines = [line.strip() for line in text.split('\n') if line.strip()]

    for line in lines:
        # Look for patterns like "SYMBOL - description" or "symbol: description"
        match = re.match(r'^([^:\-\n]+)[\s:\-]+\s*(.+)$', line)
        if match:
            symbol = match.group(1).strip()
            desc = match.group(2).strip()
            if len(symbol) < 20 and len(desc) > 2:  # Reasonable length check
                items.append({"symbol": symbol, "desc": desc})

    return items
