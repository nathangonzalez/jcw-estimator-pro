# JCW | Run LYNN RAW ESTIMATE (plans -> quantities -> priced) with logging and commit
# Mode: execute. No vendor quotes. Optional Playwright E2E (non-blocking).

param(
  [string]$PdfPath = "C:\Users\natha\OneDrive\Aquisition Lab\Deals\JC Welton\Post Day 1 Ops\Estimating\Lynn\251020_291 SOD - Building Permit Set.pdf",
  [string]$ApiHost = "127.0.0.1"
)

$ErrorActionPreference = "Stop"
New-Item -ItemType Directory -Force -Path output | Out-Null
$runtimeLog = "output\EXEC_RUNTIME.log"
$summaryMd  = "output\RUN_SUMMARY.md"
$stdoutLog  = "output\SMOKE_STDOUT.log"
$baseUrl    = $null
$portUsed   = $null
$timeStart  = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
$stopAfterTakeoff = $false

function Append-Log($msg) {
  $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
  "$ts $msg" | Out-File -FilePath $runtimeLog -Encoding UTF8 -Append
}

function Test-Port {
  param([string]$HostName, [int]$Port)
  try { $tcp = New-Object Net.Sockets.TcpClient($HostName, $Port); $tcp.Close(); return $true } catch { return $false }
}

function Wait-HttpOk {
  param([string]$Url, [int]$TimeoutSec=60)
  $deadline = (Get-Date).AddSeconds($TimeoutSec)
  while ((Get-Date) -lt $deadline) {
    try {
      $r = Invoke-WebRequest -UseBasicParsing -Uri $Url -TimeoutSec 2
      if ($r.StatusCode -ge 200) { return $true }
    } catch {}
    Start-Sleep -Milliseconds 500
  }
  return $false
}

# STEP 0: Ensure environment
Append-Log "STEP0: pip install -r requirements.txt"
try {
  python -m pip install -r requirements.txt | Out-Null
} catch {
  Append-Log "pip install failed: $($_.Exception.Message)"; throw
}
if (-not (Test-Path $PdfPath)) {
  Append-Log "PDF not found at: $PdfPath"; throw "PDF not found: $PdfPath"
}

# STEP 1: Start API (try 8001 then 8002)
$ports = @(8001,8002)
foreach ($p in $ports) {
  if (-not (Test-Port -HostName $ApiHost -Port $p)) {
    $portUsed = $p
    break
  }
}
if (-not $portUsed) {
  # both in use; prefer 8001 anyway
  $portUsed = 8001
}
$baseUrl = "http://$ApiHost`:$portUsed"
$healthUrl = "$baseUrl/health"

if (-not (Test-Port -HostName $ApiHost -Port $portUsed)) {
  Append-Log "Starting API at $baseUrl ..."
  $uv = Start-Process -PassThru -WindowStyle Hidden `
    -FilePath python `
    -ArgumentList "-m","uvicorn","web.backend.app_comprehensive:app","--host",$ApiHost,"--port",$portUsed,"--reload" `
    -RedirectStandardOutput "output\UVICORN_STDOUT.log" `
    -RedirectStandardError "output\UVICORN_STDERR.log"
  if (-not (Wait-HttpOk -Url $healthUrl -TimeoutSec 90)) {
    Append-Log "API failed to become healthy at $healthUrl"
    throw "API did not become healthy"
  }
} else {
  Append-Log "API already running at $baseUrl"
}

"API_READY: $baseUrl" | Out-File -FilePath $runtimeLog -Encoding UTF8 -Append

# STEP 2: TAKEOFF
$takeoffReqJson = @{ project_id = "LYNN-001"; pdf_path = $PdfPath } | ConvertTo-Json -Depth 6
$takeoffUri = "$baseUrl/v1/takeoff"
$takeoffStatus = $null
try {
  $resp = Invoke-WebRequest -Method Post -Uri $takeoffUri -ContentType "application/json; charset=utf-8" -Body $takeoffReqJson
  $takeoffStatus = [int]$resp.StatusCode
  $resp.Content | Out-File -Encoding UTF8 "output\TAKEOFF_RESPONSE.json"
  Append-Log "TAKEOFF HTTP $takeoffStatus -> output\TAKEOFF_RESPONSE.json"
} catch {
  $takeoffStatus = if ($_.Exception.Response) { $_.Exception.Response.StatusCode.value__ } else { -1 }
  $errBody = ""
  if ($_.Exception.Response) {
    $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
    $errBody = $reader.ReadToEnd()
  } else { $errBody = $_.Exception.Message }
  $errBody | Out-File -Encoding UTF8 "output\TAKEOFF_ERROR.json"
  Append-Log "TAKEOFF ERROR HTTP $takeoffStatus -> output\TAKEOFF_ERROR.json"
  # Stop here per spec (but still commit later)
  $stopAfterTakeoff = $true
}

