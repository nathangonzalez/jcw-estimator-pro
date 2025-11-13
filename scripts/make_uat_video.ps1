param(
    [string]$UatReportJson = "output/uat-report.json",
    [string]$ArtifactsDir = "output/playwright-artifacts",
    [string]$OutputDir = "output/uat",
    [string]$OutputVideo = "UAT_ANNOTATED.mp4",
    [string]$OutputMd = "UAT_ANNOTATED.md"
)

# Ensure output directory exists
if (!(Test-Path $OutputDir)) {
    New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null
}

# Check for ffmpeg
try {
    $ffmpegVersion = & ffmpeg -version 2>&1 | Select-Object -First 1
    if ($LASTEXITCODE -ne 0) { throw "ffmpeg not found" }
    Write-Host "Found ffmpeg: $ffmpegVersion"
} catch {
    $errorContent = @"
# UAT Video Generation Error

**Error:** ffmpeg not found in PATH
**Time:** $(Get-Date -Format o)

Please install ffmpeg:

- Windows: `choco install ffmpeg` or `winget install ffmpeg`
- Download from: https://ffmpeg.org/download.html

Then add to PATH and re-run: `pwsh -File scripts/make_uat_video.ps1`
"@
    $errorContent | Out-File -FilePath "$OutputDir/UAT_VIDEO_ERROR.md" -Encoding utf8
    Write-Error "ffmpeg not found. See $OutputDir/UAT_VIDEO_ERROR.md"
    exit 1
}

# Check for UAT report
if (!(Test-Path $UatReportJson)) {
    $errorContent = @"
# UAT Video Generation Error

**Error:** UAT report not found at $UatReportJson
**Time:** $(Get-Date -Format o)

Run UAT tests first:
```
npx playwright test tests/e2e/uat.interactive.spec.ts --reporter=json
```

This should generate output/uat-report.json
"@
    $errorContent | Out-File -FilePath "$OutputDir/UAT_VIDEO_ERROR.md" -Encoding utf8
    Write-Error "UAT report not found. See $OutputDir/UAT_VIDEO_ERROR.md"
    exit 1
}

# Parse UAT report
try {
    $uatReport = Get-Content $UatReportJson -Raw | ConvertFrom-Json
} catch {
    $errorContent = @"
# UAT Video Generation Error

**Error:** Failed to parse UAT report JSON
**File:** $UatReportJson
**Time:** $(Get-Date -Format o)

Ensure UAT tests completed successfully and generated valid JSON.
"@
    $errorContent | Out-File -FilePath "$OutputDir/UAT_VIDEO_ERROR.md" -Encoding utf8
    Write-Error "Failed to parse UAT report. See $OutputDir/UAT_VIDEO_ERROR.md"
    exit 1
}

# Extract test results
$testResults = @()
foreach ($suite in $uatReport.suites) {
    foreach ($spec in $suite.specs) {
        foreach ($test in $spec.tests) {
            $result = $test.results[0]  # Take first result
            if ($result) {
                $testResults += @{
                    title = $spec.title
                    status = $result.status
                    duration = $result.duration
                    startTime = $result.startTime
                    videoPath = $null  # Will find this
                }
            }
        }
    }
}

Write-Host "Found $($testResults.Count) test results"

# Find video files and match to tests
$videoFiles = Get-ChildItem -Path $ArtifactsDir -Recurse -Include "*.webm", "*.mp4" | Sort-Object LastWriteTime
$concatList = @()
$mdTable = @()

