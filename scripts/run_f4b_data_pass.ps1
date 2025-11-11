# Run F4b Data Pass: parse vendor PDFs -> train calibration -> calibrated estimate -> dashboard -> (optional) commit
[CmdletBinding()]
param(
  [ValidateSet('All','Parse','Train','Calibrated','Dashboard')]
  [string]$Step = 'All',
  [switch]$Commit
)

$ErrorActionPreference = 'Stop'

# Always use Windows PowerShell executable on this host (avoid pwsh detection issues)
$PSExe = 'powershell'

# Paths
$outDir   = 'output'
$workDir  = 'data/lynn/working'
$logPath  = Join-Path $outDir 'LYNN_F4B_PIPELINE.log'
$errPath  = Join-Path $outDir 'LYNN_F4B_ERROR.md'
$summary  = Join-Path $outDir 'RUN_SUMMARY.md'

New-Item -ItemType Directory -Force -Path $outDir  | Out-Null
New-Item -ItemType Directory -Force -Path $workDir | Out-Null

function Invoke-Step {
  param(
    [Parameter(Mandatory=$true)][string]$Name,
    [Parameter(Mandatory=$true)][string]$ScriptPath
  )
  Write-Host ("== {0} ==" -f $Name)
  try {
    & $PSExe -NoProfile -ExecutionPolicy Bypass -File $ScriptPath 2>&1 | Tee-Object -FilePath $logPath -Append
  } catch {
    $msg = "STEP FAILED: $Name`n$($_.Exception.Message)"
    Write-Host $msg
    $lines = @(
      "# LYNN F4B PIPELINE ERROR",
      "",
      "**Step:** $Name",
      "**When:** $(Get-Date -Format o)",
      "",
      "````",
      $($_ | Out-String),
      "````"
    )
    $lines -join "`n" | Out-File -Encoding UTF8 $errPath
    # Continue to allow later steps or summary to run
  }
}

function Get-FactorsCount {
  $modelPath = 'models/calibration/lynn_v0.json'
  if (-not (Test-Path $modelPath)) { return 0 }
  try {
    $j = Get-Content -Raw $modelPath | ConvertFrom-Json
    if ($null -eq $j -or $null -eq $j.factors) { return 0 }
    # ConvertFrom-Json yields PSCustomObject; count NoteProperty members
    try {
      $props = $j.factors.PSObject.Properties
      if ($props) { return ($props | Measure-Object).Count }
    } catch {}
    # Fallback if it's a hashtable in some environments
    try {
      return ($j.factors.Keys | Measure-Object).Count
    } catch {
      return 0
    }
  } catch { return 0 }
}

function Get-CanonicalRowCount {
  $canon = Join-Path $workDir 'vendor_quotes.canonical.csv'
  if (-not (Test-Path $canon)) { return 0 }
  try {
    $rows = Import-Csv -Path $canon
    # Count only rows with trade,item,quoted_total>0
    $valid = 0
    foreach ($r in $rows) {
      $trade = ($r.trade  | ForEach-Object { $_.Trim().ToLower() })
      $item  = ($r.item   | ForEach-Object { $_.Trim().ToLower() })
      $qtRaw = if ($r.PSObject.Properties['quoted_total']) { $r.quoted_total } else { $r.line_total }
      $qt = 0.0
      try { $qt = [double]($qtRaw -replace '[\$,]', '') } catch { $qt = 0.0 }
      if ($trade -and $item -and ($qt -gt 0)) { $valid++ }
    }
    return $valid
  } catch { return 0 }
}

function Get-TopDeltas {
  $cmp = Join-Path $workDir 'vendor_vs_estimate.csv'
  if (-not (Test-Path $cmp)) { return @() }
  try {
    $rows = Import-Csv -Path $cmp
    foreach ($r in $rows) {
      try {
        $r.est_total   = [double]$r.est_total
        $r.vdr_total   = [double]$r.vdr_total
        $r.delta_total = [double]$r.delta_total
      } catch {}
    }
    return $rows | Sort-Object @{Expression={ [math]::Abs([double]$_.delta_total) }; Descending=$true} | Select-Object -First 3
  } catch { return @() }
}

