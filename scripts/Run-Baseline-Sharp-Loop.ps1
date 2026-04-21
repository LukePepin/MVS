param(
    [string]$RobotIp = "192.168.0.223",
    [double]$BaselineSleep = 1.0,
    [double]$InjectionDurationSeconds = 5.0,
    [double]$InjectionSpeedup = 4.0,
    [double]$TargetAnomalyInterval = 30.0,
    [double]$DurationSeconds = 300,
    [int]$MaxSteps = 0,
    [int]$StatusEvery = 5,
    [int]$Seed = 42,
    [switch]$Calibrate
)

$ErrorActionPreference = "Stop"

$root = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $root

$venvPath = Join-Path $root ".venv\Scripts\Activate.ps1"
if (Test-Path $venvPath) {
    & $venvPath
}

$cmd = @(
    "python -u .\backend\robot_baseline_sharp_repeat.py",
    "--ip", $RobotIp,
    "--baseline-sleep", $BaselineSleep,
    "--injection-duration-seconds", $InjectionDurationSeconds,
    "--injection-speedup", $InjectionSpeedup,
    "--target-anomaly-interval", $TargetAnomalyInterval,
    "--duration-seconds", $DurationSeconds,
    "--max-steps", $MaxSteps,
    "--status-every", $StatusEvery,
    "--seed", $Seed,
    "--clear-estop"
)

if ($Calibrate) {
    $cmd += "--calibrate"
}

$full = $cmd -join " "
Write-Host "Running: $full"
cmd.exe /d /c $full

if ($LASTEXITCODE -ne 0) {
    throw "Run failed with exit code $LASTEXITCODE"
}
