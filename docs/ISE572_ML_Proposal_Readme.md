# ISE572 ML Proposal Handoff (Teammate Readme)

Concise handoff for the ML side of the ISE572 proposal. Focus is on what has already been run, the best reported metrics (recall and F1), and what can still be done fully online (no hardware required).

## What was run (Week 2 closeout)
- Windowed autoencoder sweep completed with consolidated outputs.
- Best setting selector run against the consolidated CSV.
- Artifacts saved under backend/ml/anomaly_detection/results/week2/window_sweep_results/.

## Headline metrics (selected model for future work)
This uses the strongest sweep result under the current selector constraints.

- window_config: ws512_st16_thr0p25
- run_tag: thr85p0_it250_h384-192-384_seed42
- test_f1: 0.8680851063829788
- test_precision: 1.0
- test_recall: 0.7669172932330827
- test_fpr_normal: 0.0

## Repro commands (online-only)
Run from backend/ml/anomaly_detection/scripts:

```powershell
# Re-select best setting from consolidated sweep
python .\find_best_sweep_setting.py --csv ..\results\week2\window_sweep_results\summaries\consolidated_sweep.csv --status ok

# Compare windowed split runs (label balance sanity check)
python .\compare_window_runs.py --runs-root ..\results\week2\window_runs
```

## What still needs to be done (online, no hardware)
- Search for better variable combinations (windowing, threshold percentile, architecture) to improve scores.
- Test and validate new runs against the current model with consistent selection criteria.
- Check stability across seeds and confirm the best setting holds under repeat runs.

## Week 4 note (current pass)

Week 4 is currently documentation-first: validation criteria, test matrix definitions, and evidence packaging are being finalized before additional engineering implementation.

For Week 4 execution details, see:

- `docs/weekly/Week4.md`
- `README.md` (Week 4 Validation Quickstart)

## Key files
- docs/weekly/Week2.md
- docs/weekly/Week4.md
- README.md
- backend/ml/anomaly_detection/results/week2/window_sweep_results/summaries/best_setting.json
- backend/ml/anomaly_detection/results/week2/window_sweep_results/summaries/consolidated_sweep.csv
- backend/ml/anomaly_detection/scripts/find_best_sweep_setting.py
- backend/ml/anomaly_detection/scripts/compare_window_runs.py
