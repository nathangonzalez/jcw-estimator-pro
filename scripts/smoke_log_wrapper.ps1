# Smoke wrapper: runs scripts/smoke_estimate_v1.ps1 and captures console output to output/SMOKE_STDOUT.log
$ErrorActionPreference = "Continue"

# Ensure output directory exists
New-Item -ItemType Directory -Force -Path "output" | Out-Null

$logPath = "output\SMOKE_STDOUT.log"

# Start transcript to capture all console output (stdout/stderr)
try {
  Start-Transcript -Path $logPath -Force | Out-Null
} catch {
  # Fallback: if transcript fails, just proceed without it
}

try {
  & ".\scripts\smoke_estimate_v1.ps1"
} finally {
  try { Stop-Transcript | Out-Null } catch {}
}
