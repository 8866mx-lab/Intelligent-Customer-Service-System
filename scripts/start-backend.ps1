# Customer Service - start backend (dev port 8099)
# Usage: cd <project>\scripts ; .\start-backend.ps1
# Keep this window open. Ctrl+C to stop.

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$BackendDir = Join-Path $ProjectRoot "backend"
$VenvPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"

if (-not (Test-Path $VenvPython)) {
    Write-Host "[ERROR] venv not found: $VenvPython" -ForegroundColor Red
    Write-Host "[HINT] Create .venv under project root and install backend deps." -ForegroundColor Yellow
    exit 1
}

Set-Location $BackendDir
$env:PYTHONPATH = ".."
Write-Host "[OK] Starting backend at http://127.0.0.1:8099 ..." -ForegroundColor Green
& $VenvPython -m uvicorn src.main:app --host 127.0.0.1 --port 8099 --reload
