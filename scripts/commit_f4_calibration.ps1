# Commit F4 calibration artifacts and push + lightweight tag; write receipt
param()

$ErrorActionPreference = 'Stop'

# Stage core code/docs/scripts
$files = @(
  'web/backend/model_calibration.py',
  'web/backend/pricing_engine_calibrated.py',
  'scripts/train_lynn_model_from_vendor.ps1',
  'scripts/run_calibrated_estimate.ps1',
  'docs/CALIBRATION.md'
)

foreach ($f in $files) {
  if (Test-Path $f) { git add -- $f | Out-Null }
}

# Stage generated artifacts if present
$maybe = @(
  'models/calibration/lynn_v0.json',
  'output/CALIBRATION_REPORT.md',
  'data/lynn/working/PIPELINE_ESTIMATE_RESPONSE_CALIBRATED.json',
  'data/lynn/working/estimate_lines_calibrated.csv'
)
foreach ($p in $maybe) {
  if (Test-Path $p) { git add -- $p | Out-Null }
}

# Commit (continue if nothing to commit)
$MSG = 'feat(f4-calibration): vendor-trained multipliers and calibrated estimate path (dev-fast)'
try {
  git commit -m $MSG | Out-Null
} catch {
  Write-Host "Commit encountered an issue (possibly no changes). Continuing. $_"
}

# Push
git push origin master | Out-Null

# Tag
$shaShort = (git rev-parse --short HEAD).Trim()
$tag = "chkpt-f4-$shaShort"
try { git tag -f $tag | Out-Null } catch {}
git push origin --tags | Out-Null

# Receipt
$outDir = 'output'
New-Item -ItemType Directory -Force -Path $outDir | Out-Null
$receipt = Join-Path $outDir 'F4_CALIBRATION_RECEIPT.md'

$factorsCount = 0
$modelPath = 'models/calibration/lynn_v0.json'
if (Test-Path $modelPath) {
  try {
    $j = Get-Content -Raw $modelPath | ConvertFrom-Json
    $factorsCount = ($j.factors.Keys | Measure-Object).Count
  } catch {}
}

@"
# F4 Calibration Receipt

Inputs:
- RAW estimate lines: data/lynn/working/estimate_lines.csv
- Vendor canonical:   data/lynn/working/vendor_quotes.canonical.csv

Outputs:
- Model JSON: models/calibration/lynn_v0.json
- Report MD:  output/CALIBRATION_REPORT.md
- Calibrated response: data/lynn/working/PIPELINE_ESTIMATE_RESPONSE_CALIBRATED.json
- Calibrated lines:    data/lynn/working/estimate_lines_calibrated.csv

Factors learned: $factorsCount

Commit: $(git rev-parse HEAD)
Tag: $tag
"@ | Out-File -Encoding UTF8 $receipt

Write-Host ("F4_CALIBRATION_COMMIT {0} TAG {1}" -f (git rev-parse HEAD), $tag)
