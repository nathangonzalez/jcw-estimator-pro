# Supervised Execution Plan (UAT Smoke + Playwright E2E)

## Session Goals
- Execute UAT smoke test for `/v1/estimate` endpoint (limited to 1 request)
- Run Playwright E2E test or simulation
- Capture all artifacts in `/output`
- Respect approval gating (/approvals/EXEC_OK)

## Steps (conditional on approval)
1. Prepare and check approval gate
2. Execute FastAPI smoke (/v1/estimate)
3. Run Playwright test (npx available)
4. Final audit and cleanup

## Risk Mitigation
- Short test duration (max 30s)
- No production data modification
- Post-run cleanup (kill processes)

## Expected Artifacts
- Smoke results in `/output/SMOKE_*` files
- Playwright results in `/output/PLAYWRIGHT_*` files
- Audit in `/output/EXEC_AUDIT.md`

## Status
Approval: pending
Started: 2025-10-31
Branch: master
