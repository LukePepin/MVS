# Week 1: MVS ROS, Hardware, and Baseline Data Collection
Date: 2026-04-08
Status: Complete

## Week 1 Goals

- Establish physical robot + IMU data pipeline.
- Execute repeatable robot motion script for nominal behavior capture.
- Produce baseline training dataset for model development.
- Integrate architecture pivot decisions into implementation status.

## Pivot-Integrated Decisions

- Baseline collection mode for Week 1 is 6-axis host CSV (Accel + Gyro + host UTC timestamp).
- Collision events observed during runs are not discarded; they will be treated as anomaly events in later model phases.
- Software serial e-stop path established from Arduino to host backend, superseding the original hardware GPIO Ned2 requirement for this MVP.

## Evidence Collected

- Robot motion script running with pose validation and collision recovery:
   - `tinyml-anomaly/MVS_data_collection.py`
- Datalogger supports reconnect behavior and COM failover (COM9 and COM14):
   - `tinyml-anomaly/phase2_datalogger.py`
- Continuous baseline dataset available:
   - `tinyml-anomaly/data/training_data_0001.csv`
- Architecture pivot reference:
   - `docs/design/architecturepivot.md`

## Checklist

### Phase 1: Serial and Host Pipeline

- [x] Arduino serial connectivity verified on Windows host.
- [x] Host datalogger captures IMU rows with UTC timestamp.
- [x] CSV schema aligned for 6-axis baseline collection.
- [x] Reconnect logic added for serial disconnects.

### Phase 2: Physical Hardware Assembly

- [x] Arduino mounted at wrist/end-effector region.
- [x] Robot saved poses validated and executable.
- [x] Calibration workflow tested before motion run.
- [x] Software E-STOP feature (Arduino Serial -> Host Backend) completed.
- [x] E-STOP pipeline tested and documented.

### Phase 4: Baseline Execution and Validation

- [x] Continuous nominal loop executed and logged.
- [x] Baseline data artifact created: training_data_0001.csv.
- [x] Collision handling added in motion script (clear and retry once).
- [x] Collision event boundaries formally annotated in dataset metadata file (none in baseline).
- [x] Final Week 1 sign-off complete.

## Known Issues and Mitigations

- USB serial instability observed (port flips and intermittent disconnects).
   - Mitigation: fallback ports and reconnect logic in datalogger.
- Collision event occurred around minute 21 in one run.
   - Mitigation: automatic collision-clear retry implemented.
   - Forward use: treat these events as anomaly candidates.

## Next Steps
1. Keep data output path standardized at `tinyml-anomaly/data` for all new runs in Week 2.
