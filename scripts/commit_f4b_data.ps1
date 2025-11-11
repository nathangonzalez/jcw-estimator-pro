# Commit F4b-data: parsed vendor PDFs → non-zero calibration + delta dashboard; push, tag, and write receipt
param()

$ErrorActionPreference = 'Stop'

# Stage core + taxonomy/mapping updates if any
$files = @(
  'schemas/taxonomy.schema.json',
  'data/taxonomy/trade_item_catalog.csv',
  'data/taxonomy/vendor_map.yaml',
  'web/backend/vendor_quote_parser_lynn.py',
  'web/backend/model_calibration.py',
  'scripts/make_delta_dashboard.ps1',
  'scripts/train_lynn_model_from_vendor.ps1',
  'scripts/run_calibrated_estimate.ps1',
  'scripts/run_lynn_f3b_vendor.ps1',
  'scripts/lynn_vendor_compare_v0.py'
)

foreach ($f in $files) {
  if (Test-Path $f) { git add -- $f | Out-Null }
}

# Stage generated artifacts expected from F4b-data run
$maybe = @(
  'data/lynn/working/vendor/rows/*.rows.json',
  'data/lynn/working/vendor/rows/*.rows.csv',
  'data/lynn/working/vendor_quotes.canonical.csv',
  'data/lynn/working/vendor_quotes.canonical.json',
  'data/lynn/working/vendor_vs_estimate.csv',
  'data/lynn/working/vendor_vs_estimate.json',
  'data/lynn/working/VENDOR_COMPARE_SUMMARY.md',
  'data/lynn/working/PIPELINE_ESTIMATE_RESPONSE_CALIBRATED.json',
  'data/lynn/working/estimate_lines_calibrated.csv',
  'models/calibration/lynn_v0.json',
  'output/LYNN_DELTA_DASHBOARD.html',
  'output/CALIBRATION_REPORT.md',
  'output/CALIBRATION_DIAGNOSE.md',
  'data/lynn/working/vendor_mapping_coverage.json'
)
foreach ($pat in $maybe) {
  Get-ChildItem -Path $pat -ErrorAction SilentlyContinue | ForEach-Object {
    git add -- $_.FullName | Out-Null
  }
}

# Commit with F4b-data message
$MSG = "feat(f4b-data): parse Lynn vendor PDFs -> non-zero calibration + delta dashboard"
try {
  git commit -m $MSG | Out-Null
} catch {
  Write-Host "Commit encountered an issue (possibly no changes). Continuing. $_"
}

# Push and lightweight tag
git push origin master | Out-Null
$shaShort = (git rev-parse --short HEAD).Trim()
$tag = "chkpt-f4b-data-$shaShort"
try { git tag -f $tag | Out-Null } catch {}
git push origin --tags | Out-Null

# Build receipt
$outDir = 'output'
New-Item -ItemType Directory -Force -Path $outDir | Out-Null
$receipt = Join-Path $outDir 'F4B_DATA_RECEIPT.md'

# Pull metrics
$mapped = 0; $unmapped = 0
$coveragePath = 'data/lynn/working/vendor_mapping_coverage.json'
if (Test-Path $coveragePath) {
  try {
    $cov = Get-Content -Raw $coveragePath | ConvertFrom-Json
    if ($cov.mapped -ne $null)   { $mapped = [int]$cov.mapped }
    if ($cov.unmapped -ne $null) { $unmapped = [int]$cov.unmapped }
  } catch {}
}

$factorsCount = 0
$modelPath = 'models/calibration/lynn_v0.json'
if (Test-Path $modelPath) {
  try {
    $j = Get-Content -Raw $modelPath | ConvertFrom-Json
    $factorsCount = ($j.factors.Keys | Measure-Object).Count
  } catch {}
}

$dashboardPath = 'output/LYNN_DELTA_DASHBOARD.html'

@"
# F4b Data Receipt

Coverage:
- Mapped rows:   $mapped
- Unmapped rows: $unmapped

Calibration:
- Factors learned: $factorsCount
- Model JSON: $modelPath

Dashboard:
- Path: $dashboardPath

Commit: $(git rev-parse HEAD)
Tag: $tag
"@ | Out-File -Encoding UTF8 $receipt

Write-Host ("F4B_DATA_COMMIT {0} TAG {1}" -f (git rev-parse HEAD), $tag)
