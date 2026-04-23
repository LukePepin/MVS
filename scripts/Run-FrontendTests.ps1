$ErrorActionPreference = "Stop"

$root = Resolve-Path (Join-Path $PSScriptRoot "..")
$frontend = Join-Path $root "frontend"
Set-Location $frontend

Write-Host ""
Write-Host "===================================" -ForegroundColor Cyan
Write-Host "  MVS Frontend Test Suite (vitest)" -ForegroundColor Cyan
Write-Host "===================================" -ForegroundColor Cyan
Write-Host ""

if (!(Test-Path (Join-Path $frontend "node_modules"))) {
    Write-Host "node_modules not found. Running npm install..." -ForegroundColor Yellow
    npm install
}

npm run test
