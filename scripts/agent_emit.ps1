param(
  [Parameter(Mandatory=$true)][ValidateSet("CLINE","GEMINI")]$Agent,
  [Parameter(Mandatory=$true)][string]$Title,
  [Parameter(Mandatory=$true)][ValidateSet("OK","FAIL","INFO","PENDING")]$Status,
  [string[]]$Artifacts=@(),
  [string]$Notes=""
)

$ErrorActionPreference="Stop"

# Determine repo context
$branch = (git rev-parse --abbrev-ref HEAD) 2>$null
$sha = (git rev-parse HEAD) 2>$null
$ts = (Get-Date).ToString("o")
$stamp = (Get-Date).ToString("yyyyMMdd_HHmmss")

# Ensure dirs
$evtDir = "output/agents/$Agent/events"
$null = New-Item -ItemType Directory -Force -Path $evtDir, "output" | Out-Null

# Build event object
$event = [ordered]@{
  agent     = $Agent
  ts        = $ts
  branch    = $branch
  sha       = $sha
  status    = $Status
  title     = $Title
  artifacts = $Artifacts
  notes     = $Notes
}

# Write event json
$slug = ($Title -replace '[^\w\-]+','-').Trim('-').ToLower()
if ([string]::IsNullOrWhiteSpace($slug)) { $slug = "event" }
$evtPath = Join-Path $evtDir "$stamp`_$slug.json"
$event | ConvertTo-Json -Depth 6 | Set-Content -Path $evtPath -Encoding UTF8

Write-Host "Wrote $evtPath"
