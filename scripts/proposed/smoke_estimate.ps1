# PowerShell smoke test (no-run until /approvals/EXEC_OK exists)
param(
  [string]$Port = "8001"
)
$ErrorActionPreference = "Stop"
$body = @{
    "project_name" = "smoke"
    "square_feet"  = 2000
    "bedrooms"     = 3
    "bathrooms"    = 2
    "quality_level"= "standard"
} | ConvertTo-Json
$env:PYTHONPATH="."
python -m venv .venv
. .\.venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt
$env:PORT=$Port
Start-Process -FilePath "uvicorn" -ArgumentList "web.backend.app_comprehensive:app","--port",$Port,"--host","127.0.0.1" -PassThru | Tee-Object -Variable serverProc | Out-Null
Start-Sleep -Seconds 5
$resp = Invoke-RestMethod -Method POST -Uri "http://127.0.0.1:$Port/v1/estimate" -ContentType "application/json" -Body $body
"SMOKE_OK: $($resp | ConvertTo-Json -Depth 4)" | Out-File -FilePath "output/EXEC_RESULT.md" -Encoding utf8
Stop-Process -Id $serverProc.Id -Force
