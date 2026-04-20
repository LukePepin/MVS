# Week 4 Evidence Template (Fillable)
Date: 2026-04-19
Prepared by: Luke Pepin
Project: MVS (Minimum Viable Spring)
Week: 4
Status: In Progress (Offline Evidence Captured)

## Instructions
- Fill one section per validation item.
- Keep raw command output excerpts short and focused.
- Add links/paths to saved artifacts.
- Mark each item Pass, Fail, or Deferred.

## Validation Summary
| Test ID | Objective | Result | Evidence Path | Notes |
|---|---|---|---|---|
| W4-T1 | Hybrid payload and R6 mapping | Pass | artifacts/week4/payloads/test_hybrid_20260419_204319.txt; artifacts/week4/payloads/hybrid_payload_20260419_204319.json | Hybrid endpoint responded with schema/mode and R6 fields; Disconnected is expected with serial-disabled setup. |
| W4-T2 | Mock scenario baseline | Pass | artifacts/week4/tests/mock_scenario_20260419_202720.txt | 2/2 tests passed; baseline mock engine behavior is stable. |
| W4-T3 | E-STOP safety path regression | Pass | artifacts/week4/tests/estop.txt | 2/2 tests passed; E-STOP flag and datalogger stop-path validated. |
| W4-T4 | Mock transition regression | Pass | artifacts/week4/tests/mock_scenario.txt | Connector transition test passed and routing connector keys validated. |
| W4-T5 | Telemetry schema continuity | Pass (Offline) | backend/data/week2_data_audit.json | Week2 audit confirms expected schema, no nulls, and baseline timestamp continuity; fresh hardware capture deferred. |
| W4-T6 | Dashboard/API consistency | Pass | artifacts/week4/payloads/hybrid_payload_20260419_204319.json | Payload structure aligns with /hybrid/dashboard_data contract in backend/app/main.py. |
| W4-T7 | Anomaly evidence chain | Pass (Offline) | backend/ml/anomaly_detection/results/week2/window_sweep_results/summaries/best_setting_20260419_211322.json; artifacts/week4/notes/ml_ranked_summary_20260419_211322.txt | Best-setting selection and ranked summary provide reproducible anomaly-model evidence for offline closure. |

## Environment Snapshot
- OS: Windows
- Python version: 3.13.13
- Backend start command: uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
- Frontend start command: cd frontend && npm run dev -- --host 0.0.0.0 --port 5173
- Active branch: main
- Commit hash: e225d03
- Serial port(s): Deferred tonight (no Arduino/robot session)

## Evidence Records

### W4-T1 Hybrid Payload and R6 Mapping
- Objective: Validate that `/hybrid/dashboard_data` is reachable and that node R6 is present with hybrid/live source metadata fields.
- Command/script: `./scripts/Test-Hybrid.ps1 *>&1 | Tee-Object -FilePath .\artifacts\week4\payloads\test_hybrid_20260419_204319.txt`
- Execution timestamp (local): 2026-04-19 20:43:28
- Execution timestamp (UTC): 2026-04-20 00:43:28Z (derived from local run window)
- Result: Pass
- Key output excerpt: `Schema version: 1`, `Mode: hybrid`, `R6 status: Disconnected`, `R6 source: live`, `R6 raw_imu: <none>`
- Payload snippet: R6 fields observed and populated for hybrid contract (`source`, `status`, `host_time`, `device_time`, `raw_imu`).
- Artifact path(s): `artifacts/week4/payloads/test_hybrid_20260419_204319.txt`; `artifacts/week4/payloads/hybrid_payload_20260419_204319.json`
- Interpretation (what this proves): Hybrid endpoint and R6 field mapping are functioning. `Disconnected` with empty IMU fields is expected when serial input is intentionally unavailable/disabled for offline validation.
- If failed/deferred, triage note: N/A

### W4-T2 Mock Scenario Baseline
- Objective: Confirm the mock scenario test suite executes cleanly as a baseline before hybrid validation.
- Command/script: `./scripts/Run-MockScenario.ps1`
- Execution timestamp (local): 2026-04-19 20:27:20
- Execution timestamp (UTC): 2026-04-20 00:27:20Z
- Result: Pass
- Key output excerpt: `Ran 2 tests ... OK`
- Artifact path(s): `artifacts/week4/tests/mock_scenario_20260419_202720.txt`
- Interpretation (what this proves): Core mock workload generation and scenario execution are stable for Week 4 validation runs.
- If failed/deferred, triage note: N/A

### W4-T3 E-STOP Safety Path Regression
- Objective: Verify software E-STOP path creates/observes stop signal behavior in both datalogger and motion sequence logic.
- Command/script: `python -m unittest backend.tests.test_estop_pipeline -v`
- Execution timestamp (local): 2026-04-19 (evening session)
- Execution timestamp (UTC): 2026-04-20 (early UTC session)
- Result: Pass
- Key output excerpt: `Ran 2 tests ... OK` and `[!] E-STOP received from Arduino: ESTOP:COLLISION`
- Artifact path(s): `artifacts/week4/tests/estop.txt`
- Interpretation (what this proves): The safety stop signal chain is functionally validated in test harness conditions, reducing risk before hardware validation.
- If failed/deferred, triage note: N/A

