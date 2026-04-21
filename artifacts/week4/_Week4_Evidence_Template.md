# Week 4 Evidence Template (Fillable)
Date: 2026-04-19
Prepared by: Luke Pepin
Project: MVS (Minimum Viable Spring)
Week: 4
Status: In Progress (Offline Complete + Live Hybrid Evidence Captured)

## Instructions
- Fill one section per validation item.
- Keep raw command output excerpts short and focused.
- Add links/paths to saved artifacts.
- Mark each item Pass, Fail, or Deferred.

## Validation Summary
| Test ID | Objective | Result | Evidence Path | Notes |
|---|---|---|---|---|
| W4-T1 | Hybrid payload and R6 mapping | Pass | artifacts/week4/payloads/test_hybrid_20260420_103445.txt; artifacts/week4/payloads/hybrid_payload_20260420_103445.json | Live capture confirms `source=live` and R6 transitioned to `Busy` with non-null IMU fields. |
| W4-T2 | Mock scenario baseline | Pass | artifacts/week4/tests/mock_scenario_20260419_202720.txt | 2/2 tests passed; baseline mock engine behavior is stable. |
| W4-T3 | E-STOP safety path regression | Pass | artifacts/week4/tests/estop.txt | 2/2 tests passed; E-STOP flag and datalogger stop-path validated. |
| W4-T4 | Mock transition regression | Pass | artifacts/week4/tests/mock_scenario.txt | Connector transition test passed and routing connector keys validated. |
| W4-T5 | Telemetry schema continuity | Pass | artifacts/week4/tests/datalogger_20260420_104459.txt; artifacts/week4/notes/w4_t5_continuity_20260420_104459.txt; backend/data/training_data_0002.csv | Live COM9 capture completed; continuity report shows no missing columns, no timestamp parse failures, and no gaps > 1s. |
| W4-T6 | Dashboard/API consistency | Pass | artifacts/week4/payloads/hybrid_payload_20260420_103445.json | Live hybrid payload includes expected schema/mode and frontend-consumed R6 fields under active telemetry. |
| W4-T7 | Anomaly evidence chain | Pass | artifacts/week4/tests/robot_adversarial_20260420_104459.txt; artifacts/week4/notes/anomaly_window_20260420_104459.csv; artifacts/week4/notes/w4_t7_live_note_20260420_104459.md | Live robot adversarial run captured with multiple anomaly-like event types and linked IMU window evidence. |

## Environment Snapshot
- OS: Windows
- Python version: 3.13.13
- Backend start command: uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
- Frontend start command: cd frontend && npm run dev -- --host 0.0.0.0 --port 5173
- Active branch: main
- Commit hash: e225d03
- Serial port(s): COM9 (live hybrid evidence session)

## Evidence Records

### W4-T1 Hybrid Payload and R6 Mapping
- Objective: Validate that `/hybrid/dashboard_data` is reachable and that node R6 is present with hybrid/live source metadata fields.
- Command/script: `.\scripts\Test-Hybrid.ps1 *>&1 | Tee-Object -FilePath .\artifacts\week4\payloads\test_hybrid_20260420_103445.txt`
- Execution timestamp (local): 2026-04-20 10:34:45
- Execution timestamp (UTC): 2026-04-20 14:34:59Z (from payload host_time window)
- Result: Pass
- Key output excerpt: `Schema version: 1`, `Mode: hybrid`, `R6 status: Busy`, `R6 source: live`, `R6 raw_imu: ax=-0.606934 ay=-0.02478 az=0.785889 gx=2.807617 gy=0.305176 gz=-0.12207`
- Payload snippet: R6 fields observed and populated for hybrid contract (`source`, `status`, `host_time`, `device_time`, `raw_imu`).
- Artifact path(s): `artifacts/week4/payloads/test_hybrid_20260420_103445.txt`; `artifacts/week4/payloads/hybrid_payload_20260420_103445.json`
- Interpretation (what this proves): Hybrid endpoint and R6 field mapping are functioning under live telemetry conditions. This evidence closes the live transition requirement for Week 4 hybrid validation.
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
- Data source: `backend/data/training_data_0002.csv` (live COM9 capture session).
- Validation method: Datalogger run log review plus continuity summary produced from terminal verification.
- Execution timestamp (local): 2026-04-20 (hardware session)
- Execution timestamp (UTC): 2026-04-20 (hardware session)
- Result: Pass
- CSV sample excerpt: Continuity report summary: `rows=2092`, `missing_columns=`, `timestamp_parse_failures=0`, `gaps_gt_1s=0`.
- Timestamp gap notes: No timestamp parsing failures and no gaps over 1 second were observed in the continuity summary.
- Artifact path(s): `artifacts/week4/tests/datalogger_20260420_104459.txt`; `artifacts/week4/notes/w4_t5_continuity_20260420_104459.txt`; `backend/data/training_data_0002.csv`
- Interpretation (what this proves): Live telemetry capture and schema continuity are validated on the current hardware session.
- If failed/deferred, triage note: N/A

