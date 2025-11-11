# Commit and push CI Gut-Check workflow and wrapper, robustly
param()

$ErrorActionPreference = 'Stop'

# Files to stage
$files = @(
  '.github/workflows/gutcheck.yml',
  'scripts/ci_gutcheck.py'
)

foreach ($f in $files) {
  if (Test-Path $f) { git add -- $f | Out-Null }
}

# Commit (continue if nothing to commit)
try {
  git commit -m "chore(ci): add read-only Gut-Check workflow and script" | Out-Null
} catch {
  Write-Host "Commit encountered an issue (possibly no changes). Continuing. $_"
}

# Push
git push origin master | Out-Null

# Record SHA
$sha = git rev-parse HEAD
Set-Content -Path 'output\CLINE_LAST_COMMIT_SHA.txt' -Value $sha -Encoding ascii
Write-Host ("NEW_CI_COMMIT {0}" -f $sha)
