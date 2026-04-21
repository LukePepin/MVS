param(
    [string]$Port = "COM9",
    [string]$Fqbn = "arduino:mbed_nano:nano33ble",
    [string]$SketchPath = "backend/arduino_nano_anomaly_status",
    [switch]$InstallCore
)

$ErrorActionPreference = "Stop"

$root = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $root

$arduinoCli = $null
$cliCommand = Get-Command arduino-cli -ErrorAction SilentlyContinue
if ($cliCommand) {
    $arduinoCli = $cliCommand.Source
} else {
    $fallbackCli = "C:\Program Files\Arduino CLI\arduino-cli.exe"
    if (Test-Path $fallbackCli) {
        $arduinoCli = $fallbackCli
        Write-Host "arduino-cli not found on PATH. Using fallback: $arduinoCli"
    }
}

if (-not $arduinoCli) {
    Write-Error "arduino-cli not found. Install Arduino CLI first: https://arduino.github.io/arduino-cli/"
}

if ($InstallCore) {
    & $arduinoCli core update-index
    & $arduinoCli core install arduino:mbed_nano
}

if (-not (Test-Path $SketchPath)) {
    Write-Error "Sketch path '$SketchPath' not found. Create your TinyML inference sketch first, then rerun."
}

Write-Host "Compiling $SketchPath for $Fqbn ..."
& $arduinoCli compile --fqbn $Fqbn $SketchPath
if ($LASTEXITCODE -ne 0) {
    throw "Compile failed with exit code $LASTEXITCODE"
}

Write-Host "Uploading to $Port ..."
& $arduinoCli upload -p $Port --fqbn $Fqbn $SketchPath
if ($LASTEXITCODE -ne 0) {
    throw "Upload failed with exit code $LASTEXITCODE"
}

Write-Host "Upload complete."
Write-Host "Open serial monitor to verify inference output:"
Write-Host "`"$arduinoCli`" monitor -p $Port -c baudrate=115200"
