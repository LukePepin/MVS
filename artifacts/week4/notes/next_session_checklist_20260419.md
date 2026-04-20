# Week 4 Next Session Checklist (Hardware Follow-up)

Date: 2026-04-19
Owner: Luke Pepin

## Completed Tonight (Offline)
- W4-T1 hybrid payload contract captured (`test_hybrid_20260419_204319.txt`, `hybrid_payload_20260419_204319.json`).
- W4-T2/T3/T4 regression checks verified from saved test artifacts (all passing).
- W4-T5 offline schema continuity evidence documented from `backend/data/week2_data_audit.json`.
- W4-T7 anomaly reproducibility evidence added via:
  - `best_setting_20260419_211322.json`
  - `ml_ranked_summary_20260419_211322.txt`
- Week 4 template and docs updated with deferred hardware items.

## Needs Hardware Later
- Verify R6 transitions into `Idle`/`Busy` with actual serial IMU stream (not just `Disconnected`).
- Capture a fresh `training_data_*.csv` run and repeat continuity check for Week 4 timestamp window.
- Produce one live anomaly candidate/replay snippet tied to current hybrid session.

## Commands To Run First Next Session
1. Backend with serial enabled for live check:
   - `Set-Location C:\Users\lukep\Documents\MVS`
   - `$env:MVS_SERIAL_ENABLED = "true"`
   - `uvicorn backend.app.main:app --host 0.0.0.0 --port 8000`
2. Hybrid capture in second terminal:
   - `$ts = Get-Date -Format "yyyyMMdd_HHmmss"`
   - `.\scripts\Test-Hybrid.ps1 *>&1 | Tee-Object -FilePath ".\artifacts\week4\payloads\test_hybrid_$ts.txt"`
   - `$payload = Invoke-RestMethod -Uri "http://localhost:8000/hybrid/dashboard_data" -Method Get`
   - `$payload | ConvertTo-Json -Depth 30 | Out-File -Encoding utf8 ".\artifacts\week4\payloads\hybrid_payload_$ts.json"`
3. Safety regressions (quick sanity):
   - `python -m unittest backend.tests.test_estop_pipeline -v`
   - `python -m unittest backend.tests.test_mock_scenarios -v`

## Notes
- `rg` is optional; missing ripgrep is not a test failure.
- `compare_window_runs.py` expects `window_runs` manifests and is currently not part of tonight's closure evidence set.