### W4-T4 Mock Transition Regression
- Objective: Validate route transitions and connector metadata integrity used by dashboard rendering and state flow analysis.
- Command/script: `python -m unittest backend.tests.test_mock_scenarios -v`
- Execution timestamp (local): 2026-04-19 (evening session)
- Execution timestamp (UTC): 2026-04-20 (early UTC session)
- Result: Pass
- Key output excerpt: `test_transitions_mark_connectors ... ok` and `Ran 2 tests ... OK`
- Artifact path(s): `artifacts/week4/tests/mock_scenario.txt`
- Interpretation (what this proves): Transition and connector contract assumptions are passing, supporting confidence in schematic flow visualization during Week 4 closure checks.
- If failed/deferred, triage note: N/A

### W4-T5 Telemetry Schema Continuity
- Objective: Verify telemetry dataset schema continuity and timestamp quality for offline ML/replay usage.
- Data source: `backend/data/week2_data_audit.json` summary over baseline and adversarial datasets.
- Validation method: Review expected columns, null counts, timestamp parse failures, and timestamp gap statistics from the saved audit artifact.
- Execution timestamp (local): 2026-04-19 (offline evidence pass)
- Execution timestamp (UTC): 2026-04-20 (early UTC session)
- Result: Pass (Offline)
- CSV sample excerpt: Expected columns present (`NodeID, Accel_X, Accel_Y, Accel_Z, Gyro_X, Gyro_Y, Gyro_Z, Timestamp`) with baseline `rows=43337`, `null_counts=0`, `timestamp_parse_failures=0`.
- Timestamp gap notes: Baseline stream continuity appears healthy (`gaps_gt_1s=0`); adversarial balanced set intentionally shows non-monotonic/reordered windows and large gaps due to synthesis/rebalancing.
- Artifact path(s): `backend/data/week2_data_audit.json`
- Interpretation (what this proves): Offline datasets used for current validation preserve required schema continuity and are suitable for reproducibility checks.
- If failed/deferred, triage note: Fresh live serial continuity capture is deferred to hardware session.

### W4-T6 Dashboard/API Consistency
- Objective: Confirm hybrid payload contract remains frontend-safe and consistent with backend implementation.
- Endpoint checked: `http://localhost:8000/hybrid/dashboard_data`
- Frontend check method: Endpoint JSON captured with `Invoke-RestMethod`; field semantics cross-checked against `backend/app/main.py` hybrid handler.
- Execution timestamp (local): 2026-04-19 20:43:39
- Execution timestamp (UTC): 2026-04-20 00:43:39Z (derived from local run window)
- Result: Pass
- Payload or UI excerpt: Response includes `schema_version`, `mode`, schematic nodes, and R6 hybrid fields; mode set to `hybrid`.
- Artifact path(s): `artifacts/week4/payloads/hybrid_payload_20260419_204319.json`; `artifacts/week4/payloads/test_hybrid_20260419_204319.txt`
- Interpretation (what this proves): API contract used by dashboard remains stable for hybrid mode in an offline validation session; no schema-breaking behavior observed.
- If failed/deferred, triage note: N/A

### W4-T7 Anomaly Evidence Chain
- Objective: Provide reproducible evidence that anomaly-model selection can be traced from sweep summary to selected best configuration.
- Candidate event source: Week2 window sweep consolidated results (`consolidated_sweep.csv`) and generated best-setting artifact.
- Analysis method: Executed `find_best_sweep_setting.py` with timestamped output JSON and produced ranked top-5 summary (sorted by `test_f1`, status `ok`).
- Execution timestamp (local): 2026-04-19 21:13:22
- Execution timestamp (UTC): 2026-04-20 01:13:22Z
- Result: Pass (Offline)
- Event window excerpt: Best selection `window_config=ws512_st16_thr0p25`, `run_tag=thr85p0_it250_h384-192-384_seed42`, `test_f1=0.8680851063829788`, `test_recall=0.7669172932330827`, `test_fpr_normal=0.0`.
- Artifact path(s): `backend/ml/anomaly_detection/results/week2/window_sweep_results/summaries/best_setting_20260419_211322.json`; `artifacts/week4/notes/ml_ranked_summary_20260419_211322.txt`
- Interpretation (what this proves): The anomaly workflow has a reproducible offline evidence chain from sweep outputs to a traceable selected configuration suitable for Week 4 closure packet.
- If failed/deferred, triage note: Hardware-coupled real-time anomaly event replay remains deferred to next live session.

## Deferred Items Log
| Item | Reason Deferred | Owner | Planned Follow-up Date |
|---|---|---|---|
| Live R6 telemetry state transitions (Disconnected->Idle/Busy) | No robot/Arduino connected during offline session | Luke Pepin | Next hardware session |
| Fresh serial continuity capture for Week 4 (new `training_data_*.csv`) | Tonight scope intentionally excluded hardware collection | Luke Pepin | Next hardware session |
| Real-time anomaly candidate replay from live stream | Requires live telemetry event injection/capture | Luke Pepin | Next hardware session |

## Risks and Limitations
- Risk 1: Live serial integration may still surface timing/staleness edge cases not visible in offline validation.
- Risk 2: Dashboard behavior under sustained live packet bursts remains unverified in this session.
- Limitation 1: No physical robot/Arduino telemetry was used tonight; hybrid verification is contract-level only.
- Limitation 2: `compare_window_runs.py` expects `window_runs` manifests not currently present in this result tree.

## Final Week 4 Signoff
- Acceptance criteria complete: Partial (offline complete; hardware-dependent items deferred)
- README and weekly docs aligned: Yes
- Ready for engineering next phase: Yes (with deferred hardware follow-up)
- Reviewer: Luke Pepin
- Review date: 2026-04-19
- Notes: Week 4 packet now contains offline regression, hybrid contract checks, and anomaly-model reproducibility evidence with explicit deferred hardware log.
