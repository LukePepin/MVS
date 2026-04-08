# Week 2: Model Bootstrap and Data Validation Plan
Date: 2026-04-08
Status: Planned

## Week 2 Objective

Start anomaly model development using current baseline data and establish a reproducible training and evaluation workflow.

## Inputs

- Primary baseline dataset:
  - `backend/data/training_data_0001.csv`
- Motion execution and anomaly behavior context:
  - `backend/MVS_data_collection.py`
- Collection reliability behavior:
  - `backend/phase2_datalogger.py`

## Work Plan

### 1. Data Audit and Preparation

- Verify CSV schema consistency:
  - `NodeID, Accel_X, Accel_Y, Accel_Z, Gyro_X, Gyro_Y, Gyro_Z, Timestamp`
- Validate timestamp monotonicity and gap statistics.
- Compute summary stats per axis (mean, std, min, max).
- Detect and document low-quality windows (disconnects, malformed rows).

### 2. Label Strategy for Anomalies

- Baseline assumption: most of `training_data_0001.csv` is nominal.
- Collision-related windows should be tagged as anomaly candidates.
- Create sidecar annotation file for event windows:
  - `event_type, start_timestamp, end_timestamp, source, confidence`

### 3. Baseline Model Training

- Build first autoencoder on 6-axis features.
- Train on nominal-only windows first.
- Hold out validation windows for threshold calibration.
- Save model artifact and scaler/normalizer artifacts.

### 4. Thresholding and Detection Logic

- Compute reconstruction error distribution on validation set.
- Define initial anomaly threshold (for example percentile-based).
- Test sensitivity around known collision-window candidates.
- Document false positives and missed events.

### 5. Test Matrix

- Data ingestion test:
  - schema, nulls, type conversion, timestamp parsing
- Feature pipeline test:
  - scaling consistency and inverse checks
- Model test:
  - train convergence and stable validation loss
- Detection test:
  - expected anomaly score increase during collision windows
- Runtime test:
  - model inference on rolling windows from CSV stream replay

### 6. Hybrid Integration Task (Week 2 Requirement)

- Assign one simulated robot node in the testbed to consume real robot telemetry as the primary integration milestone.
- Keep the rest of the node table simulated while preserving the same schema and state semantics.
- Validate that hybrid node updates remain synchronized with dashboard rendering.

### 7. Deliverables for Week 2

- Cleaned modeling dataset split summary.
- First-pass anomaly model and threshold report.
- Confusion-style analysis on labeled candidate events.
- Updated next-step recommendations for Week 3.

## Week 2 Exit Criteria

- A trainable baseline model exists and runs end-to-end.
- At least one documented anomaly-window evaluation is completed.
- Threshold and performance limitations are explicitly documented.
- Clear decision recorded on whether additional data capture is needed before Week 3.
- One robot node is successfully mapped to real telemetry inside the hybrid testbed path.
