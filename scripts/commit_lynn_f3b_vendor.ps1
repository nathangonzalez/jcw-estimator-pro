# Commit Lynn F3b vendor parsing + compare artifacts; push and tag (no force)
param()

$ErrorActionPreference = 'Stop'

# Stage code
$files = @(
  'web/backend/vendor_quote_parser_lynn.py',
  'scripts/lynn_vendor_compare_v0.py'
)

foreach ($f in $files) {
  if (Test-Path $f) { git add -- $f | Out-Null }
}

# Stage generated artifacts under data/lynn/working if present
$working = 'data/lynn/working'
$patterns = @(
  "$working/vendor/rows/*.rows.json",
  "$working/vendor/rows/*.rows.csv",
  "$working/vendor_quotes.canonical.csv",
  "$working/vendor_quotes.canonical.json",
  "$working/vendor_vs_estimate.csv",
  "$working/vendor_vs_estimate.json",
  "$working/VENDOR_COMPARE_SUMMARY.md"
)
foreach ($pat in $patterns) {
  Get-ChildItem -Path $pat -ErrorAction SilentlyContinue | ForEach-Object {
    git add -- $_.FullName | Out-Null
  }
}

# Commit (continue if nothing to commit)
$MSG = 'feat(lynn-f3b): vendor parsing → canonical + compare vs RAW estimate'
try {
  git commit -m $MSG | Out-Null
} catch {
  Write-Host "Commit encountered an issue (possibly no changes). Continuing. $_"
}

# Push (no force)
git push origin master | Out-Null

# Tag checkpoint and push tags
$shaShort = (git rev-parse --short HEAD).Trim()
$tag = "chkpt-lynn-f3b-$shaShort"
try { git tag -f $tag | Out-Null } catch {}
git push origin --tags | Out-Null

# Record SHA
New-Item -ItemType Directory -Force -Path 'output' | Out-Null
$sha = (git rev-parse HEAD).Trim()
Set-Content -Path 'output\CLINE_LAST_COMMIT_SHA.txt' -Value $sha -Encoding ascii

Write-Host ("LYNN_F3B_COMMIT {0} TAG {1}" -f $sha, $tag)
