# Check for approval gate
if (-not (Test-Path "approvals/EXEC_OK")) {
    New-Item -ItemType Directory -Force -Path "output" | Out-Null
    "Execution not approved. Create approvals/EXEC_OK to proceed." | Out-File "output/UELTCHI_WAITING.md"
    exit 1
}

# Run importers
python scripts/import_estimate_template.py --template-path "data/templates/estimating/Estimating Sheet for Jack 9.28.23.xls"
python scripts/import_schedule_template.py --template-path "data/templates/schedule/Schedule Blank.xls"

# Run output generators
python scripts/make_estimate_outputs.py
python scripts/make_schedule_outputs.py

# Write receipts
$estimate_lines = Get-Content "data/ueltchi/working/estimate_lines.v0.json" | ConvertFrom-Json
$schedule_tasks = Get-Content "data/ueltchi/working/schedule_tasks.v0.json" | ConvertFrom-Json

$status = @{
    estimate_lines = $estimate_lines.Count
    schedule_tasks = $schedule_tasks.Count
    total_estimate = ($estimate_lines | Measure-Object -Property line_total -Sum).Sum
}

$status | ConvertTo-Json | Out-File "output/UELTCHI_STATUS.json"

@"
# Ueltchi MVP Smoke Test Receipt

- Estimate Lines: $($status.estimate_lines)
- Schedule Tasks: $($status.schedule_tasks)
- Total Estimate: $($status.total_estimate)
"@ | Out-File "output/UELTCHI_MVP_RECEIPT.md"
