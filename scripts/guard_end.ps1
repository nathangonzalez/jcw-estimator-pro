$state = Get-Content -Path 'output/guard_state.json' | ConvertFrom-Json

$startTime = [DateTime]::Parse($state.startTime)

$timeElapsed = (Get-Date) - $startTime

Write-Host "Session ended. Commands: $($state.commandCount), Time: $($timeElapsed.TotalMinutes) minutes"

if ($state.commandCount -gt 6 -or $timeElapsed.TotalMinutes -gt 12) {

    exit 1

}

Remove-Item -Path 'output/guard_state.json'
