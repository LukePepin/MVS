# Week 5 Feed - What Needs To Be Done

## Week Goal
Close out Week 5 with a verification-first MES increment that is showcase-ready.

## Scope Confirmed
- Build a start control that supports both mock mode and real backend mode.
- Prioritize three expansions this week:
1. Operator Dashboard
2. Performance Panel
3. Raspberry Pi extension *(DEFERRED TO BACKLOG)*
- Physical Pi A (Supervisor) and Pi B (MITM) hardware endpoints exist but testing is postponed to focus on core MES logic.
- Adversarial tests in scope:
1. Packet loss / jamming simulation
2. Livelock / deadlock stress tests
3. Replay attack simulation
- Smart power grid integration is not in scope for Week 5.

## Deliverables
1. Working Start Button
- Single clear control to begin execution.
- Supports mock scenario runs and real backend runs.
- Exposes run state (idle, running, halted, failed).

2. Operator Dashboard (Primary)
- Constraint-focused live panel for active cell state.
- Shows current work center/node state and anomaly status.
- Usable as the main showcase view.

3. Performance Panel (Primary)
- Displays key MES KPIs for review and closure.
- Include OEE-oriented metrics and shift-level summary outputs.
- Tie displayed values to recorded backend artifacts.

4. Raspberry Pi Extension *(DEFERRED TO BACKLOG)*
- Physical endpoints setup and architecture mapped, but full integration is postponed.
- Adversarial tests utilizing these network nodes will move to the next-week backlog.

5. Verification Evidence Pack
- Passing test logs.
- Dashboard screenshots (normal and adversarial states).
- CSV/JSON telemetry artifacts for runs.
- Updated architecture/flow figures.
- Demo script and runbook.

## Execution Checklist
1. Start Path
- Implement and validate mock start sequence.
- Implement and validate real backend start sequence.
- Confirm status transitions and safe stop behavior.

2. Dashboard + Performance
- Finalize operator dashboard layout for showcase readability.
- Wire performance panel metrics from backend outputs.
- Validate that panels remain stable during adversarial scenarios.

3. Raspberry Pi Testbed
- *(DEFERRED)* Move network physical startup and baseline communication testing to the next iteration.

4. Adversarial Campaign
- *(DEFERRED)* Run formal adversarial experiments (packet loss, jamming, livelock) alongside Pi integration in subsequent weeks.
- Note: Mock versions inside simulation are permitted, but hardware-level MITM is deferred.

5. Documentation + Closure
- Capture required screenshots and artifact outputs.
- Update architecture and data/flow visuals.
- Finalize demo script and runbook for presentation.

## Definition Of Done (Week 5)
MES dashboard displays the testbed model effectively for showcase, adversarial tests are logged, and MVS Week 5 is closed out with verification tests plus complete supporting documentation.

## Assignment Closure Notes
- Focus on completion quality, not added scope.
- Keep verification traceable from scenario run to artifact.
- Any deferred feature moves to next-week backlog with explicit reason. (e.g., Raspberry Pi MITM nodes and adversarial campaigns are deferred to prioritize the core MES database backend and MESA-11 implementations matching cMES.)
