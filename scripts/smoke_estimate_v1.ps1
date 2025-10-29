# Run FastAPI (adjust if you use different entry)
$env:PYTHONPATH="."
$process = Start-Process -NoNewWindow -FilePath "python" -ArgumentList "-m", "web.backend.app_comprehensive" -PassThru

# Give server a moment (or use uvicorn if you prefer)
Start-Sleep -Seconds 2

# Smoke POST
$payload = @{
  area_sqft = 2500
  bedrooms = 3
  bathrooms = 2.5
  quality = "standard"
  complexity = 3
  location_zip = "02139"
  features = @{ garage = $true }
} | ConvertTo-Json

try {
  $res = Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8000/v1/estimate" -ContentType "application/json" -Body $payload
  $res | ConvertTo-Json -Depth 6 | Set-Content -Encoding UTF8 "output/SMOKE_ESTIMATE_V1.json"
} catch {
  $_ | Out-String | Set-Content -Encoding UTF8 "output/SMOKE_ESTIMATE_V1_ERROR.txt"
} finally {
    Stop-Process -Id $process.Id
}
