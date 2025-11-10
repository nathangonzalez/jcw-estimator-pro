param(
  [string]$ListenHost = "127.0.0.1",
  [int]$Port = 8001
)

if (!(Test-Path "output")) { New-Item -ItemType Directory -Path "output" | Out-Null }

$env:PYTHONPATH = "$PWD"
Write-Host "Starting API on http://$ListenHost`:$Port ..."
python -m uvicorn web.backend.app_comprehensive:app --host $ListenHost --port $Port --reload 2> output\UVICORN_STDERR.log 1> output\UVICORN_STDOUT.log
