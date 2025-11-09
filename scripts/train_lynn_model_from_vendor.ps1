param(
  [string]$EstimateCsv  = "data/lynn/working/estimate_lines.csv",
  [string]$VendorCsv    = "data/lynn/working/vendor_quotes.canonical.csv",
  [string]$OutJson      = "models/calibration/lynn_v0.json",
  [string]$ReportMd     = "output/CALIBRATION_REPORT.md"
)

$ErrorActionPreference = "Stop"
Write-Host "== F4: Training calibration from vendor vs raw estimate =="

# Python inline runner (PowerShell-safe temp file)
$RepoRoot = (Split-Path $PSScriptRoot -Parent)
$py = @"
import sys, pathlib
sys.path.insert(0, r'$RepoRoot')
from pathlib import Path
from web.backend.model_calibration import (load_raw_estimate_lines, load_vendor_canonical,
    compute_multipliers, save_calibration_json, digest_file)

est_p = Path(r'$EstimateCsv'); ven_p = Path(r'$VendorCsv')
est = load_raw_estimate_lines(est_p)
ven = load_vendor_canonical(ven_p)
factors = compute_multipliers(est, ven)

meta = {
  "estimate_csv_sha256": digest_file(est_p),
  "vendor_csv_sha256":   digest_file(ven_p),
  "count_factors":       str(len(factors))
}
out_p = Path(r'$OutJson')
save_calibration_json(out_p, factors, meta)

print("FACTORS", len(factors))
"@

$tmp = Join-Path $env:TEMP ("train_lynn_model_{0}.py" -f ([guid]::NewGuid().ToString("N")))
Set-Content -Path $tmp -Value $py -Encoding UTF8
try {
  python $tmp
} finally {
  if (Test-Path $tmp) { Remove-Item $tmp -Force -ErrorAction SilentlyContinue }
}

# Minimal MD report
$factorsCount = (Get-Content -Raw $OutJson | ConvertFrom-Json).factors.Keys.Count
"## LYNN Calibration Report (F4)
- Factors learned: $factorsCount
- Estimate CSV: $EstimateCsv
- Vendor CSV:   $VendorCsv
- Output:       $OutJson
" | Out-File -Encoding utf8 $ReportMd

Write-Host "Calibration complete -> $OutJson"
