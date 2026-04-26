# Presentation Topics: MVS (Minimum Viable Spring)

Date: 2026-04-06

## Core Terms and Definitions

1. MVS (Minimum Viable Spring)
- Definition: A scoped implementation of the MES cyber-physical pipeline that proves end-to-end telemetry ingestion, storage, visualization, and analytics with realistic hardware constraints.
- Speaker note: Say "small but complete". The point is integration quality, not full production scale.

2. MES (Manufacturing Execution System)
- Definition: The operational software layer between planning and machine control that tracks state, work orders, machine health, and material flow in near real time.
- Speaker note: Emphasize that MES is the bridge between what should happen and what is happening now.

3. EARC (Expeditionary Automated Repair Cell)
- Definition: A distributed manufacturing and repair concept used as the operating scenario for this project's digital twin and telemetry flows.
- Speaker note: This provides the mission context for queue behavior, machine states, and resilience requirements.

4. Digital Twin
- Definition: A live software representation of manufacturing states, inventory queues, and routing logic used for monitoring and decision support.
- Speaker note: Clarify that this twin is behaviorally aligned for decision support, not a perfect physics simulator.

5. IMU Telemetry (6-axis)
- Definition: Accelerometer (x,y,z) and gyroscope (x,y,z) signals collected from Arduino Nano 33 BLE for motion-state and anomaly analysis, with host-generated UTC timestamp.
- Speaker note: This is the raw observable used for baseline and anomaly detection.

6. Telemetry Translation Engine
- Definition: Backend logic that maps physical or ROS2/serial signals into the exact dashboard schema consumed by the visualization frontend.
- Speaker note: This is the interoperability layer that makes mixed data sources look uniform.

7. Queue Depth
- Definition: Number of jobs waiting at inventory or machine-adjacent buffers.
- Speaker note: Use this as your visual indicator of bottlenecks and blocked flow.

8. Work Center State Model
- Definition: Node status categories such as Idle, Busy, Blocked, and Offline used by the testbed and dashboard.
- Speaker note: Keep this model consistent inside the hybrid mode where real telemetry feeds simulated node behavior.

9. Baseline Dataset
- Definition: Nominal-operation IMU samples collected under standard robot motion loops for training and validating anomaly methods.
- Speaker note: Baseline quality controls downstream model credibility.

10. DIL (Disconnected, Intermittent, and Limited)
- Definition: Communication conditions where bandwidth, continuity, or reliability are degraded.
- Speaker note: Architecture choices should maintain observability despite DIL constraints.

## Important Project Details

1. Primary stack
- Backend: FastAPI + async processing + SQLite persistence.
- Frontend: React/Vite dashboard with schematic visualization.
- Hardware: Arduino Nano 33 BLE IMU attached to robot end-effector region.

2. Data path
- Sensor output: Arduino serial prints IMU CSV rows.
- Host processing: Python reads serial, appends timestamp/NodeID, writes incrementing CSV files in `tinyml-anomaly/data`.
- Dashboard feed: Backend publishes hybrid telemetry + simulated node state to frontend.

3. Current status (April 6, 2026)
- Arduino serial connectivity validated on COM15 at 115200 baud.
- Stable heartbeat/ACK workflow previously verified.
- Docker and Git workflow operational.
- Project transitioned to Week 1 Phase 2 (physical hardware assembly).

4. Phase 2 focus
- Rigid sensor mounting near tool flange/end-effector region.
- Reliable serial telemetry capture during repeatable motion loops.
- Baseline capture quality checks before longer acquisition windows.

5. Network requirement decision
- Same network is required when integrating directly with Niryo control/ROS2 state messaging.
- Same network is not required for local USB-only Arduino logging to a single host.

6. Mounting decision
- Use the wrist-side end-effector region (near final joint/tool flange).
- Do not mount on base or shoulder joints if the objective is tool-path anomaly visibility.

## Project Explanation: Nontechnical Audience

MVS is a practical pilot system that watches how a robotic manufacturing setup behaves in real time. A small sensor on the robot captures movement signals, and software turns those signals into a live dashboard that shows what machines are doing, where queues are forming, and whether operations look normal. The value is early visibility: teams can spot slowdowns, unusual behavior, and reliability risks before they become expensive failures. This project is intentionally scoped so every major piece works together end-to-end.

## Project Explanation: Undergraduate Audience

MVS is an integrated cyber-physical pipeline for manufacturing observability. The Arduino Nano 33 BLE collects 6-axis IMU signals, which are streamed over serial to a Python/FastAPI backend. The backend normalizes telemetry, stores operational records, and serves a React dashboard with machine states and queue depths. The demonstrated architecture is a hybrid testbed: simulated process-state nodes remain active while at least one robot node is driven by real telemetry from physical execution loops. In short, MVS demonstrates how to connect embedded sensing, async backend services, and a visualization layer into one reproducible system.

## Project Explanation: Graduate Audience

MVS operationalizes a constrained MES-aligned architecture for distributed manufacturing observability under realistic integration and DIL-adjacent assumptions. The system combines: (a) physical 6-DoF IMU telemetry from an end-effector-mounted Nano 33 BLE, (b) an asynchronous FastAPI ingestion/translation layer with persistent state, and (c) a hybrid digital twin interface where simulated node semantics (Idle/Busy/Blocked/Offline, queue-depth propagation, routing state) are driven by real telemetry inputs. The methodological emphasis is representation fidelity across interfaces: serial/ROS2-origin signals are translated into a stable dashboard schema, enabling longitudinal baseline capture and subsequent anomaly detection workflows. The research contribution is not novelty in individual components, but in robust end-to-end coupling, schema consistency, and verifiable transition from synthetic to physically sourced telemetry in a manufacturing context.

## Demo Talking Points (Speaker Notes)

1. Start with architecture in one sentence
- "Sensor to backend to dashboard, with real telemetry driving a simulated-node hybrid state model."

2. Show one queue bottleneck and one recovery
- Explain queue depth growth, then return to nominal flow.

3. Show physical telemetry capture
- Confirm serial line structure and timestamped host logging.

4. Close on why MVS matters
- Integration confidence now, model-driven anomaly capability next.
