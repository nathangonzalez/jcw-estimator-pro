# Commit and tag F4 (assemblies + cashflow) changes, then write F4 summary
param()

$ErrorActionPreference = "Stop"

# Files to stage
$files = @(
  'web/backend/assemblies_engine.py',
  'data/assemblies/interior.yaml',
  'data/assemblies/exterior.yaml',
  'data/benchmarks/us_boston_sod_v0.csv',
  'web/backend/benchmarking.py',
  'web/backend/cashflow.py',
  'schemas/schedule.schema.json',
  'docs/SCHEDULING_TEMPLATES.md',
  'docs/FINANCE_CASHFLOW_MODEL.md',
  'scripts/generate_schedule_from_estimate.ps1',
  'scripts/demo_assemblies_and_cashflow.ps1',
  'requirements.txt'
)

foreach ($f in $files) {
  if (Test-Path $f) { git add -- $f | Out-Null }
}

# Commit with exact message (continue if nothing to commit)
$MSG = @"
feat(f4-assemblies-cashflow): assemblies engine + benchmarks by project_type + cashflow + schedule bootstrap

Add YAML-driven assemblies and seeds (interior/exterior)

Extend benchmarking to choose band by project_type (CSV)

Introduce cashflow module (weekly) with retainage

Add schedule schema+docs and a generator

Demo script emits ASSEMBLIES_SAMPLE.md and CASHFLOW_SAMPLE.json
"@

try {
  git commit -m $MSG | Out-Null
} catch {
  Write-Host "Commit encountered an issue (possibly no changes). Continuing. $_"
}

# Determine short SHA and tag
$shaShort = (git rev-parse --short HEAD).Trim()
$tag = "chkpt-f4-$shaShort"

# Create/overwrite tag and push
try { git tag -f $tag | Out-Null } catch {}
git push origin master | Out-Null
git push origin --tags | Out-Null

# Write F4 summary
$outDir = "output"
New-Item -ItemType Directory -Force -Path $outDir | Out-Null
$summaryPath = Join-Path $outDir "F4_SUMMARY.md"
$summary = @"
# Sprint F4 Summary

- Assemblies engine + seeds created.
- Benchmarking picks $/SF band by project_type (CSV-backed).
- Cashflow module + schedule schema and generator.
- Demo script emits:
  - output/ASSEMBLIES_SAMPLE.md
  - output/CASHFLOW_SAMPLE.json

Tag: $tag
"@
$summary | Out-File -Encoding UTF8 $summaryPath

Write-Host ("NEW_F4_COMMIT {0} TAG {1}" -f $shaShort, $tag)
