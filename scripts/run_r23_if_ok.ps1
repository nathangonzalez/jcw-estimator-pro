Param(
  [string]$GateFile = "prompts/OK_TO_EXECUTE_R2_3.md"
)

$ErrorActionPreference = "Stop"
if (-not (Test-Path $GateFile)) {
  Write-Host "[R2.3] Gate missing: $GateFile"
  exit 0
}
$content = Get-Content $GateFile -Raw
if ($content -match '(?im)^\s*status\s*:\s*APPROVED\s*$') {
  Write-Host "[R2.3] Gate APPROVED. Running demo…"
} else {
  Write-Host "[R2.3] Gate NOT approved. Skipping."
  exit 0
}

# Ensure output dirs
New-Item -ItemType Directory -Force -Path output | Out-Null
New-Item -ItemType Directory -Force -Path output\uat | Out-Null

# Run the one-click demo script if present; else no-op receipt
if (Test-Path "scripts/demo_run.ps1") {
  & "$PSScriptRoot\demo_run.ps1"
} else {
  "demo_run.ps1 missing; wrote placeholder receipt" | Out-File -Encoding utf8 output\R23_DEMO_ERROR.md
  exit 1
}
