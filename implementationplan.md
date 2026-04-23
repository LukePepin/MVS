# Implementation Plan: Live Simulation & Frontend Overhaul

Your feedback highlights the next crucial evolution for the MVS testbed. To achieve the same depth as the `cMES` prototype, we need to transition the SimPy simulation from a "headless, instant calculation" into a **stateful, interactive engine**. This will allow the frontend to visually track individual jobs moving through the factory floor in real-time, govern simulation speeds, and cleanly separate the massive influx of data into structured pages.

Additionally, to harden this system for your thesis, we will establish strict verification test suites for both the backend algorithms and frontend components.

## User Review Required

> [!IMPORTANT]

> This plan introduces structural changes to how the backend handles simulation state and overhauls the React frontend using a router-based multi-page layout. Please review the proposed simulation controls and testing strategy before we execute.

---

## Proposed Changes

### 1. Stateful DES Engine & Simulation Controls (Backend)

We will refactor the SimPy `des_engine.py` to run asynchronously in the background. It will maintain a live registry of "Active Jobs" and their physical coordinate mappings across the EARC topology.

#### [MODIFY] [backend/simulation/des_engine.py](file:///c:/Users/lukep/Documents/MVS/backend/simulation/des_engine.py)

-**Live State Tracker**: Implement an internal dictionary tracking every Work Order's exact location (e.g., `Job_101` is currently processing at `M2`).

-**Speed Multiplier**: Integrate an `env.timeout` scalar. When `speed = 1.0`, the simulation runs at real-time. When `speed = 100.0`, it accelerates.

-**Instant Finish**: A function to immediately drop the wait-times and jump to `env.now = target_end_time` to spit out the final OEE metrics instantly.

#### [MODIFY] [backend/app/main.py](file:///c:/Users/lukep/Documents/MVS/backend/app/main.py)

-**New API Endpoints**:

  -`POST /api/sim/speed`: Adjust simulation speed ratio.

  -`POST /api/sim/finish_instantly`: Calculate remaining operations immediately.

  -`GET /api/sim/state`: Return the exact live positions of all WIP tokens for the frontend to animate.

### 2. Frontend Overhaul & Token Animation

The single-page dashboard is becoming cluttered. We will break it into a professional, multi-page application (similar to standard industrial MES interfaces) and implement visual token tracking.

#### [NEW] [frontend/package.json](file:///c:/Users/lukep/Documents/MVS/frontend/package.json)

- Install `react-router-dom` to support deep linking and multi-page routing.

#### [MODIFY] [frontend/src/dashboard.jsx] -> Refactored into distinct route pages

-**/factory**: The main visualizer. We will update `SchematicVisualizer.jsx` to parse the `/api/sim/state` and render glowing CSS/SVG tokens floating between `R0`, `M1..3`, and `R1`. It will include the new playback controls (▶ Play, ⏸ Pause, ⏩ Speed Up, ⏭ Finish).

-**/analytics**: The deep statistical OEE and MTBF views.

-**/mrp**: A new page to show the PuLP EDD schedule, work orders, and raw inventory levels (the "Brain" of the MES).

-**/traceability**: Your backwards/forwards genealogy tables.

### 3. Verification & Testing Suites

To ensure reliability for future ML optimization tests, we need formalized automated testing.

#### [NEW] [backend/tests/test_des_routing.py](file:///c:/Users/lukep/Documents/MVS/backend/tests/test_des_routing.py)

-**Pytest Suite**: Write unit tests to explicitly verify that the PuLP optimizer actually schedules shorter due-date items before longer ones, and that SimPy processes them without throwing queueing errors.

#### [NEW] [frontend/src/__tests__/SimulationControls.test.jsx](file:///c:/Users/lukep/Documents/MVS/frontend/src/__tests__/SimulationControls.test.jsx)

-**Vitest Suite**: Add DOM rendering tests to verify the UI correctly mounts the new speed controls and router links.

#### [MODIFY] [scripts/Start-Backend.ps1] & [scripts/Start-Frontend.ps1]

- We will add explicit flags or create dedicated `Run-Tests.ps1` wrapper scripts that trigger `pytest` and `npm run test` seamlessly in your Windows environment.

---

## Open Questions

> [!WARNING]

> Please confirm the following:

1.**Frontend Architecture**: Are you comfortable with me pulling in `react-router-dom` to separate the dashboard into distinct URLs (e.g. `http://localhost:5173/factory`, `/analytics`, `/mrp`), or do you strictly prefer a single-page app where the URL never changes?

You can separtate the dashboard into distinct URLs.

2.**Animation Style**: For part motion, the simplest and most performant method is having small circular tokens (labeled with the Job ID) jump between the nodes (e.g., from `R0` to `M2`) when their status changes. Is this sufficient for your visual verification?

That sounds like a plan.

## Verification Plan

### Automated Tests

- Running `pytest backend/tests/` will confirm 100% pass rate on PuLP routing algorithms and DES state manipulation.
- Running `npm run test` will confirm Vitest passes the React component mounting tests.

### Manual Verification

- We will boot the frontend, click **Start Execution**, and visually watch tokens move across the layout.
- We will click **Speed Up (5x)** and observe the tokens moving faster.
- We will click **Finish Instantly** and verify the Analytics tab instantly populates with the final shift OEE calculations.
