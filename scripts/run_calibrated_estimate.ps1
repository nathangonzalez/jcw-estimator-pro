param(
  [string]$QuantitiesJson = "data/lynn/working/takeoff_quantities.json",
  [string]$PolicyYaml     = "schemas/pricing_policy.v0.yaml",
  [string]$UnitCostsCsv   = "data/unit_costs.sample.csv",
  [string]$CalibJson      = "models/calibration/lynn_v0.json",
  [string]$OutJson        = "data/lynn/working/PIPELINE_ESTIMATE_RESPONSE_CALIBRATED.json",
  [string]$OutLinesCsv    = "data/lynn/working/estimate_lines_calibrated.csv"
)

$ErrorActionPreference = "Stop"

# Python runner via temp file (PowerShell-safe)
$RepoRoot = (Split-Path $PSScriptRoot -Parent)
$py = @"
import csv, json
from io import StringIO
import sys, pathlib
sys.path.insert(0, r'$RepoRoot')
from pathlib import Path
from web.backend.pricing_engine import price_quantities
from web.backend.pricing_engine_calibrated import load_calibration, apply_calibration

q_p = Path(r'$QuantitiesJson'); pol_p=Path(r'$PolicyYaml'); uc_p=Path(r'$UnitCostsCsv'); cal_p=Path(r'$CalibJson')
out_json = Path(r'$OutJson'); out_lines = Path(r'$OutLinesCsv')

def _flatten_quantities(takeoff):
    if isinstance(takeoff, list):
        out = []
        for it in takeoff:
            out.append({
                "trade": it.get("trade",""),
                "code": it.get("code",""),
                "description": it.get("description",""),
                "uom": (it.get("uom") or it.get("unit") or "EA").upper(),
                "qty": float(it.get("qty") or it.get("quantity") or 0.0),
                "notes": it.get("notes"),
            })
        return out
    if isinstance(takeoff, dict) and takeoff.get("version") == "v0" and isinstance(takeoff.get("trades"), dict):
        out = []
        for trade, tdata in (takeoff.get("trades") or {}).items():
            for it in (tdata.get("items") or []):
                out.append({
                    "trade": trade,
                    "code": it.get("code",""),
                    "description": it.get("description",""),
                    "uom": (it.get("unit") or "EA").upper(),
                    "qty": float(it.get("quantity") or 0.0),
                    "notes": it.get("notes"),
                })
        return out
    return []

# Load calibration factors
factors = load_calibration(cal_p)

# Load base unit costs CSV -> {(trade,code): unit_cost}
base_costs = {}
if uc_p.exists():
    with uc_p.open("r", newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        # Accept common headers: trade,code,unit_cost (ignore others)
        for row in r:
            t = (row.get("trade") or "").strip()
            c = (row.get("code") or row.get("item") or "").strip()
            if not t or not c: 
                continue
            try:
                cost = float((row.get("unit_cost") or "0").replace(",",""))
            except Exception:
                cost = 0.0
            base_costs[(t, c)] = max(0.0, cost)

# Apply calibration
adj_costs = {}
for (trade, code), c in base_costs.items():
    adj_costs[(trade, code)] = apply_calibration(c, trade, code, factors)

# Build CSV text that pricing_engine expects (headers: trade,code,unit_cost)
buf = StringIO()
w = csv.writer(buf)
w.writerow(["trade","code","unit_cost"])
for (t, c), cost in adj_costs.items():
    w.writerow([t, c, f"{cost:.6f}"])
unit_costs_csv_text = buf.getvalue()

# Load and flatten quantities
quantities_raw = {}
if q_p.exists():
    quantities_raw = json.loads(q_p.read_text(encoding="utf-8"))
quantities = _flatten_quantities(quantities_raw)

# Load policy
policy_yaml = pol_p.read_text(encoding="utf-8") if pol_p.exists() else ""

# Price with calibrated unit costs (no vendor quotes)
resp = price_quantities(
    quantities=quantities,
    policy_yaml=policy_yaml,
    region="US-MA-Boston",
    unit_costs_csv=unit_costs_csv_text,
    vendor_quotes_csv=None,
)

# Persist output JSON
out_json.parent.mkdir(parents=True, exist_ok=True)
out_json.write_text(json.dumps(resp, indent=2), encoding="utf-8")

# Emit flat lines CSV for downstream tools
with out_lines.open("w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["project_id","trade","item","quantity","unit","unit_cost","line_total","source"])
    pid = (quantities_raw.get("project_id") if isinstance(quantities_raw, dict) else None) or "LYNN-001"
    for li in resp.get("line_items", []):
        trade = li.get("trade","")
        item  = li.get("code") or li.get("description") or ""
        qty   = li.get("qty") or li.get("quantity") or 0
        unit  = li.get("uom") or li.get("unit") or "EA"
        unit_cost = li.get("unit_cost") or 0
        line_total = li.get("total") or li.get("line_total") or 0
        source = li.get("source") or "engine:unit_costs"
        w.writerow([pid, trade, item, qty, unit, unit_cost, line_total, source])

print("OK")
"@

$tmp = Join-Path $env:TEMP ("run_calibrated_estimate_{0}.py" -f ([guid]::NewGuid().ToString("N")))
Set-Content -Path $tmp -Value $py -Encoding UTF8
try {
  python $tmp
} finally {
  if (Test-Path $tmp) { Remove-Item $tmp -Force -ErrorAction SilentlyContinue }
}
