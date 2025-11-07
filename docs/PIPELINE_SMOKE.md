# Pipeline Smoke (Plan → Quantities → Estimate)

Run locally to verify the end-to-end flow without external services.

## Start API

Terminal 1:
```
python -m uvicorn web.backend.app_comprehensive:app --host 127.0.0.1 --port 8001 --reload
```

## Execute pipeline

Terminal 2:
```
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\pipeline_smoke.ps1 -PdfPath "data\blueprints\LYNN-001.sample.pdf"
```

Outputs (created in output/):
- output/TAKEOFF_RESPONSE.json
- output/PIPELINE_ESTIMATE_RESPONSE.json
- output/PIPELINE_JUNIT.xml
- output/PIPELINE_SUMMARY.html

Place a sample PDF at data/blueprints/LYNN-001.sample.pdf (local only; do not commit PDFs).

## Optional helper

Create a JUnit file elsewhere:

```
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\make_junit.ps1 -Suite "pipeline" -Case "plan-takeoff-estimate" -Success:$true -Out "output\JUNIT.xml"
