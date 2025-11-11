# CLINE SUPERVISED PUSH — NO EXECUTION, JUST GIT NETWORK I/O
# Scope:
# - Push current local HEAD to origin/master
# - Write push audit artifacts
# - (Optional) create a lightweight tag for this F1 checkpoint

$ErrorActionPreference = "Stop"
Set-Location "C:\Users\natha\dev\repos\jcw-estimator-pro"

# 0) Snapshot pre-push
$branch = git rev-parse --abbrev-ref HEAD
$head   = git rev-parse HEAD
$now    = Get-Date -Format "yyyy-MM-ddTHH:mm:ssK"

New-Item -ItemType Directory -Force -Path output | Out-Null
@"
# PUSH_REQUEST
- Time: $now
- Branch: $branch
- Local HEAD: $head
- Action: push origin $branch (no tests / no installs / no servers)
"@ | Out-File -Encoding UTF8 output/PUSH_REQUEST.md

# 1) Optional: create/update a lightweight tag for this checkpoint (safe if already exists)
$tag = "chkpt-f1-" + $head.Substring(0,7)
try { git tag -f $tag $head | Out-Null } catch {}

# 2) Push branch and tag
git push origin $branch
git push origin $tag

# 3) Record post-push state
$remoteHead = git ls-remote origin "refs/heads/$branch" | ForEach-Object { ($_ -split "`t")[0] }
$now2 = Get-Date -Format "yyyy-MM-ddTHH:mm:ssK"

@"
# PUSH_RESULT
- Time: $now2
- Branch: $branch
- Local HEAD: $head
- Remote HEAD: $remoteHead
- Tag: $tag
"@ | Out-File -Encoding UTF8 output/PUSH_RESULT.md

@{
  result = "pushed"
  time = $now2
  branch = $branch
  local_head = $head
  remote_head = $remoteHead
  tag = $tag
} | ConvertTo-Json -Depth 6 | Out-File -Encoding UTF8 output/PUSH_RESULT.json
