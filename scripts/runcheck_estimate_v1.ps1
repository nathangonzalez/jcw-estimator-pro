$ErrorActionPreference = "Stop"
function Test-PortOpen {
param([int]$Port=8000)
try { (New-Object Net.Sockets.TcpClient).Connect("127.0.0.1", $Port); return $true } catch { return $false }
}
$serverStartedHere = $false
if (-not (Test-PortOpen -Port 8000)) {
    $serverStartedHere = $true
    Start-Process -WindowStyle Hidden powershell -ArgumentList 'uvicorn web.backend.app_comprehensive:app --host 127.0.0.1 --port 8000' | Out-Null
    
    # Wait for server to be ready by polling the health endpoint
    Write-Host "Waiting for server to start..."
    $ready = $false
    for ($i = 0; $i -lt 15; $i++) { # Wait up to 30 seconds
        try {
            $res = Invoke-WebRequest -Uri "http://127.0.0.1:8000/health" -UseBasicParsing -TimeoutSec 2
            if ($res.StatusCode -eq 200) {
                Write-Host "Server is up."
                $ready = $true
                break
            }
        } catch {
            # Ignore and retry
        }
        Start-Sleep -Seconds 2
    }

    if (-not $ready) {
        throw "Server failed to become healthy within the timeout period."
    }
}
try {
    powershell -ExecutionPolicy Bypass -File "scripts/smoke_estimate_v1.ps1"
} finally {
    if ($serverStartedHere) {
        # Find and stop the process listening on port 8000
        $processId = (Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1).OwningProcess
        if ($processId) {
            Write-Host "Stopping server process with ID $processId..."
            Stop-Process -Id $processId -Force -ErrorAction SilentlyContinue
        }
    }
}
