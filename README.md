# MVS (Minimum Viable Spring)

## Backend (FastAPI + Async UDP + SQLite)

```powershell
docker compose up --build
```

For local backend execution without a virtual environment:

```powershell
pip install -r backend/requirements.txt
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
```

### Backend behavior
- UDP listener bound to `0.0.0.0:5005`
- Parses incoming telemetry and normalizes to the project schema
- Uses non-blocking queue handoff from UDP callback to async writer
- Writes telemetry to CSV and SQLite for downstream analysis
- Persists telemetry to SQLite via SQLAlchemy async + `aiosqlite`
- Serves `/dashboard_data` as a single async JSON payload
- Serves `/hybrid/dashboard_data` for hybrid mode (default UI mode)
- Serves `/mock/dashboard_data` for fully simulated mode

## Frontend (React + Tailwind utility classes)

```powershell
cd frontend
npm install
npm run dev -- --host 0.0.0.0 --port 5173
```

Dashboard polls `http://localhost:8000/hybrid/dashboard_data` every 1000ms by default,
with a mode toggle to `http://localhost:8000/mock/dashboard_data`.

## Arduino Nano 6-Axis CSV Capture

Use `backend/arduino_nano_6axis_csv_stream/arduino_nano_6axis_csv_stream.ino` on the Nano 33 BLE for initial accel+gyro CSV capture.

1. Flash the 6-axis sketch to the board.
2. Find the serial port:

```powershell
python backend/phase2_datalogger.py --list-ports
```

3. Capture 60 seconds to CSV (host appends UTC timestamp):

```powershell
python backend/phase2_datalogger.py --port COM15 --baud 115200 --axes 6 --duration 60 --out auto --node-id niryo-wrist-imu
```

Default `--out auto` writes incrementing files to `backend/data/training_data_XXXX.csv`.

Expected serial row format from the sketch:

`ax,ay,az,gx,gy,gz`

## CI Docker Publish (GHCR)

The workflow in `.github/workflows/docker-publish.yml` publishes images to `ghcr.io`.

If you see `permission_denied: write_package`, verify the following:

- Repository settings: `Settings -> Actions -> General -> Workflow permissions` is set to `Read and write permissions`.
- Repository secret: add `GHCR_TOKEN` (classic PAT) with at least `write:packages` scope.
- Package access: in GHCR package settings for `mvs`, grant this repository `Write` access under `Manage Actions access`.

The workflow prefers `GHCR_TOKEN` when available and falls back to `GITHUB_TOKEN`.

## Telemetry Mode (Primary)

- `Hybrid Testbed Mode` (primary mode): frontend polls `/hybrid/dashboard_data`, where simulated node behavior is preserved while one robot node is designated to consume real robot telemetry as integration work progresses.

## Week 4 Validation + TinyML Quickstart

Week 4 now includes both validation evidence capture and true on-device TinyML inference on Nano 33 BLE.

### Recommended run order

1. Backend mock scenario baseline:

```powershell
./scripts/Run-MockScenario.ps1
```

2. Safety path regression:

```powershell
python -m unittest backend.tests.test_estop_pipeline -v
```

3. Mock engine transition regression:

```powershell
python -m unittest backend.tests.test_mock_scenarios -v
```

4. Hybrid payload smoke check (R6 mapping):

```powershell
./scripts/Test-Hybrid.ps1
```

5. Build TinyML bundle for Arduino inference sketch:

```powershell
python backend/ml/anomaly_detection/scripts/generate_tinyml_arduino_bundle.py --model-tflite backend/ml/anomaly_detection/results/tinyml_raw32_week2/export/model_fp32.tflite --scaling-json backend/ml/anomaly_detection/results/tinyml_raw32_week2/model/scaling.json --threshold-json backend/ml/anomaly_detection/results/tinyml_raw32_week2/model/threshold.json --out-sketch-dir backend/arduino_nano_tinyml_inference --window-size 32 --axis-count 6
```

6. Upload TinyML inference sketch:

```powershell
./scripts/Upload-TinyML-ToArduino.ps1 -Port COM9 -SketchPath backend/arduino_nano_tinyml_inference
```

7. Run continuous baseline with explicit anomaly injections:

