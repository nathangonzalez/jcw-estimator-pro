# CLINE SUPERVISED COMMIT + PUSH — F3 Pipeline Smoke
# Stages pipeline artifacts, commits, pushes with annotated tag chkpt-f3.

$ErrorActionPreference = "Stop"
Set-Location "C:\Users\natha\dev\repos\jcw-estimator-pro"

# Files to stage
$paths = @(
  "data/fixtures.rules.yaml",
  "web/backend/takeoff_engine.py",
  "scripts/pipeline_smoke.ps1",
  "scripts/make_junit.ps1",
  "web/backend/app_comprehensive.py",
  "docs/PIPELINE_SMOKE.md"
)

git add $paths | Out-Null

# Pending staged list
$pending = @(git diff --cached --name-only)

New-Item -ItemType Directory -Force -Path "output" | Out-Null

if ($pending.Count -eq 0) {
  $now = Get-Date -Format "o"
  @"
# CLINE_COMMIT_F3 (noop)
- Status: nothing to commit (index clean)
- Time: $now
- Branch: $(git rev-parse --abbrev-ref HEAD)
- Head: $(git rev-parse HEAD)
"@ | Out-File -Encoding UTF8 "output/CLINE_COMMIT_F3.md"
  @{ status = "noop"; time = $now; branch = (git rev-parse --abbrev-ref HEAD); head = (git rev-parse HEAD) } |
    ConvertTo-Json -Depth 6 | Out-File -Encoding UTF8 "output/CLINE_COMMIT_F3.json"
  Write-Output "F3_PUSH_NOOP"
  exit 0
}

# Commit
$subject = "feat(f3-pipeline): one-shot plan→takeoff→estimate smoke + fixtures rules and stricter M01 validation"
git commit -m $subject | Out-Null

# Tag and push (annotated)
$head = (git rev-parse HEAD).Trim()
git tag -a -f chkpt-f3 -m "F3 pipeline smoke" $head
git push origin master --follow-tags

# Audit
$short = (git rev-parse --short HEAD).Trim()
@"
# PUSH_RESULT_F3
- Branch: $(git rev-parse --abbrev-ref HEAD)
- Commit: $head
- Tag: chkpt-f3 ($short)
- Files committed:
$($pending -join "`r`n")
"@ | Out-File -Encoding UTF8 "output/PUSH_RESULT_F3.md"

Write-Output ("F3_PUSH_OK sha=" + $head)
