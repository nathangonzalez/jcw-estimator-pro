# RUN SUMMARY

- When: 2025-11-11T13:10:39.2890456-05:00
- Canonical rows (valid trade,item,quoted_total>0): 377
- Factors count: 8
- Dashboard: output/LYNN_DELTA_DASHBOARD.html
- Receipt (if committed): output/F4B_DATA_RECEIPT.md
- HEAD: 00e710b8e5fa0735cf60f646c835ec43dce1ec5c

## Top 3 deltas (by |Vendor-Est|)
| trade | item | est_total | vdr_total | delta_total |
|---|---|---:|---:|---:|
| concrete | 1_message | 0 | 1,000,000 | -1,000,000 |
| insulation | 21263 | 0 | 21,263 | -21,263 |
| concrete | cost_to_make_and_install_locally_would_b | 0 | 11,000 | -11,000 |

## R2.2 Interactive Status
- Current SHA: f6a9ac0
- Branch: master
- Timestamp: 2025-11-12T11:16:51-05:00
- Preconditions check: scripts/uat_run.ps1 ✓, tests/e2e/uat.release.spec.ts ✓, web/backend/app_comprehensive.py ✓
- TAKEOFF_ENABLE_LAYOUT: available for toggle

## R2.4 Demo Hot Keys Start
- Timestamp: 2025-11-13T14:00:00-05:00
- Branch: master
- Short SHA: a7b42cc
## Playwright Visual Run (2025-11-13T17:20:23.7270668-05:00)
HEAD: fb32ec4
## master...origin/master [ahead 4]
 M output/R2_INTERACTIVE_RUN.md
 M output/RUN_SUMMARY.md
 M output/TAKEOFF_RUN.log
 M output/UAT_ANNOTATED.md
 M output/UAT_RECEIPT.md
 M output/UAT_STATUS.json
 M output/UVICORN_STDERR.log
 M output/UVICORN_STDOUT.log
 M output/playwright-artifacts/.last-run.json
 D output/playwright-artifacts/estimate-Estimator-smoke-supervised-scaffold-loads-UI-frame-chromium/trace.zip
 M output/playwright-artifacts/estimate-Estimator-smoke-supervised-scaffold-loads-UI-frame-chromium/video.webm
 D output/playwright-artifacts/uat.interactive-UAT-Intera-11f5a-tion-generation-determinism-chromium/trace.zip
 D output/playwright-artifacts/uat.interactive-UAT-Intera-9f0de--endpoint-processes-answers-chromium/trace.zip
 D output/playwright-artifacts/uat.interactive-UAT-Interactive---Assess-endpoint-with-PDF-chromium/trace.zip
 D output/playwright-artifacts/uat.interactive-UAT-Interactive---Assess-validation-errors-chromium/trace.zip
 D output/playwright-artifacts/uat.interactive-UAT-Interactive---Files-cleanup-chromium/trace.zip
 D output/playwright-artifacts/uat.interactive-UAT-Interactive---Health-check-chromium/trace.zip
 D output/playwright-artifacts/uat.interactive-UAT-Interactive---QnA-validation-errors-chromium/trace.zip
 D output/playwright-artifacts/uat.r2-UAT-R2---Estimate-API-chromium/trace.zip
 D output/playwright-artifacts/uat.r2-UAT-R2---Files-exist-chromium/trace.zip
 D output/playwright-artifacts/uat.r2-UAT-R2---Health-check-chromium/trace.zip
 D output/playwright-artifacts/uat.r2-UAT-R2-Interactive---Assess-endpoint-chromium/trace.zip
 D output/playwright-artifacts/uat.r2-UAT-R2-Interactive---Estimate-interactive-mode-chromium/trace.zip
 D "output/playwright-artifacts/uat.release-R1-UAT-\342\200\224-API-h-5f9bd--returns-v0-like-quantities-chromium/trace.zip"
 D "output/playwright-artifacts/uat.release-R1-UAT-\342\200\224-API-h-71491--returns-v0-shaped-response-chromium/trace.zip"
 D "output/playwright-artifacts/uat.release-R1-UAT-\342\200\224-API-h-a38a7-eturns-200-and-minimal-body-chromium/trace.zip"
 D "output/playwright-artifacts/uat.release-R1-UAT-\342\200\224-Pipel-fcefa-output-passes-into-estimate-chromium/trace.zip"
 D output/playwright-report/data/1a2254969a2b77cacd14778dab18bdeb9770e6bd.webm
 D output/playwright-report/data/5e401a3fbc1e7930108ead3289914752d90da846.webm
 M output/playwright-report/index.html
 M output/uat-report.json
 M web/backend/__pycache__/app_comprehensive.cpython-311.pyc
 M web/backend/__pycache__/schemas.cpython-311.pyc
 M web/backend/__pycache__/takeoff_engine.cpython-311.pyc
 M web/backend/app_comprehensive.py
 M web/backend/blueprint_parsers/layout_stage.py
 M web/backend/takeoff_engine.py
?? data/lynn/plans/
?? data/taxonomy/legend_map.yaml
?? output/INTERACTIVE/INTERACTIVE_RUN.log
?? output/R22_RUN_SUMMARY.md
?? output/playwright-artifacts/estimate-Estimator-smoke-supervised-scaffold-loads-UI-frame-chromium/test-finished-1.png
?? "output/playwright-artifacts/uat.story.video-R2-2-2-Sto-73be8-timate-\342\206\222-Interactive-video--chromium/"
?? output/playwright-report/data/a000b326bdc8b932b7948532bf00b6cfd3b2af4d.webm
?? output/playwright-report/data/b66b3e07eff9b76881cddf4ec25d041988b01b6d.webm
?? output/uat-assess-request-id-test/
?? output/uat-qna-well-formed-test/
?? web/backend/__pycache__/interactive_engine.cpython-311.pyc
?? web/backend/blueprint_parsers/__pycache__/layout_stage.cpython-311.pyc
?? web/backend/blueprint_parsers/__pycache__/room_stage.cpython-311.pyc
?? web/backend/blueprint_parsers/room_stage.py
Version 1.56.1
HEALTH: 200
FOUND: data\quantities.sample.json
2025-11-13T17:26:13.6053976-05:00 - story test exit code: 
FOUND: output\uat-report.json
Reel build attempt: OK