```powershell
./scripts/Run-Baseline-Sharp-Loop.ps1 -RobotIp 192.168.0.223 -TargetAnomalyInterval 30 -BaselineSleep 1.0 -InjectionDurationSeconds 5.0 -InjectionSpeedup 4.0 -StatusEvery 5
```

### Expected outputs

- Mock scenario run writes timestamped output under `artifacts/`.
- Backend test commands print unittest pass/fail summaries.
- Hybrid script prints schema/mode and R6 source/status/timestamps.
- TinyML sketch prints `READY:TINYML_INFERENCE`, `WARMING_UP`, and `ML_SCORE=<value> THRESH=<value> STATUS=NORMAL|ANOMALY_DETECTED`.
- Motion script prints explicit anomaly markers: `INJECTION STARTED`, `INJECTION BURST`, `INJECTION STOPPED`.

### Evidence expectations

For each validation run, capture:

- command used,
- execution timestamp,
- pass/fail result,
- key output excerpt,
- artifact path.

Detailed acceptance criteria and artifact requirements are defined in `docs/weekly/Week4.md`.

### Week 4 structure (canonical locations)

- Planning and weekly summary: `docs/weekly/Week4.md`
- Operational command reference: `docs/weekly/week4/TerminalB_Commands.md`
- Evidence template in use: `artifacts/week4/_Week4_Evidence_Template.md`
- Collected logs and notes: `artifacts/week4/tests/`, `artifacts/week4/notes/`, `artifacts/week4/payloads/`

Naming convention used in this repo:

- Weekly summaries use `WeekN.md` files under `docs/weekly/`
- Week-specific support material uses `weekN/` folders under `docs/weekly/`

### Repository closeout checklist

- `README.md`, `docs/weekly/Week3.md`, and `docs/weekly/Week4.md` are status-aligned.
- Week 4 command and evidence-template docs each have a single canonical location.
- `docs/assignments/Week10_Assignment_Prompt.md` is the canonical prompt filename.
- TinyML generated binary outputs are excluded from version control via `.gitignore`.
- Trackable evidence remains in `artifacts/week4/notes/`, `artifacts/week4/tests/`, and `artifacts/week4/payloads/`.

## Testbed Implementation Status

- Completed: Assumed EARC triangular branch/merge topology
- Completed: Mock telemetry flow model with dynamic routing, block/offline states, and rework path injection
- Completed: Frontend schematic rendering aligned to backend node coordinates and connectors
- Completed: Testbed architecture documentation in `docs/design/testbed.md`
- Completed: Validation checks (backend and frontend editor diagnostics clean)

## Project Learning Path (Recommended)

Read these in order to understand architecture intent, implementation state, and Week 4 validation goals:

1. `docs/design/Official_Project_Proposal.md`
2. `docs/design/architecturepivot.md`
3. `docs/design/testbed.md`
4. `docs/weekly/Week1.md`
5. `docs/weekly/Week2.md`
6. `docs/weekly/Week3.md`
7. `docs/weekly/Week4.md`
8. `docs/ISE572_ML_Proposal_Readme.md`

## Week 4 Scope Boundary

Completed in this pass:

- validation criteria and evidence chain hardening,
- hybrid payload and continuity evidence,
- TinyML model training/export pipeline for raw 32x6 windows,
- true on-device inference sketch for Nano 33 BLE,
- repeatable anomaly-injection motion runner for live demo.

Still future scope:

- additional model architectures and long-horizon tuning,
- expanded multi-node live telemetry beyond current R6-focused flow.

## Mock Model Notes

- Node-level capacity values are included in schematic node payloads
- Queue depth is computed from `active_jobs - capacity` per node
- Conveyor links are represented as bidirectional connectors with active transition highlighting

## Planned Frontend Improvements (Future Work)
- **WebGL Rendering:** Transition the current `SVG`/`DOM`-based layout to a true canvas/WebGL solution (via Three.js or React-Three-Fiber) to support massive industrial scaling beyond 1000 nodes without DOM lag.
- **3D Digital Twin Overlay:** Implement basic extrusions on the 2D layout to mimic the vertical profile of CNCs versus standard conveyor belts.
- **Interactive Camera Controls:** Institute formal pinch-and-zoom matrix transformations and drag-to-pan camera systems utilizing `d3-zoom` for easier navigation of dense topology maps.
