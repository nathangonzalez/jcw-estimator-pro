# Smoke test for /v1/takeoff (F2)
# Posts a path-based request to /v1/takeoff and writes:
# - output/TAKEOFF_RESPONSE.json
# Server-side extraction steps are appended by the API to: output/TAKEOFF_RUN.log

param(
  [string]$HostA = "http://127.0.0.1:8000",
  [string]$HostB = "http://127.0.0.1:8001",
  [string]$PdfPath = "data\blueprints\LYNN-001.sample.pdf"
)

$ErrorActionPreference = "Stop"
New-Item -ItemType Directory -Force -Path "output" | Out-Null

function Test-Health([string]$baseUrl) {
  try {
    $u = "$baseUrl/health"
    $r = Invoke-WebRequest -Uri $u -UseBasicParsing -TimeoutSec 3
    if ($r.StatusCode -eq 200) { return $true } else { return $false }
  } catch { return $false }
}

# Pick first healthy host
$BaseUrl = $null
if (Test-Health $HostA) { $BaseUrl = $HostA }
elseif (Test-Health $HostB) { $BaseUrl = $HostB }

if (-not $BaseUrl) {
  $msg = @"
TAKEOFF_SMOKE: server not reachable
Hint: start the API and retry

For legacy dev hint:
  uvicorn web.backend.app:app --reload

Recommended for F2 (/v1/takeoff present):
  uvicorn web.backend.app_comprehensive:app --reload
"@
  $msg | Out-File -Encoding UTF8 output\TAKEOFF_RESPONSE.json
  Write-Host $msg
  exit 2
}

# Ensure there is at least a placeholder guidance if the sample PDF is missing
if (-not (Test-Path $PdfPath)) {
  $placeholder = "data\blueprints\LYNN-001.sample.placeholder.txt"
  if (-not (Test-Path $placeholder)) {
    @"
No sample PDF committed.

Drop a local plan PDF at:
  $PdfPath

Then re-run:
  pwsh -File scripts\smoke_takeoff_v1.ps1
"@ | Out-File -Encoding UTF8 $placeholder
  }
}

$Body = [ordered]@{
  project_id = "LYNN-001"
  pdf_path   = $PdfPath
} | ConvertTo-Json -Depth 6

$Uri = "$BaseUrl/v1/takeoff"

try {
  $resp = Invoke-RestMethod -Uri $Uri -Method POST -ContentType "application/json; charset=utf-8" -Body $Body
  $json = $resp | ConvertTo-Json -Depth 12
  $json | Out-File -Encoding UTF8 output\TAKEOFF_RESPONSE.json
  Write-Host "HTTP: 200 OK"
  Write-Host "Wrote output/TAKEOFF_RESPONSE.json"
  exit 0
}
catch {
  if ($_.Exception.Response -ne $null) {
    $status = $_.Exception.Response.StatusCode.value__
    $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
    $errBody = $reader.ReadToEnd()
    $msg = "HTTP: $status`n$errBody"
    $msg | Out-File -Encoding UTF8 output\TAKEOFF_RESPONSE.json
    Write-Host $msg
  } else {
    $msg = "HTTP: ERROR`n$($_.Exception.Message)"
    $msg | Out-File -Encoding UTF8 output\TAKEOFF_RESPONSE.json
    Write-Host $msg
  }
  exit 1
}
