# Commit F4b taxonomy + vendor mapping + calibration dashboard; push and tag; write receipt
param()

$ErrorActionPreference = 'Stop'

# Stage core changes
$files = @(
  'schemas/taxonomy.schema.json',
  'data/taxonomy/trade_item_catalog.csv',
  'data/taxonomy/vendor_map.yaml',
  'web/backend/vendor_quote_parser_lynn.py',
  'web/backend/model_calibration.py',
  'scripts/make_delta_dashboard.ps1'
)

foreach ($f in $files) {
  if (Test-Path $f) { git add -- $f | Out-Null }
}

# Stage generated artifacts if present
$maybe = @(
  'models/calibration/lynn_v0.json',
  'output/CALIBRATION_REPORT.md',
  'output/CALIBRATION_DIAGNOSE.md',
  'output/LYNN_DELTA_DASHBOARD.html',
  'data/lynn/working/vendor_mapping_coverage.json',
  'data/lynn/working/vendor_quotes.canonical.csv',
  'data/lynn/working/vendor_vs_estimate.csv',
  'data/lynn/working/vendor_vs_estimate.json',
  'data/lynn/working/VENDOR_COMPARE_SUMMARY.md'
)
foreach ($p in $maybe) {
  if (Test-Path $p) { git add -- $p | Out-Null }
}

# Commit
$MSG = "feat(f4b-matching): taxonomy + vendor mapping -> non-zero calibration + delta dashboard"
try {
  git commit -m $MSG | Out-Null
} catch {
  Write-Host "Commit encountered an issue (possibly no changes). Continuing. $_"
}

# Push and tag
git push origin master | Out-Null
$shaShort = (git rev-parse --short HEAD).Trim()
$tag = "chkpt-f4b-$shaShort"
try { git tag -f $tag | Out-Null } catch {}
git push origin --tags | Out-Null

# Build F4B receipt
$outDir = 'output'
New-Item -ItemType Directory -Force -Path $outDir | Out-Null
$receipt = Join-Path $outDir 'F4B_RECEIPT.md'

# Read coverage (if exists)
$mapped = 0; $unmapped = 0
$coveragePath = 'data/lynn/working/vendor_mapping_coverage.json'
if (Test-Path $coveragePath) {
  try {
    $cov = Get-Content -Raw $coveragePath | ConvertFrom-Json
    if ($cov.mapped -ne $null)   { $mapped = [int]$cov.mapped }
    if ($cov.unmapped -ne $null) { $unmapped = [int]$cov.unmapped }
  } catch {}
}

# Factors count
$factorsCount = 0
$modelPath = 'models/calibration/lynn_v0.json'
if (Test-Path $modelPath) {
  try {
    $j = Get-Content -Raw $modelPath | ConvertFrom-Json
    $factorsCount = ($j.factors.Keys | Measure-Object).Count
  } catch {}
}

# Dashboard path
$dashboard = 'output/LYNN_DELTA_DASHBOARD.html'

@"
# F4b Matching Receipt

Coverage:
- Mapped rows:   $mapped
- Unmapped rows: $unmapped

Calibration:
- Factors learned: $factorsCount
- Model JSON: models/calibration/lynn_v0.json

Dashboard:
- Path: $dashboard

Commit: $(git rev-parse HEAD)
Tag: $tag
"@ | Out-File -Encoding UTF8 $receipt

Write-Host ("F4B_MATCHING_COMMIT {0} TAG {1}" -f (git rev-parse HEAD), $tag)
