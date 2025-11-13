param(
  [string]$PlanPdf = ""
)

$ErrorActionPreference = "Stop"

# Ensure output directories
if (!(Test-Path "output")) { New-Item -ItemType Directory -Path "output" | Out-Null }

# Install dev deps if needed (Playwright + Node types)
if (!(Test-Path "node_modules")) {
  npm init -y | Out-Null
  npm i -D @playwright/test playwright @types/node | Out-Null
  npx playwright install --with-deps | Out-Null
}

# Helper: wait for API health
function Wait-Health {
  param([string]$Url, [int]$TimeoutSec = 30)
  $deadline = (Get-Date).AddSeconds($TimeoutSec)
  while ((Get-Date) -lt $deadline) {
    try {
      $r = Invoke-WebRequest -UseBasicParsing -Uri $Url -TimeoutSec 2
      if ($r.StatusCode -ge 200) { return $true }
    } catch {}
    Start-Sleep -Milliseconds 500
  }
  return $false
}

# Start API (background)
$api = Start-Process -FilePath "python" -ArgumentList "-m","uvicorn","web.backend.app_comprehensive:app","--host","127.0.0.1","--port","8001","--reload" -PassThru `
  -RedirectStandardOutput "output\UVICORN_STDOUT.log" -RedirectStandardError "output\UVICORN_STDERR.log"

# Wait until healthy (best effort)
if (-not (Wait-Health -Url "http://127.0.0.1:8001/health" -TimeoutSec 45)) {
  Write-Host "WARN: API health not detected within timeout; continuing."
}

# Set environment variables for tests
$env:API_URL = "http://127.0.0.1:8001"
$env:UI_URL  = "http://127.0.0.1:8001"

# Pass PLAN_PDF to tests if provided
if ($PlanPdf -ne "") { $env:PLAN_PDF = $PlanPdf }

# Run tests with HTML report + artifacts
npx playwright test --config=playwright.config.ts
$n = $LASTEXITCODE

# Human receipt
@"
# R1 UAT Run

ExitCode: $n
API PID: $($api.Id)
Artifacts:
- output/playwright-report/index.html
- output/playwright-artifacts/
"@ | Out-File output/UAT_RECEIPT.md -Encoding UTF8

# Machine status
@{
  exit_code   = $n
  api_pid     = $api.Id
  report      = "output/playwright-report/index.html"
  artifacts   = "output/playwright-artifacts"
  timestamp   = (Get-Date).ToString("s")
  plan_pdf    = $PlanPdf
} | ConvertTo-Json | Out-File output/UAT_STATUS.json -Encoding UTF8

# Stop API
try { Stop-Process -Id $api.Id -Force } catch {}

exit $n
