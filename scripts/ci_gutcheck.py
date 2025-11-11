import os, sys, json, pathlib, datetime
ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "output" / "BENCH"
OUT_DIR.mkdir(parents=True, exist_ok=True)

estimate_csv   = ROOT / "output" / "LYNN-001" / "raw_estimate" / "estimate_lines.csv"
features_json  = ROOT / "output" / "TAKEOFF_RESPONSE.json"
vendor_csv     = ROOT / "data" / "vendor_quotes" / "LYNN-001" / "quotes.canonical.csv"

def exists(p: pathlib.Path) -> bool:
    return p.exists() and p.is_file()

if not exists(estimate_csv) or not exists(features_json):
    print("SKIP: missing inputs for gut-check; requires estimate_lines.csv and TAKEOFF_RESPONSE.json")
    sys.exit(0)

# Import the existing benchmarking module (read-only)
from web.backend import benchmarking  # must already exist per prior commit

# Load inputs
est_df   = benchmarking.load_estimate_lines(str(estimate_csv))
features = benchmarking.load_plan_features(str(features_json))
vendor_df = benchmarking.load_vendor_quotes(str(vendor_csv)) if exists(vendor_csv) else None

# Compute metrics (read-only)
metrics = benchmarking.metrics(est_df, features, vendor_df)

# Basic rule gates (do not overfit; just a sanity PASS/FAIL)
status_notes = []
pass_flag = True

dpsf = metrics.get("totals", {}).get("dollars_per_sf")
ptype = (features.get("project_type") if isinstance(features, dict) else None) or "SOD"
band  = benchmarking.bands_from_history(dpsf or 0.0, project_type=ptype)
if dpsf is not None and band:
    lo, hi = band.get("lo", 0), band.get("hi", 0)
    if not (lo <= dpsf <= hi):
        pass_flag = False
        status_notes.append(f"dollars_per_sf {dpsf:.2f} out of band [{lo:.2f}, {hi:.2f}]")

cov = metrics.get("coverage", {})
missing = set(cov.get("missing_trades", []))
majors = {"Concrete","Framing","Electrical","Plumbing","HVAC"}
if missing & majors:
    pass_flag = False
    status_notes.append("major trade missing from estimate")

if vendor_df is not None:
    mape = (metrics.get("vendor") or {}).get("MAPE_project")
    if isinstance(mape, (int, float)) and mape > 0.15:
        pass_flag = False
        status_notes.append(f"MAPE {mape:.3f} > 0.15")

# Write outputs
json_out = OUT_DIR / "LYNN_GUTCHECK.json"
md_out   = OUT_DIR / "LYNN_GUTCHECK.md"
with open(json_out, "w", encoding="utf-8") as f:
    json.dump(metrics, f, indent=2)

now = datetime.datetime.utcnow().isoformat() + "Z"
status_line = "PASS" if pass_flag else "FAIL"
if vendor_df is None:
    status_line += " (no vendor quotes; vendor metrics skipped)"
if status_notes:
    status_line += " — " + "; ".join(status_notes)

lines = []
lines.append(f"# LYNN Gut-Check — {status_line}")
tot = metrics.get("totals", {})
est_total = tot.get("estimate_total", 0) or 0
lines.append(f"- Estimate Total: ${est_total:,.2f}")
if tot.get("area_sqft"):
    lines.append(f"- Area (SF): {int(tot['area_sqft'])}")
if dpsf is not None:
    lines.append(f"- $/SF: ${dpsf:.2f}")
if band:
    lines.append(f"- Band: [{band.get('lo',0):.2f}, {band.get('hi',0):.2f}]")

lines.append("\n## Trade Subtotals (Top)")
for row in sorted(metrics.get("trade_breakdown", []), key=lambda r: r.get("subtotal",0) or 0, reverse=True)[:10]:
    lines.append(f"- {row.get('trade')}: ${float(row.get('subtotal',0) or 0):,.2f} ({(row.get('pct',0) or 0)*100:.1f}%)")

if vendor_df is not None:
    v = metrics.get("vendor") or {}
    lines.append("\n## Vendor Comparison")
    lines.append(f"- Project MAPE: {v.get('MAPE_project')}")
    if isinstance(v.get("WAPE_by_trade"), list):
        lines.append("- WAPE by Trade (Top):")
        for r in v['WAPE_by_trade'][:10]:
            lines.append(f"  - {r.get('trade')}: {r.get('wape')}")

if isinstance(metrics.get("warnings"), list) and metrics["warnings"]:
    lines.append("\n## Notes & Warnings")
    for w in metrics["warnings"][:10]:
        lines.append(f"- {w}")

with open(md_out, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))

print(status_line)

# Actions
# - Stage the two files only:
#     .github/workflows/gutcheck.yml
#     scripts/ci_gutcheck.py
# - Commit with EXACT message:
#     chore(ci): add read-only Gut-Check workflow and script
# - Push to origin (current default branch).
# - Echo the new commit SHA upon success.
