# R1 UAT Plan (Playwright)
- Verify /health
- Verify /v1/estimate (M01)
- Verify /v1/takeoff (pdf_path)
- Verify pipeline pass: takeoff ➜ estimate

Artifacts:
- Playwright HTML report: output/playwright-report/index.html
- Trace/Video/Screenshots: output/playwright-artifacts/
- Human receipt: output/UAT_RECEIPT.md
- Machine status: output/UAT_STATUS.json

Run sequence:
1) Start API and run tests with scripts/uat_run.ps1
   - Optional: set a real PDF path
     - PowerShell: $env:PLAN_PDF="C:\path\to\LYNN.pdf"
     - Or pass -PlanPdf to scripts/uat_run.ps1

2) Commit + tag ready:
   git add playwright.config.ts tests/e2e/uat.release.spec.ts scripts/uat_start_api.ps1 scripts/uat_run.ps1 output/UAT_PLAN.md
   git commit -m "feat(uat-r1): Playwright UAT suite with trace/video + receipts"
   git tag -a "uat-r1-ready" -m "UAT R1 suite ready"
   git push origin master --tags

3) Execute UAT:
   pwsh -File scripts/uat_run.ps1 # -PlanPdf $PLAN_PDF

4) Post-run commit and tag:
   git add output/UAT_RECEIPT.md output/UAT_STATUS.json output/playwright-report output/playwright-artifacts
   git commit -m "chore(uat-r1): attach Playwright UAT artifacts (report + traces + receipt)"
   git tag -a "uat-r1-done" -m "R1 UAT run complete"
   git push origin master --tags
