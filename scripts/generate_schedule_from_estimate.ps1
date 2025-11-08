Param(
  [string]$EstimateCsv = "output/LYNN-001/raw_estimate/estimate_lines.csv",
  [string]$Out = "output/SCHEDULE_SAMPLE.json",
  [string]$Start = "",
  [int]$Phases = 2,
  [int]$DurationDays = 56
)

# Generate a minimal v0 schedule JSON with evenly weighted phases.
# Does not read or execute any external tools; estimate CSV is optional context.
$ErrorActionPreference = "Stop"

# Ensure output directory exists
$outDir = Split-Path -Path $Out -Parent
if ([string]::IsNullOrWhiteSpace($outDir)) { $outDir = "." }
New-Item -ItemType Directory -Force -Path $outDir | Out-Null

# Parse start date
try {
  if ([string]::IsNullOrWhiteSpace($Start)) {
    $startDate = Get-Date
  } else {
    $startDate = Get-Date $Start
  }
} catch {
  Write-Host "Invalid Start date '$Start'; using today."
  $startDate = Get-Date
}

if ($Phases -lt 1) { $Phases = 1 }
if ($DurationDays -lt 1) { $DurationDays = 28 }

$phaseDur = [math]::Max(1, [math]::Floor($DurationDays / $Phases))
$tasks = @()
$cursor = $startDate

for ($i = 0; $i -lt $Phases; $i++) {
  $pStart = $cursor
  $pEnd = $pStart.AddDays($phaseDur - 1)
  if ($i -eq ($Phases - 1)) {
    # Ensure final phase ends exactly at DurationDays - 1 from start
    $pEnd = $startDate.AddDays($DurationDays - 1)
  }
  $weight = [math]::Round(1.0 / $Phases, 4)
  $name = "Phase " + ([char]([int][char]'A' + $i))

  $tasks += [pscustomobject]@{
    name   = $name
    start  = $pStart.ToString("yyyy-MM-dd")
    end    = $pEnd.ToString("yyyy-MM-dd")
    weight = $weight
  }

  $cursor = $pEnd.AddDays(1)
}

$schedule = [pscustomobject]@{
  version = "v0"
  tasks   = $tasks
}

$schedule | ConvertTo-Json -Depth 6 | Out-File -FilePath $Out -Encoding UTF8

Write-Host ("Wrote {0} with {1} phase(s), start={2}, duration={3} days" -f $Out, $Phases, $startDate.ToString("yyyy-MM-dd"), $DurationDays)
