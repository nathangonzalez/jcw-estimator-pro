$ErrorActionPreference="Stop"

$root = Split-Path -Parent $PSCommandPath
Set-Location (Resolve-Path "$root\..")  # repo root

$clDir = "output/agents/CLINE/events"
$gmDir = "output/agents/GEMINI/events"
$all = @()
if (Test-Path $clDir) { $all += Get-ChildItem $clDir -Filter *.json -File }
if (Test-Path $gmDir) { $all += Get-ChildItem $gmDir -Filter *.json -File }

if ($all.Count -eq 0) {
  Write-Host "No events yet."
  exit 0
}

# Load + sort by ts
$events = $all | ForEach-Object {
  $o = Get-Content $_.FullName -Raw | ConvertFrom-Json
  $o | Add-Member NoteProperty __path $_.FullName
  $o
} | Sort-Object { [DateTime]$_.ts }

# Update FEED
$feedPath = "output/AGENTS_FEED.md"
"# Agents Feed (most recent last)" | Set-Content -Path $feedPath -Encoding UTF8
"" | Add-Content -Path $feedPath -Encoding UTF8
foreach ($e in $events) {
  $art = ($e.artifacts -join ", ")
  $line = "- **[$($e.agent)] $($e.status)** - $($e.title)"
  Add-Content -Path $feedPath -Value $line
  $line = "  ts: $($e.ts)  branch: $($e.branch)  sha: $($e.sha)"
  Add-Content -Path $feedPath -Value $line
  if ($art) {
    $line = "  artifacts: $art"
    Add-Content -Path $feedPath -Value $line
  }
  if ($e.notes) {
    $notes = $e.notes -replace '\r?\n',' '
    $line = "  notes: $notes"
    Add-Content -Path $feedPath -Value $line
  }
  "" | Add-Content -Path $feedPath -Encoding UTF8
}

# Update STATE (last entry per agent)
$state = [ordered]@{}
foreach ($agent in @("CLINE","GEMINI")) {
  $last = $events | Where-Object { $_.agent -eq $agent } | Select-Object -Last 1
  if ($last) { $state[$agent] = $last }
}
$statePath = "output/AGENTS_STATE.json"
$state | ConvertTo-Json -Depth 6 | Set-Content -Path $statePath -Encoding UTF8

Write-Host "Updated $feedPath and $statePath"
