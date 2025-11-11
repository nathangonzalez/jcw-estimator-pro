Param()
$ErrorActionPreference = 'Stop'

# Ensure paths
New-Item -ItemType Directory -Force -Path 'prompts' | Out-Null
New-Item -ItemType Directory -Force -Path 'output'  | Out-Null

# Receipt
$shaShort = (git rev-parse --short HEAD).Trim()
$ts = Get-Date -Format o
"## R2 commit prep ($ts)" | Add-Content output/R2_INTERACTIVE_RUN.md
"HEAD(before): $shaShort"   | Add-Content output/R2_INTERACTIVE_RUN.md

# Stage & commit
git add prompts/R2_INTERACTIVE_SUPERPROMPT.md
git add scripts/commit_r2_interactive.ps1
git add output/R2_INTERACTIVE_RUN.md

git commit -m "chore(r2): persist interactive superprompt + commit helper (no-exec)"

# Post-receipt
$shaAfter = (git rev-parse --short HEAD).Trim()
"HEAD(after): $shaAfter" | Add-Content output/R2_INTERACTIVE_RUN.md

Write-Host "R2 superprompt committed: $shaAfter"
