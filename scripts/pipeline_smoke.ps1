# Starts API on 127.0.0.1:8001 if not running, runs /v1/takeoff (pdf_path),
# feeds its quantities directly into /v1/estimate (M01 body),
# then writes JSON, JUnit, and a tiny HTML summary in /output.

param(
  [string]$ApiHost = "127.0.0.1",
  [int]$ApiPort = 8001,
  [string]$ProjectId = "LYNN-001",
  [string]$PdfPath = "data/blueprints/LYNN-001.sample.pdf",
  [string]$PolicyPath = "schemas/pricing_policy.v0.yaml",
  [string]$UnitCostsCsv = "data/unit_costs.sample.csv",
  [string]$VendorCsv = "data/vendor_quotes.sample.csv"
)

$ErrorActionPreference = "Stop"
New-Item -ItemType Directory -Force -Path output | Out-Null

function Test-Port {
  param([string]$HostName, [int]$Port)
  try { $tcp = New-Object Net.Sockets.TcpClient($HostName,$Port); $tcp.Close(); return $true } catch { return $false }
}

function Wait-HttpOk {
  param([string]$Url, [int]$Retries=30, [int]$DelayMs=500)
  for ($i=0; $i -lt $Retries; $i++) {
    try { $r = Invoke-WebRequest -UseBasicParsing -Uri $Url -TimeoutSec 2; if ($r.StatusCode -ge 200) { return $true } } catch {}
    Start-Sleep -Milliseconds $DelayMs
  }
  return $false
}

$baseUrl = ('http://{0}:{1}' -f $ApiHost, $ApiPort)
$healthUrl = ($baseUrl + '/docs')

if (-not (Test-Port -HostName $ApiHost -Port $ApiPort)) {
  Write-Host "Starting API on $ApiHost:$ApiPort..."
  $uv = Start-Process -PassThru -WindowStyle Hidden `
    python -ArgumentList "-m","uvicorn","web.backend.app_comprehensive:app","--host",$ApiHost,"--port",$ApiPort,"--reload"
  if (-not (Wait-HttpOk -Url $healthUrl)) { throw "API did not become healthy on $healthUrl" }
} else {
  Write-Host "API detected on $ApiHost:$ApiPort — not starting a new one."
}

# 1) TAKEOFF
$takeoffReq = @{ project_id = $ProjectId; pdf_path = $PdfPath } | ConvertTo-Json -Depth 6
$takeoffRespPath = "output/TAKEOFF_RESPONSE.json"
try {
  $takeoffResp = Invoke-RestMethod -Method Post -Uri "$baseUrl/v1/takeoff" -ContentType "application/json" -Body $takeoffReq
  $takeoffResp | ConvertTo-Json -Depth 10 | Out-File -Encoding utf8 $takeoffRespPath
} catch {
  $_ | Out-String | Out-File -Encoding utf8 "output/TAKEOFF_ERROR.log"
  throw "TAKEOFF failed. See output/TAKEOFF_ERROR.log"
}

# 2) ESTIMATE (M01)
$quantities = Get-Content $takeoffRespPath | ConvertFrom-Json
$estimateReqObj = @{
  project_id   = $ProjectId
  region       = "boston.ma"
  policy       = $PolicyPath
  unit_costs_csv = $UnitCostsCsv
  vendor_quotes_csv = $VendorCsv
  quantities   = $quantities
}
$estimateReqJson = $estimateReqObj | ConvertTo-Json -Depth 12
$estimateRespPath = "output/PIPELINE_ESTIMATE_RESPONSE.json"

try {
  $estimateResp = Invoke-RestMethod -Method Post -Uri "$baseUrl/v1/estimate" -ContentType "application/json" -Body $estimateReqJson
  $estimateResp | ConvertTo-Json -Depth 12 | Out-File -Encoding utf8 $estimateRespPath
} catch {
  $_ | Out-String | Out-File -Encoding utf8 "output/ESTIMATE_ERROR.log"
  throw "ESTIMATE failed. See output/ESTIMATE_ERROR.log"
}

# 3) Emit JUnit + HTML summary
function New-JUnit {
  param([string]$SuiteName,[string]$CaseName,[bool]$Success,[string]$OutXml)
  $status = if ($Success) { "" } else { "<failure message=`"pipeline failed`"></failure>" }
  $xml = @"
<testsuite name="$SuiteName" tests="1" failures="${([int](-not $Success))}">
  <testcase classname="$SuiteName" name="$CaseName">
    $status
  </testcase>
</testsuite>
"@
  $xml | Out-File -Encoding utf8 $OutXml
}
function Get-Total {
  try {
    $obj = Get-Content $estimateRespPath | ConvertFrom-Json
    return [double]$obj.totals.grand_total
  } catch { return $null }
}
$total = Get-Total
$ok = $null -ne $total -and $total -gt 0
New-JUnit -SuiteName "pipeline-smoke" -CaseName "plan→takeoff→estimate" -Success:$ok -OutXml "output/PIPELINE_JUNIT.xml"

$summary = @"
<!doctype html>
<html><head><meta charset="utf-8"><title>Pipeline Smoke</title></head>
<body>
  <h1>Pipeline Smoke</h1>
  <ul>
    <li>Project: <code>$ProjectId</code></li>
    <li>Takeoff: <code>$takeoffRespPath</code></li>
    <li>Estimate: <code>$estimateRespPath</code></li>
    <li>Grand Total: <strong>$total</strong></li>
    <li>Status: <strong>$(if($ok){"PASS"}else{"FAIL"})</strong></li>
  </ul>
</body></html>
"@
$summary | Out-File -Encoding utf8 "output/PIPELINE_SUMMARY.html"

Write-Host "Done. Total = $total. JUnit: output/PIPELINE_JUNIT.xml"
