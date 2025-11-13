param(
    [switch]$V3
)

$ErrorActionPreference = "Stop"

function Show-Menu {
    Clear-Host
    Write-Host "=== JCW Estimator Demo Hot Keys ===" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "[A] Run full demo (scripts/demo_run.ps1)" -ForegroundColor White
    Write-Host "[R] Re-record: archive existing reel(s) then re-run demo" -ForegroundColor White
    Write-Host "[C] Build per-test clips + Reel V3 (no UAT run)" -ForegroundColor White
    Write-Host "[F] Overlay finance watermark onto latest reel" -ForegroundColor White
    Write-Host "[S] Serve output/ over HTTP (scripts/serve_output.ps1)" -ForegroundColor White
    Write-Host "[Q] Quit" -ForegroundColor White
    Write-Host ""
    Write-Host "Choose an option:" -NoNewline
}

function Log-Action {
    param([string]$action)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    "$timestamp - $action" | Out-File -FilePath "output/R24_RECEIPT.md" -Append -Encoding utf8
}

do {
    Show-Menu
    $choice = Read-Host

    try {
        switch ($choice.ToUpper()) {
            "A" {
                Write-Host "Running full demo..." -ForegroundColor Green
                Log-Action "Full demo run started"
                & "$PSScriptRoot\demo_run.ps1"
                Log-Action "Full demo run completed"
            }
            "R" {
                Write-Host "Archiving existing reels and re-running demo..." -ForegroundColor Green
                Log-Action "Re-record: archive + demo started"
                & "$PSScriptRoot\reel_archive.ps1"
                & "$PSScriptRoot\demo_run.ps1"
                Log-Action "Re-record: archive + demo completed"
            }
            "C" {
                Write-Host "Building per-test clips + Reel V3..." -ForegroundColor Green
                Log-Action "Per-test clips + Reel V3 build started"
                & "$PSScriptRoot\make_uat_video.ps1" -V3
                Log-Action "Per-test clips + Reel V3 build completed"
            }
            "F" {
                Write-Host "Overlaying finance watermark..." -ForegroundColor Green
                Log-Action "Finance overlay started"
                & "$PSScriptRoot\overlay_finance.ps1"
                Log-Action "Finance overlay completed"
            }
            "S" {
                Write-Host "Starting HTTP server..." -ForegroundColor Green
                Log-Action "HTTP server started"
                & "$PSScriptRoot\serve_output.ps1"
            }
            "Q" {
                Write-Host "Goodbye!" -ForegroundColor Yellow
                break
            }
            default {
                Write-Host "Invalid choice. Press any key to continue..." -ForegroundColor Red
                $null = Read-Host
            }
        }
    } catch {
        Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
        "Error in $choice action: $($_.Exception.Message)" | Out-File -FilePath "output/R24_DIAGNOSE.md" -Append -Encoding utf8
        Write-Host "Press any key to continue..." -ForegroundColor Yellow
        $null = Read-Host
    }

} while ($true)
