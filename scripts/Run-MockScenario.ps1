$ErrorActionPreference = "Stop"

$root = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $root

$venvPath = Join-Path $root ".venv\Scripts\Activate.ps1"
if (Test-Path $venvPath) {
    & $venvPath
}

$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$outDir = Join-Path $root "artifacts"
if (!(Test-Path $outDir)) {
    New-Item -ItemType Directory -Path $outDir | Out-Null
}

$outFile = Join-Path $outDir "mock_scenario_$stamp.txt"

Write-Host "Running mock scenario tests..."
python -m unittest backend.tests.test_mock_scenarios -v | Tee-Object -FilePath $outFile

Write-Host "Saved output to $outFile"
