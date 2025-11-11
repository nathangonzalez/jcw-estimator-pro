# Create folder if needed, write file, commit & (optionally) push
$newPath = "prompts"
$newFile = "SNREVIEW_CONTEXT.txt"
$newFull = Join-Path $newPath $newFile
if (!(Test-Path $newPath)) { New-Item -ItemType Directory -Path $newPath | Out-Null }
@'
# SNREVIEW_CONTEXT (JCW Estimator Suite — Current State & Guardrails)

## # Purpose
Provide Gemini with the authoritative, compact context so it can assist Cline without re-deriving project history. This file summarizes **what exists**, **how to run/check it**, **where not to touch**, and **what to do next**.

## # Repo
- **Name:** jcw-estimator-pro  
- **Primary app:** `web/backend/app_comprehensive.py` (FastAPI)  
- **Front-end (vanilla JS):** `web/frontend/*`  
- **Schemas & contracts:** `schemas/*`, `openapi/contracts/*`  
- **Estimating core:** `web/backend/pricing_engine.py`, `web/backend/pricing_engine_calibrated.py`  
- **Takeoff / plan reader:** `web/backend/takeoff_engine.py`, `web/backend/plan_reader.py`, `web/backend/blueprint_parsers/pdf_titleblock.py`  
- **Calibration & benchmarking:**  
  - `web/backend/model_calibration.py`  
  - `web/backend/benchmarking.py`  
  - `web/backend/vendor_quote_parser_lynn.py`  
- **UAT / E2E:** `tests/e2e/uat.release.spec.ts`, `playwright.config.ts`, scripts under `scripts/*`  
- **Data (pilot):** `data/lynn/*` (ingest, vendor, working), `data/taxonomy/*`  
- **Docs (selected):** `docs/ESTIMATING_PIPELINE.md`, `docs/JCW_SUITE_BIGPICTURE.md`, `docs/CALIBRATION.md`, `docs/UELTCHI_MVP.md` (WIP)  
- **Outputs:** `output/*` + `data/lynn/working/*`

## # Guardrails (DEV-FAST mode)
- **OK to run**: local scripts and UAT; commits & normal pushes are allowed.  
- **Not allowed**: force-push, destructive deletes, external network installs unless explicitly stated in scripts.  
- **Approval Gate** (used when needed): `approvals/EXEC_OK` (create an empty file to permit supervised runs).

## # Key Endpoints
- `GET /health` → 200  
- `POST /v1/estimate`  
  - **Dual-shape** request: legacy or M01 body (M01 preferred).  
  - Returns **v0** estimate response (totals + per-trade).  
- `POST /v1/takeoff`  
  - Accepts `{ project_id, pdf_path }` or `{ project_id, pdf_base64 }`.  
  - **Server normalizes** `trades` to **array** shape before returning.
- `POST /v1/plan/features` → plan features (F2)

## # Current Feature Milestones (Lynn pilot)
- **F1** Pricing engine ✅  
- **F2** Plan reader + Takeoff endpoint ✅  
- **F3** Pipeline smoke + fixture rules + strict M01 validation ✅  
- **F3b** Vendor quotes: parse → canonical → compare ✅ (heuristic; mapping rules in `data/taxonomy/vendor_map.yaml`)  
- **F4** Calibration: learn multipliers, re-score estimate ✅  
- **F4b** Matching/Taxonomy/Calibration hardening ✅ (non-zero factors produced; ratio acceptance still being tuned)

## # UAT Status (R1 / R1.1)
- Playwright suite delivered: `tests/e2e/uat.release.spec.ts`  
- Artifacts: `output/playwright-report/index.html`, `output/playwright-artifacts/`  
- **/v1/takeoff** normalization patch applied: always emits `trades` **array** (tolerant tests for placeholder PDFs).  
- Scripts:
  - Start API: `pwsh -File scripts/uat_start_api.ps1`
  - Run UAT: `pwsh -File scripts/uat_run.ps1`

## # Lynn Data Flow (RAW-first)
1. **Ingest** raw files → registry: `scripts/ingest_lynn.py`  
2. **Takeoff** (v0) → `data/lynn/working/takeoff_quantities.json`: `scripts/lynn_takeoff_v0.py`  
3. **Estimate** (quote-free baseline) → v0 response + lines CSV: `scripts/lynn_estimate_v0.py`  
4. **Gut-check** (read-only metrics): `scripts/lynn_gutcheck_v0.py`  
5. **Vendor parse → canonical → compare**: `scripts/lynn_vendor_compare_v0.py`  
6. **Calibration** (factors) + **Calibrated estimate**:  
   - `scripts/train_lynn_model_from_vendor.ps1`  
   - `scripts/run_calibrated_estimate.ps1`  
7. **Dashboard** (deltas): `scripts/make_delta_dashboard.ps1`

Important inputs for improving calibration:
- Place **real vendor PDFs** under: `data/lynn/raw/vendor/&lt;VendorName&gt;/raw/*.pdf`  
- Mapping rules to improve coverage: `data/taxonomy/vendor_map.yaml`

## # Acceptance Receipts & Diagnostics (F4b)
- `output/CALIBRATION_STATUS.json` → includes `sum_ven`, `sum_est`, `factors`, `outliers_count`, `dupes_count`  
- `output/CALIBRATION_BEFORE_AFTER.md` → shows changes after parsing-tightening  
- `output/CALIBRATION_ACCEPTANCE.md` → **PASS target**: `sum_ven / sum_est` within **[0.3, 3.0]**  
- `output/CALIBRATION_OUTLIERS.csv`, `output/CALIBRATION_DUPES.csv`  
- Dashboard: `output/LYNN_DELTA_DASHBOARD.html`

