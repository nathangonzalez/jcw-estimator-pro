# run_plan_reader_local.ps1
# DEV-FAST: Posts a local PDF path to /v1/plan/features and writes output/plan_features.sample.json

param(
  [Parameter(Mandatory = $true)]
  [string]$PdfPath,
  [string]$BaseUrl = "http://127.0.0.1:8001"
)

$ErrorActionPreference = "Stop"
New-Item -ItemType Directory -Force -Path "output" | Out-Null

function Test-ApiHealth([string]$url) {
  try {
    $u = "$url/health"
    $r = Invoke-WebRequest -Uri $u -UseBasicParsing -TimeoutSec 3
    return ($r.StatusCode -eq 200)
  } catch { return $false }
}

if (-not (Test-Path $PdfPath)) {
  $msg = "PLAN_READER: PDF path not found: $PdfPath"
  $msg | Out-File -Encoding UTF8 output\plan_features.sample.json
  Write-Host $msg
  exit 2
}

if (-not (Test-ApiHealth $BaseUrl)) {
  $hint = @"
PLAN_READER: API not reachable at $BaseUrl
Hint: start the API and retry:

  python -m uvicorn web.backend.app_comprehensive:app --host 127.0.0.1 --port 8001 --reload
"@
  $hint | Out-File -Encoding UTF8 output\plan_features.sample.json
  Write-Host $hint
  exit 3
}

$Body = @{ pdf_path = $PdfPath } | ConvertTo-Json -Depth 4
$Uri = "$BaseUrl/v1/plan/features"

try {
  $resp = Invoke-RestMethod -Uri $Uri -Method POST -ContentType "application/json; charset=utf-8" -Body $Body
  $json = $resp | ConvertTo-Json -Depth 12
  $json | Out-File -Encoding UTF8 output\plan_features.sample.json
  Write-Host "HTTP: 200 OK"
  Write-Host "Wrote output/plan_features.sample.json"
  exit 0
}
catch {
  if ($_.Exception.Response -ne $null) {
    $status = $_.Exception.Response.StatusCode.value__
    $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
    $errBody = $reader.ReadToEnd()
    $msg = "HTTP: $status`n$errBody"
    $msg | Out-File -Encoding UTF8 output\plan_features.sample.json
    Write-Host $msg
  } else {
    $msg = "HTTP: ERROR`n$($_.Exception.Message)"
    $msg | Out-File -Encoding UTF8 output\plan_features.sample.json
    Write-Host $msg
  }
  exit 1
}
