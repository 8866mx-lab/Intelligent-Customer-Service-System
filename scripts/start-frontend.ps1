# Customer Service - start frontend (dev port 5199)
# Usage: open a NEW PowerShell window, cd <project>\scripts ; .\start-frontend.ps1
# Keep this window open. Open http://127.0.0.1:5199/login in browser.

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$FrontendDir = Join-Path $ProjectRoot "frontend"

if (-not (Test-Path (Join-Path $FrontendDir "package.json"))) {
    Write-Host "[ERROR] frontend not found: $FrontendDir" -ForegroundColor Red
    exit 1
}

Set-Location $FrontendDir
Write-Host "[OK] Starting frontend at http://127.0.0.1:5199 ..." -ForegroundColor Green
npm run dev -- --host 127.0.0.1 --port 5199
