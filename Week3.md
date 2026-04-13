# Week 3: Hybrid Mode Integration and Validation
Date: 2026-04-08
Status: Planned

## Week 3 Objective

Implement and validate **Live Mode** where physical 6-axis robot telemetry streams directly from the USB serial hardware and feeds exclusively into robot node **R6** inside the simulated MES Mock Bed. The core goal of the MVS project is to run this Mock Bed with one node representing real data, piping raw environmental context directly into the dashboard UI while preserving simulated logic for the rest of the factory.

## Inputs

- Live physical hardware telemetry source (direct USB streaming from Arduino).
- (Optional fallback) Baseline datalog and replay:
  - `backend/data/training_data_0001.csv`
- Motion execution and anomaly behavior:
  - `backend/MVS_data_collection.py`
- Datalogger resilience and schema behavior:
  - `backend/phase2_datalogger.py`
- Simulated node engine:
  - `backend/app/mock_telemetry.py`
- API mode orchestration:
  - `backend/app/main.py`

## Work Plan

### 1. Hybrid Mode Contract

- Define a single canonical payload contract for dashboard consumption.
- Keep simulated node table and routing engine active.
- Mark one robot node as telemetry-backed (real source) and include source metadata in payload.

### 2. Live Mode Telemetry Mapping (Node R6)

- Hardcode the testbed integration specifically to node **R6**.
- Directly stream the raw 6-axis IMU packet through the backend to the UI for this node.
- Do NOT translate physical IMU data into discrete state enums (e.g., skip `Idle`, `Busy`) for R6. The frontend UI will display the raw continuous metrics for R6 instead.
- Ensure host sequence timestamps propagate cleanly through the live stream payload.

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
