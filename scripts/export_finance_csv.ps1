# Finance Export Runner v0
# Calls Python script to export estimate data to finance-ready CSVs

Write-Host "Starting Finance Export v0..."

try {
    # Run the Python export script
    python scripts/export_finance_csv.py

    if ($LASTEXITCODE -eq 0) {
        Write-Host "Finance export completed successfully!"

        # Check if files were created
        $files = @(
            "output/finance/estimate_export.csv",
            "output/finance/sov_seed.csv",
            "output/finance/forecast_seed.csv",
            "output/FINANCE_RECEIPT.md"
        )

        Write-Host "Generated files:"
        foreach ($file in $files) {
            if (Test-Path $file) {
                Write-Host "  ✓ $file"
            } else {
                Write-Host "  ✗ $file (missing)"
            }
        }
    } else {
        Write-Host "Finance export failed with exit code $LASTEXITCODE"
        exit $LASTEXITCODE
    }
} catch {
    Write-Host "Error running finance export: $($_.Exception.Message)"
    exit 1
}
