# Week 4: Validation Definition, Evidence Plan, and Closure Prep
Date: 2026-04-19
Status: In Progress (Offline Evidence Captured, Hardware Follow-up Pending)

## Week 4 Objective

Freeze a clear, testable Week 4 validation plan for the hybrid 6-axis MVS system before starting additional engineering work.

This week pass is intentionally focused on:
- defining tests,
- defining pass/fail criteria,
- defining evidence artifacts,
- defining run order,
- documenting deferred engineering scope.

## Scope Boundary (Important)

### Included in this Week 4 pass
- Validation planning and acceptance criteria hardening.
- Test matrix definition using existing scripts and tests.
- Evidence standards and artifact naming conventions.
- README runbook and learning-resource updates.

### Deferred to later engineering pass
- New feature implementation for on-device Nano inference.
- New model-conversion/export pipelines.
- New anomaly detection runtime components.

## Final Goal Statement

The final demonstrated system target remains a hybrid testbed with one robot node backed by real telemetry, simulated MES behavior preserved for the remaining nodes, and anomaly workflow evidence captured against real-formatted data.

## Requirement Traceability Snapshot

| Area | Requirement | Current Status | Notes |
|---|---|---|---|
| Telemetry Reliability | Stable serial capture with reconnect/failover and valid CSV schema | Partial (Offline Evidence Captured) | `backend/data/week2_data_audit.json` confirms schema continuity on existing datasets; fresh live serial capture deferred to hardware session |
| Hybrid Node Correctness | R6 reflects live source while other nodes remain simulated | Pass (Offline Hybrid Contract) | Captured `/hybrid/dashboard_data` payload and script output with R6 `source=live` plus expected `Disconnected` when serial input is unavailable |
| Anomaly Workflow Validation | Collision/anomaly candidate windows are surfaced and reportable | Pass (Offline Reproducibility) | Timestamped `best_setting_20260419_211322.json` and ranked summary recorded for repeatable model-selection evidence; live replay deferred |
| Dashboard/API Consistency | Frontend-safe payload schema and no core regressions | Pass (Offline) | Hybrid payload contract verified (`schema_version`, `mode`, R6 mapping fields) with no schema-breaking changes observed |
| Documentation/Closure | README and weekly chain match actual validation flow | In Progress | Week 4 evidence template and Terminal B command guide moved to `docs/weekly/week4`; deferred-item log and next-session checklist captured under `artifacts/week4/notes` |

## Week 4 Acceptance Test Matrix (Executable Definition)

| ID | Objective | Source/Input | Command or Script | Expected Result | Evidence Artifact | Failure Triage Note |
|---|---|---|---|---|---|---|
| W4-T1 | Validate hybrid payload availability and R6 live mapping | Running backend + telemetry stream | `./scripts/Test-Hybrid.ps1` | Returns schema version, mode, and R6 fields without missing-node failure | Terminal output log and payload snippet | If R6 missing, verify backend startup mode and serial node id mapping |
| W4-T2 | Validate mock scenario stability baseline | Backend unit/integration tests | `./scripts/Run-MockScenario.ps1` | Mock scenario tests complete and output file created in artifacts | `artifacts/mock_scenario_*.txt` | If failures occur, isolate deterministic seed and compare to recent changes |
| W4-T3 | Validate safety/E-STOP signal path behavior | Backend safety pipeline tests | `python -m unittest backend.tests.test_estop_pipeline -v` | E-STOP flag creation and stop behavior validated by tests | Terminal output capture and test summary | If failing, inspect serial parsing and estop flag file handling |
| W4-T4 | Validate mock engine transitions and connector model assumptions | Backend mock tests | `python -m unittest backend.tests.test_mock_scenarios -v` | Work-order spawn and connector transition checks pass | Terminal output capture and test summary | If failing, inspect route assumptions and connector build logic |
| W4-T5 | Validate telemetry schema continuity in data files | `backend/data/training_data_*.csv` | Manual schema/timestamp audit against latest run output | Required columns present, no malformed rows, acceptable timestamp gaps | CSV sample excerpt and audit notes | If malformed rows appear, verify logger parsing and reconnect behavior |
| W4-T6 | Validate dashboard/API consistency in hybrid mode | `/hybrid/dashboard_data` payload + frontend rendering | Manual endpoint inspection + frontend smoke check | No schema-breaking changes, core views remain operational | Screenshot + payload snippet + date/time stamp | If schema mismatch appears, reconcile field names with frontend expectations |
| W4-T7 | Validate anomaly-candidate evidence chain | Collision event window or annotated candidate | Replay/annotation check workflow | Candidate event can be shown in logs and summarized in report | Event window snippet + short narrative | If unavailable, document as deferred evidence with reason and next action |

## Evidence Capture Standard

For every accepted test item, capture all of the following:

1. Command/script used.
2. Execution date/time (local and UTC when possible).
3. Pass/fail result.
4. Short excerpt of output (or payload snippet).
5. Artifact location path.
6. One-line interpretation (what this proves).

### Suggested artifact folders
- `artifacts/week4/tests/`
- `artifacts/week4/payloads/`
- `artifacts/week4/screenshots/`
- `artifacts/week4/notes/`

### Week 4 docs location (updated)
- `docs/weekly/week4/_Week4_Evidence_Template.md`
- `docs/weekly/week4/TerminalB_Commands.md`

## Week 4 Validation Cadence

1. Day 1: Environment dry run and command sanity
- Confirm backend/frontend start commands and script availability.
- Run W4-T2, W4-T3, W4-T4 to establish baseline stability.

2. Day 2: Hybrid mapping and payload evidence
- Run W4-T1 and W4-T6.
- Capture R6 evidence, payload snapshots, and frontend screenshots.

