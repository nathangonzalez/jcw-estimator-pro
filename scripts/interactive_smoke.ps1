# Interactive Smoke Test
# Calls /v1/plan/assess and /v1/estimate?mode=interactive
# Writes receipts to output/INTERACTIVE/

$ErrorActionPreference = 'Stop'

# Create output dir
New-Item -ItemType Directory -Force -Path 'output/INTERACTIVE' | Out-Null

# Assess
$assessResponse = Invoke-RestMethod -Method Post -Uri 'http://localhost:8000/v1/plan/assess' -Body (@{ project_id = 'smoke_test'; pdf_path = 'dummy.pdf' } | ConvertTo-Json) -ContentType 'application/json'
$assessResponse | ConvertTo-Json -Depth 10 | Out-File 'output/INTERACTIVE/ASSESS.json'

# Estimate interactive
$estimateResponse = Invoke-RestMethod -Method Post -Uri 'http://localhost:8000/v1/estimate' -Body (@{ mode = 'interactive'; project_id = 'smoke_test'; region = 'default'; quality = 'standard'; complexity = 'normal' } | ConvertTo-Json) -ContentType 'application/json'
$estimateResponse | ConvertTo-Json -Depth 10 | Out-File 'output/INTERACTIVE/ESTIMATE.json'

# Receipt
$receipt = @"
# Interactive Smoke Receipt

Timestamp: $(Get-Date -Format o)

Assess Response: $($assessResponse.trades_inferred.Count) trades inferred

Estimate Response: Total cost $($estimateResponse.total_cost)

Interactive Metadata: $($estimateResponse.metadata.interactive.questions_count) questions, $($estimateResponse.metadata.interactive.unresolved_count) unresolved

"@
$receipt | Out-File 'output/INTERACTIVE/RECEIPT.md'
