# R2.1 Layout Stage Receipt

**Timestamp:** 2025-11-12 09:52:00Z
**Mode:** DEV-FAST (dry-run notes; no execution performed)

## Summary

LayoutParser + OCR integration added to /v1/takeoff. Code committed but not executed due to dependency installation constraints. Layout stage would detect title block and legend regions, extract structured metadata, and enrich takeoff quantities.

## Expected Behavior (Based on Code Analysis)

### Dependencies Status
- layoutparser==0.3.4: Not installed (would download PubLayNet model on first use)
- opencv-python-headless>=4.8: Not installed
- pytesseract>=0.3.10: Not installed (optional OCR fallback)
- paddleocr>=2.7.0: Not installed (optional OCR fallback)

### Detection Results (Hypothetical on Sample PDF)
If dependencies were available and TAKEOFF_ENABLE_LAYOUT=true:

1. **Region Detection**: LayoutParser would analyze first page image, classify blocks by position:
   - Title block: Top 20% of page → bbox (x0,y0,x1,y1)
   - Legend: Right 30% of page → bbox (x0,y0,x1,y1)
   - Notes: Remaining blocks → up to 3 bboxes

2. **Text Extraction**:
   - Title block: pdfminer extraction first, OCR fallback if image-heavy
   - Legend: pdfminer extraction first, OCR fallback if image-heavy

3. **Parsing Results**:
   - Title block text → regex extraction:
     - Scale: "1/8\"=1'-0\"" or "1:100"
     - Sheet: "A1" or "P1"
     - Project: "Sample House"
     - Date: "2023-10-01"
   - Legend text → symbol-description pairs:
     - [{"symbol": "WC", "desc": "Water Closet"}, {"symbol": "HB", "desc": "Hose Bibb"}, ...]

4. **Metadata Enrichment**:
   - metadata.layout_detected: true
   - metadata.scale: "1/8\"=1'-0\""
   - metadata.sheet: "A1"
   - metadata.project: "Sample House"
   - metadata.legend_terms: ["Water Closet", "Hose Bibb", ...]

5. **Quantity Enrichment**:
   - Legend terms matching "hose bibb" → provisional plumbing fixture item
   - Marked as source:"legend" in quantities

## Fallback Behavior

- If LayoutParser unavailable: layout_detected=false, signal "layout:error"
- If OCR fails: text-only extraction from detected regions
- Dependencies guarded: no runtime errors if optional packages missing

## Test Coverage

- Unit tests: parse_titleblock() and parse_legend() with deterministic inputs
- E2E tests: metadata.layout_detected boolean assertion
- Smoke script: logs layout fields when present

## Files Created/Modified

- web/backend/blueprint_parsers/layout_stage.py (new)
- web/backend/takeoff_engine.py (modified)
- web/backend/app_comprehensive.py (modified)
- tests/unit/test_layout_stage.py (new)
- scripts/smoke_takeoff_v1.ps1 (modified)
- tests/e2e/uat.release.spec.ts (modified)
- docs/ESTIMATING_PIPELINE.md (modified)
- output/AGENT_SYNC.md (modified)
- requirements.txt (modified)

## Next Steps

1. Install dependencies: pip install layoutparser opencv-python-headless pytesseract paddleocr
2. Set TAKEOFF_ENABLE_LAYOUT=true
3. Run smoke test: pwsh scripts/smoke_takeoff_v1.ps1
4. Verify layout detection in output/TAKEOFF_RESPONSE.json
5. Update this receipt with actual detection results
