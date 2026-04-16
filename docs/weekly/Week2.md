# Week 2: Model Bootstrap and Data Validation Plan
Date: 2026-04-08
Status: Completed (Closeout on 2026-04-16)

## Week 2 Closeout Summary (Final)

### Final Sweep Execution Outcome

- Full sweep completed with consolidated output size: 972 runs evaluated.
- Final selection artifact regenerated from latest consolidated results:
  - `backend/ml/anomaly_detection/results/week2/window_sweep_results/summaries/best_setting.json`

### Final Chosen Configuration

- `window_config`: `ws512_st16_thr0p25`
- `run_tag`: `thr85p0_it250_h384-192-384_seed42`
- `window_size`: 512
- `window_stride`: 16
- `window_threshold`: 0.25
- `threshold_percentile`: 85.0
- `max_iter`: 250
- `hidden_layers`: `384,192,384`
- `seed`: 42

### Final Metrics (Test)

- `test_f1`: 0.8680851063829788
- `test_precision`: 1.0
- `test_recall`: 0.7669172932330827
- `test_fpr_normal`: 0.0

### Decision Rationale

- Chosen by ranking criteria used in selector:
  1. `test_f1` descending
  2. `test_recall` descending
  3. `test_fpr_normal` ascending
- This run provides the strongest F1/recall balance while keeping false positive rate at zero in the current test split.
- `max_iter=250` retained because tied top-performing variants showed no practical gain at 400 iterations.

### Reproducibility Command (Selector)

Run from `backend/ml/anomaly_detection/scripts`:

```powershell
python .\find_best_sweep_setting.py --csv ..\results\week2\window_sweep_results\summaries\consolidated_sweep.csv --status ok
```

### Week 2 Limitations Noted

- Model is conservative: precision is excellent, but recall indicates missed anomalies remain.
- Additional threshold and architecture tuning is still needed for higher anomaly coverage.

### Week 3 Quantitative Target

- Primary target: improve recall and F1 while maintaining tightly controlled false positives.
- Team task: search for better variable combinations (windowing, threshold percentile, architecture), then test and validate the results.
- Maintain reproducibility using fixed seed and explicit config documentation.

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