function Get-SumVen {
  # Prefer mapped vendor sum from compare output (apples-to-apples with estimate)
  $cmp = Join-Path $workDir 'vendor_vs_estimate.csv'
  if (Test-Path $cmp) {
    try {
      $sum = 0.0
      $rows = Import-Csv -Path $cmp
      foreach ($r in $rows) {
        try { $v = [double]$r.vdr_total } catch { $v = 0.0 }
        if ($v -gt 0) { $sum += $v }
      }
      return [math]::Round($sum,2)
    } catch {}
  }

  # Fallback: sum of canonical CSV totals
  $canon = Join-Path $workDir 'vendor_quotes.canonical.csv'
  if (-not (Test-Path $canon)) { return 0.0 }
  $sum = 0.0
  try {
    $rows = Import-Csv -Path $canon
    foreach ($r in $rows) {
      $raw = if ($r.PSObject.Properties['quoted_total']) { $r.quoted_total } else { $r.line_total }
      try {
        $v = [double]($raw -replace '[\$,]', '')
        if ($v -gt 0) { $sum += $v }
      } catch {}
    }
  } catch {}
  return [math]::Round($sum,2)
}

function Get-SumEst {
  # Prefer raw_estimate CSV if present
  $est = 'output/LYNN-001/raw_estimate/estimate_lines.csv'
  if (-not (Test-Path $est)) { $est = 'data/lynn/working/estimate_lines.csv' }
  if (-not (Test-Path $est)) { return 0.0 }
  $sum = 0.0
  try {
    $rows = Import-Csv -Path $est
    foreach ($r in $rows) {
      $v = 0.0
      if ($r.PSObject.Properties['line_total']) {
        try { $v = [double]($r.line_total -replace '[\$,]', '') } catch { $v = 0.0 }
      } elseif ($r.PSObject.Properties['ext_cost']) {
        try { $v = [double]($r.ext_cost -replace '[\$,]', '') } catch { $v = 0.0 }
      } elseif ($r.PSObject.Properties['total']) {
        try { $v = [double]($r.total -replace '[\$,]', '') } catch { $v = 0.0 }
      } else {
        # qty * unit_cost fallback
        $qty = 0.0; $uc = 0.0
        if ($r.PSObject.Properties['qty']) { try { $qty = [double]$r.qty } catch {} }
        if ($r.PSObject.Properties['quantity']) { try { $qty = [double]$r.quantity } catch {} }
        if ($r.PSObject.Properties['unit_cost']) { try { $uc = [double]$r.unit_cost } catch {} }
        $v = $qty * $uc
      }
      if ($v -gt 0) { $sum += $v }
    }
  } catch {}
  return [math]::Round($sum,2)
}

function Get-CountFromCsv {
  param([string]$Path)
  if (-not (Test-Path $Path)) { return 0 }
  try { return (Get-Content -ReadCount 0 -Path $Path | Measure-Object -Line).Lines - 1 } catch { return 0 }
}

function Read-Metrics {
  $sum_est = Get-SumEst
  $sum_ven = Get-SumVen
  # counts: use canonical valid row count as VEN_COUNT
  $ven_count = Get-CanonicalRowCount
  # estimate count: lines with positive totals
  $est_csv = 'output/LYNN-001/raw_estimate/estimate_lines.csv'
  if (-not (Test-Path $est_csv)) { $est_csv = 'data/lynn/working/estimate_lines.csv' }
  $est_count = 0
  if (Test-Path $est_csv) {
    try {
      $rows = Import-Csv -Path $est_csv
      foreach ($r in $rows) {
        $v = 0.0
        if ($r.PSObject.Properties['line_total']) {
          try { $v = [double]($r.line_total -replace '[\$,]', '') } catch {}
        } elseif ($r.PSObject.Properties['ext_cost']) {
          try { $v = [double]($r.ext_cost -replace '[\$,]', '') } catch {}
        } elseif ($r.PSObject.Properties['total']) {
          try { $v = [double]($r.total -replace '[\$,]', '') } catch {}
        }
        if ($v -gt 0) { $est_count++ }
      }
    } catch {}
  }
  $outliers = Get-CountFromCsv (Join-Path $outDir 'CALIBRATION_OUTLIERS.csv')
  $dupes    = Get-CountFromCsv (Join-Path $outDir 'CALIBRATION_DUPES.csv')
  $factors  = Get-FactorsCount
  return @{
    sum_est = $sum_est
    sum_ven = $sum_ven
    est_count = $est_count
    ven_count = $ven_count
    outliers_count = $outliers
    dupes_count = $dupes
    factors = $factors
    timestamp = (Get-Date).ToString('s')
  }
}

