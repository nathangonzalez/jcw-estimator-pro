# F4: Vendor-Driven Calibration (LYNN)

**Purpose:** Learn per-(trade,item) multipliers from vendor quotes vs the RAW policy-based estimate, then re-score the estimate using those factors (without using vendor quotes at scoring time).

## Pipeline
1. RAW estimate exists → `data/lynn/working/estimate_lines.csv`
2. Canonical vendor quotes → `data/lynn/working/vendor_quotes.canonical.csv`
3. Train: `pwsh -File scripts/train_lynn_model_from_vendor.ps1`
   - Output: `models/calibration/lynn_v0.json` (factors + meta digests)
4. Score: `pwsh -File scripts/run_calibrated_estimate.ps1`
   - Output: `data/lynn/working/PIPELINE_ESTIMATE_RESPONSE_CALIBRATED.json`
   - Lines:  `data/lynn/working/estimate_lines_calibrated.csv`

## Notes
- Multipliers are clamped (default [0.4, 2.5]) to avoid instability on sparse v0.
- No vendor quotes are used at scoring time; they’re training-only.
- Safe to iterate per project; future step will generalize across projects.

Minimal updates (none required to run)

No server changes required: we run calibration & calibrated estimate via scripts (faster).

No Playwright involvement for F4.

Commit & Push (Cline to execute)

Stage + commit + push + tag

Commit message:
feat(f4-calibration): vendor-trained multipliers and calibrated estimate path (dev-fast)

Lightweight tag: chkpt-f4-<shortSHA>

Write run receipt

output/F4_CALIBRATION_RECEIPT.md with:

Paths of inputs/outputs

Count of factors learned

Result files created

After commit — Quick run (you or Cline)
# Train factors from vendor vs raw
pwsh -File scripts/train_lynn_model_from_vendor.ps1

# Re-score a calibrated estimate (no server required)
pwsh -File scripts/run_calibrated_estimate.ps1


Expected new artifacts

models/calibration/lynn_v0.json

output/CALIBRATION_REPORT.md

data/lynn/working/PIPELINE_ESTIMATE_RESPONSE_CALIBRATED.json

data/lynn/working/estimate_lines_calibrated.csv

Guardrails

Operate only under repo paths listed above.

No force-push.

No package installs unless explicitly approved.

If any input file is missing, create a clear placeholder and continue (don’t fail hard).
