# JCW Estimator Pro – Local Playwright env helper (NO-RUN)
# Usage later (when allowed): .\scripts\playwright_env.ps1; pwsh -c "pwsh -File scripts\playwright_env.ps1"

# Core targets
$env:UI_BASE_URL    = "http://localhost:8000"
$env:FRONTEND_ENTRY = "web/frontend/index.html"
$env:PDF_PATH       = "C:\Users\natha\OneDrive\Aquisition Lab\Deals\JC Welton\Post Day 1 Ops\Estimating\Lynn\251020_291 SOD - Building Permit Set.pdf"

Write-Host "UI_BASE_URL    = $env:UI_BASE_URL"
Write-Host "FRONTEND_ENTRY = $env:FRONTEND_ENTRY"
Write-Host "PDF_PATH       = $env:PDF_PATH"
