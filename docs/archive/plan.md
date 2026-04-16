# SentryC2 EARC MES Project Plan

Date: 2026-03-31
Owner: Luke Pepin
Project: SpringMVP

## 1. Executive Summary
SentryC2 EARC is an edge-first Manufacturing Execution System (MES) designed for expeditionary and disconnected naval environments. The system couples deterministic backend telemetry ingestion with an operational dashboard and a mock testbed for rapid flow and control validation.

This plan consolidates the complete project from MVP status through hardened operational capability. It defines architecture, milestone roadmap, testing strategy, latency governance, safety constraints, and engineering risk management.

## 2. Mission and Scope
### Mission
Provide a resilient Level 3 MES that can:
- Ingest high-frequency hardware telemetry over UDP.
- Maintain traceable process and inventory records.
- Deliver actionable operations visibility through a low-latency dashboard.
- Emulate production flow with a realistic mock testbed for algorithm and layout iteration.

### In Scope
- FastAPI backend for live and mock telemetry endpoints.
- SQLite persistence with asynchronous access patterns.
- CSV training log output for future model development.
- React frontend with polling, operations tables, and 2D schematic visualizer.
- Triangular branch/merge EARC mock topology including robots, conveyors, inventory, QA, and output spots.

### Out of Scope (Current Phase)
- Multi-node distributed database replication.
- Final cybersecurity hardening package (encryption/key rotation/attestation at rest).
- Full ISA-95 Level 4 ERP integration.
- Formal DO-178C certification package artifacts.

## 3. Current Implementation Baseline
### Backend
- FastAPI service with CORS enabled for local UI development.
- UDP listener on port 5005 using explicit network big-endian unpacking (`!9f`) for IMU payloads.
- Async queue handoff from datagram callback to writer worker.
- Async CSV writing and async SQLite writes via SQLAlchemy + aiosqlite.
- Live endpoint: `/dashboard_data`.
- Mock endpoint: `/mock/dashboard_data` backed by simulated state engine.

### Frontend
- React + Vite + Tailwind dashboard.
- Polling telemetry hook with mode toggle:
  - Live Mode: `/dashboard_data`
  - Mock Testbed Mode: `/mock/dashboard_data`
- Operational tables for Work Orders and Machine Status.
- Schematic visualizer rendering graph nodes and conveyor edges with state highlighting.

### Todo Closure Snapshot
- Completed: Defined assumed EARC topology for triangular branch/merge flow.
- Completed: Updated mock telemetry flow model with dynamic part-family routing and rework injection.
- Completed: Aligned frontend schematic rendering to backend coordinates and connector states.
- Completed: Authored comprehensive testbed design document (`docs/design/testbed.md`).
- Completed: Ran validation checks on updated backend/frontend files.

### Documentation
- README with startup commands and mode descriptions.
- docs/design/testbed.md with assumptions, flow model, and technical rationale.
- testbedlayout.md with user-authored graph variant.

## 4. Architecture Plan
### 4.1 Runtime Components
- Telemetry Ingest Layer
  - `asyncio.DatagramProtocol` receives UDP payloads.
  - Bounded queue protects event loop from downstream I/O delays.
- Persistence Layer
  - Async worker performs CSV and DB writes.
  - SQLAlchemy models manage normalized entities.
- API Layer
  - FastAPI serves live and mock dashboard contracts.
- Simulation Layer
  - MockTelemetryEngine runs periodic tick updates.
  - Simulates routes, inventory depletion, machine states, blocking, and rework.
- UI Layer
  - Polling hook abstracts data source mode.
  - Schematic and tables present operational state.

### 4.2 Data Contract Principles
- Keep dashboard payload stable across modes to simplify UI logic.
- Add optional `schematic` section for richer graph rendering.
- Preserve explicit state enums for deterministic style mapping:
  - Idle
  - Busy
  - Blocked
  - Offline

### 4.3 Determinism and Latency
- Enforce bounded queues and O(1) enqueue path in UDP callback.
- Avoid blocking I/O in request handlers.
- Track endpoint latency in response payload for self-observability.
- Maintain target: max 500 ms response path under expected load.

## 5. Testbed Design Critique and Improvement Plan
### 5.1 Assessment of Current testbedlayout.md
The graph is valid and operationally expressive, but it is visually dense because robot and conveyor nodes are both first-class vertices at high count. This introduces crossing edges that hide branch hierarchy.

### 5.2 Key Issues Identified
1. Semantic overload
- Conveyors as explicit nodes and edges simultaneously make path reading harder.

2. Duplicate and non-canonical links
- `c5 <--> r6` appears twice.
- Inconsistent spacing (`c9<--> tra`, `r6<--> c9`) reduces readability.

3. Missing subgraph framing
- No separated lanes for Source, Fabrication, QA, and Output, so triangular intent is not obvious.

4. Ambiguous control points
- It is unclear which robot owns which transfer zones and whether each conveyor has capacity constraints.

5. No path classification
- Direct path vs multi-op path is not encoded (all edges look equal).

### 5.3 Recommended Graph Refactor Pattern
- Use subgraphs to define layers:
  - Source
  - Divergence
  - Fabrication Branches
  - Merge/Inspection
  - Output
- Keep conveyors as edge labels, not intermediate nodes, unless conveyor occupancy is a first-class simulation object.
- Explicitly mark rework edges with a distinct style/class.
- Add legend node cluster for status colors and edge semantics.

## 6. Work Breakdown Structure (WBS)
### Phase 1: Stabilize MVP (Completed/Active)
- [x] Live telemetry ingest and persistence.
- [x] Async dashboard endpoint.
- [x] Frontend polling and tables.
- [x] Mock testbed mode with dynamic transitions.
- [x] Triangular branch/merge schematic rendering.