## # Ueltchi MVP (Exploded → Collapsed Rollup)
Goal: **Keep rich exploded lines** for AI/analytics, **produce collapsed scope+amount** matching the legacy template.

- Library: `web/backend/rollup.py`  
- Importer: `scripts/import_estimating_template.py` → produces  
  - exploded: `data/ueltchi/working/estimate_lines.v0.csv|json`  
  - map: `data/ueltchi/working/template_row_map.csv`  
- Exports:  
  - collapsed CSV/XLSX: `output/ueltchi/estimate_collapsed.csv|xlsx`  
  - summary: `output/ueltchi/ESTIMATE_SUMMARY.md` (must include a “Collapsed View” section)  
- Smoke test parity: `scripts/ueltchi_mvp_smoke.ps1`  
  - **Totals parity**: `|Σ exploded − Σ collapsed| ≤ 0.5%`

## # What Gemini Should Do (Right Now)
**Do**
1. **Read** these first (in this order):  
   - `README.md`, `docs/JCW_SUITE_BIGPICTURE.md`, `docs/ESTIMATING_PIPELINE.md`  
   - `schemas/*`, `openapi/contracts/*`  
   - `web/backend/app_comprehensive.py`, `web/backend/pricing_engine.py`, `web/backend/takeoff_engine.py`  
   - `data/taxonomy/vendor_map.yaml`, `web/backend/vendor_quote_parser_lynn.py`  
   - `tests/e2e/uat.release.spec.ts`, `playwright.config.ts`  
   - For Ueltchi: `web/backend/rollup.py`, `scripts/import_estimating_template.py`, `scripts/ueltchi_mvp_smoke.ps1`  
2. **Run** only these **local** commands (no internet installs unless script says so):
   - API start (for UAT): `pwsh -File scripts/uat_start_api.ps1`
   - UAT run: `pwsh -File scripts/uat_run.ps1`
   - Lynn RAW pipeline: `python scripts/ingest_lynn.py` → `python scripts/lynn_takeoff_v0.py` → `python scripts/lynn_estimate_v0.py` → `python scripts/lynn_gutcheck_v0.py`
   - Vendor & calibration orchestrator: `pwsh -File scripts/run_f4b_data_pass.ps1 -Step Parse|Train|Calibrated|Dashboard`  
   - Ueltchi MVP smoke: `pwsh -File scripts/ueltchi_mvp_smoke.ps1`
3. **Write artifacts** only under `output/` and `data/*/working/`.  
4. **Commit** with clear messages; create tags when instructed.

**Don’t**
- Don’t force-push.  
- Don’t remove guardrails or edit `.gitignore` to include raw vendor PDFs.  
- Don’t hit external services or change cloud endpoints.  
- Don’t refactor core contracts without updating schemas/tests.

## # Open Issues / Next Actions
1. **Calibration acceptance**: current `sum_ven / sum_est` ratio still high; use `vendor_map.yaml` to drop non-scope lines (fees, totals, carry-forwards) and improve mapping. Re-run **Parse → Train → Calibrated → Dashboard**. Target band: **[0.3, 3.0]**.  
2. **UAT R1.1**: /v1/takeoff normalized; ensure tests pass **strict** when real plan is provided (`PLAN_PDF`), tolerant for placeholder.  
3. **Ueltchi MVP**: complete **collapsed export** parity (≤0.5% diff vs exploded).  
4. **Lynn → Quotes**: after non-zero factors stabilize, compare **RAW vs Vendor vs Calibrated** on the dashboard and capture decisions.  
5. **Docs**: keep `output/*_RECEIPT.md` and `*_STATUS.json` up to date for every supervised run.

## # Quick Commands (copy/paste)

### Start API + UAT
pwsh -File scripts/uat_start_api.ps1
pwsh -File scripts/uat_run.ps1

### Lynn pipeline (step-by-step)
python scripts/ingest_lynn.py
python scripts/lynn_takeoff_v0.py
python scripts/lynn_estimate_v0.py
python scripts/lynn_gutcheck_v0.py

### F4b Orchestrator
pwsh -File scripts/run_f4b_data_pass.ps1 -Step Parse
pwsh -File scripts/run_f4b_data_pass.ps1 -Step Train
pwsh -File scripts/run_f4b_data_pass.ps1 -Step Calibrated
pwsh -File scripts/run_f4b_data_pass.ps1 -Step Dashboard

### Ueltchi MVP Smoke
pwsh -File scripts/ueltchi_mvp_smoke.ps1

### Standard Commit
git add -A
git commit -m "chore: supervised run — update receipts & outputs"
git push

## # Success Criteria (what to show me)
- `output/UAT_STATUS.json` → `exit_code: 0` (and HTML report path)  
- `output/CALIBRATION_STATUS.json` → band PASS (0.3–3.0), `factors &gt; 0`  
- `output/LYNN_DELTA_DASHBOARD.html` renders  
- `output/ueltchi/estimate_collapsed.csv|xlsx` + parity PASS in `output/ueltchi/SMOKE_RECEIPT.md`
'@ | Set-Content -Path $newFull -Encoding UTF8

git add $newFull
git commit -m "docs(context): add SNREVIEW_CONTEXT for Gemini+Cline single-window guidance"
# Optional:
# git push
Write-Host "Saved -> $newFull"