function Write-BeforeAfter {
  param([hashtable]$Before, [hashtable]$After)
  $md = @()
  $md += "# CALIBRATION BEFORE / AFTER"
  $md += ""
  $md += "| metric | before | after |"
  $md += "|---|---:|---:|"
  foreach ($k in @('sum_est','sum_ven','est_count','ven_count','outliers_count','dupes_count','factors')) {
    $md += ("| {0} | {1} | {2} |" -f $k, ($Before[$k]), ($After[$k]))
  }
  $md += ""
  # top 10 outliers preview
  $outliersPath = Join-Path $outDir 'CALIBRATION_OUTLIERS.csv'
  if (Test-Path $outliersPath) {
    try {
      $rows = Import-Csv -Path $outliersPath | Select-Object -First 10
      if ($rows.Count -gt 0) {
        $md += "## Top dropped lines (reason, vendor, value)"
        $md += "| reason | vendor | value | desc |"
        $md += "|---|---|---:|---|"
        foreach ($r in $rows) {
          $md += ("| {0} | {1} | {2} | {3} |" -f $r.reason, $r.vendor, $r.value, ($r.desc -replace '\|','/'))
        }
      }
    } catch {}
  }
  ($md -join "`n") | Out-File -Encoding UTF8 (Join-Path $outDir 'CALIBRATION_BEFORE_AFTER.md')

  # status JSON = After snapshot
  $After | ConvertTo-Json | Out-File -Encoding UTF8 (Join-Path $outDir 'CALIBRATION_STATUS.json')
}

function Write-RunSummary {
  $canonRows = Get-CanonicalRowCount
  $factors   = Get-FactorsCount
  $top3      = Get-TopDeltas
  $dashPath  = 'output/LYNN_DELTA_DASHBOARD.html'
  $receipt   = 'output/F4B_DATA_RECEIPT.md'
  $sha       = ""
  try { $sha = (& git rev-parse HEAD).Trim() } catch {}

  $lines = @(
    "# RUN SUMMARY",
    "",
    "- When: $(Get-Date -Format o)",
    "- Canonical rows (valid trade,item,quoted_total>0): $canonRows",
    "- Factors count: $factors",
    "- Dashboard: $dashPath",
    "- Receipt (if committed): $receipt",
    "- HEAD: $sha",
    ""
  )
  if ($top3.Count -gt 0) {
    $lines += "## Top 3 deltas (by |Vendor-Est|)"
    $lines += "| trade | item | est_total | vdr_total | delta_total |"
    $lines += "|---|---|---:|---:|---:|"
    foreach ($r in $top3) {
      $lines += ("| {0} | {1} | {2:N0} | {3:N0} | {4:N0} |" -f $r.trade, $r.item, $r.est_total, $r.vdr_total, $r.delta_total)
    }
    $lines += ""
  }
  $lines -join "`n" | Out-File -Encoding UTF8 $summary

  # Also store last commit SHA (if any)
  if ($sha) {
    Set-Content -Path 'output\CLINE_LAST_COMMIT_SHA.txt' -Value $sha -Encoding ascii
  }
}

# Dispatch by step
switch ($Step) {
  'Parse' {
    Invoke-Step -Name 'Parse vendor PDFs' -ScriptPath 'scripts/run_lynn_f3b_vendor.ps1'
  }
  'Train' {
    Invoke-Step -Name 'Train calibration' -ScriptPath 'scripts/train_lynn_model_from_vendor.ps1'
  }
  'Calibrated' {
    Invoke-Step -Name 'Run calibrated estimate' -ScriptPath 'scripts/run_calibrated_estimate.ps1'
  }
  'Dashboard' {
    Invoke-Step -Name 'Make delta dashboard' -ScriptPath 'scripts/make_delta_dashboard.ps1'
  }
  'All' {
    $before = Read-Metrics
    Invoke-Step -Name 'Parse vendor PDFs'        -ScriptPath 'scripts/run_lynn_f3b_vendor.ps1'
    Invoke-Step -Name 'Train calibration'        -ScriptPath 'scripts/train_lynn_model_from_vendor.ps1'
    Invoke-Step -Name 'Run calibrated estimate'  -ScriptPath 'scripts/run_calibrated_estimate.ps1'
    Invoke-Step -Name 'Make delta dashboard'     -ScriptPath 'scripts/make_delta_dashboard.ps1'
    $after = Read-Metrics
    Write-BeforeAfter -Before $before -After $after
    if ($Commit.IsPresent) {
      Invoke-Step -Name 'Commit + tag (F4b-data)' -ScriptPath 'scripts/commit_f4b_data.ps1'
    }
  }
}

# Always write a summary at the end of any step
Write-RunSummary

Write-Host ("F4B_DATA_PASS_DONE step={0} log={1}" -f $Step, $logPath)
