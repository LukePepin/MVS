# Arduino Upload and Test Commands

Use these commands from PowerShell at:

C:\Users\lukep\Documents\MVS

## 1) Activate environment

```powershell
Set-Location C:\Users\lukep\Documents\MVS
if (Test-Path .\.venv\Scripts\Activate.ps1) { . .\.venv\Scripts\Activate.ps1 }
```

## 2) Upload firmware to Arduino (COM9)

```powershell
.\scripts\Upload-TinyML-ToArduino.ps1 -Port COM9 -SketchPath backend/arduino_nano_anomaly_status -InstallCore
```

## 3) Open serial monitor (anomaly status only)

```powershell
& "C:\Program Files\Arduino CLI\arduino-cli.exe" monitor -p COM9 -c baudrate=115200
```

Expected output includes `READY:ANOMALY_STATUS` and then only:

- `NORMAL`
- `ANOMALY_DETECTED`

## 4) Run robot anomaly motion test (new terminal)

```powershell
Set-Location C:\Users\lukep\Documents\MVS
if (Test-Path .\.venv\Scripts\Activate.ps1) { . .\.venv\Scripts\Activate.ps1 }
$runId = Get-Date -Format "yyyyMMdd_HHmmss"
.\scripts\Run-Anomaly-Motion-Test.ps1 -RobotIp 192.168.0.223 -RunId $runId -MaxCycles 120 -Sleep 0.8 -ImproperRate 0.7
```

## 5) Verify artifacts from motion run

```powershell
Set-Location C:\Users\lukep\Documents\MVS
Get-ChildItem .\artifacts\week4\tests\robot_adversarial_*.txt | Sort-Object LastWriteTime -Descending | Select-Object -First 3 Name,LastWriteTime,Length
Get-ChildItem .\artifacts\week4\notes\robot_window_*.txt | Sort-Object LastWriteTime -Descending | Select-Object -First 3 Name,LastWriteTime,Length
```

## 6) Optional: re-upload quickly without core install

```powershell
.\scripts\Upload-TinyML-ToArduino.ps1 -Port COM9 -SketchPath backend/arduino_nano_anomaly_status
```

## Important note

This uploads an anomaly-status firmware that emits `NORMAL` or `ANOMALY_DETECTED` using IMU magnitude thresholds. It is not yet running the trained desktop joblib autoencoder on-device.
