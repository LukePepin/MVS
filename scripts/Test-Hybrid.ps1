$ErrorActionPreference = "Stop"

$endpoint = "http://localhost:8000/hybrid/dashboard_data"

Write-Host "Fetching hybrid payload from $endpoint ..."
$payload = Invoke-RestMethod -Uri $endpoint -Method Get

$schema = $payload.schema_version
$mode = $payload.mode
$r6 = $payload.schematic.nodes | Where-Object { $_.id -eq "r6" }

Write-Host "Schema version: $schema"
Write-Host "Mode: $mode"

if ($null -eq $r6) {
    Write-Host "R6 node not found in payload." -ForegroundColor Yellow
    exit 1
}

Write-Host "R6 status: $($r6.status)"
Write-Host "R6 source: $($r6.source)"
Write-Host "R6 host_time: $($r6.host_time)"
Write-Host "R6 device_time: $($r6.device_time)"

if ($null -eq $r6.raw_imu) {
    Write-Host "R6 raw_imu: <none>"
} else {
    Write-Host "R6 raw_imu: ax=$($r6.raw_imu.ax) ay=$($r6.raw_imu.ay) az=$($r6.raw_imu.az) gx=$($r6.raw_imu.gx) gy=$($r6.raw_imu.gy) gz=$($r6.raw_imu.gz)"
}
