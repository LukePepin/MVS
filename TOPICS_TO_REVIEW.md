# Topics To Review (MVS Presentation)

## 1) Problem Framing and Why MVS Matters
- What manufacturing pain point is being solved.
- Why anomaly detection at the robot-wrist telemetry layer is useful.
- Why a hybrid architecture (one live node + simulated nodes) was chosen.

## 2) System Architecture Story
- High-level data flow: Arduino IMU -> serial logger -> backend API -> frontend dashboard.
- Role of `/dashboard_data`, `/mock/dashboard_data`, and `/hybrid/dashboard_data`.
- How R6 live mapping works while other nodes remain simulated.

## 3) Week 4 Validation Strategy
- Acceptance matrix approach (W4-T1..W4-T7).
- Evidence standards (command, timestamp, output snippet, artifact path, interpretation).
- Why this creates auditability and repeatability.

## 4) Data and Feature Pipeline
- Raw sensor axes used: Accel_X/Y/Z and Gyro_X/Y/Z.
- Windowing configuration used in TinyML run (window size 32, flattened input dim 192).
- Why stratified split was required for appended labeled data.

## 5) Model Design and Training Choices
- Small dense autoencoder choice for edge feasibility.
- Training objective: reconstruct normal behavior, anomaly via reconstruction error.
- Threshold calibration and tradeoff discussion (precision/recall/FPR).

## 6) TinyML Conversion and Deployment
- Keras model -> TFLite export -> model header generation.
- Runtime config coupling: mean/std scaling and threshold consistency.
- Board constraints: flash/RAM usage and why model size matters.

## 7) True On-Device Inference Demo
- What confirms true ML (model inference path, not heuristic-only thresholds).
- Serial evidence lines to show:
  - `READY:TINYML_INFERENCE`
  - `WARMING_UP`
  - `ML_SCORE=<value> THRESH=<value> STATUS=<...>`
- How to explain model score and anomaly decision in plain language.

## 8) Motion Injection Demo Design
- Continuous baseline with increasing anomaly injection probability.
- Clear demo markers:
  - `INJECTION STARTED`
  - `INJECTION BURST`
  - `INJECTION STOPPED`
- Why 5-second burst at higher speed improves visual clarity.

## 9) Results and Evidence to Present
- Model metrics summary from Week 2 labeled run (`eval_report.json`).
- Live run logs and anomaly marker alignment.
- One or two screenshots/payload snippets that show end-to-end behavior.

## 10) Limitations and Honest Risk Discussion
- Domain shift risk: Week 2 labeled data vs live session behavior.
- Threshold retuning needs for new conditions.
- Remaining engineering scope for broader generalization.

## 11) Next Steps (What You Would Do In Week 5+)
- Add new labeled live data and retrain.
- Improve model robustness and calibration protocol.
- Expand from single live node to multi-node live telemetry.
- Add automated evaluation scripts for deployment regression checks.

## 12) Likely Q&A Prompts to Practice
- "How do you prove this is true on-device ML and not rule-based?"
- "Why an autoencoder instead of a classifier?"
- "How was threshold selected, and what happens when environment changes?"
- "What is the fallback plan if false positives rise in production?"
- "What parts of the pipeline are reproducible today?"
