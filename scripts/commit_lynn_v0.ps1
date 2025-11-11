# Commit Lynn v0 ingest/baseline artifacts and push (no force), printing SHA
param()

$ErrorActionPreference = 'Stop'

# Files to stage for Lynn v0 package
$files = @(
  'docs/LYNN_README.md',
  'data/lynn/vendor_rules.yaml',
  'data/lynn/raw/plans/.gitkeep',
  'data/lynn/raw/vendor/.gitkeep',
  'data/lynn/raw/other/.gitkeep',
  'data/lynn/working/.gitkeep',
  'data/lynn/_archive/.gitkeep',
  'scripts/ingest_lynn.py',
  'scripts/lynn_takeoff_v0.py',
  'scripts/lynn_estimate_v0.py',
  'scripts/lynn_gutcheck_v0.py'
)

foreach ($f in $files) {
  if (Test-Path $f) { git add -- $f | Out-Null }
}

# Commit (continue if nothing to commit)
$MSG = 'feat(lynn-v0): ingest registry + plan features + RAW estimate + gutcheck'
try {
  git commit -m $MSG | Out-Null
} catch {
  Write-Host "Commit encountered an issue (possibly no changes). Continuing. $_"
}

# Push (no force)
git push origin master | Out-Null

# Record SHA and echo
$sha = (git rev-parse HEAD).Trim()
New-Item -ItemType Directory -Force -Path 'output' | Out-Null
Set-Content -Path 'output\CLINE_LAST_COMMIT_SHA.txt' -Value $sha -Encoding ascii
Write-Host ("LYNN_V0_COMMIT {0}" -f $sha)
