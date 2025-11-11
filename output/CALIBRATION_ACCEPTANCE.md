# Calibration Acceptance Check (F4b)

- Timestamp: 2025-11-09T22:08:24
- Config acceptable_ratio (vendor_map.yaml): 3.0
- SUM_EST: 62,232.38
- SUM_VEN: 3,945,026.90
- Ratio (SUM_VEN / SUM_EST): 63.37
- FACTORS count: 8
- outliers_count: 0
- dupes_count: 0
- Dashboard: output/LYNN_DELTA_DASHBOARD.html
- Before/After: output/CALIBRATION_BEFORE_AFTER.md
- Status JSON: output/CALIBRATION_STATUS.json

Result: FAIL
Reason: Ratio 63.37 exceeds acceptable bounds (0.3×–3.0×).

Notes:
- The pipeline now normalizes money (US/EU, k/m suffixes, parentheses negatives), de-duplicates across pages and files (choose_latest), and drops non-scope keywords (tax/allowance/freight/alt/permit/etc.).
- Numeric-only descriptions are filtered (e.g., “360000”), which removed a large class of OCR artifacts.
- SUM_VEN calculation in receipts now uses vendor_vs_estimate.csv (apples-to-apples against estimate rollups).

Recommended next tightening for PASS:
1) Numeric-only description threshold: drop pure-numeric desc length ≥ 5 (currently ≥ 6). This will filter items like “65000” (seen in vendor sample keys).
2) Expand non-scope keyword list if needed (e.g., “delivery fee”, “freight charge”, “insurance certificate”, “bond cost”, “permit fee”), already configurable in data/taxonomy/vendor_map.yaml under parsing.drop_line_keywords.
3) Consider carry-forward subtotals: add rolling-sum duplicate detection to drop page-level “carry forward” lines that exactly match the sum of prior lines on the same vendor document.
4) If SUM_VEN remains above range, add vendor-specific normalizers for known header/footer sections in data/taxonomy/vendor_map.yaml → normalizers (regex replace).

Acceptance Gate
- SUM_VEN within 0.3×–3× SUM_EST: FAIL (63.37×)
- FACTORS > 0: PASS (8)
- outliers_count, dupes_count present: PRESENT but counts are 0 (investigate CSV reader vs writer if this remains 0 while markdown shows examples)

Commit Plan (when ready to tag a checkpoint)
- Code: web/backend/vendor_quote_parser_lynn.py, web/backend/model_calibration.py, scripts/run_f4b_data_pass.ps1, data/taxonomy/vendor_map.yaml
- Schemas: schemas/vendor_quotes_canonical.strict.schema.json
- Tests: tests/unit/test_money_parse.py (+ add test_vendor_dedupe.py, test_latest_vendor_package.py)
- Artifacts: output/CALIBRATION_OUTLIERS.csv, output/CALIBRATION_DUPES.csv, output/CALIBRATION_BEFORE_AFTER.md, output/CALIBRATION_STATUS.json, output/CALIBRATION_ACCEPTANCE.md, output/LYNN_DELTA_DASHBOARD.html

Proposed commit:
  git add web/backend/vendor_quote_parser_lynn.py web/backend/model_calibration.py \
          scripts/run_f4b_data_pass.ps1 data/taxonomy/vendor_map.yaml \
          schemas/vendor_quotes_canonical.strict.schema.json \
          tests/unit/test_money_parse.py \
          output/CALIBRATION_OUTLIERS.csv output/CALIBRATION_DUPES.csv \
          output/CALIBRATION_BEFORE_AFTER.md output/CALIBRATION_STATUS.json output/CALIBRATION_ACCEPTANCE.md
  git commit -m "fix(calibration): robust money parsing, dedupe, non-scope drops; receipts and acceptance check"
  # Optional tag
  # git tag -a "chkpt-f4b-fix-<shortSHA>" -m "F4b calibration parsing/dedupe fix"
  # git push origin --tags

Next Action
- Implement the threshold change for numeric-only descriptions and re-run:
  powershell -NoProfile -ExecutionPolicy Bypass -File scripts/run_f4b_data_pass.ps1 -Step All
