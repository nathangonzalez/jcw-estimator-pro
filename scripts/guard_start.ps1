$state = @{
    commandCount = 0
    startTime = (Get-Date).ToString()
}
$state | ConvertTo-Json | Set-Content -Path 'output/guard_state.json'
Write-Host "Guard started"