### W4-T6 Dashboard/API Consistency
- Objective: Confirm hybrid payload contract remains frontend-safe and consistent with backend implementation.
- Endpoint checked: `http://localhost:8000/hybrid/dashboard_data`
- Frontend check method: Endpoint JSON captured with `Invoke-RestMethod`; field semantics cross-checked against `backend/app/main.py` hybrid handler.
- Execution timestamp (local): 2026-04-20 10:34:45
- Execution timestamp (UTC): 2026-04-20 14:34:59Z (payload host_time window)
- Result: Pass
- Payload or UI excerpt: Response includes `schema_version=1`, `mode=hybrid`, `r6.source=live`, `r6.status=Busy`, and populated `raw_imu`/`host_time` fields.
- Artifact path(s): `artifacts/week4/payloads/hybrid_payload_20260420_103445.json`; `artifacts/week4/payloads/test_hybrid_20260420_103445.txt`
- Interpretation (what this proves): API contract used by dashboard remains stable for hybrid mode during live telemetry capture; no schema-breaking behavior observed.
- If failed/deferred, triage note: N/A

### W4-T7 Anomaly Evidence Chain
- Objective: Provide reproducible evidence that anomaly-model selection can be traced from sweep summary to selected best configuration.
- Candidate event source: Live robot adversarial motion run (`robot_adversarial_20260420_104459.txt`) aligned with live telemetry capture window.
- Analysis method: Extracted event lines (`stoppage`, `burst`, `jitter`, `home_interrupt`, `freeze`) and linked them to an exported trailing telemetry window.
- Execution timestamp (local): 2026-04-20 (hardware session)
- Execution timestamp (UTC): 2026-04-20 (hardware session)
- Result: Pass
- Event window excerpt: Robot log contains repeated anomaly-like events across 120 cycles, including stoppage holds and burst/jitter behavior; linked telemetry window saved for evidence.
- Artifact path(s): `artifacts/week4/tests/robot_adversarial_20260420_104459.txt`; `artifacts/week4/notes/anomaly_window_20260420_104459.csv`; `artifacts/week4/notes/w4_t7_live_note_20260420_104459.md`
- Interpretation (what this proves): Live anomaly-candidate evidence chain is captured from robot behavior to saved telemetry window and narrative note.
- If failed/deferred, triage note: N/A

## Deferred Items Log
| Item | Reason Deferred | Owner | Planned Follow-up Date |
|---|---|---|---|
| N/A | N/A | N/A | N/A |

## Risks and Limitations
- Risk 1: Longer live runs may still surface timing/staleness edge cases not visible in this capture duration.
- Risk 2: On-device TinyML inference on Arduino remains outside this Week 4 validation scope.
- Limitation 1: Evidence uses host-side anomaly candidate linkage; embedded model inference is not yet implemented.
- Limitation 2: `compare_window_runs.py` expects `window_runs` manifests not currently present in this result tree.

## Final Week 4 Signoff
- Acceptance criteria complete: Yes (W4-T1 through W4-T7 completed with artifacts)
- README and weekly docs aligned: Yes
- Ready for engineering next phase: Yes
- Reviewer: Luke Pepin
- Review date: 2026-04-20
- Notes: Week 4 packet includes live hybrid evidence, live telemetry continuity evidence (`training_data_0002.csv`), and live anomaly-candidate evidence chain for run `20260420_104459`.
