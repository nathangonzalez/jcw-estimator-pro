# run_smoke_m01_local.ps1
# Posts an M01 request to app_comprehensive on http://127.0.0.1:8001/v1/estimate
# Saves JSON response to output/SMOKE_RESPONSE.json

$ErrorActionPreference = "Stop"

# Ensure output dir
New-Item -ItemType Directory -Force -Path "output" | Out-Null

# Load M01 quantities (v0 schema object with trades/items)
$quantities = Get-Content -Raw "data\quantities.sample.json" | ConvertFrom-Json

# Build request body (server will read CSV and policy when given file paths)
$bodyObj = [ordered]@{
  project_id        = "LYNN-001"
  region            = "boston-ma"
  policy            = "schemas/pricing_policy.v0.yaml"   # path string; server reads file
  quantities        = $quantities                         # object; server will flatten v0 trades
  unit_costs_csv    = "data/unit_costs.sample.csv"        # path string; server reads file
  vendor_quotes_csv = "data/vendor_quotes.sample.csv"     # path string; server reads file
}

$bodyJson = $bodyObj | ConvertTo-Json -Depth 16

try {
  $resp = Invoke-RestMethod -Uri "http://127.0.0.1:8001/v1/estimate" -Method Post -ContentType "application/json" -Body $bodyJson
  $out = $resp | ConvertTo-Json -Depth 16
  $out | Out-File -FilePath "output\SMOKE_RESPONSE.json" -Encoding utf8
  Write-Host "HTTP: 200 OK"
  Write-Host "Wrote output/SMOKE_RESPONSE.json"
  exit 0
}
catch {
  if ($_.Exception.Response -ne $null) {
    $status = $_.Exception.Response.StatusCode.value__
    $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
    $errBody = $reader.ReadToEnd()
    $msg = "HTTP: $status`n$errBody"
    $msg | Out-File -FilePath "output\SMOKE_RESPONSE.json" -Encoding utf8
    Write-Host $msg
  } else {
    $msg = "HTTP: ERROR`n$($_.Exception.Message)"
    $msg | Out-File -FilePath "output\SMOKE_RESPONSE.json" -Encoding utf8
    Write-Host $msg
  }
  exit 1
}
