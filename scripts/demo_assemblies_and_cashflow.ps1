Param(
  [string]$TakeoffJson = "output/TAKEOFF_RESPONSE.json",
  [string]$EstimateCsv = "output/LYNN-001/raw_estimate/estimate_lines.csv",
  [string]$ScheduleJson = "output/SCHEDULE_SAMPLE.json"
)

$ErrorActionPreference = "Stop"

# Validate inputs that must exist
if (-not (Test-Path $TakeoffJson)) {
  Write-Error "Missing $TakeoffJson; run pipeline smoke first."
  exit 1
}

# Python inline program written to a temp file (PowerShell-safe)
$python = "python"
$pyCode = @"
import json, os
from web.backend.assemblies_engine import expand_from_files
from web.backend.cashflow import cashflow_from_schedule, load_estimate_lines_csv

takeoff_path = r'''$TakeoffJson'''
estimate_csv = r'''$EstimateCsv'''
schedule_json = r'''$ScheduleJson'''

with open(takeoff_path, "r", encoding="utf-8") as f:
    to = json.load(f)

plan_features = {
    "project_id": to.get("project_id") or to.get("meta",{}).get("project_id") or "UNKNOWN",
    "project_type": to.get("project_type") or "SOD",
    "area_sqft": float(to.get("area_sqft") or to.get("meta",{}).get("area_sqft") or 0.0),
    "fixtures": to.get("fixtures") or to.get("meta",{}).get("fixtures") or {},
}

# Expand assemblies
lines, applied = expand_from_files(plan_features, ["data/assemblies/interior.yaml","data/assemblies/exterior.yaml"])
os.makedirs("output", exist_ok=True)
with open("output/ASSEMBLIES_SAMPLE.md","w",encoding="utf-8") as f:
    f.write("# Assemblies Sample (v0)\\n\\n")
    f.write(f"Applied: {applied}\\n\\n")
    f.write("| trade | item | quantity | unit | notes |\\n|---|---:|---:|---|---|\\n")
    for r in lines:
        f.write(f"| {r['trade']} | {r['item']} | {r['quantity']:.2f} | {r['unit']} | {r.get('notes','')} |\\n")

# If schedule missing, try to generate one via PowerShell helper
if not os.path.exists(schedule_json):
    import subprocess
    subprocess.run(["pwsh","-NoProfile","-File","scripts/generate_schedule_from_estimate.ps1"], check=False)

# Build cashflow
if os.path.exists(schedule_json):
    import json as _json
    sched = _json.load(open(schedule_json, "r", encoding="utf-8"))
else:
    # Minimal fallback schedule (2 months, equal weights)
    from datetime import date, timedelta
    start = date.today()
    sched = {
        "version":"v0",
        "tasks":[
            {"name":"Phase A","start": start.isoformat(),"end": (start+timedelta(days=21)).isoformat(),"weight":0.5},
            {"name":"Phase B","start": (start+timedelta(days=22)).isoformat(),"end": (start+timedelta(days=56)).isoformat(),"weight":0.5},
        ],
    }

rows = load_estimate_lines_csv(estimate_csv)
series = cashflow_from_schedule(rows, sched, retainage_pct=0.1)
with open("output/CASHFLOW_SAMPLE.json","w",encoding="utf-8") as f:
    import json as _json
    _json.dump(series, f, indent=2)

print("Wrote output/ASSEMBLIES_SAMPLE.md and output/CASHFLOW_SAMPLE.json")
"@

# Write temp python file, run, then clean up
$tmp = Join-Path $env:TEMP ("demo_assemblies_and_cashflow_{0}.py" -f ([guid]::NewGuid().ToString("N")))
Set-Content -Path $tmp -Value $pyCode -Encoding UTF8
try {
  & $python $tmp
} finally {
  if (Test-Path $tmp) { Remove-Item $tmp -Force -ErrorAction SilentlyContinue }
}
