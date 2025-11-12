# Estimating Pipeline: Plan → Quantities → Pricing (M01/F2)

This living document summarizes the minimal, deterministic flow for generating estimates from construction plans.

## Overview

- Plan (PDF) → Takeoff (Quantities v0) → Estimate (Pricing/Policy) → Totals
- Endpoints:
  - POST /v1/takeoff → returns Trade Quantities v0 (schemas/trade_quantities.schema.json)
  - POST /v1/estimate → accepts either:
    - M01 quantities (v0 object or flattened line items)
    - Legacy body (backward compatible; deprecated)

## F2: Minimal Plan Reader (Takeoff)

Goal: robust, small, deterministic takeoff with clear logging and runtime validation.

- Input (A/B shapes):
  - A: {"project_id":"LYNN-001","pdf_path":"data/blueprints/LYNN-001.sample.pdf"}
  - B: {"project_id":"LYNN-001","pdf_base64":"<base64-encoded-pdf>"}
- Output: v0-conformant quantities (concrete / framing / plumbing) with notes and signals.

### Extraction Strategy

- Text scan (first N=3 pages):
  - Detect common scale labels (e.g., 1/8"=1'-0", 1:100).
  - Fixture keywords: fixtures, toilet, sink, lav, shower, bath, WH, hose bibb.
- Geometry (heuristics):
  - If PyMuPDF available: sum drawing lines for wall_lf; rect path areas for slab_sf.
  - Fallback: deterministic estimates by page count.
- Scale:
  - Normalize architectural/metric patterns into a ratio.
  - If missing, assume 1/8"=1'-0" (ratio 96.0) and add signal "scale:assumed".

### Layout Stage (R2.1)

Optional layout analysis using LayoutParser + OCR for enhanced blueprint understanding.

- **Knobs**: Enabled via `TAKEOFF_ENABLE_LAYOUT=true` environment variable.
- **Detection**: Uses LayoutParser to identify title block, legend, and notes regions.
- **Extraction**:
  - Title block: scale, sheet, project, date via regex patterns.
  - Legend: symbol-description pairs (e.g., "WC - Water Closet").
  - Fallback: pdfminer text extraction first, OCR (Tesseract/PaddleOCR) if needed.
- **Enrichment**: Adds `metadata.layout_detected=true/false`, `meta.scale`, `meta.sheet`, `meta.project`, `meta.legend_terms[]`.
- **Quantities**: Provisional legend items (e.g., "hose bibb" → plumbing fixture) marked as `source:"legend"`.
- **Fallbacks**:
  - If LayoutParser unavailable: skip with signal "layout:error".
  - If OCR fails: use text-only extraction.
  - Dependencies guarded: layoutparser, opencv-python-headless, pytesseract/paddleocr (optional).

### Files

- web/backend/blueprint_parsers/pdf_titleblock.py
  - find_scale_strings(text) → [labels]
  - normalize_scale(label) → { ratio, label }
- web/backend/takeoff_engine.py
  - load_pdf(pdf_path|base64), detect_scale, extract_geometry, detect_fixtures
  - to_quantities(project_id, pdf_meta, geom, fixtures, scale) → v0 dict
- web/backend/app_comprehensive.py
  - POST /v1/takeoff runtime-validates response against schemas/trade_quantities.schema.json
  - Logs extraction to output/TAKEOFF_RUN.log

### Schemas & Contracts

- schemas/takeoff_request.schema.json
- schemas/takeoff_response.schema.json (allOf trade_quantities.schema.json)
- openapi/contracts/takeoff.v1.contract.json

### Smoke

- scripts/smoke_takeoff_v1.ps1
  - POSTs path variant
  - Writes output/TAKEOFF_RESPONSE.json
  - API appends extraction log to output/TAKEOFF_RUN.log
  - If server is down, prints a friendly hint:
    - uvicorn web.backend.app_comprehensive:app --reload

## Estimating (Pricing)

- /v1/estimate
  - Prefers M01 quantities (v0 object or flattened)
  - Accepts policy, unit_costs_csv, vendor_quotes_csv as file paths (server reads)
  - Legacy request shape remains supported with deprecation warning
- Pricing Engine (web/backend/pricing_engine.py)
  - Vendor quotes > unit costs > policy defaults
  - Waste, markups, tax, escalation
  - Input digests for traceability

## Security & Determinism

- No randomness in takeoff heuristics; guard divisions; clamp negatives to zero.
- Avoid committing real client PDFs. Use a local placeholder path:
  - data/blueprints/LYNN-001.sample.pdf (not committed)
  - data/blueprints/LYNN-001.sample.placeholder.txt (instructions)

## Roadmap

- F2+: Improve geometry classification/filters
- F3: Enrich trades and mapping to pricing codes
- F4: Interactive plan viewer integrations (optional)

## Vendor Quote Comparison (LYNN pilot)
1) Run pipeline smoke to produce `output/PIPELINE_ESTIMATE_RESPONSE.json`.
2) Place vendor PDFs under `data/vendor_quotes/LYNN-001/*/raw/`, run the parser to produce `parsed/` JSON, then `normalized/` CSV.
3) Aggregate all normalized CSVs → `data/vendor_quotes/LYNN-001/quotes.canonical.csv`.
4) Run `pwsh -File scripts/compare_lynn_quotes.ps1`.
5) Review `output/LYNN-001/compare/report.csv` and update policy/unit_costs as needed.
