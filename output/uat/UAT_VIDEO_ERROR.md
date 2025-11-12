# UAT Video Generation Error

**Error:** UAT report not found at output/uat-report.json
**Time:** 2025-11-12T14:50:13.5671806-05:00

Run UAT tests first:
`
npx playwright test tests/e2e/uat.interactive.spec.ts --reporter=json
`

This should generate output/uat-report.json
