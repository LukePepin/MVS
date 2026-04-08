# Week 4: Final Validation, Wrap-Up Testing, and Project Closure
Date: 2026-04-08
Status: Planned (Final Week)

## Week 4 Objective

Complete final wrap-up testing and produce closure evidence for the hybrid 6-axis MVS system where real robot telemetry drives simulated node behavior.

## Final Goal Statement

The final demonstrated system is a hybrid testbed with one robot node backed by real telemetry, simulated MES node behavior preserved, and anomaly detection workflows validated against real-formatted data.

## Final Acceptance Test Matrix

### 1. Telemetry Reliability

- Continuous capture run with reconnect and COM9/COM14 failover enabled.
- Verify no schema corruption in output CSV files in `backend/data`.
- Verify timestamp continuity and acceptable gap profile.

### 2. Hybrid Node Correctness

- Verify real-backed robot node state transitions track physical run behavior.
- Verify non-backed nodes remain simulation-driven and consistent.
- Verify queue depth and routing visuals remain coherent under mixed-source input.

### 3. Anomaly Workflow Validation

- Inject/observe at least one collision event scenario.
- Verify collision event is captured as anomaly candidate in annotation workflow.
- Verify anomaly scoring/reporting pipeline can surface the event window.

### 4. Dashboard and API Consistency

- Validate frontend renders without schema errors in final hybrid mode.
- Validate endpoint payload includes required fields for all nodes.
- Validate no regression against core machine/inventory/work-order views.

### 5. Documentation and Evidence

- Update final README runbook to match demonstrated flow.
- Archive test outputs and logs for final review.
- Produce final summary with limitations and next-step recommendations.

## Closure Deliverables

- Final hybrid-mode test report.
- Final anomaly-evaluation summary.
- Final dataset inventory list in `backend/data`.
- Final known-limitations and risk register.
- Presentation-ready evidence packet.

## Week 4 Exit Criteria (Project Closure)

- All acceptance tests executed and results documented.
- Hybrid mode demonstrated end-to-end with real telemetry-backed node.
- Anomaly handling path validated with collision event candidate(s).
- README and weekly plan chain are fully consistent with delivered system.
