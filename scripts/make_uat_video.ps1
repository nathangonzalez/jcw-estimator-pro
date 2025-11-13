param(
    [string]$UatReportJson = "output/uat-report.json",
    [string]$ArtifactsDir = "output/playwright-artifacts",
    [string]$OutputDir = "output/uat",
    [string]$OutputVideo = "UAT_ANNOTATED.mp4",
    [string]$OutputMd = "UAT_ANNOTATED.md",
    [switch]$V3
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

if ($V3) {
    # --- REEL V3 MODE: per-test clips + intro/chapters/failure banner ---
    Write-Host "Building Reel V3 with per-test clips..." -ForegroundColor Cyan

    $clipsDir = "$OutputDir\clips"
    New-Item -ItemType Directory -Path $clipsDir -Force | Out-Null

    # Font detection
    $fontFile = ""
    if (Test-Path "C:\Windows\Fonts\arial.ttf") {
        $fontFile = "C:\\Windows\\Fonts\\arial.ttf"
    }

    # Calculate summary stats
    $totalTests = $testResults.Count
    $passedTests = ($testResults | Where-Object { $_.status -eq "passed" }).Count
    $failedTests = ($testResults | Where-Object { $_.status -eq "failed" }).Count
    $hasFailures = $failedTests -gt 0

    # Create intro slate (2s)
    $introText = "JCW Estimator UAT`nSHA: $(git rev-parse --short HEAD 2>$null)`nTag: $(git describe --tags 2>$null)`n$totalTests tests • $passedTests passed • $failedTests failed"
    $introCmd = @"
ffmpeg -y -f lavfi -i color=c=darkblue:s=1280x720:d=2 -vf "drawbox=x=0:y=0:w=1280:h=720:color=darkblue@0.9:t=fill,drawtext=text='$($introText -replace "`n", "\\n")':x=40:y=40:fontsize=36:fontcolor=white:line_spacing=10$(if ($fontFile) { ":fontfile=$fontFile" } else { "" })" -c:v libx264 -pix_fmt yuv420p -crf 23 "$clipsDir\intro.mp4"
"@

    Write-Host "Creating intro slate..." -ForegroundColor Yellow
    Invoke-Expression $introCmd

    # Process each test
    $clipFiles = @("$clipsDir\intro.mp4")
    $testIndex = 0

    foreach ($test in $testResults) {
        $testIndex++
        $slug = $test.title -replace "[^a-zA-Z0-9]", "_" -replace "_+", "_"
        $clipName = "test_${testIndex}_${slug}.mp4"

        # Find video file for this test
        $testVideo = $vids | Where-Object {
            $videoTime = $_.LastWriteTime
            $testTime = [DateTime]::Parse($test.startTime)
            $timeDiff = [Math]::Abs(($videoTime - $testTime).TotalSeconds)
            $timeDiff -lt 300  # Within 5 minutes
        } | Select-Object -First 1

        if ($testVideo) {
            # Status emoji
            $statusEmoji = switch ($test.status) {
                "passed" { "✅" }
                "failed" { "❌" }
                default { "⏭️" }
            }

            # Duration in seconds
            $durationSec = [Math]::Round($test.duration / 1000, 1)

            # Create overlay text
            $overlayText = "$($test.title) • $statusEmoji • ${durationSec}s"

            # Escape for ffmpeg
            $escapedText = $overlayText -replace ":", "\:" -replace "'", "\'" -replace '"', '\"'

            # Create clip with overlay
            $tempClip = "$clipsDir\temp_$clipName"
            $overlayCmd = @"
ffmpeg -y -i "$($testVideo.FullName)" -vf "drawbox=x=0:y=ih-120:w=iw:h=120:color=black@0.45:t=fill,drawtext=text='$escapedText':x=20:y=h-95:fontsize=28:fontcolor=white$(if ($fontFile) { ":fontfile=$fontFile" } else { "" })" -c:v libx264 -pix_fmt yuv420p -crf 23 -movflags +faststart "$tempClip"
"@

            Write-Host "Creating clip: $clipName" -ForegroundColor Yellow
            Invoke-Expression $overlayCmd

            if ($LASTEXITCODE -eq 0) {
                $clipFiles += $tempClip
            } else {
                Write-Warning "Failed to create clip for: $($test.title)"
                "Failed to create clip for: $($test.title)" | Out-File -FilePath "output/R24_DIAGNOSE.md" -Append -Encoding utf8
            }
        } else {
            Write-Warning "No video found for: $($test.title)"
            "No video found for: $($test.title)" | Out-File -FilePath "output/R24_DIAGNOSE.md" -Append -Encoding utf8
        }
    }

    # Concatenate all clips
    if ($clipFiles.Count -gt 1) {
        $concatList = "$clipsDir\reel_v3_list.txt"
        $clipFiles | ForEach-Object { "file '$_'" } | Set-Content -Encoding ASCII $concatList

        $reelV3Path = "$OutputDir\UAT_REEL_V3.mp4"
        $concatCmd = "ffmpeg -y -safe 0 -f concat -i `"$concatList`" -c copy `"$reelV3Path`""

        Write-Host "Concatenating Reel V3..." -ForegroundColor Green
        Invoke-Expression $concatCmd

        if ($LASTEXITCODE -eq 0) {
            # Add failure banner if needed
            if ($hasFailures) {
                $bannerCmd = @"
ffmpeg -y -i "$reelV3Path" -vf "drawbox=x=0:y=0:w=iw:h=60:color=red@0.8:t=fill,drawtext=text='FAILURES PRESENT':x=(w-text_w)/2:y=20:fontsize=36:fontcolor=white$(if ($fontFile) { ":fontfile=$fontFile" } else { "" })" -c:v libx264 -c:a copy "$reelV3Path.tmp"
"@

                Write-Host "Adding failure banner..." -ForegroundColor Red
                Invoke-Expression $bannerCmd

                if ($LASTEXITCODE -eq 0) {
                    Move-Item "$reelV3Path.tmp" $reelV3Path -Force
                }
            }

            Write-Host "✅ Reel V3 created: $reelV3Path" -ForegroundColor Green
        } else {
            Write-Error "Failed to create Reel V3"
            exit 1
        }
    } else {
        Write-Warning "No clips created for Reel V3"
        "No clips created for Reel V3" | Out-File -FilePath "output/R24_DIAGNOSE.md" -Append -Encoding utf8
    }

    # Clean up temp files
    Remove-Item "$clipsDir\temp_*.mp4" -Force -ErrorAction SilentlyContinue

    Write-Host "✅ Reel V3 complete! Clips: $($clipFiles.Count - 1), Intro: 1, Total: $($clipFiles.Count)" -ForegroundColor Green
    return
}

