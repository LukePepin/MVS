# Week 4: Validation + TinyML Deployment Completion
Date: 2026-04-20
Status: Complete

## Week 4 Objective

Deliver an evidence-backed hybrid validation packet and run true on-device TinyML inference on Arduino Nano 33 BLE for anomaly status demonstration.

## Final Outcome

Week 4 completed with:
- hybrid payload validation in live workflow,
- telemetry continuity evidence capture,
- anomaly event evidence chain,
- tiny dense model training/export pipeline,
- true on-device TinyML inference sketch compile/upload,
- repeatable motion script with explicit anomaly injection markers.

## Completed Scope

1. Hybrid validation evidence
- Verified `/hybrid/dashboard_data` contract with R6 live mapping.
- Captured payload/test evidence under `artifacts/week4/payloads` and `artifacts/week4/tests`.

2. Telemetry continuity and dataset evidence
- Logged continuity notes and run-aligned references under `artifacts/week4/notes`.
- Preserved run-specific logs for traceability.

3. TinyML training/export (raw 32x6 windows)
- Built labeled window dataset with stratified split support.
- Trained small dense autoencoder and exported threshold/scaling.
- Exported TFLite artifacts and model header.

4. True on-device inference
- Added Arduino TinyML inference sketch at `tinyml-anomaly/arduino_nano_tinyml_inference/arduino_nano_tinyml_inference.ino`.
- Bundled runtime config + model header into sketch folder.
- Compiled successfully for `arduino:mbed_nano:nano33ble` and uploaded to COM9.

5. Live motion anomaly injection for demo
- Added continuous motion runner with timer-ramped injection probability.
- Added explicit log markers:
  - `INJECTION STARTED`
  - `INJECTION BURST`
  - `INJECTION STOPPED`
- Added configurable burst behavior (duration + speedup) for presentation visibility.

## Commands Used (Final Working Flow)

1. Build TinyML runtime bundle for sketch

```powershell
python tinyml-anomaly/ml/anomaly_detection/scripts/generate_tinyml_arduino_bundle.py --model-tflite tinyml-anomaly/ml/anomaly_detection/results/tinyml_raw32_week2/export/model_fp32.tflite --scaling-json tinyml-anomaly/ml/anomaly_detection/results/tinyml_raw32_week2/model/scaling.json --threshold-json tinyml-anomaly/ml/anomaly_detection/results/tinyml_raw32_week2/model/threshold.json --out-sketch-dir tinyml-anomaly/arduino_nano_tinyml_inference --window-size 32 --axis-count 6
```

2. Compile/upload TinyML sketch

```powershell
./scripts/Upload-TinyML-ToArduino.ps1 -Port COM9 -SketchPath tinyml-anomaly/arduino_nano_tinyml_inference
```

3. Monitor TinyML output

```powershell
& "C:\Program Files\Arduino CLI\arduino-cli.exe" monitor -p COM9 -c baudrate=115200
```

4. Run motion loop with clear injection markers

```powershell
./scripts/Run-Baseline-Sharp-Loop.ps1 -RobotIp 192.168.0.223 -TargetAnomalyInterval 30 -BaselineSleep 1.0 -InjectionDurationSeconds 5.0 -InjectionSpeedup 4.0 -StatusEvery 5
```

## Key Artifacts

- Week 4 evidence template in use: `artifacts/week4/_Week4_Evidence_Template.md`
- Test logs: `artifacts/week4/tests/`
- Notes and continuity references: `artifacts/week4/notes/`
- TinyML model outputs:
  - `tinyml-anomaly/ml/anomaly_detection/results/tinyml_raw32_week2/model/eval_report.json`
  - `tinyml-anomaly/ml/anomaly_detection/results/tinyml_raw32_week2/export/model_fp32.tflite`
  - `tinyml-anomaly/ml/anomaly_detection/results/tinyml_raw32_week2/export/model_int8.tflite`
  - `tinyml-anomaly/ml/anomaly_detection/results/tinyml_raw32_week2/export/model_data.h`

## Structure Cleanup Notes

Week 4 structure was normalized to keep a single canonical path per document type:
- Weekly summary stays at `docs/weekly/Week4.md`.
- Command references stay at `docs/weekly/week4/TerminalB_Commands.md`.
- Execution evidence stays in `artifacts/week4/...` (single canonical evidence root).
- Duplicate `TerminalB_Commands.md` was removed from `artifacts/week4/`.
- Duplicate `_Week4_Evidence_Template.md` was removed from `docs/weekly/week4/`.
- Assignment prompt naming was normalized to `docs/assignments/Week10_Assignment_Prompt.md`.
- Generated TinyML binaries were moved to ignore policy while metadata/evaluation JSON remains trackable.

## Week 4 Exit Criteria Check

- [x] Hybrid validation evidence captured.
- [x] Telemetry continuity evidence captured.
- [x] Anomaly evidence chain captured.
- [x] TinyML training/export pipeline completed.
- [x] True on-device inference compile/upload completed.
- [x] Presentation-ready anomaly injection loop implemented.