if (-not $stopAfterTakeoff) {
# STEP 3: ESTIMATE (RAW — no vendor quotes)
$takeoffJson = Get-Content "output\TAKEOFF_RESPONSE.json" -Raw | ConvertFrom-Json
$estimateReqObj = [ordered]@{
  project_id      = "LYNN-001"
  region          = "Boston"
  policy          = "schemas/pricing_policy.v0.yaml"
  unit_costs_csv  = "data/unit_costs.sample.csv"
  quantities      = $takeoffJson
}
$estimateReqJson = $estimateReqObj | ConvertTo-Json -Depth 20
$estimateUri = "$baseUrl/v1/estimate"
$estimateStatus = $null
try {
  $resp2 = Invoke-WebRequest -Method Post -Uri $estimateUri -ContentType "application/json; charset=utf-8" -Body $estimateReqJson
  $estimateStatus = [int]$resp2.StatusCode
  $resp2.Content | Out-File -Encoding UTF8 "output\PIPELINE_ESTIMATE_RESPONSE.json"
  Append-Log "ESTIMATE HTTP $estimateStatus -> output\PIPELINE_ESTIMATE_RESPONSE.json"
} catch {
  $estimateStatus = if ($_.Exception.Response) { $_.Exception.Response.StatusCode.value__ } else { -1 }
  $errBody2 = ""
  if ($_.Exception.Response) {
    $reader2 = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
    $errBody2 = $reader2.ReadToEnd()
  } else { $errBody2 = $_.Exception.Message }
  $errBody2 | Out-File -Encoding UTF8 "output\PIPELINE_ESTIMATE_ERROR.json"
  Append-Log "ESTIMATE ERROR HTTP $estimateStatus -> output\PIPELINE_ESTIMATE_ERROR.json"
}

# Emit flat CSV summary (best-effort)
try {
  $outDir = "output\LYNN-001\raw_estimate"
  New-Item -ItemType Directory -Force -Path $outDir | Out-Null
  $estObj = Get-Content "output\PIPELINE_ESTIMATE_RESPONSE.json" -Raw | ConvertFrom-Json
  $items = @()
  if ($estObj.line_items) {
    $items = $estObj.line_items
  } elseif ($estObj.trades) {
    foreach ($tb in ($estObj.trades)) {
      if ($tb.line_items) { $items += $tb.line_items }
    }
  }
  $csvPath = Join-Path $outDir "estimate_lines.csv"
  "trade,item,qty,unit,unit_cost,ext_cost,notes" | Out-File -Encoding UTF8 $csvPath
  foreach ($li in $items) {
    $trade = $li.trade

    # item selection (first non-empty of code, item, description)
    $item = ""
    if ($li.code) { $item = $li.code }
    elseif ($li.item) { $item = $li.item }
    elseif ($li.description) { $item = $li.description }

    # qty
    $qty = 0.0
    if ($null -ne $li.qty -and $li.qty -ne "") {
      try { $qty = [double]$li.qty } catch { $qty = 0.0 }
    }

    # unit
    $unit = ""
    if ($li.uom) { $unit = $li.uom }
    elseif ($li.unit) { $unit = $li.unit }

    # unit cost
    $ucost = 0.0
    if ($null -ne $li.unit_cost -and $li.unit_cost -ne "") {
      try { $ucost = [double]$li.unit_cost } catch { $ucost = 0.0 }
    }

    # extended cost
    $ext = 0.0
    if ($null -ne $li.total -and $li.total -ne "") {
      try { $ext = [double]$li.total } catch { $ext = [double]($qty * $ucost) }
    } else {
      $ext = [double]($qty * $ucost)
    }

    # notes
    $notes = ""
    if ($li.notes) { $notes = [string]$li.notes }

    $line  = ('"{0}","{1}",{2},"{3}",{4},{5},"{6}"' -f $trade, $item.Replace('"','""'), $qty, $unit, $ucost, $ext, ($notes.Replace("`n"," ").Replace('"','""')))
    $line | Out-File -Encoding UTF8 -Append $csvPath
  }
  Append-Log "CSV summary -> $csvPath"
} catch {
  Append-Log "CSV summary error: $($_.Exception.Message)"
}

}
# STEP 4: OPTIONAL Playwright E2E (non-blocking)
try {
  $nodeVersion = & node -v 2>$null
  if ($LASTEXITCODE -eq 0 -and $nodeVersion) {
    Append-Log "Node detected ($nodeVersion), attempting Playwright E2E (non-blocking)"
    if (Test-Path "package-lock.json") { npm ci | Out-Null } else { npm install | Out-Null }
    try { npx playwright install --with-deps | Out-Null } catch {}
    try {
      if (Test-Path "package.json") {
        # prefer script if exists; else fallback
        npm run e2e 2>&1 | Tee-Object -FilePath "output\PLAYWRIGHT_SUMMARY.md"
      }
    } catch {
      "Playwright run failed (non-blocking): $($_.Exception.Message)" | Out-File -FilePath "output\PLAYWRIGHT_SUMMARY.md" -Encoding UTF8
    }
  } else {
    Append-Log "Node not detected; skipping Playwright"
  }
} catch {
  Append-Log "Playwright section error (ignored): $($_.Exception.Message)"
}

