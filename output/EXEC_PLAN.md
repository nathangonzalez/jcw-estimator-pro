# Supervised Remediation Execution Plan (No-Run)

## Objective
Patch the UAT smoke JSON body, add Playwright dependencies/config, then re-run smoke + E2E under explicit approval gating with auditable artifacts.

## Scope
- Do not execute installs or tests until approval is confirmed.
- All outputs must be written to /output and committed.

## Remediation Changes (applied in this commit)
- scripts/smoke_estimate_v1.ps1: send valid JSON payload and robust error capture
- package.json: add @playwright/test + playwright and npm scripts (e2e, e2e:ui, e2e:report)
- playwright.config.ts: minimal config with baseURL, timeout, reporters
- scripts/install_playwright.ps1: supervised install script

## Runbook (execute only when /approvals/EXEC_OK is present)
1) Install Playwright dependencies (supervised)
   pwsh -File scripts/install_playwright.ps1

2) Start API locally if not already running (supervised)
   # Adjust entrypoint as needed; example:
   # uvicorn web.backend.app:app --reload

3) Run UAT smoke (logs captured)
   pwsh -File scripts/smoke_estimate_v1.ps1 | Tee-Object -FilePath output/SMOKE_STDOUT.log

4) Run E2E headless (Playwright)
   npm run e2e || true
   npx playwright show-report --output output/playwright-report > output/PLAYWRIGHT_SUMMARY.md 2>&1

## Expected Artifacts to (re)generate
- output/SMOKE_STDOUT.log
- output/SMOKE_ESTIMATE_RUN.md and output/SMOKE_ESTIMATE_RUN.json
- output/PLAYWRIGHT_SUMMARY.md
- output/playwright-report/** (HTML artifacts)
- output/EXEC_AUDIT.md (Append new 'Remediation Run' section with pass/fail)

## Gating
- Approval file: /approvals/EXEC_OK
- Action: STOP here and await explicit approval before running any commands

## Metadata
- Branch: master
- Approval: pending (no-run)
- Session: remediation plan prepared
