# Compares Best Guess (PIPELINE_ESTIMATE_RESPONSE.json) against vendor canonical CSV.
# Outputs CSV+JSON under output/LYNN-001/compare/ and appends a human note to UAT doc.

$ErrorActionPreference = "Stop"
New-Item -ItemType Directory -Force -Path output\LYNN-001\compare | Out-Null

$resp = "output/PIPELINE_ESTIMATE_RESPONSE.json"
$canon = "data/vendor_quotes/LYNN-001/quotes.canonical.csv"
if (-not (Test-Path $resp)) { throw "Missing $resp. Run the pipeline smoke first." }
if (-not (Test-Path $canon)) { throw "Missing $canon. Normalize vendor CSVs, then aggregate to this file." }

$pyCode = @"
from pathlib import Path
from web.backend.compare_estimate_vs_vendor import (
    load_vendor_canonical, load_estimate_response, compare, write_report, digest_path
)
out_dir = Path("output/LYNN-001/compare"); out_dir.mkdir(parents=True, exist_ok=True)
rows = compare(
    load_estimate_response(Path("output/PIPELINE_ESTIMATE_RESPONSE.json")),
    load_vendor_canonical(Path("data/vendor_quotes/LYNN-001/quotes.canonical.csv"))
)
write_report(rows, out_dir/"report.csv", out_dir/"report.json")
# also write a small markdown summary
est_dig = digest_path(Path("output/PIPELINE_ESTIMATE_RESPONSE.json"))
vdr_dig = digest_path(Path("data/vendor_quotes/LYNN-001/quotes.canonical.csv"))
summary = out_dir/"SUMMARY.md"
summary.write_text(
    f"# LYNN-001 — Estimate vs Vendor Comparison\n\n"
    f"- estimate_digest: `{est_dig}`\n- vendor_digest: `{vdr_dig}`\n"
    f"- rows: {len(rows)}\n\n"
    f"See `report.csv` and `report.json` for per-trade/item deltas.\n", encoding="utf-8"
)
"@
$pyPath = Join-Path $env:TEMP "compare_lynn_quotes.py"
$pyCode | Out-File -Encoding UTF8 $pyPath
python $pyPath
Remove-Item -Force $pyPath

# Append breadcrumb to training notes (non-destructive)
$note = @"
### $(Get-Date -Format "yyyy-MM-dd HH:mm")
- Ran compare_lynn_quotes.ps1
- Inputs: output/PIPELINE_ESTIMATE_RESPONSE.json vs data/vendor_quotes/LYNN-001/quotes.canonical.csv
- Outputs: output/LYNN-001/compare/report.(csv|json), SUMMARY.md
"@
Add-Content -Encoding utf8 docs/UAT_TRAINING_NOTES_VENDOR_QUOTES.md $note

Write-Host "Comparison complete. See output/LYNN-001/compare/"
