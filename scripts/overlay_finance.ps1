$ErrorActionPreference = "Stop"

# Try to read finance data
$financeData = $null
$forecastPath = "output/finance/forecast.json"

if (Test-Path $forecastPath) {
    try {
        $financeData = Get-Content $forecastPath -Raw | ConvertFrom-Json
    } catch {
        Write-Warning "Failed to parse finance forecast JSON"
        "Failed to parse finance forecast JSON: $($_.Exception.Message)" | Out-File -FilePath "output/R24_DIAGNOSE.md" -Append -Encoding utf8
    }
} else {
    Write-Warning "Finance forecast not found at $forecastPath"
    "Finance forecast not found at $forecastPath" | Out-File -FilePath "output/R24_DIAGNOSE.md" -Append -Encoding utf8
    exit 0  # Non-fatal
}

if (-not $financeData) {
    Write-Host "No finance data available, skipping overlay" -ForegroundColor Yellow
    exit 0
}

# Find latest reel (prefer V3, else V2, else annotated)
$reelPath = $null
$possibleReels = @(
    "output\uat\UAT_REEL_V3.mp4",
    "output\uat\UAT_REEL_V2.mp4",
    "output\uat\UAT_ANNOTATED.mp4"
)

foreach ($reel in $possibleReels) {
    if (Test-Path $reel) {
        $reelPath = $reel
        break
    }
}

if (-not $reelPath) {
    Write-Warning "No reel found to overlay finance data on"
    "No reel found to overlay finance data on" | Out-File -FilePath "output/R24_DIAGNOSE.md" -Append -Encoding utf8
    exit 0
}

# Extract finance metrics
$cashOnHand = $financeData.cash_on_hand
$monthlyBurn = $financeData.monthly_burn
$runwayMonths = $financeData.runway_months

if (-not ($cashOnHand -and $monthlyBurn -and $runwayMonths)) {
    Write-Warning "Incomplete finance data, skipping overlay"
    "Incomplete finance data (missing cash_on_hand, monthly_burn, or runway_months)" | Out-File -FilePath "output/R24_DIAGNOSE.md" -Append -Encoding utf8
    exit 0
}

# Format overlay text
$cashFormatted = if ($cashOnHand -ge 1000000) {
    "$([Math]::Round($cashOnHand / 1000000, 1))M"
} elseif ($cashOnHand -ge 1000) {
    "$([Math]::Round($cashOnHand / 1000, 0))k"
} else {
    "$([Math]::Round($cashOnHand, 0))"
}

$burnFormatted = if ($monthlyBurn -ge 1000000) {
    "$([Math]::Round($monthlyBurn / 1000000, 1))M"
} elseif ($monthlyBurn -ge 1000) {
    "$([Math]::Round($monthlyBurn / 1000, 0))k"
} else {
    "$([Math]::Round($monthlyBurn, 0))"
}

$overlayText = "Runway ${runwayMonths}mo • Burn $${burnFormatted}/mo • Cash $${cashFormatted}"

# Font detection
$fontFile = ""
if (Test-Path "C:\Windows\Fonts\arial.ttf") {
    $fontFile = "C:\\Windows\\Fonts\\arial.ttf"
}

# Escape for ffmpeg
$escapedText = $overlayText -replace ":", "\:" -replace "'", "\'" -replace '"', '\"'

# Create overlay
$tempOutput = "$reelPath.tmp"
$overlayCmd = @"
ffmpeg -y -i "$reelPath" -vf "drawbox=x=0:y=ih-80:w=iw:h=80:color=black@0.7:t=fill,drawtext=text='$escapedText':x=20:y=h-50:fontsize=24:fontcolor=white$(if ($fontFile) { ":fontfile=$fontFile" } else { "" })" -c:v libx264 -c:a copy "$tempOutput"
"@

Write-Host "Overlaying finance data: $overlayText" -ForegroundColor Green
Invoke-Expression $overlayCmd

if ($LASTEXITCODE -eq 0) {
    Move-Item $tempOutput $reelPath -Force
    Write-Host "✅ Finance overlay applied to $reelPath" -ForegroundColor Green

    # Log success
    "Finance overlay applied: $overlayText" | Out-File -FilePath "output/R24_RECEIPT.md" -Append -Encoding utf8
} else {
    Write-Error "Failed to apply finance overlay"
    "Failed to apply finance overlay" | Out-File -FilePath "output/R24_DIAGNOSE.md" -Append -Encoding utf8
    if (Test-Path $tempOutput) {
        Remove-Item $tempOutput -Force
    }
    exit 1
}
