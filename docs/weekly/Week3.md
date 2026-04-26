# Week 3: Hybrid Mode Integration and Validation
Date: 2026-04-17
Status: Complete (Closed via Week 4 validation handoff)

## Week 3 Objective

Implement and validate **Live Mode** where physical 6-axis robot telemetry streams directly from the USB serial hardware and feeds exclusively into robot node **R6** inside the simulated MES Mock Bed. The core goal of the MVS project is to run this Mock Bed with one node representing real data, piping raw environmental context directly into the dashboard UI while preserving simulated logic for the rest of the factory.

## Inputs

- Live physical hardware telemetry source (direct USB streaming from Arduino).
- (Optional fallback) Baseline datalog and replay:
  - `tinyml-anomaly/data/training_data_0001.csv`
- Motion execution and anomaly behavior:
  - `tinyml-anomaly/MVS_data_collection.py`
- Datalogger resilience and schema behavior:
  - `tinyml-anomaly/phase2_datalogger.py`
- Simulated node engine:
  - `backend/app/mock_telemetry.py`
- API mode orchestration:
  - `backend/app/main.py`

## Work Plan

### 1. Hybrid Mode Contract

- Define a single canonical payload contract for dashboard consumption.
- Keep simulated node table and routing engine active.
- Mark one robot node as telemetry-backed (real source) and include source metadata in payload.
- Add numeric `schema_version` at payload root.
- Ensure per-node timestamps include `host_time` and optional `device_time`.

### 2. Live Mode Telemetry Mapping (Node R6)

- Hardcode the testbed integration specifically to node **R6**.
- Directly stream the raw 6-axis IMU packet through the backend to the UI for this node.
- Derive `status` from IMU thresholds (Busy if accel or gyro exceeds threshold), otherwise Idle.
- If `device_time` is missing, force `status = Disconnected` and freeze the last sample.
- Ensure host timestamps propagate cleanly through the live stream payload.

### 3. Anomaly Signal Path

- Treat collision events as anomaly candidates.
- Add an annotation sidecar file format and ingestion utility:
  - `event_type,start_timestamp,end_timestamp,source,confidence`
- Ensure anomaly windows can be overlaid on replay and runtime analysis.

### 4. Integration Tests

- Endpoint schema regression test (no frontend-breaking changes).
- Node assignment test (real-backed robot node updates as expected).
- Live-stream USB disconnect/reconnect behavior test.
- Timestamp monotonicity and gap-threshold checks under hybrid flow.
- Mode toggle test (Mock vs Hybrid) to verify schema stability and R6 override.
- Evidence capture checklist: screenshots, payload snippets, and log excerpts.

### 5. Deliverables

- Hybrid mode design note and payload schema summary.
- Working backend path for hybrid node updates.
- Test evidence for real-node assignment and replay correctness.
- Updated risk list entering Week 4 final validation.

## Week 3 Exit Criteria

- Live Mode streams directly from USB and maps flawlessly into node R6.
- The UI exposes raw 6-axis IMU strings for node R6 while the rest of the Mock Bed remains simulated.
- Collision anomaly windows from the live stream successfully branch into the evaluation pipeline.
- Integration tests pass with documented evidence of correct Live Mode bridging.
- Validation evidence (screenshots + logs) is archived in Week 3 notes.

## Work Completed (as of 2026-04-17)

- Added hybrid backend endpoint with serial ingest and host/device timestamp handling.
- Implemented schema_version at payload root and per-node source metadata.
- Added stale timeout behavior for live telemetry and disconnect handling.
- Updated frontend to consume hybrid endpoint and surface R6 live telemetry panel.
- Adjusted mock testbed layout and inspection buffers (Q-IA/Q-IB) plus routing metadata.
- Added reset endpoint and reduced spawn rate to prevent mock lockups.
- Added scripts to start backend/frontend and run hybrid/mock scenario tests.
- Added Vitest + frontend tests and backend mock scenario tests.
- Refined dashboard layout (analytics right, work orders below model) and reduced margins.

## Closeout Notes

- Week 3 implementation items were validated and evidence capture was completed during Week 4.
- Hybrid contract and R6 mapping checks are documented in Week 4 artifacts and summary.
- Any remaining improvements are now treated as post-closeout enhancement scope, not Week 3 blockers.

## Week 4 Handoff (Documentation-First)

The following open items are explicitly carried into Week 4 validation planning:

1. Finalize evidence capture for hybrid payload and frontend behavior under R6 live mapping.
2. Complete checklist-driven execution of existing scripts/tests and archive outcomes.
3. Consolidate anomaly-candidate evidence and reporting notes into Week 4 closure artifacts.
4. Ensure README runbook and weekly plan chain reflect actual execution order and acceptance criteria.
