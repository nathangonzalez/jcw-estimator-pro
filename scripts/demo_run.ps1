param(
    [string]$PlanPdf = "data/blueprints/LYNN-001.sample.pdf"
)

$ErrorActionPreference = "Stop"

Write-Host "Starting JCW Estimator Demo..."
Write-Host "================================"

# Kill any stale API processes
Get-Process -Name "python" -ErrorAction SilentlyContinue | Where-Object {
    $_.CommandLine -like "*uvicorn*app_comprehensive*"
} | Stop-Process -Force -ErrorAction SilentlyContinue

# Start fresh API
Write-Host "Starting API server..."
$api = Start-Process -FilePath "python" -ArgumentList "-m","uvicorn","web.backend.app_comprehensive:app","--host","127.0.0.1","--port","8001","--reload" -PassThru -WindowStyle Hidden

# Wait for health
$healthy = $false
for ($i = 0; $i -lt 30; $i++) {
    try {
        $response = Invoke-WebRequest -Uri "http://127.0.0.1:8001/health" -TimeoutSec 2
        if ($response.StatusCode -eq 200) {
            $healthy = $true
            break
        }
    } catch {}
    Start-Sleep -Seconds 1
}

if (-not $healthy) {
    Write-Error "API failed to start"
    exit 1
}

Write-Host "API ready at http://127.0.0.1:8001"

# Run UAT
Write-Host "Running UAT tests..."
& "$PSScriptRoot\uat_run.ps1" -PlanPdf $PlanPdf
$uatExit = $LASTEXITCODE

# Generate video
Write-Host "Generating video reel..."
& "$PSScriptRoot\make_uat_video.ps1"

# Generate metrics and dashboard
Write-Host "Generating analytics dashboard..."
& "$PSScriptRoot\demo_metrics.ps1"

# Serve results
Write-Host "Serving demo results..."
Write-Host "   Video: http://127.0.0.1:8000/output/uat/UAT_ANNOTATED.mp4"
Write-Host "   Report: http://127.0.0.1:8000/output/playwright-report/index.html"
& "$PSScriptRoot\serve_output.ps1"

# Cleanup
Stop-Process -Id $api.Id -Force -ErrorAction SilentlyContinue
Write-Host "Demo complete! UAT exit code: $uatExit"