### Phase 2: Model Fidelity Upgrade
- [ ] Add per-node capacities and queue limits.
- [ ] Add conveyor occupancy tokens and transfer contention model.
- [ ] Add robot reachability matrix and service-time distributions.
- [ ] Add dispatch policies (FIFO/SPT/EDD) as runtime switch.
- [ ] Add rework policy controls and traceability fields.

### Phase 3: Reliability and Safety Controls
- [ ] Structured event log stream for all state transitions.
- [ ] Watchdog for stale data and health degradation states.
- [ ] Input schema validation and defensive payload handling.
- [ ] Rate-limits and backpressure metrics exposure.

### Phase 4: Verification and Benchmarking
- [ ] Synthetic load generation for UDP + API concurrency.
- [ ] Latency envelope tests across scenarios.
- [ ] Deterministic seed replay tests for mock simulations.
- [ ] Baseline statistical reports for flow-time and queue behavior.

### Phase 5: Operationalization
- [ ] Deployment scripts for Raspberry Pi target.
- [ ] Config profiles (dev, shipboard demo, stress).
- [ ] Backup/restore workflow for SQLite and CSV archives.
- [ ] Operational runbook and fault-recovery playbooks.

## 7. Detailed Milestone Plan
### Milestone M1: Testbed Clarity and Controls (1 week)
Deliverables:
- Refined Mermaid layout with subgraphs and legend.
- Capacity fields on nodes and limits in mock engine.
- UI display of queue saturation and blocked causes.
Acceptance Criteria:
- Graph readable in under 10 seconds by new reviewer.
- Capacity overflow transitions tested and visible.

### Milestone M2: Dispatch and Rework Policy Layer (1-2 weeks)
Deliverables:
- Policy engine: FIFO/SPT/EDD.
- Rework gating logic with configurable probability and route constraints.
- Policy impact metrics panel (flow time, WIP, utilization).
Acceptance Criteria:
- Policy switch changes observed behavior and metrics in mock mode.

### Milestone M3: Reliability Envelope (1 week)
Deliverables:
- Health endpoints and watchdog metrics.
- Error classification and resilient fallback behavior.
- Latency benchmark scripts and report.
Acceptance Criteria:
- API remains within latency threshold under planned load profile.

### Milestone M4: Demonstration Readiness (1 week)
Deliverables:
- Scenario scripts for mission demos.
- Screenshot/video artifacts and concise architecture slide.
- Runbook with startup/shutdown and troubleshooting.
Acceptance Criteria:
- Demo can be executed end-to-end without code changes.

## 8. Technical Debt Register
1. CSV writer + DB writes currently serialized in one worker path; add batched DB writes for throughput headroom.
2. Node-level capacity model is now present in mock payload, but queue arbitration policy remains simplified.
3. Frontend graph does not yet show lane constraints or robot reachability polygons.
4. No authN/authZ or endpoint hardening in current MVP.
5. No formal migration strategy for schema evolution.

## 9. Verification and Test Strategy
### 9.1 Unit Tests
- Route generation correctness per part family.
- State transition functions for Blocked/Offline behaviors.
- Inventory depletion constraints never below zero.

### 9.2 Integration Tests
- UDP packet ingestion to DB persistence chain.
- `/dashboard_data` and `/mock/dashboard_data` response shape parity.
- Frontend mode toggle and polling resilience.

### 9.3 Performance Tests
- UDP burst handling under queue limits.
- API response time distribution under concurrent polling clients.
- Event loop lag measurement during combined ingest + mock simulation.

### 9.4 Statistical Validation (Mock)
- Replication runs with fixed seeds.
- Confidence intervals for flow time and WIP.
- Comparative policy testing with paired analysis.

## 10. Risk Register and Mitigations
1. Risk: Event-loop contention from mixed background tasks.
- Mitigation: isolate responsibilities, batch writes, track loop lag metrics.

2. Risk: Visual model diverges from physical reality.
- Mitigation: topology config file with explicit station/edge declarations and review checkpoints.

3. Risk: Queue blow-up under pathological route cycles.
- Mitigation: per-node queue caps, deadlock/livelock detectors, route timeout fail-safe.

4. Risk: Debuggability gap during demo failures.
- Mitigation: structured logs, scenario seeds, reproducible replay endpoint.

5. Risk: Latency regression from feature growth.
- Mitigation: performance budget per endpoint and CI guardrail tests.

## 11. Configuration Strategy
- Consolidate operational settings into explicit config groups:
  - runtime (ports, poll rates)
  - simulation (seed, failure probabilities, capacities)
  - latency/safety thresholds
- Keep environment-specific overrides isolated.

## 12. Governance and Change Control
- Version graph topology as data, not code.
- Require change notes for routing or capacity updates.
- Tag demo-ready baselines for reproducibility.

## 13. Deliverables Checklist
- [x] Working backend live ingest + dashboard endpoint.
- [x] Working mock endpoint and branch/merge simulation.
- [x] Frontend mode toggle and schematic visualizer.
- [x] docs/design/testbed.md assumptions and rationale.
- [x] testbedlayout.md custom topology draft.
- [x] plan.md consolidated program plan (this document).

## 14. Immediate Next Actions
1. Refactor testbedlayout graph into lane-based subgraphs with edge labels.
2. Add per-node capacity and queue-limit controls to mock engine.
3. Add conveyor occupancy tracking and robot transfer contention metrics.
4. Add regression tests for payload contract and simulation transitions.
5. Prepare a demo script for three representative part families.
