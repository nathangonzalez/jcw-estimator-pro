# Next Actions for R2 Interactive

## Issues Found
- API not running during UAT/smoke tests
- data/quantities.sample.json not found (test failure)
- Interactive endpoints return 500 when API not running

## Required Fixes
1. Start API server before running UAT/smoke tests
2. Fix path to quantities.sample.json in test (should be data/quantities.sample.json)
3. Test interactive endpoints with API running
4. Verify CSV outputs are generated correctly

## Commands to Run Next
- Start API: python web/backend/app_comprehensive.py
- Fix test: Update path in tests/e2e/uat.r2.spec.ts
- Re-run UAT: pwsh -File scripts/uat_run.ps1
- Re-run smoke: pwsh -File scripts/interactive_smoke.ps1
- Verify artifacts in output/INTERACTIVE/
