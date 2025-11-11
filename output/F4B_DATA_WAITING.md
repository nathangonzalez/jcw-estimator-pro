# F4b Data Pass — Waiting for Vendor PDFs

Status
- Orchestrator and pipeline are wired and tested.
- Parse step ran; training used fallback canonical (header-only), so factors == 0.
- Awaiting real vendor PDFs to produce non-zero calibration factors.

What you need to do (owner action)
1) Place your Lynn vendor PDFs locally (they are git-ignored) under:
   - data/lynn/raw/vendor/ABCO/raw/Lynn-ABCO Proposal Package 10.23.25.pdf
   - data/lynn/raw/vendor/ABCO/raw/Lynn-ABCO (REV) Proposal Package 10.28.25.pdf
   - data/lynn/raw/vendor/AdvancedElectrical/raw/Lynn-Advanced Electrical 11.4.25.pdf
   - data/lynn/raw/vendor/TileAbbate/raw/Lynn-Abbate Tile 10.31.25.pdf
   - data/lynn/raw/vendor/CitrusRoofing/raw/Lynn-Cirtus Roofing 10.24.25.pdf
   - …repeat per vendor (folder/vendor mapping is the key; filenames can vary)

2) If needed, refine vendor mapping phrases (already seeded) in:
   - data/taxonomy/vendor_map.yaml
   Add/adjust rules for any unmapped heavy lines after the first pass.

Run plan (exact step-by-step commands)
- Parse vendors → canonical + compare:
  powershell -NoProfile -ExecutionPolicy Bypass -File scripts/run_f4b_data_pass.ps1 -Step Parse

- Train calibration factors:
  powershell -NoProfile -ExecutionPolicy Bypass -File scripts/run_f4b_data_pass.ps1 -Step Train

- Calibrated estimate:
  powershell -NoProfile -ExecutionPolicy Bypass -File scripts/run_f4b_data_pass.ps1 -Step Calibrated

- Delta dashboard (adds diagnosis if factors == 0):
  powershell -NoProfile -ExecutionPolicy Bypass -File scripts/run_f4b_data_pass.ps1 -Step Dashboard

- Commit + tag (code + artifacts only; vendor PDFs are ignored):
  powershell -NoProfile -ExecutionPolicy Bypass -File scripts/commit_f4b_data.ps1

Acceptance criteria
- data/lynn/working/vendor_quotes.canonical.csv has ≥ 1 data row with trade,item,quoted_total > 0
- models/calibration/lynn_v0.json shows factors_count > 0
- output/LYNN_DELTA_DASHBOARD.html exists and renders
- data/lynn/working/VENDOR_COMPARE_SUMMARY.md shows top deltas
- Commit & tag created successfully (no force-push)

Where to look (artifacts)
- Mapping coverage: data/lynn/working/vendor_mapping_coverage.json
- Canonical (combined): data/lynn/working/vendor_quotes.canonical.csv / .json
- Compare deltas: data/lynn/working/vendor_vs_estimate.csv / .json
- Calibration model: models/calibration/lynn_v0.json
- Dashboard: output/LYNN_DELTA_DASHBOARD.html
- Diagnosis (if factors == 0): output/CALIBRATION_DIAGNOSE.md
- Receipt after commit: output/F4B_DATA_RECEIPT.md
- Run log (append): output/LYNN_F4B_PIPELINE.log
- Run summary: output/RUN_SUMMARY.md

Notes
- .gitignore blocks committing vendor PDFs and data/lynn/_archive/**.
- If factors remain 0, open output/CALIBRATION_DIAGNOSE.md and copy 1–2 top unmapped phrases into data/taxonomy/vendor_map.yaml under the correct trade/item rules, then re-run Parse → Train → Calibrated → Dashboard.
