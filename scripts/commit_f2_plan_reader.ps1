# CLINE SUPERVISED COMMIT + PUSH — F2 Plan Reader (DEV-FAST)
# Stages F2 Plan Reader artifacts, commits with exact file list in body, pushes to origin/master, tags checkpoint.

$ErrorActionPreference = "Stop"
Set-Location "C:\Users\natha\dev\repos\jcw-estimator-pro"

# Files to stage (exact per plan)
$paths = @(
  "schemas/plan_features.schema.json",
  "web/backend/plan_reader.py",
  "web/backend/app_comprehensive.py",
  "openapi/contracts/plan.features.v1.contract.json",
  "data/plan/README.md",
  "scripts/run_plan_reader_local.ps1",
  "tests/unit/test_plan_reader.py",
  "docs/ESTIMATING_DATA_FLOW.md",
  "output/AGENT_SYNC.md"
)

git add $paths | Out-Null

# Pending staged list
$pending = @(git diff --cached --name-only)

New-Item -ItemType Directory -Force -Path "output" | Out-Null

if ($pending.Count -eq 0) {
  $now = Get-Date -Format "o"
  @"
# CLINE_COMMIT_F2_PLAN (noop)
- Status: nothing to commit (index clean)
- Time: $now
- Branch: $(git rev-parse --abbrev-ref HEAD)
- Head: $(git rev-parse HEAD)
"@ | Out-File -Encoding UTF8 "output/CLINE_COMMIT_F2_PLAN.md"
  @{ status = "noop"; time = $now; branch = (git rev-parse --abbrev-ref HEAD); head = (git rev-parse HEAD) } |
    ConvertTo-Json -Depth 6 | Out-File -Encoding UTF8 "output/CLINE_COMMIT_F2_PLAN.json"
  exit 0
}

# Commit message
$subject = "feat(f2-plan-reader): add minimal plan features extractor + /v1/plan/features (dev-fast)"
$body = @'
- add schemas/plan_features.schema.json
- add web/backend/plan_reader.py
- modify web/backend/app_comprehensive.py (add /v1/plan/features)
- add openapi/contracts/plan.features.v1.contract.json
- add data/plan/README.md
- add scripts/run_plan_reader_local.ps1
- add tests/unit/test_plan_reader.py (no-run scaffold)
- add docs/ESTIMATING_DATA_FLOW.md
- update output/AGENT_SYNC.md (append F2 entry)
'@

# Local commit
git commit -m $subject -m $body | Out-Null

# Prepare push request audit
$branch = (git rev-parse --abbrev-ref HEAD).Trim()
$head   = (git rev-parse HEAD).Trim()
$now1   = Get-Date -Format "yyyy-MM-ddTHH:mm:ssK"
@"
# PUSH_REQUEST_F2_PLAN
- Time: $now1
- Branch: $branch
- Local HEAD: $head
- Action: push origin $branch (commit + tag)
"@ | Out-File -Encoding UTF8 "output/PUSH_REQUEST_F2_PLAN.md"

# Tag and push
$short = (git rev-parse --short HEAD).Trim()
$tag = "chkpt-f2-plan-$short"
try { git tag -f $tag $head | Out-Null } catch {}

git push origin $branch
git push origin $tag

# Post-push audit
$remoteHead = git ls-remote origin "refs/heads/$branch" | ForEach-Object { ($_ -split "`t")[0] }
$now2 = Get-Date -Format "yyyy-MM-ddTHH:mm:ssK"

@"
# PUSH_RESULT_F2_PLAN
- Time: $now2
- Branch: $branch
- Local HEAD: $head
- Remote HEAD: $remoteHead
- Tag: $tag

## Files committed
$($pending -join "`r`n")
"@ | Out-File -Encoding UTF8 "output/PUSH_RESULT_F2_PLAN.md"

@{
  result = "pushed"
  time = $now2
  branch = $branch
  local_head = $head
  remote_head = $remoteHead
  tag = $tag
  files = $pending
} | ConvertTo-Json -Depth 6 | Out-File -Encoding UTF8 "output/PUSH_RESULT_F2_PLAN.json"

Write-Host "F2_PLAN_PUSH_OK`nbranch=$branch`nsha=$head`ntag=$tag`nendpoint=/v1/plan/features"