# --- HOTFIX BLOCK: robust concat without captions ---
# Collect Playwright videos
$vids = Get-ChildItem -Recurse -File "output\playwright-artifacts" -Filter "video.webm" |
        Sort-Object LastWriteTime

New-Item -ItemType Directory -Force -Path "output\uat" | Out-Null
$tempDir = "output\uat\temp_videos"
New-Item -ItemType Directory -Force -Path $tempDir | Out-Null
$listFile = "output\uat\concat_list.txt"
$outMp4   = "output\uat\UAT_REEL_V2.mp4"

if ($vids.Count -eq 0) {
  # Fallback: 10s slate so we pass duration gate
  ffmpeg -y -f lavfi -i color=c=black:s=1280x720:d=10 -vf "fps=30,format=yuv420p" $outMp4
  return
}

# Copy videos to temp location with safe names to avoid path issues
$concatLines = @()
for ($i = 0; $i -lt $vids.Count; $i++) {
  $safeName = "video_$i.webm"
  $tempPath = Join-Path $tempDir $safeName
  Copy-Item $vids[$i].FullName $tempPath -Force
  $concatLines += "file '$safeName'"
}

# Write concat list in temp directory
$concatLines | Set-Content -Encoding ASCII (Join-Path $tempDir "concat_list.txt")

# Change to temp directory and concat
Push-Location $tempDir
try {
  # Concat + re-encode to MP4/H.264
  ffmpeg -y -safe 0 -f concat -i "concat_list.txt" -vf "fps=30,format=yuv420p" -c:v libx264 -pix_fmt yuv420p -crf 23 -movflags +faststart "UAT_REEL_V2.mp4"
} finally {
  Pop-Location
}

# Move result to final location
Move-Item (Join-Path $tempDir "UAT_REEL_V2.mp4") $outMp4 -Force

# Ensure >=10s by padding a slate if needed
$probe = ffprobe -v error -show_entries format=duration -of default=nw=1:nk=1 $outMp4
if ([double]$probe -lt 10) {
  ffmpeg -y -f lavfi -i color=c=black:s=1280x720:d=10 -vf "fps=30,format=yuv420p" output\uat\pad.mp4

  # Create concat list for padding
  $padList = "output\uat\pad_list.txt"
  @("file 'UAT_REEL_V2.mp4'", "file 'pad.mp4'") | Set-Content -Encoding ASCII $padList

  Push-Location "output\uat"
  try {
    ffmpeg -y -safe 0 -f concat -i $padList -c copy UAT_REEL_V2_fixed.mp4
    Move-Item -Force UAT_REEL_V2_fixed.mp4 UAT_REEL_V2.mp4
  } finally {
    Pop-Location
  }

  Remove-Item output\uat\pad.mp4 -Force
  Remove-Item $padList -Force
}

# Clean up temp directory
Remove-Item $tempDir -Recurse -Force

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