foreach ($test in $testResults) {
    # Find matching video (by timestamp proximity or directory name)
    $matchingVideo = $null
    foreach ($video in $videoFiles) {
        # Simple heuristic: check if video was created around test time
        $testTime = [DateTime]::Parse($test.startTime)
        $videoTime = $video.LastWriteTime
        $timeDiff = [Math]::Abs(($videoTime - $testTime).TotalSeconds)

        if ($timeDiff -lt 300) {  # Within 5 minutes
            $matchingVideo = $video
            break
        }
    }

    if ($matchingVideo) {
        $test.videoPath = $matchingVideo.FullName
        Write-Host "Matched: $($test.title) -> $($matchingVideo.Name)"

        # Create captioned version with Reel V2 graphics
        $tempCaptioned = "$OutputDir/tmp/$([guid]::NewGuid()).mp4"
        New-Item -ItemType Directory -Path "$OutputDir/tmp" -Force | Out-Null

        $project = "JCW Estimator"
        $status = $test.status.ToUpper()
        $duration = [Math]::Round($test.duration / 1000, 1)
        $timestamp = [DateTime]::Parse($test.startTime).ToString("HH:mm:ss")

        # Escape single quotes in title
        $title = $test.title -replace "'", "\'"

        # Lower-thirds captions with enhanced styling
        $statusColor = if ($status -eq "PASSED") { "green" } else { "red" }

        $ffmpegCmd = @"
ffmpeg -i "$($test.videoPath)" -vf "drawtext=text='$project - Test: $title':fontcolor=white:fontsize=36:box=1:boxcolor=black@0.7:boxborderw=10:x=50:y=h-150,drawtext=text='Status: $status':fontcolor=$statusColor:fontsize=28:x=50:y=h-100,drawtext=text='Duration: ${duration}s, Started: $timestamp':fontcolor=white:fontsize=24:x=50:y=h-60" -c:v libx264 -c:a aac -y "$tempCaptioned"
"@

        Write-Host "Creating Reel V2 captioned video: $tempCaptioned"
        Invoke-Expression $ffmpegCmd

        if ($LASTEXITCODE -eq 0) {
            $concatList += "file '$tempCaptioned'"
        }
    } else {
        Write-Host "No video found for: $($test.title)"
    }

    # Add to markdown table
    $videoStatus = if ($test.videoPath) { "✅ Video" } else { "❌ No video" }
    $mdTable += "| $($test.title) | $($test.status) | $videoStatus |"
}

# Create concat file or placeholder video
if ($concatList.Count -gt 0) {
    $concatFile = "$OutputDir/tmp/concat.txt"
    $concatList | Out-File -FilePath $concatFile -Encoding utf8

    # Concatenate videos
    $outputPath = "$OutputDir/$OutputVideo"
    $ffmpegConcat = "ffmpeg -f concat -safe 0 -i `"$concatFile`" -c copy -y `"$outputPath`""
    Write-Host "Concatenating videos to: $outputPath"
    Invoke-Expression $ffmpegConcat

    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Video created: $outputPath"
    } else {
        Write-Error "Failed to concatenate videos"
        exit 1
    }
} else {
    # Create a placeholder video when no real videos exist
    Write-Host "No videos found, creating placeholder video..."
    $outputPath = "$OutputDir/$OutputVideo"

    # Create a simple 5-second black video with text overlay
    $ffmpegPlaceholder = @"
ffmpeg -f lavfi -i color=black:size=1920x1080:duration=5 -vf "drawtext=text='JCW Estimator - UAT Results':fontcolor=white:fontsize=48:x=(w-text_w)/2:y=(h-text_h)/2,drawtext=text='No videos were recorded':fontcolor=yellow:fontsize=24:x=(w-text_w)/2:y=(h+text_h)/2+10" -c:v libx264 -c:a aac -y "$outputPath"
"@

    Invoke-Expression $ffmpegPlaceholder

    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Placeholder video created: $outputPath"
    } else {
        Write-Error "Failed to create placeholder video"
        exit 1
    }
}

# Create markdown receipt
$mdContent = @"
# UAT Annotated Video

**Generated:** $(Get-Date -Format o)
**Source:** $UatReportJson
**Videos:** $($concatList.Count) clips concatenated

## Video Link

[▶️ Open the UAT video]($OutputVideo)

## Test Results

| Test Title | Status | Video |
|------------|--------|-------|
"@

$mdContent += "`n" + ($mdTable -join "`n")

$mdContent | Out-File -FilePath "$OutputDir/$OutputMd" -Encoding utf8

# Clean up temp files
if (Test-Path "$OutputDir/tmp") {
    Remove-Item "$OutputDir/tmp" -Recurse -Force
}

Write-Host "✅ Complete! See $OutputDir/$OutputMd"
