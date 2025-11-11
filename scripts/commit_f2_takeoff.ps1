# CLINE SUPERVISED COMMIT + PUSH — F2 Takeoff
# Stages F2 artifacts, commits with exact file list in body, pushes to origin/master, tags checkpoint.

$ErrorActionPreference = "Stop"
Set-Location "C:\Users\natha\dev\repos\jcw-estimator-pro"

# Files to stage (exact per plan)
$paths = @(
  "web/backend/takeoff_engine.py",
  "web/backend/blueprint_parsers/pdf_titleblock.py",
  "schemas/takeoff_request.schema.json",
  "schemas/takeoff_response.schema.json",
  "openapi/contracts/takeoff.v1.contract.json",
  "tests/unit/test_takeoff_engine.py",
  "scripts/smoke_takeoff_v1.ps1",
  "docs/ESTIMATING_PIPELINE.md",
  "data/blueprints/LYNN-001.sample.placeholder.txt",
  "web/backend/app_comprehensive.py",
  "requirements.txt"
)

git add $paths | Out-Null

# Pending staged list
$pending = @(git diff --cached --name-only)

New-Item -ItemType Directory -Force -Path "output" | Out-Null

if ($pending.Count -eq 0) {
  $now = Get-Date -Format "o"
  @"
# CLINE_COMMIT_F2 (noop)
- Status: nothing to commit (index clean)
- Time: $now
- Branch: $(git rev-parse --abbrev-ref HEAD)
- Head: $(git rev-parse HEAD)
"@ | Out-File -Encoding UTF8 "output/CLINE_COMMIT_F2.md"
  @{ status = "noop"; time = $now; branch = (git rev-parse --abbrev-ref HEAD); head = (git rev-parse HEAD) } |
    ConvertTo-Json -Depth 6 | Out-File -Encoding UTF8 "output/CLINE_COMMIT_F2.json"
  exit 0
}

# Commit message
$subject = "feat(f2-takeoff): minimal PDF plan reader and /v1/takeoff + smoke (dev)"
$body = @'
- add web/backend/takeoff_engine.py
- add web/backend/blueprint_parsers/pdf_titleblock.py
- add schemas/takeoff_request.schema.json
- add schemas/takeoff_response.schema.json
- add openapi/contracts/takeoff.v1.contract.json
- add tests/unit/test_takeoff_engine.py
- add scripts/smoke_takeoff_v1.ps1
- add docs/ESTIMATING_PIPELINE.md (F2)
- add data/blueprints/LYNN-001.sample.placeholder.txt
- modify web/backend/app_comprehensive.py
- update requirements.txt (pdfminer.six, jsonschema)
'@

# Local commit
git commit -m $subject -m $body | Out-Null

# Prepare push request audit
$branch = (git rev-parse --abbrev-ref HEAD).Trim()
$head   = (git rev-parse HEAD).Trim()
$now1   = Get-Date -Format "yyyy-MM-ddTHH:mm:ssK"
@"
# PUSH_REQUEST_F2
- Time: $now1
- Branch: $branch
- Local HEAD: $head
- Action: push origin $branch (commit + tag)
"@ | Out-File -Encoding UTF8 "output/PUSH_REQUEST_F2.md"

# Tag and push
$short = (git rev-parse --short HEAD).Trim()
$tag = "chkpt-f2-$short"
try { git tag -f $tag $head | Out-Null } catch {}

git push origin $branch
git push origin $tag

# Post-push audit
$remoteHead = git ls-remote origin "refs/heads/$branch" | ForEach-Object { ($_ -split "`t")[0] }
$now2 = Get-Date -Format "yyyy-MM-ddTHH:mm:ssK"

@"
# PUSH_RESULT_F2
- Time: $now2
- Branch: $branch
- Local HEAD: $head
- Remote HEAD: $remoteHead
- Tag: $tag

## Files committed
$($pending -join "`r`n")
"@ | Out-File -Encoding UTF8 "output/PUSH_RESULT_F2.md"

@{
  result = "pushed"
  time = $now2
  branch = $branch
  local_head = $head
  remote_head = $remoteHead
  tag = $tag
  files = $pending
} | ConvertTo-Json -Depth 6 | Out-File -Encoding UTF8 "output/PUSH_RESULT_F2.json"

Write-Host "F2_PUSH_OK`nbranch=$branch`nsha=$head`ntag=$tag`nendpoint=/v1/takeoff"
