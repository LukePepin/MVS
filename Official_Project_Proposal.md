# Official Project Proposal: MVS (Minimum Viable Spring)
**Author**: Luke Pepin
**Date**: March 31, 2026

## Executive Summary
This project proposes a localized, decentralized Manufacturing Execution System (MES) for an Expeditionary Automated Repair Cell (EARC) operating in Disconnected, Intermittent, and Limited (DIL) environments. The architecture bridges three advanced engineering disciplines:
1. **Manufacturing Execution Systems** (ISE573): Decentralized MES operations utilizing an Earliest Due Date (EDD) and Shortest Processing Time (SPT) deterministic scheduling framework.
2. **Industrial Machine Learning / TinyML** (ISE572): Edge-first kinematic anomaly detection employing an unsupervised Autoencoder Neural Network on constrained hardware (Arduino Nano 33 BLE Cortex-M4).
3. **Cyber-Physical Systems (CPS) Security**: A Probabilistic Trust Equation integrating Zero-Knowledge Proof (ZKP) verification to combat adversarial command injection and signal jamming, enabling autonomous resilience.

## 1. Problem Statement
Industry 4.0 relies on centralized cloud authentication, creating critical single points of failure. In tactical DIL environments (such as forward-deployed Navy/Marine Corps logistics or remote submarine tenders), adversary-induced communication jamming severs backhaul connectivity. This causes short-lived authorization leases to expire, plunging the robotic systems into involuntary DO-178C "safety stops" and resulting in mission failure. We require a decentralized verification framework capable of validating that physical robot kinematics match the intended toolpath without reliance on a central server.

## 2. Technical Architecture Layers

### 2.1 The Logistics Layer (Decentralized MES)
- **Host**: Raspberry Pi 4 (Cortex-A72) Supervisor Node.
- **Function**: Executes Master Production Scheduling (MPS) offline utilizing a hybrid push/pull strategy.
- **Queueing Theory Integration**: To combat high variability (e.g., CNC Lathe CV=1.5), the cell utilizes a Shortest Processing Time (SPT) dispatching algorithm to clear low-complexity jobs (like gaskets on the Dual Laser Cutters) rapidly, drastically reducing Mean Time to Recovery (MTTR) and Work-in-Process (WIP).

### 2.2 The Intelligence Layer (Edge Machine Learning)
- **Host**: Arduino Nano 33 BLE Sense.
- **Sensor (Current Implementation Scope)**: Onboard LSM9DS1 IMU using 6-axis telemetry (accelerometer + gyroscope) with host-side UTC timestamping.
- **Constraint**: Strict 200KB SRAM maximum footprint.
- **Mechanism**: A TinyML Autoencoder processes continuous physical telemetry. Given a standard kinematic loop learned via a Unity Digital Twin, any adversarial payload that alters the physical path registers a massive spike in Reconstruction Error.

### 2.3 The Response Layer (Autonomous Resilience)
- **Mechanism**: Decentralized MANET authorization using Schnorr-based ZKP.
- **Trust Equation**: $\Gamma(t+1) = \alpha \cdot \Gamma(t) + (1-\alpha) \cdot N_0$
- **Degradation Policy**: If an anomaly drives the reconstruction error above threshold, the trust score decays. Once the score hits Critical Threshold (0.30), the edge node autonomously forces a fail-safe electrical disconnect within $\le 500ms$, quarantining the compromised segment while the rest of the cell continues operations.

## 3. Implementation Phasing

**Phase 1: Admin & Baseline Visualization (MVP)**
- Formulate the FastAPI/SQLite data pipeline.
- Develop the initial React.js visual dashboard with simulated mock telemetry and Triangular branch/merge rendering.

**Phase 2: Layout Realism & Aesthetics**
- Scale the testbed layout to a 27-node capability representing distinct Fab Branches (Mill, Laser, Lathe).
- Professionalize the visual command interface (MVS Glassmorphic Theme).

**Phase 3: Queueing & Routing Intelligence**
- Inject explicit stochastic processing times reflecting high-mix repair geometries.
- Introduce advanced Shortest Processing Time (SPT) dispatching versus naive FIFO rules.

**Phase 4: Hardware Porting & Defense Applications**
- Quantize the Autoencoder and flash to the Arduino Cortex-M4.
- Conduct live physical tests under simulated 20% packet loss environments to validate ZKP viability against traditional ECC authentication models.

---
## Final Goal Update (Implementation Pivot)

- The final demonstrated system is a **hybrid testbed**: real robot/IMU telemetry is ingested in real format and fed into simulated MES node behavior.
- The mock table and routing engine are retained, but at least one robot node is assigned to real robot telemetry input.
- Collision events observed during physical runs are treated as anomaly signals for detection and evaluation.

---
## Future Work: Migration to Real Application
To transition the current `SchematicVisualizer` from standard React props to physical operations:
- **Telemetry Translation Engine:** Modify the FastAPI backend to ingest live physical hardware states (e.g., raw ROS2 MQTT messages from real Niryo Ned2 arms and physical Python serial port connectors from Arduino) and translate them into exactly matching JSON format `data.machine_status` required by the `SchematicVisualizer.jsx`.
- **Dynamic Node Registration:** Since the real environment may suffer from network node drops, the visualizer array `data.schematic.nodes` must actively deregister shapes if a physical edge node stops broadcasting heartbeats, rather than statically assuming all 27 nodes exist perpetually.
