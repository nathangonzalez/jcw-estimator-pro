# Next Actions for R2 Interactive

## Issues Found
- Interactive endpoints return 500 (internal server error)
- data/quantities.sample.json not found (test failure)
- API started OK, but endpoints have bugs

## Required Fixes
1. Debug 500 errors in /v1/plan/assess and /v1/estimate?mode=interactive
2. Create data/quantities.sample.json or fix test path
3. Test endpoints manually: curl -X POST http://127.0.0.1:8001/v1/plan/assess -H "Content-Type: application/json" -d '{"project_id":"test","pdf_path":"dummy.pdf"}'
4. Verify CSV outputs are generated correctly in output/<project>/

## Commands to Run Next
- Debug API: Check output/UVICORN_STDERR.log for errors
- Fix test: Create data/quantities.sample.json or update require path
- Re-run UAT: pwsh -File scripts/uat_run.ps1
- Re-run smoke: pwsh -File scripts/interactive_smoke.ps1
- Verify artifacts in output/INTERACTIVE/
