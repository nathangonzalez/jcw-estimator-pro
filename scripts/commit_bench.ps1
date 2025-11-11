# Commit and push BENCH artifacts with robust logging
param()

$ErrorActionPreference = 'Stop'

# Paths to stage
$files = @(
  'web/backend/benchmarking.py',
  'output/BENCH/LYNN_GUTCHECK.json',
  'output/BENCH/LYNN_GUTCHECK.md'
)

# Stage files (ignore missing individually)
foreach ($f in $files) {
  if (Test-Path $f) { git add -- $f | Out-Null }
}

# Try to commit; if nothing to commit, continue
try {
  git commit -m "chore(bench): add LYNN gut-check metrics and report (read-only)" | Out-Null
} catch {
  Write-Host "Commit step encountered an issue (likely no changes). Continuing. $_"
}

# Push
git push origin master | Out-Null

# Record SHA
$sha = git rev-parse HEAD
Set-Content -Path 'output\CLINE_LAST_COMMIT_SHA.txt' -Value $sha -Encoding ascii

Write-Host ("NEW_BENCH_COMMIT {0}" -f $sha)
