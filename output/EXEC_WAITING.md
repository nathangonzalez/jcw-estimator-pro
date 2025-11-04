# Supervised Remediation — Awaiting Approval (No-Run)

## Status: PAUSED (Approval Gate)

Remediation files have been staged and pushed. Execution is paused until explicit approval to proceed with installs/tests.

- Last commit: 0d75f15 (feat(testing): fix smoke JSON and add Playwright toolchain)
- Gate file: /approvals/EXEC_OK (reuse existing gate)

## What will run on approval

1) Install Playwright dependencies (supervised)
   pwsh -File scripts/install_playwright.ps1

2) Start API locally if not already running (supervised)
   # Adjust entrypoint as needed; example:
   # uvicorn web.backend.app:app --reload

3) Run UAT smoke and capture logs
   pwsh -File scripts/smoke_estimate_v1.ps1 | Tee-Object -FilePath output/SMOKE_STDOUT.log

4) Run E2E headless and export HTML report
   npm run e2e || true
   npx playwright show-report --output output/playwright-report > output/PLAYWRIGHT_SUMMARY.md 2>&1

## Expected Artifacts
- output/SMOKE_STDOUT.log
- output/SMOKE_ESTIMATE_RUN.md and output/SMOKE_ESTIMATE_RUN.json
- output/PLAYWRIGHT_SUMMARY.md
- output/playwright-report/**
- output/EXEC_AUDIT.md (append “Remediation Run” section with pass/fail)

## Approval Instructions
- Ensure /approvals/EXEC_OK exists (reuse is acceptable)
- Then confirm “approve run” to proceed with supervised execution
- All actions and results will be written to /output and committed incrementally

## Notes
- No installs or tests will run until approval is confirmed
- Scope is limited to a single smoke request and a headless E2E run
