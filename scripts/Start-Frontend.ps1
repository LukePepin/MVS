$ErrorActionPreference = "Stop"

$root = Resolve-Path (Join-Path $PSScriptRoot "..")
$frontend = Join-Path $root "frontend"
Set-Location $frontend

Write-Host "Starting frontend (Vite) on http://localhost:5173 ..."
if (!(Test-Path (Join-Path $frontend "node_modules"))) {
    Write-Host "node_modules not found. Running npm install..."
    npm install
}

npm run dev
