# CLINE SUPERVISED COMMIT + PUSH — F3b Vendor Quotes Compare Scaffolding (sync-only)
# Stages files, commits, pushes with annotated tag chkpt-f3b.

$ErrorActionPreference = "Stop"
Set-Location "C:\Users\natha\dev\repos\jcw-estimator-pro"

# Files to stage (exact per plan)
$paths = @(
  "docs/UAT_TRAINING_NOTES_VENDOR_QUOTES.md",
  "schemas/vendor_quote_row.schema.json",
  "schemas/vendor_quotes_canonical.schema.json",
  "data/vendor_quotes/LYNN-001/README.md",
  "data/vendor_quotes/LYNN-001/quotes.canonical.csv",
  "data/vendor_quotes/LYNN-001/acme_plumbing/raw/.gitkeep",
  "data/vendor_quotes/LYNN-001/acme_plumbing/parsed/.gitkeep",
  "data/vendor_quotes/LYNN-001/acme_plumbing/normalized/.gitkeep",
  "web/backend/vendor_quote_parser.py",
  "web/backend/compare_estimate_vs_vendor.py",
  "scripts/compare_lynn_quotes.ps1",
  "docs/ESTIMATING_PIPELINE.md"
)

git add $paths | Out-Null

# Pending staged list
$pending = @(git diff --cached --name-only)

New-Item -ItemType Directory -Force -Path "output" | Out-Null

if ($pending.Count -eq 0) {
  $now = Get-Date -Format "o"
  @"
# CLINE_COMMIT_F3B (noop)
- Status: nothing to commit (index clean)
- Time: $now
- Branch: $(git rev-parse --abbrev-ref HEAD)
- Head: $(git rev-parse HEAD)
"@ | Out-File -Encoding UTF8 "output/CLINE_COMMIT_F3B.md"
  @{ status = "noop"; time = $now; branch = (git rev-parse --abbrev-ref HEAD); head = (git rev-parse HEAD) } |
    ConvertTo-Json -Depth 6 | Out-File -Encoding UTF8 "output/CLINE_COMMIT_F3B.json"
  Write-Output "F3B_PUSH_NOOP"
  exit 0
}

# Commit
$subject = "feat(f3b-quotes): add vendor quote schemas, parser stub, and compare script + UAT training notes (sync-only)"
git commit -m $subject | Out-Null

# Tag and push (annotated)
$head = (git rev-parse HEAD).Trim()
git tag -a -f chkpt-f3b -m "F3b vendor quotes compare scaffolding" $head
git push origin master --follow-tags

# Audit
$short = (git rev-parse --short HEAD).Trim()
@"
# PUSH_RESULT_F3B
- Branch: $(git rev-parse --abbrev-ref HEAD)
- Commit: $head
- Tag: chkpt-f3b ($short)
- Files committed:
$($pending -join "`r`n")
"@ | Out-File -Encoding UTF8 "output/PUSH_RESULT_F3B.md"

Write-Output ("F3B_PUSH_OK sha=" + $head)
