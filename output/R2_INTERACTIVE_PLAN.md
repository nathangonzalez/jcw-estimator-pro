# R2 Interactive Estimator Implementation Plan

## Overview
Implement the R2 "Polymath Estimator" with plan assessment and interactive estimate loop, using existing stubs and adding minimal new code.

## Steps
1. Verify existing schemas and backend stubs (trade_inference.py, clarifier.py, default_mappings.yaml)
2. Enhance /v1/plan/assess endpoint in app_comprehensive.py
3. Enhance /v1/estimate interactive mode in app_comprehensive.py
4. Add minimal frontend tab for interactive (if web/frontend exists)
5. Update UAT tests in tests/e2e/uat.release.spec.ts
6. Add interactive_smoke.ps1 script
7. Run UAT and smoke tests
8. Generate receipts
9. Commit changes

## Acceptance Criteria
- /v1/plan/assess returns questions >=3
- /v1/estimate?mode=interactive works with Q/A
- output/INTERACTIVE/ files created
- UAT passes
- Receipts generated
