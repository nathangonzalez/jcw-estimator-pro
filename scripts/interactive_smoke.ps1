# Interactive Smoke Test
# Calls /v1/interactive/assess, /v1/interactive/qna, /v1/interactive/estimate
# Writes receipts to output/INTERACTIVE/

$ErrorActionPreference = 'Stop'

# Resolve repo root
$repoRoot = Split-Path -Parent $PSScriptRoot

# Create output dir
New-Item -ItemType Directory -Force -Path 'output/INTERACTIVE' | Out-Null

# Load quantities
$quantitiesPath = Join-Path $repoRoot 'data/quantities.sample.json'
$quantities = Get-Content $quantitiesPath | ConvertFrom-Json

# Assess
try {
    $assessBody = @{ project_id = 'LYNN-001'; goal = 'baseline' } | ConvertTo-Json
    $assessResponse = Invoke-RestMethod -Method Post -Uri 'http://127.0.0.1:8001/v1/interactive/assess' -Body $assessBody -ContentType 'application/json'
    $assessResponse | ConvertTo-Json -Depth 10 | Out-File 'output/INTERACTIVE/ASSESS.json'
} catch {
    @{ status = $_.Exception.Response.StatusCode; text = $_.Exception.Message } | ConvertTo-Json | Out-File 'output/INTERACTIVE/ERROR_ASSESS.json'
}

# QnA
try {
    $qnaBody = @{ project_id = 'LYNN-001'; answers = @() } | ConvertTo-Json
    $qnaResponse = Invoke-RestMethod -Method Post -Uri 'http://127.0.0.1:8001/v1/interactive/qna' -Body $qnaBody -ContentType 'application/json'
    $qnaResponse | ConvertTo-Json -Depth 10 | Out-File 'output/INTERACTIVE/QNA.json'
} catch {
    @{ status = $_.Exception.Response.StatusCode; text = $_.Exception.Message } | ConvertTo-Json | Out-File 'output/INTERACTIVE/ERROR_QNA.json'
}

# Estimate
try {
    $estimateBody = @{
        project_id = 'LYNN-001'
        quantities = $quantities
        policy = 'schemas/pricing_policy.v0.yaml'
        unit_costs_csv = 'data/unit_costs.sample.csv'
        vendor_quotes_csv = $null
    } | ConvertTo-Json -Depth 10
    $estimateResponse = Invoke-RestMethod -Method Post -Uri 'http://127.0.0.1:8001/v1/interactive/estimate' -Body $estimateBody -ContentType 'application/json'
    $estimateResponse | ConvertTo-Json -Depth 10 | Out-File 'output/INTERACTIVE/ESTIMATE.json'
} catch {
    @{ status = $_.Exception.Response.StatusCode; text = $_.Exception.Message } | ConvertTo-Json | Out-File 'output/INTERACTIVE/ERROR_ESTIMATE.json'
}

# Receipt
$receipt = @"
# Interactive Smoke Receipt

Timestamp: $(Get-Date -Format o)

Assess: $(if (Test-Path 'output/INTERACTIVE/ASSESS.json') { 'OK' } else { 'ERROR' })
QnA: $(if (Test-Path 'output/INTERACTIVE/QNA.json') { 'OK' } else { 'ERROR' })
Estimate: $(if (Test-Path 'output/INTERACTIVE/ESTIMATE.json') { 'OK' } else { 'ERROR' })

"@
$receipt | Out-File 'output/INTERACTIVE/INTERACTIVE_RECEIPT.md'
