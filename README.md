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
- Parses 9-axis float32 payload using network big-endian (`!9f`)
- Uses non-blocking queue handoff from UDP callback to async writer
- Writes telemetry to `training_data.csv` using `aiofiles`
- Persists telemetry to SQLite via SQLAlchemy async + `aiosqlite`
- Serves `/dashboard_data` as a single async JSON payload
- Serves `/mock/dashboard_data` with simulated EARC work-center state transitions

## Frontend (React + Tailwind utility classes)

```powershell
cd frontend
npm install
npm run dev -- --host 0.0.0.0 --port 5173
```

Dashboard component polls `http://localhost:8000/dashboard_data` every 1000ms.

## Telemetry Modes

- `Live Mode` (default): frontend polls `/dashboard_data`
- `Mock Testbed Mode`: frontend polls `/mock/dashboard_data` and animates package flow in the 2D schematic visualizer

## Testbed Implementation Status

- Completed: Assumed EARC triangular branch/merge topology
- Completed: Mock telemetry flow model with dynamic routing, block/offline states, and rework path injection
- Completed: Frontend schematic rendering aligned to backend node coordinates and connectors
- Completed: Testbed architecture documentation in `testbed.md`
- Completed: Validation checks (backend and frontend editor diagnostics clean)

## Mock Model Notes

- Node-level capacity values are included in schematic node payloads
- Queue depth is computed from `active_jobs - capacity` per node
- Conveyor links are represented as bidirectional connectors with active transition highlighting

## Planned Frontend Improvements (Future Work)
- **WebGL Rendering:** Transition the current `SVG`/`DOM`-based layout to a true canvas/WebGL solution (via Three.js or React-Three-Fiber) to support massive industrial scaling beyond 1000 nodes without DOM lag.
- **3D Digital Twin Overlay:** Implement basic extrusions on the 2D layout to mimic the vertical profile of CNCs versus standard conveyor belts.
- **Interactive Camera Controls:** Institute formal pinch-and-zoom matrix transformations and drag-to-pan camera systems utilizing `d3-zoom` for easier navigation of dense topology maps.
