# UAT R2 Runner
# Start API if needed (placeholder)
# Run Playwright tests

npx playwright test tests/e2e/uat.r2.spec.ts --reporter=json | Out-File -FilePath output/UAT_R2_STATUS.json -Encoding UTF8

# Write receipt
$status = Get-Content output/UAT_R2_STATUS.json | ConvertFrom-Json
$exitCode = if ($status.stats.failures -gt 0) { 1 } else { 0 }

$receipt = @"
# UAT R2 Receipt

Timestamp: $(Get-Date -Format 'yyyy-MM-ddTHH:mm:ssK')

Exit Code: $exitCode

Passed: $($status.stats.passes)

Failed: $($status.stats.failures)

Total: $($status.stats.tests)

"@

$receipt | Out-File -FilePath output/UAT_R2_RECEIPT.md -Encoding UTF8
