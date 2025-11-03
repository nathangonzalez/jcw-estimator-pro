# scripts/smoke_estimate_v1.ps1
# Sends a minimal valid JSON request to /v1/estimate and prints status + body.

param(
  [string]$BaseUrl = "http://localhost:8000",
  [string]$Endpoint = "/v1/estimate"
)

$uri = "$BaseUrl$Endpoint"

# NOTE: Align these fields to the FastAPI/Pydantic schema you implemented.
# If additional fields are required, add them here (and keep types JSON-safe).
$bodyObj = @{
  square_footage = 5000
  project_type   = "Residential"
  finish_quality = "Standard"
  complexity     = "Moderate"
  bedrooms       = 0
  bathrooms      = 0
  features       = @()   # e.g., ["Pool","Elevator"]
}

# Convert to JSON (depth > 2 for nested objects/arrays)
$bodyJson = $bodyObj | ConvertTo-Json -Depth 8

try {
  $response = Invoke-RestMethod -Uri $uri -Method POST `
    -ContentType "application/json; charset=utf-8" `
    -Body $bodyJson

  Write-Host "HTTP: 200 OK"
  $response | ConvertTo-Json -Depth 8
  exit 0
}
catch {
  if ($_.Exception.Response -ne $null) {
    $status = $_.Exception.Response.StatusCode.value__
    $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
    $errBody = $reader.ReadToEnd()
    Write-Host ("HTTP: {0}`n{1}" -f $status, $errBody)
  } else {
    Write-Host ("HTTP: ERROR`n{0}" -f $_.Exception.Message)
  }
  exit 1
}