3. Day 3: Telemetry and anomaly workflow evidence
- Execute W4-T5 and W4-T7.
- Capture timestamp/gap audit and anomaly candidate notes.

4. Day 4: Closure packet assembly
- Build final report, risk list, and limitation summary.
- Ensure README and weekly documentation consistency checks are complete.

## Learning Resources for Week 4 Execution

### Internal project reading order
1. `docs/design/Official_Project_Proposal.md`
2. `docs/design/architecturepivot.md`
3. `docs/design/testbed.md`
4. `docs/weekly/Week1.md`
5. `docs/weekly/Week2.md`
6. `docs/weekly/Week3.md`
7. `docs/weekly/Week4.md`
8. `docs/ISE572_ML_Proposal_Readme.md`

### External references (implementation understanding)
1. FastAPI docs: https://fastapi.tiangolo.com/
2. React docs: https://react.dev/
3. Arduino Nano 33 BLE board docs: https://docs.arduino.cc/hardware/nano-33-ble/
4. Arduino LSM9DS1 library docs: https://docs.arduino.cc/libraries/arduino_lsm9ds1/
5. TinyML overview (TensorFlow Lite Micro): https://www.tensorflow.org/lite/microcontrollers

## Closure Deliverables (Week 4)

- Final hybrid-mode validation report.
- Final anomaly-workflow evidence summary.
- Final dataset inventory list in `backend/data`.
- Final known limitations and risk register.
- Presentation-ready evidence packet with test traces.

## Tonight Work Completed (2026-04-19)

- Executed and documented offline regression evidence for W4-T2/W4-T3/W4-T4 with passing artifacts under `artifacts/week4/tests`.
- Captured hybrid API contract evidence for W4-T1/W4-T6 under `artifacts/week4/payloads`.
- Added offline telemetry continuity evidence (W4-T5) using `backend/data/week2_data_audit.json`.
- Added anomaly reproducibility evidence (W4-T7) using:
	- `backend/ml/anomaly_detection/results/week2/window_sweep_results/summaries/best_setting_20260419_211322.json`
	- `artifacts/week4/notes/ml_ranked_summary_20260419_211322.txt`
- Updated evidence template with deferred items, risks, limitations, and signoff fields.
- Added next-session hardware checklist at `artifacts/week4/notes/next_session_checklist_20260419.md`.

## Remaining To Finish (Hardware Session)

1. Capture a live serial session where R6 transitions from `Disconnected` to `Idle` or `Busy`.
2. Record a fresh Week 4 serial dataset (`training_data_*.csv`) and repeat continuity checks against current run output.
3. Capture one live anomaly-candidate replay/event window and add a short evidence narrative.
4. Add at least one frontend screenshot tied to the same hybrid payload window used for final signoff.

## Full Project Understanding Sources

### Core architecture and intent
1. `docs/design/Official_Project_Proposal.md`
2. `docs/design/architecturepivot.md`
3. `docs/design/testbed.md`
4. `docs/ISE572_ML_Proposal_Readme.md`

### Weekly implementation chain
1. `docs/weekly/Week1.md`
2. `docs/weekly/Week2.md`
3. `docs/weekly/Week3.md`
4. `docs/weekly/Week4.md`

### Backend runtime and integration surfaces
1. `backend/app/main.py` (`/dashboard_data`, `/mock/dashboard_data`, `/hybrid/dashboard_data`)
2. `backend/phase2_datalogger.py` (serial capture and CSV output)
3. `backend/tests/test_estop_pipeline.py` (safety path assertions)
4. `backend/tests/test_mock_scenarios.py` (transition and connector assumptions)

### Frontend and API contract usage
1. `frontend/src/dashboard.jsx` (polling and payload usage)
2. `frontend/src/components/` (rendering details)
3. `scripts/Test-Hybrid.ps1` (hybrid payload quick validation)

### ML evidence and reproducibility
1. `backend/ml/anomaly_detection/scripts/find_best_sweep_setting.py`
2. `backend/ml/anomaly_detection/scripts/automate_train_window_sweep.py`
3. `backend/ml/anomaly_detection/results/week2/window_sweep_results/summaries/consolidated_sweep.csv`
4. `backend/ml/anomaly_detection/results/week2/window_sweep_results/summaries/best_setting.json`

## Presentation Topics To Review (Next Week)

1. Hybrid architecture story: why one live node (R6) plus simulated MES nodes reduces risk while preserving integration realism.
2. Safety story: how E-STOP flows from telemetry parsing to control stop behavior and what was validated offline.
3. API contract stability: demonstrate schema-versioned payload, `mode=hybrid`, and R6 mapping fields expected by the UI.
4. Evidence-driven validation workflow: show the acceptance matrix (W4-T1..W4-T7), artifact paths, and deferred-log discipline.
5. ML reproducibility story: explain sweep criteria (`test_f1`, recall, FPR), selected best setting, and why reproducibility matters before deployment.
6. Remaining risk and next hardware steps: stale/live transition checks, fresh serial capture, and live anomaly replay plan.

## Week 4 Exit Criteria (Project Closure)

- All planned acceptance tests executed or explicitly deferred with rationale.
- Hybrid mode evidence captured end-to-end with real telemetry-backed node behavior.
- Anomaly handling path evidenced with at least one candidate window or documented deferred reason.
- README and weekly documentation chain are consistent with executed validation flow.

## Week 4 Definition-Complete Checklist

- [x] Acceptance categories translated into executable tests.
- [x] Pass/fail and artifact requirements defined.
- [x] Validation cadence documented for the week.
- [x] Learning resources listed for implementation understanding.
- [x] Deferred engineering scope explicitly declared.
