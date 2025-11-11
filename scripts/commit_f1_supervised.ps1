# CLINE SUPERVISED COMMIT — COMMIT ONLY (NO PUSH)
# Stages F1 + high-context artifacts, writes commit notes, performs local commit only.

$ErrorActionPreference = "Stop"

# Move to repo root based on script location
Set-Location (Join-Path $PSScriptRoot "..")

# 1) Stage files (idempotent)
$paths = @(
  "web/backend/pricing_engine.py",
  "web/backend/app_comprehensive.py",
  "tests/unit/test_pricing_engine.py",
  "data/unit_costs.sample.csv",
  "data/vendor_quotes.sample.csv",
  "output/AGENT_SYNC.md",
  "prompts/MAXI_SUPERPROMPT.md",
  "scripts/high_context_session.ply",
  "output/CTX_INDEX.json",
  "output/CTX_SUMMARY.md",
  "output/TOKEN_POLICY.md",
  "scripts/audit_m01.ps1"
)

git add $paths | Out-Null

# 2) Pending list
$pending = @(git diff --cached --name-only)

# Ensure output directory
New-Item -ItemType Directory -Force -Path "output" | Out-Null

# 3) If nothing to commit, write noop notes and exit 0
if ($pending.Count -eq 0) {
  $now = Get-Date -Format "o"
  $branch = git rev-parse --abbrev-ref HEAD
  $head = git rev-parse HEAD

  @"
# CLINE_COMMIT (noop)
- Status: nothing to commit (index clean)
- Time: $now
- Branch: $branch
- Head: $head
"@ | Out-File -Encoding UTF8 "output/CLINE_COMMIT.md"

  @{ status = "noop"; time = $now; branch = $branch; head = $head } |
    ConvertTo-Json -Depth 6 | Out-File -Encoding UTF8 "output/CLINE_COMMIT.json"
  exit 0
}

# 4) Commit locally with provided message file
git commit -F "COMMIT_F1.txt" | Out-Null

# 5) Write commit audit artifacts
$now = Get-Date -Format "o"
$branch = git rev-parse --abbrev-ref HEAD
$head = git rev-parse HEAD

@"
# CLINE_COMMIT
- Result: committed locally (no push)
- Time: $now
- Branch: $branch
- Commit: $head

## Files staged
$($pending -join "`r`n")
"@ | Out-File -Encoding UTF8 "output/CLINE_COMMIT.md"

@{
  result = "committed"
  time = $now
  branch = $branch
  commit = $head
  files = $pending
} | ConvertTo-Json -Depth 6 | Out-File -Encoding UTF8 "output/CLINE_COMMIT.json"
