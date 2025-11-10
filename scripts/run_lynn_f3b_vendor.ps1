# Lynn F3b — Vendor Calibration & Comparison runner (supervised)
param()

$ErrorActionPreference = 'Stop'

# Supervised execution gate
$approveFlag = 'approvals\EXEC_OK'
$outDir = 'output'
New-Item -ItemType Directory -Force -Path $outDir | Out-Null

if (-not (Test-Path $approveFlag)) {
  $waitPath = Join-Path $outDir 'LYNN_F3B_WAITING.md'
  @"
# Lynn F3b — Waiting for Approval

This run is gated. Create the approval file, then re-run:

PowerShell:
  New-Item -ItemType File -Path approvals/EXEC_OK -Force

Bash:
  mkdir -p approvals && : > approvals/EXEC_OK
"@ | Out-File -Encoding UTF8 $waitPath
  Write-Host "WAITING: create approvals/EXEC_OK to proceed. Wrote $waitPath"
  exit 0
}

# Run compare pipeline
$logPath = Join-Path $outDir 'LYNN_F3B_PIPELINE.log'
$runJson = Join-Path $outDir 'LYNN_F3B_RUN.json'

try {
  $python = 'python'
  $proc = & $python 'scripts/lynn_vendor_compare_v0.py' 2>&1
  $proc | Out-File -Encoding UTF8 $logPath
  # Also persist the printed JSON tail if present
  # Try to parse last JSON block
  $jsonText = $proc | Select-Object -Last 200 | Out-String
  try {
    $obj = $null
    $obj = $jsonText | ConvertFrom-Json -ErrorAction Stop
    ($obj | ConvertTo-Json -Depth 6) | Out-File -Encoding UTF8 $runJson
  } catch {
    # could not parse; write raw
    $jsonText | Out-File -Encoding UTF8 $runJson
  }
  Write-Host ("LYNN_F3B_RUN OK log={0}" -f $logPath)
} catch {
  Write-Host ("LYNN_F3B_RUN FAILED: {0}" -f $_.ToString())
  throw
}