# STEP 5: LOGS & SUMMARY
Append-Log "BaseURL used: $baseUrl ; TAKEOFF=$takeoffStatus ; ESTIMATE=$estimateStatus"
if (Test-Path "output\TAKEOFF_RUN.log") {
  try {
    Get-Content "output\TAKEOFF_RUN.log" -Raw | Out-File -Append -Encoding UTF8 $stdoutLog
    Append-Log "Appended server extraction log to $stdoutLog"
  } catch {}
}

# Build RUN_SUMMARY.md
try {
  $totalCost = ""
  if (Test-Path "output\PIPELINE_ESTIMATE_RESPONSE.json") {
    $eobj = Get-Content "output\PIPELINE_ESTIMATE_RESPONSE.json" -Raw | ConvertFrom-Json
    if ($eobj.grand_total) { $totalCost = [string]$eobj.grand_total }
    elseif ($eobj.totals -and $eobj.totals.grand_total) { $totalCost = [string]$eobj.totals.grand_total }
  }
  $summary = @"
# RUN SUMMARY — LYNN RAW ESTIMATE

- API base: $baseUrl
- TAKEOFF status: $takeoffStatus
- ESTIMATE status: $estimateStatus
- Artifacts:
  - output/TAKEOFF_RESPONSE.json
  - output/PIPELINE_ESTIMATE_RESPONSE.json
  - output/LYNN-001/raw_estimate/estimate_lines.csv
  - output/PLAYWRIGHT_SUMMARY.md (optional)
  - output/EXEC_RUNTIME.log
  - output/SMOKE_STDOUT.log
- Total cost (if present): $totalCost

"@
  $summary | Out-File -Encoding UTF8 $summaryMd
} catch {
  Append-Log "RUN_SUMMARY error: $($_.Exception.Message)"
}


# STEP 6: COMMIT RESULTS
try {
  git add "output/TAKEOFF_RESPONSE.json" `
          "output/TAKEOFF_ERROR.json" `
          "output/PIPELINE_ESTIMATE_RESPONSE.json" `
          "output/PIPELINE_ESTIMATE_ERROR.json" `
          "output/LYNN-001/raw_estimate/estimate_lines.csv" `
          "output/PLAYWRIGHT_SUMMARY.md" `
          "output/playwright-report" `
          "output/SMOKE_STDOUT.log" `
          "output/EXEC_RUNTIME.log" `
          "output/RUN_SUMMARY.md" 2>$null
  git add output | Out-Null
  git commit -m "feat(lynn-raw): raw estimate from plans (no quotes) + logs + optional e2e report" | Out-Null
  git push origin master | Out-Null
  Append-Log "Committed and pushed results."
} catch {
  Append-Log "Commit/push error (continuing): $($_.Exception.Message)"
}

Append-Log "DONE start=$timeStart end=$(Get-Date -Format "yyyy-MM-dd HH:mm:ss") port=$portUsed"
Write-Host "DONE. See $summaryMd and $runtimeLog"
