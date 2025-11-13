param(
    [switch]$SkipCollection,
    [switch]$SkipTrend,
    [switch]$SkipDashboard
)

$ErrorActionPreference = "Stop"

Write-Host "🎯 Starting Demo Metrics Pipeline..." -ForegroundColor Cyan

# Step 1: Collect metrics
if (-not $SkipCollection) {
    Write-Host "📊 Collecting metrics..." -ForegroundColor Yellow
    try {
        & python scripts/metrics_collect.py
        if ($LASTEXITCODE -ne 0) { throw "Metrics collection failed" }
    } catch {
        Write-Host "❌ Metrics collection failed: $($_.Exception.Message)" -ForegroundColor Red
        exit 1
    }
}

# Step 2: Update trends
if (-not $SkipTrend) {
    Write-Host "📈 Updating trends..." -ForegroundColor Yellow
    try {
        & python scripts/metrics_trend_update.py
        if ($LASTEXITCODE -ne 0) { throw "Trend update failed" }
    } catch {
        Write-Host "❌ Trend update failed: $($_.Exception.Message)" -ForegroundColor Red
        exit 1
    }
}

# Step 3: Build dashboard
if (-not $SkipDashboard) {
    Write-Host "🎨 Building dashboard..." -ForegroundColor Yellow
    try {
        & python scripts/metrics_dashboard_build.py
        if ($LASTEXITCODE -ne 0) { throw "Dashboard build failed" }
    } catch {
        Write-Host "❌ Dashboard build failed: $($_.Exception.Message)" -ForegroundColor Red
        exit 1
    }
}

Write-Host "✅ Demo Metrics Pipeline Complete!" -ForegroundColor Green
Write-Host ""
Write-Host "📁 Generated Files:" -ForegroundColor Cyan
Write-Host "  📄 output/metrics/run.json" -ForegroundColor White
Write-Host "  📊 output/metrics/summary.json" -ForegroundColor White
Write-Host "  🎨 output/metrics/dashboard.html" -ForegroundColor White
Write-Host ""
Write-Host "🌐 Dashboard URL (when serving):" -ForegroundColor Cyan
Write-Host "  http://127.0.0.1:8000/output/metrics/dashboard.html" -ForegroundColor White
