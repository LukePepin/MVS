# Week 3: Hybrid Mode Integration and Validation
Date: 2026-04-08
Status: Planned

## Week 3 Objective

Implement and validate the hybrid operating mode where real 6-axis robot telemetry feeds at least one robot node inside the simulated MES testbed while preserving full dashboard schema compatibility.

## Inputs

- Baseline data and replay source:
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

### 2. Real Telemetry Mapping

- Map real 6-axis metrics into node status features used by the testbed engine.
- Define translation logic from IMU behavior to node-state updates (Idle, Busy, Blocked, Offline support remains unchanged).
- Ensure host timestamps propagate cleanly through the hybrid feed.

### 3. Anomaly Signal Path

- Treat collision events as anomaly candidates.
- Add an annotation sidecar file format and ingestion utility:
  - `event_type,start_timestamp,end_timestamp,source,confidence`
- Ensure anomaly windows can be overlaid on replay and runtime analysis.

### 4. Integration Tests

- Endpoint schema regression test (no frontend-breaking changes).
- Node assignment test (real-backed robot node updates as expected).
- Replay consistency test using `training_data_0001.csv`.
- Disconnect/reconnect behavior test with COM failover active.
- Timestamp monotonicity and gap-threshold checks under hybrid flow.

### 5. Deliverables

- Hybrid mode design note and payload schema summary.
- Working backend path for hybrid node updates.
- Test evidence for real-node assignment and replay correctness.
- Updated risk list entering Week 4 final validation.

## Week 3 Exit Criteria

- Hybrid mode works end-to-end with one telemetry-backed robot node.
- Dashboard renders hybrid payload without schema drift.
- Collision anomaly windows are represented in the evaluation pipeline.
- Integration tests pass with documented evidence.
