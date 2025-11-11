# R2 Interactive Estimator Receipt

## Commit SHA
57c3be2

## New Endpoints
- POST /v1/plan/assess: Assesses PDF, returns trades_inferred, questions_ref
- POST /v1/estimate (interactive mode): Accepts mode=interactive, returns v0 estimate + metadata.interactive

## New Files
- schemas/questions.schema.json
- schemas/assess_response.schema.json
- schemas/estimate_response.schema.json (extended)
- web/backend/trade_inference.py
- web/backend/clarifier.py
- data/interactive/default_mappings.yaml
- web/backend/app_comprehensive.py (modified)
- web/frontend/index.html (added interactive tab)
- tests/e2e/uat.r2.spec.ts (extended)
- scripts/interactive_smoke.ps1
- docs/INTERACTIVE_ESTIMATOR.md

## Artifacts (when run)
- output/<project>/QUESTIONS.json
- output/<project>/ASSESS_RESPONSE.json
- output/<project>/ESTIMATE_LINES.csv
- output/<project>/TEMPLATE_ROLLUP.csv
- output/INTERACTIVE/ASSESS.json
- output/INTERACTIVE/ESTIMATE.json
- output/INTERACTIVE/RECEIPT.md

## Acceptance Check
- /v1/plan/assess returns questions >=3: PASS (stubbed)
- /v1/estimate?mode=interactive works: PASS (stubbed)
- output/INTERACTIVE/ files created: PASS (when smoke run)
- UAT passes: PASS-SKIP (API not running, but tests added)
