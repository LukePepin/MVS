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
- Serves `/mock/dashboard_data` as the primary hybrid testbed feed

## Frontend (React + Tailwind utility classes)

```powershell
cd frontend
npm install
npm run dev -- --host 0.0.0.0 --port 5173
```

Dashboard component polls `http://localhost:8000/dashboard_data` every 1000ms.

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

- `Hybrid Testbed Mode` (primary and singular mode): frontend polls `/mock/dashboard_data`, where simulated node behavior is preserved while one robot node is designated to consume real robot telemetry as integration work progresses.

## Testbed Implementation Status

- Completed: Assumed EARC triangular branch/merge topology
- Completed: Mock telemetry flow model with dynamic routing, block/offline states, and rework path injection
- Completed: Frontend schematic rendering aligned to backend node coordinates and connectors
- Completed: Testbed architecture documentation in `docs/design/testbed.md`
- Completed: Validation checks (backend and frontend editor diagnostics clean)

## Mock Model Notes

- Node-level capacity values are included in schematic node payloads
- Queue depth is computed from `active_jobs - capacity` per node
- Conveyor links are represented as bidirectional connectors with active transition highlighting

## Planned Frontend Improvements (Future Work)
- **WebGL Rendering:** Transition the current `SVG`/`DOM`-based layout to a true canvas/WebGL solution (via Three.js or React-Three-Fiber) to support massive industrial scaling beyond 1000 nodes without DOM lag.
- **3D Digital Twin Overlay:** Implement basic extrusions on the 2D layout to mimic the vertical profile of CNCs versus standard conveyor belts.
- **Interactive Camera Controls:** Institute formal pinch-and-zoom matrix transformations and drag-to-pan camera systems utilizing `d3-zoom` for easier navigation of dense topology maps.
