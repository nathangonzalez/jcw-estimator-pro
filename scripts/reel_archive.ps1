$ErrorActionPreference = "Stop"

# Create history directory with timestamp
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$historyDir = "output\uat\_history\$timestamp"

New-Item -ItemType Directory -Path $historyDir -Force | Out-Null

$movedCount = 0

# Files to archive
$filesToArchive = @(
    "output\uat\UAT_REEL_V3.mp4",
    "output\uat\UAT_REEL_V2.mp4",
    "output\uat\UAT_ANNOTATED.mp4"
)

foreach ($file in $filesToArchive) {
    if (Test-Path $file) {
        $fileName = Split-Path $file -Leaf
        Move-Item $file "$historyDir\$fileName" -Force
        $movedCount++
        Write-Host "Archived: $fileName" -ForegroundColor Green
    }
}

# Archive clips directory if it exists
$clipsDir = "output\uat\clips"
if (Test-Path $clipsDir) {
    $clipsDest = "$historyDir\clips"
    Move-Item $clipsDir $clipsDest -Force
    $movedCount++
    Write-Host "Archived: clips/ directory" -ForegroundColor Green
}

Write-Host "Archived $movedCount items to $historyDir" -ForegroundColor Cyan

# Log to receipt
"Archived $movedCount items to $timestamp" | Out-File -FilePath "output/R24_RECEIPT.md" -Append -Encoding utf8
