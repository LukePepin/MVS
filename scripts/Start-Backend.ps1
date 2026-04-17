$ErrorActionPreference = "Stop"

$root = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $root

$venvPath = Join-Path $root ".venv\Scripts\Activate.ps1"
if (Test-Path $venvPath) {
    & $venvPath
}

$env:MVS_SERIAL_ENABLED = "true"
if (-not $env:MVS_SERIAL_PORT) { $env:MVS_SERIAL_PORT = "COM15" }
if (-not $env:MVS_SERIAL_BAUD) { $env:MVS_SERIAL_BAUD = "115200" }
if (-not $env:MVS_SERIAL_STALE_TIMEOUT_S) { $env:MVS_SERIAL_STALE_TIMEOUT_S = "2.5" }
if (-not $env:MVS_SCHEMA_VERSION) { $env:MVS_SCHEMA_VERSION = "1" }

Write-Host "Starting backend (hybrid-ready) on http://localhost:8000 ..."
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
