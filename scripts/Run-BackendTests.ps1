$ErrorActionPreference = "Stop"

$root = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $root

$venvPath = Join-Path $root ".venv\Scripts\Activate.ps1"
if (Test-Path $venvPath) {
    & $venvPath
}

Write-Host ""
Write-Host "===================================" -ForegroundColor Cyan
Write-Host "  MVS Backend Test Suite (pytest)" -ForegroundColor Cyan
Write-Host "===================================" -ForegroundColor Cyan
Write-Host ""

$env:PYTHONPATH = $root

Write-Host "Running DES routing and scheduling tests..." -ForegroundColor Yellow
python -m unittest backend.tests.test_des_routing -v

Write-Host ""
Write-Host "Running E-STOP pipeline tests..." -ForegroundColor Yellow
python -m unittest backend.tests.test_estop_pipeline -v

Write-Host ""
Write-Host "Running mock scenario tests..." -ForegroundColor Yellow
python -m unittest backend.tests.test_mock_scenarios -v

Write-Host ""
Write-Host "Running MES feature tests..." -ForegroundColor Yellow
python -m unittest backend.tests.test_mes_features -v

Write-Host ""
Write-Host "===================================" -ForegroundColor Green
Write-Host "  All backend tests completed!" -ForegroundColor Green
Write-Host "===================================" -ForegroundColor Green
