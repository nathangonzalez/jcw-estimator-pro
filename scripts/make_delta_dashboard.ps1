param(
  [string]$RawCsv   = "data/lynn/working/estimate_lines.csv",
  [string]$VendorCsv= "data/lynn/working/vendor_quotes.canonical.csv",
  [string]$CalCsv   = "data/lynn/working/estimate_lines_calibrated.csv",
  [string]$OutHtml  = "output/LYNN_DELTA_DASHBOARD.html",
  [string]$ModelJson= "models/calibration/lynn_v0.json",
  [string]$DiagMd   = "output/CALIBRATION_DIAGNOSE.md"
)

$ErrorActionPreference = "Stop"

# Python block to build dashboard and optionally write diagnosis report
$py = @"
import csv, html, json
from pathlib import Path

def rollup(p, prefer_vendor=False):
    agg={}
    path = Path(p)
    if not path.exists(): return agg
    with path.open(newline='', encoding='utf-8') as f:
        r = csv.DictReader(f)
        for row in r:
            t = (row.get('trade','').strip().lower(), row.get('item','').strip().lower())
            if not t[0] or not t[1]:
                # keep for diagnosis if vendor csv, but skip in rollup
                if prefer_vendor:
                    try: v = float((row.get('quoted_total') or row.get('line_total') or 0))
                    except: 
                        try: v = float(str(row.get('quoted_total') or row.get('line_total') or 0).replace(',','').replace('$',''))
                        except: v = 0.0
                    # store under special key for diagnosis only
                    agg.setdefault(('_UNMAPPED_', '_UNMAPPED_'), 0.0)
                    agg[('_UNMAPPED_', '_UNMAPPED_')] += max(0.0, v)
                continue
            # choose value: vendor quoted_total, else line_total; otherwise use engine line_total
            rawv = row.get('quoted_total') if prefer_vendor else row.get('line_total')
            if rawv is None and prefer_vendor:
                rawv = row.get('line_total')
            try: v = float(rawv or 0)
            except:
                try: v = float(str(rawv or 0).replace(',','').replace('$',''))
                except: v = 0.0
            agg[t] = agg.get(t,0.0) + max(0.0, v)
    return agg

raw = rollup(r'$RawCsv')
ven = rollup(r'$VendorCsv', prefer_vendor=True)
cal = rollup(r'$CalCsv')

keys = set(k for k in raw.keys() | ven.keys() | cal.keys() if k[0] != '_UNMAPPED_')
rows=[]
for k in sorted(keys):
    r = raw.get(k,0); v = ven.get(k,0); c = cal.get(k,0)
    diff_rv = v - r
    diff_rc = c - r
    rows.append((k[0], k[1], r, v, c, diff_rv, diff_rc))

html_rows = "".join(
    f"<tr><td>{html.escape(t)}</td><td>{html.escape(i)}</td>"
    f"<td>{r:,.0f}</td><td>{v:,.0f}</td><td>{c:,.0f}</td>"
    f"<td>{diff_rv:,.0f}</td><td>{diff_rc:,.0f}</td></tr>"
    for t,i,r,v,c,diff_rv,diff_rc in rows
)

doc = f"""<!doctype html><meta charset='utf-8'>
<title>LYNN Delta Dashboard</title>
<style>body{{font-family:sans-serif}} table{{border-collapse:collapse}} td,th{{border:1px solid #ddd;padding:6px}} th{{background:#f5f5f5}}</style>
<h1>LYNN Delta Dashboard</h1>
<p>RAW vs Vendor vs Calibrated (trade/item rollups)</p>
<table>
<thead><tr><th>Trade</th><th>Item</th><th>RAW</th><th>Vendor</th><th>Calibrated</th><th>Vendor - RAW</th><th>Cal - RAW</th></tr></thead>
<tbody>{html_rows}</tbody>
</table>"""

Path(r'$OutHtml').parent.mkdir(parents=True, exist_ok=True)
Path(r'$OutHtml').write_text(doc, encoding='utf-8')
print("DASHBOARD_OK")

# Diagnosis: if factors == 0, list unmapped top lines by amount from vendor CSV
def factors_count(model_path: str) -> int:
    p = Path(model_path)
    if not p.exists(): return 0
    try:
        j = json.loads(p.read_text(encoding='utf-8'))
        f = j.get('factors') or {}
        return len(f.keys())
    except Exception:
        return 0

if factors_count(r'$ModelJson') == 0:
    # gather unmapped vendor lines
    vendor_path = Path(r'$VendorCsv')
    sample = []
    if vendor_path.exists():
        with vendor_path.open(newline='', encoding='utf-8') as f:
            r = csv.DictReader(f)
            for row in r:
                trade = (row.get('trade') or '').strip()
                item  = (row.get('item') or '').strip()
                # unmapped if trade or item missing OR non-positive quoted_total
                rawv = row.get('quoted_total', None)
                if rawv is None:
                    rawv = row.get('line_total', 0)
                try: v = float(rawv or 0)
                except:
                    try: v = float(str(rawv or 0).replace(',','').replace('$',''))
                    except: v = 0.0
                if (not trade or not item) or v <= 0:
                    desc = (row.get('description') or '').strip()
                    vendor = (row.get('vendor') or '').strip()
                    sample.append((v, vendor, desc, trade, item))
    sample.sort(key=lambda x: x[0], reverse=True)
    top = sample[:50]
    lines = []
    lines.append("# CALIBRATION DIAGNOSE")
    lines.append("")
    lines.append("Factors learned were zero; likely mapping gaps. Top unmapped vendor lines by amount:")
    lines.append("")
    lines.append("| amount | vendor | trade | item | description |")
    lines.append("|---:|---|---|---|---|")
    for v, vendor, desc, tr, it in top:
        lines.append(f"| {v:,.2f} | {vendor} | {tr} | {it} | {desc.replace('|','/')} |")
    Path(r'$DiagMd').write_text("\n".join(lines) + "\n", encoding='utf-8')
    print("DIAGNOSE_WRITTEN")
"@

# Execute Python block via temp file (PowerShell-safe)
$tmp = Join-Path $env:TEMP ("make_delta_dashboard_{0}.py" -f ([guid]::NewGuid().ToString("N")))
Set-Content -Path $tmp -Value $py -Encoding UTF8
try {
  python $tmp
} finally {
  if (Test-Path $tmp) { Remove-Item $tmp -Force -ErrorAction SilentlyContinue }
}
