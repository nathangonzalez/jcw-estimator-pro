# Plan Reader (DEV-FAST) — Local PDF Placement

This repository does not include client plan PDFs. To run the minimal plan reader:

1) Place a local PDF at a path you control, for example:
   C:\Users\natha\OneDrive\...\permit.pdf

2) Start the API on port 8001:
   python -m uvicorn web.backend.app_comprehensive:app --host 127.0.0.1 --port 8001 --reload

3) Run the local plan reader script:
   PowerShell:
     powershell -NoProfile -ExecutionPolicy Bypass -File scripts\run_plan_reader_local.ps1 -PdfPath "C:\path\to\plans.pdf"

4) Outputs:
   - output\plan_features.sample.json  (PlanFeaturesV0 JSON)
   - Server logs (if any errors are raised)

Notes:
- Endpoint: POST /v1/plan/features
- Contract: openapi/contracts/plan.features.v1.contract.json
- Schema: schemas/plan_features.schema.json
