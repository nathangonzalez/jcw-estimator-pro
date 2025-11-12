param(
    [int]$Port = 8000,
    [string]$Directory = "."
)

Write-Host "Starting local HTTP server..."
Write-Host "Directory: $Directory"
Write-Host "Port: $Port"
Write-Host ""

# Check if Python is available
try {
    $pythonVersion = & python --version 2>&1
    if ($pythonVersion -match "Python") {
        Write-Host "Found Python: $pythonVersion"
        Write-Host "Starting server at http://127.0.0.1:$Port"
        Write-Host "Press Ctrl+C to stop"
        Write-Host ""

        # Change to directory and start server
        Push-Location $Directory
        try {
            & python -m http.server $Port
        } finally {
            Pop-Location
        }
    } else {
        throw "Python not found"
    }
} catch {
    Write-Host "Python not available. Opening directory in Explorer instead..."
    Write-Host ""
    Write-Host "To view files locally, you can:"
    Write-Host "1. Open $Directory in File Explorer"
    Write-Host "2. Double-click HTML/Markdown files to open in browser"
    Write-Host "3. For videos, use your default media player"
    Write-Host ""
    Write-Host "To install Python for local serving:"
    Write-Host "- Download from: https://python.org/downloads/"
    Write-Host "- Or use: winget install python.python.3.11"
    Write-Host ""

    # Open directory in explorer
    if (Test-Path $Directory) {
        Start-Process explorer.exe $Directory
    } else {
        Write-Error "Directory not found: $Directory"
    }
}
