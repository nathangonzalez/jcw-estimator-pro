# Estimating Data Flow (DEV-FAST)

Plans (PDF) → Plan Features (F2) → Quantities (M01/M02) → Pricing (F1) → Totals

## Overview

- Inputs:
  - PDF plan set on disk (no upload pipeline yet).
  - Optional: M01 quantities (v0 object) or flattened items.
  - Policy YAML, unit_costs CSV, vendor_quotes CSV as file paths.
- Outputs:
  - PlanFeaturesV0 JSON (doc meta, sheets, scales).
  - Trade Quantities v0 (concrete/framing/plumbing) via /v1/takeoff (heuristic).
  - EstimateResponse v0 via /v1/estimate.

## Flow

1) Plan Reader (F2)
   - Endpoint: POST /v1/plan/features { pdf_path }
   - Returns PlanFeaturesV0:
     - doc: { file_name, page_count, page_sizes[] }
     - sheets: [{ page_no, sheet_id?, sheet_name? }]
     - scales: [{ page_no, raw, normalized? }]
   - Contract: openapi/contracts/plan.features.v1.contract.json
   - Schema: schemas/plan_features.schema.json
   - Local smoke: scripts/run_plan_reader_local.ps1

2) Quantities (M01/M02)
   - Current heuristic (M01/M02 in progress):
     - /v1/takeoff builds minimal v0 quantities from PDF heuristics.
     - M01 quantities can also be provided manually as v0 object.
   - Schema: schemas/trade_quantities.schema.json

3) Pricing (F1)
   - Endpoint: POST /v1/estimate
   - Prefers M01 quantities (v0 object or flattened line items).
   - Reads policy/unit_costs/vendor_quotes from file paths.
   - Engine: web/backend/pricing_engine.py (vendor quotes > unit costs > policy defaults; waste/markups/tax/escalation).

## Contracts & Schemas

- Plan Features:
  - Schema: schemas/plan_features.schema.json
  - OpenAPI: openapi/contracts/plan.features.v1.contract.json

- Quantities:
  - Schema: schemas/trade_quantities.schema.json
  - OpenAPI (related): openapi/contracts/takeoff.v1.contract.json (for /v1/takeoff)

- Estimate:
  - Schema: schemas/estimate_response.schema.json
  - OpenAPI: openapi/contracts/estimate.v1.contract.json

## Local Commands

- Start API (port 8001):
  python -m uvicorn web.backend.app_comprehensive:app --host 127.0.0.1 --port 8001 --reload

- Plan features smoke:
  powershell -NoProfile -ExecutionPolicy Bypass -File scripts\run_plan_reader_local.ps1 -PdfPath "C:\path\to\plans.pdf"
  - Writes: output\plan_features.sample.json

- Takeoff smoke (optional, heuristic v0 quantities):
  powershell -NoProfile -ExecutionPolicy Bypass -File scripts\smoke_takeoff_v1.ps1
  - Writes: output\TAKEOFF_RESPONSE.json

## Notes

- Keep extraction deterministic and small; log errors clearly.
- Do not commit real client PDFs. Use local paths and placeholders in data/plan and data/blueprints.
