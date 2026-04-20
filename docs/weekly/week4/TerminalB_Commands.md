# Terminal B Commands (Week 4 Payload Capture)

Run these from a separate PowerShell terminal while backend is running in Terminal A.

## 1) Set location, timestamp, and output folder

Set-Location C:\Users\lukep\Documents\MVS
$ts = Get-Date -Format "yyyyMMdd_HHmmss"
New-Item -ItemType Directory -Force -Path .\artifacts\week4\payloads | Out-Null

## 2) Run hybrid smoke script and save full output

.\scripts\Test-Hybrid.ps1 *>&1 | Tee-Object -FilePath ".\artifacts\week4\payloads\test_hybrid_$ts.txt"

## 3) Fetch raw hybrid endpoint payload and save JSON

$payload = Invoke-RestMethod -Uri "http://localhost:8000/hybrid/dashboard_data" -Method Get
$payload | ConvertTo-Json -Depth 30 | Out-File -Encoding utf8 ".\artifacts\week4\payloads\hybrid_payload_$ts.json"

## 4) Verify files were created

Get-ChildItem .\artifacts\week4\payloads | Sort-Object LastWriteTime -Descending | Select-Object -First 5 Name,LastWriteTime,Length

## 5) Optional quick contract check in main.py

Select-String -Path .\backend\app\main.py -Pattern "hybrid/dashboard_data|schema_version|mode|source|raw_imu|host_time|device_time|status"
Get-Content .\backend\app\main.py | Select-Object -Skip 360 -First 120

## 6) Optional one-shot block (runs all core steps)

Set-Location C:\Users\lukep\Documents\MVS
$ts = Get-Date -Format "yyyyMMdd_HHmmss"
New-Item -ItemType Directory -Force -Path .\artifacts\week4\payloads | Out-Null
.\scripts\Test-Hybrid.ps1 *>&1 | Tee-Object -FilePath ".\artifacts\week4\payloads\test_hybrid_$ts.txt"
$payload = Invoke-RestMethod -Uri "http://localhost:8000/hybrid/dashboard_data" -Method Get
$payload | ConvertTo-Json -Depth 30 | Out-File -Encoding utf8 ".\artifacts\week4\payloads\hybrid_payload_$ts.json"
Get-ChildItem .\artifacts\week4\payloads | Sort-Object LastWriteTime -Descending | Select-Object -First 5 Name,LastWriteTime,Length

## Artifacts produced

- .\artifacts\week4\payloads\test_hybrid_YYYYMMDD_HHMMSS.txt
- .\artifacts\week4\payloads\hybrid_payload_YYYYMMDD_HHMMSS.json
