# scripts/audit_m01.ps1
# Purpose: Read-only M01 audit. No servers, no HTTP, no installs. Produces artifacts under /output.
# Exits nonzero if any required file missing or invalid.

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location (Resolve-Path "$root\..")

$required = @(
  "schemas\trade_quantities.schema.json",
  "schemas\estimate_response.schema.json",
  "schemas\pricing_policy.v0.yaml",
  "data\quantities.sample.json",
  "openapi\contracts\estimate.v1.contract.json",
  "web\backend\schemas.py",
  "web\backend\app_comprehensive.py",
  "tests\contract\test_estimate_v1_contract.py",
  "docs\JCW_SUITE_BIGPICTURE.md"
)

$missing = @()
foreach ($p in $required) { if (-not (Test-Path $p)) { $missing += $p } }

New-Item -ItemType Directory -Force -Path output | Out-Null
$audit = "output\M01_AUDIT.md"
$status = "output\M01_STATUS.json"

function HashFile($path) {
  if (Test-Path $path) { (Get-FileHash $path -Algorithm SHA256).Hash } else { "" }
}

# Basic JSON/YAML parse checks (PowerShell-native)
$jsonFiles = @(
  "schemas\trade_quantities.schema.json",
  "schemas\estimate_response.schema.json",
  "data\quantities.sample.json",
  "openapi\contracts\estimate.v1.contract.json"
)
$yamlFiles = @("schemas\pricing_policy.v0.yaml")

$jsonErrors = @()
foreach ($jf in $jsonFiles) {
  try { Get-Content $jf -Raw | ConvertFrom-Json | Out-Null } catch { $jsonErrors += "$jf : $($_.Exception.Message)" }
}

# Lightweight YAML check: ensure file non-empty and contains a top-level key-ish pattern
$yamlErrors = @()
foreach ($yf in $yamlFiles) {
  try {
    $txt = Get-Content $yf -Raw
    if ([string]::IsNullOrWhiteSpace($txt) -or ($txt -notmatch "^\s*\w+:\s")) { throw "YAML looks empty or lacks top-level key" }
  } catch { $yamlErrors += "$yf : $($_.Exception.Message)" }
}

# Verify /v1/estimate dual-shape shims referenced in app and schemas.py
$app = Get-Content "web\backend\app_comprehensive.py" -Raw
$schemasPy = Get-Content "web\backend\schemas.py" -Raw

$dualSignals = @{
  app_has_v1     = ($app -match "/v1/estimate");
  app_pref_M01   = ($app -match "quantities" -and $app -match "prefer" -or $app -match "warning" -or $app -match "legacy");
  schemas_has_legacy = ($schemasPy -match "Legacy" -or $schemasPy -match "area_sqft");
  schemas_has_M01 = ($schemasPy -match "quantities" -and $schemasPy -match "EstimateRequest");
}

# Summarize file hashes
$hashes = @()
foreach ($p in $required) {
  $hashes += [pscustomobject]@{ path = $p; sha256 = (HashFile $p) }
}

# Write audit markdown
@"
# M01 Read-Only Audit

## Required Files
$(
  if ($missing.Count -eq 0) { "- All required files present." } else { ($missing | ForEach-Object { "- MISSING: $_" }) -join "`n" }
)

## JSON Parse Check
$(
  if ($jsonErrors.Count -eq 0) { "- All JSON files parsed OK." } else { ($jsonErrors | ForEach-Object { "- ERROR: $_" }) -join "`n" }
)

## YAML Check
$(
  if ($yamlErrors.Count -eq 0) { "- YAML structure looks OK (light check)." } else { ($yamlErrors | ForEach-Object { "- ERROR: $_" }) -join "`n" }
)

## Dual-Shape Endpoint Signals (heuristic grep)
- app has /v1/estimate: $($dualSignals.app_has_v1)
- app indicates M01 preference / legacy warning: $($dualSignals.app_pref_M01)
- schemas.py shows Legacy shim: $($dualSignals.schemas_has_legacy)
- schemas.py shows M01 shim: $($dualSignals.schemas_has_M01)

## File Hashes (SHA-256)
$(
  $hashes | ForEach-Object { "- $($_.path)  ::  $($_.sha256)" } | Out-String
)
"@ | Out-File -Encoding UTF8 $audit

# Machine-readable status
$statusObj = [pscustomobject]@{
  module = "M01"
  mode = "sync-only"
  missing = $missing
  json_errors = $jsonErrors
  yaml_errors = $yamlErrors
  dual_signals = $dualSignals
  ok = ($missing.Count -eq 0 -and $jsonErrors.Count -eq 0 -and $yamlErrors.Count -eq 0 -and $dualSignals.app_has_v1 -and $dualSignals.schemas_has_M01)
}
$statusObj | ConvertTo-Json -Depth 6 | Out-File -Encoding UTF8 $status

Write-Host "Audit complete. See $audit and $status."
if (-not $statusObj.ok) { exit 2 }
