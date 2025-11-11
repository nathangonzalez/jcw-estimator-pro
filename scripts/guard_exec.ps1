param([string]$Cmd)

$state = Get-Content -Path 'output/guard_state.json' | ConvertFrom-Json

$startTime = [DateTime]::Parse($state.startTime)

$timeElapsed = (Get-Date) - $startTime

if ($timeElapsed.TotalMinutes -gt 12) {

    Write-Host "Time limit exceeded"

    exit 1

}

if ($state.commandCount -ge 6) {

    Write-Host "Command limit exceeded"

    exit 1

}

Write-Host "Executing command $($state.commandCount + 1): $Cmd"

try {

    Invoke-Expression $Cmd

    $state.commandCount++

    $state | ConvertTo-Json | Set-Content -Path 'output/guard_state.json'

} catch {

    Write-Host "Command failed: $_"

    exit 1

}
