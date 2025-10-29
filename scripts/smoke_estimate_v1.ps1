Param(
[string]$Url = "http://127.0.0.1:8000/v1/estimate",
[string]$InputPath = "scripts/smoke_estimate_v1.json",
[string]$OutJson = "output/ESTIMATE_V1_SMOKE_RESULT.json"
)
$ErrorActionPreference = "Stop"
if (-not (Test-Path "output")) { New-Item -ItemType Directory -Path "output" | Out-Null }
$payload = Get-Content -Raw -Path $InputPath

try {
$resp = curl.exe -s -X POST $Url -H "Content-Type: application/json" --data $payload
if ($LASTEXITCODE -ne 0 -or -not $resp) { throw "curl failed or empty response" }
$resp | Out-File -Encoding UTF8 $OutJson
}
catch {
$respObj = Invoke-RestMethod -Method Post -Uri $Url -Body $payload -ContentType "application/json"
($respObj | ConvertTo-Json -Depth 6) | Out-File -Encoding UTF8 $OutJson
}
Write-Host "Saved: $OutJson"
