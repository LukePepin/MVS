param(
    [string]$RobotIp = "192.168.0.223",
    [string]$RunId = "",
    [int]$MaxCycles = 120,
    [double]$Sleep = 0.8,
    [double]$ImproperRate = 0.7,
    [int]$NormalPhaseSeconds = 45,
    [int]$AnomalyPhaseSeconds = 45
)

$ErrorActionPreference = "Stop"

$root = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $root

$venvPath = Join-Path $root ".venv\Scripts\Activate.ps1"
if (Test-Path $venvPath) {
    & $venvPath
}

if ([string]::IsNullOrWhiteSpace($RunId)) {
    $RunId = Get-Date -Format "yyyyMMdd_HHmmss"
}

New-Item -ItemType Directory -Force -Path ".\artifacts\week4\tests", ".\artifacts\week4\notes" | Out-Null

$robotLog = ".\artifacts\week4\tests\robot_adversarial_$RunId.txt"
$windowNote = ".\artifacts\week4\notes\robot_window_$RunId.txt"

function Invoke-RobotPhase {
    param(
        [string]$PhaseName,
        [double]$PhaseImproperRate,
        [int]$PhaseDurationSeconds,
        [int]$PhaseMaxCycles
    )

    $phaseStart = (Get-Date).ToUniversalTime().ToString("o")
    "phase_start_utc=$phaseStart phase=$PhaseName improper_rate=$PhaseImproperRate duration_s=$PhaseDurationSeconds" | Out-File -Encoding utf8 -Append $windowNote
    "PHASE_START ts_utc=$phaseStart phase=$PhaseName improper_rate=$PhaseImproperRate duration_s=$PhaseDurationSeconds" | Out-File -Encoding utf8 -Append $robotLog

    $pyCmd = "python -u .\\backend\\robot_adversarial_baseline.py --ip $RobotIp --max-cycles $PhaseMaxCycles --sleep $Sleep --improper-rate $PhaseImproperRate --duration-seconds $PhaseDurationSeconds 2>&1"
    cmd.exe /d /c $pyCmd | Tee-Object -FilePath $robotLog -Append
    if ($LASTEXITCODE -ne 0) {
        throw "robot_adversarial_baseline.py phase '$PhaseName' failed with exit code $LASTEXITCODE"
    }

    $phaseEnd = (Get-Date).ToUniversalTime().ToString("o")
    "phase_end_utc=$phaseEnd phase=$PhaseName" | Out-File -Encoding utf8 -Append $windowNote
    "PHASE_END ts_utc=$phaseEnd phase=$PhaseName" | Out-File -Encoding utf8 -Append $robotLog
}

$startUtc = (Get-Date).ToUniversalTime().ToString("o")
$hadNativePref = Test-Path Variable:PSNativeCommandUseErrorActionPreference
if ($hadNativePref) {
    $previousNativePref = $PSNativeCommandUseErrorActionPreference
    $PSNativeCommandUseErrorActionPreference = $false
}

$previousErrorActionPreference = $ErrorActionPreference
$ErrorActionPreference = "SilentlyContinue"

try {
    # Phase 1: force normal behavior for baseline correlation.
    Invoke-RobotPhase -PhaseName "normal" -PhaseImproperRate 0.0 -PhaseDurationSeconds $NormalPhaseSeconds -PhaseMaxCycles 0

    # Phase 2: inject adversarial behavior.
    Invoke-RobotPhase -PhaseName "anomaly" -PhaseImproperRate $ImproperRate -PhaseDurationSeconds $AnomalyPhaseSeconds -PhaseMaxCycles $MaxCycles
}
finally {
    $ErrorActionPreference = $previousErrorActionPreference
    if ($hadNativePref) {
        $PSNativeCommandUseErrorActionPreference = $previousNativePref
    }
}
$endUtc = (Get-Date).ToUniversalTime().ToString("o")

"robot_start_utc=$startUtc" | Out-File -Encoding utf8 $windowNote
"robot_end_utc=$endUtc" | Out-File -Encoding utf8 -Append $windowNote

Write-Host "Run complete."
Write-Host "Robot log: $robotLog"
Write-Host "Window note: $windowNote"
