param(
  [string]$EstimateCsv  = "data/lynn/working/estimate_lines.csv",
  [string]$VendorCsv    = "data/lynn/working/vendor_quotes.canonical.csv",
  [string]$OutJson      = "models/calibration/lynn_v0.json",
  [string]$ReportMd     = "output/CALIBRATION_REPORT.md"
)

$ErrorActionPreference = "Stop"
Write-Host "== F4: Training calibration from vendor vs raw estimate =="
# Fallback to canonical in data/vendor_quotes if working canonical missing or header-only
$AltVendor = "data/vendor_quotes/LYNN-001/quotes.canonical.csv"
$lines = @()
if (Test-Path $VendorCsv) { $lines = Get-Content -TotalCount 2 -Encoding UTF8 $VendorCsv }
if (-not (Test-Path $VendorCsv) -or ($lines.Count -lt 2)) {
  if (Test-Path $AltVendor) {
    Write-Host "Using fallback vendor canonical -> $AltVendor"
    $VendorCsv = $AltVendor
  }
}

# Fallback to RAW estimate export if working estimate CSV missing or header-only
$AltEstimate = "output/LYNN-001/raw_estimate/estimate_lines.csv"
$elines = @()
if (Test-Path $EstimateCsv) { $elines = Get-Content -TotalCount 2 -Encoding UTF8 $EstimateCsv }
if (-not (Test-Path $EstimateCsv) -or ($elines.Count -lt 2)) {
  if (Test-Path $AltEstimate) {
    Write-Host "Using fallback estimate CSV -> $AltEstimate"
    $EstimateCsv = $AltEstimate
  }
}

# Python inline runner (PowerShell-safe temp file)
$RepoRoot = (Split-Path $PSScriptRoot -Parent)
$py = @"
import sys, pathlib, json
sys.path.insert(0, r'$RepoRoot')
from pathlib import Path
from web.backend.model_calibration import (load_raw_estimate_lines, load_vendor_canonical,
    compute_multipliers, save_calibration_json, digest_file)

est_p = Path(r'$EstimateCsv'); ven_p = Path(r'$VendorCsv')
est = load_raw_estimate_lines(est_p)
ven = load_vendor_canonical(ven_p)
factors = compute_multipliers(est, ven)

# Diagnostics: totals and trade breakdowns
from collections import defaultdict as _dd
def _sum_by_trade(d):
    res = _dd(float)
    for k, v in d.items():
        t = k.split("::", 1)[0] if "::" in k else k
        res[t] += float(v)
    return dict(res)

tot_est = sum(float(v) for v in est.values())
tot_ven = sum(float(v) for v in ven.values())
# Console diagnostics for pipeline log
print("SUM_EST", f"{tot_est:.2f}")
print("SUM_VEN", f"{tot_ven:.2f}")
print("EST_COUNT", len(est))
print("VEN_COUNT", len(ven))
try:
    print("VEN_SAMPLE_KEYS", list(ven.keys())[:5])
except Exception:
    pass
est_tr = _sum_by_trade(est)
ven_tr = _sum_by_trade(ven)

diag_md = "# CALIBRATION DIAGNOSE\n\n"
diag_md += f"- SUM_EST: {tot_est:.2f}\n- SUM_VEN: {tot_ven:.2f}\n"
diag_md += "\n## Estimate by trade\n" + json.dumps(est_tr, indent=2) + "\n"
diag_md += "\n## Vendor by trade\n" + json.dumps(ven_tr, indent=2) + "\n"

Path("output").mkdir(parents=True, exist_ok=True)
Path("output/CALIBRATION_DIAGNOSE.md").write_text(diag_md, encoding="utf-8")

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
