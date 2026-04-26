# Week 10 Best-Submission Notes (Luke)

## Goal
Score as close to 100 as possible by making your Week 10 design document:
1. Rubric-complete (all required sections, fields, formulas, mappings)
2. Course-aligned (every algorithm tied to course week)
3. Implementation-ready (specific enough for Week 11 database build)

---

## What You Must Explicitly Answer

## Section 1: System Overview (10 pts)
Answer these directly:
1. What does EARC produce, in what volume per shift, and under what operational constraints?
2. What are your minimum resource types, worker roles, and why are they each needed?
3. For each of the 11 MESA functions, what is its specific role in EARC (not generic MES language)?
4. What is the primary KPI for each function and why it matters in DIL/adversarial conditions?

Strong answer pattern:
- One sentence on business reality
- One sentence on decision/control logic
- One sentence on measurable KPI outcome

---

## Section 2: Schema + Algorithm per Function (45 pts total)
For each F1-F11, ensure you answer all four components:
1. Business role in your exact system context
2. Table specs (2-4 tables, each table >=5 fields, each FK points to a real table)
3. Mathematical algorithm details
4. Integration notes with named table-field exchanges

### Algorithm Completeness Checklist (apply to every function)
For each algorithm, confirm all six are present:
1. Objective function
2. Decision variables
3. At least one key constraint
4. Parameter values/constants
5. Course week citation
6. Read/write table mapping

If any one of the six is missing, assume points are lost.

---

## Critical Fixes from Instructor Feedback

### 1) F4 Document Control: add baseline version-control workflow
You already have crypto hash verification. Keep it.
Also add classic revision control structure (required by rubric intent):
1. document_id
2. revision_no
3. effective_from / effective_to
4. approval_status
5. change_authority
6. supersedes_revision_id

What to explicitly answer:
1. How does a revision become active?
2. Who can approve it?
3. How do you prevent old revisions from being dispatched?
4. How does hash verification layer on top of revision control?

### 2) F8 Trust Decay: tie it to course content
Your trust equation needs an explicit course anchor.
Use wording like: "This is an EWMA-style smoothing structure from Week 10 F8 adapted for trust-state estimation with fail-safe threshold."

What to explicitly answer:
1. Why smoothing is needed
2. What alpha means operationally
3. Why threshold = 0.30 is chosen
4. What action occurs at threshold breach (and latency target)

### 3) Week 12 roadmap must list 4-6 algorithms
You currently emphasize novel ones. Add the standard ones too:
1. MTBF-based PM trigger (F9)
2. Xbar-R (or Cpk) quality check (F7)

What to explicitly answer:
1. Which algorithm
2. Which function
3. Input tables
4. Output tables
5. Why this algorithm is needed in your demo

---

## Additions That Can Lift Your Grade

### A) Add two simple visuals before Week 11
Instructor explicitly asked this.
Include:
1. ERD grouped by MESA function with FK links
2. Data-flow diagram showing each algorithm's read/write path

What to explicitly answer under each figure:
1. Which tables are high-risk for FK mistakes
2. Which flows are latency-sensitive
3. Which outputs feed F11 dashboards

### B) Define dashboard views now (supports F11 schema quality)
Specify 3 views:
1. Constraint operator live view
2. Supervisor line-level view
3. End-of-shift report view

For each view, answer:
1. What 3-6 metrics are shown
2. Update frequency
3. Source tables
4. Alert thresholds

### C) Turn "formula use" into "optimization intent"
For each major function, add one sentence:
"What is being optimized and what tradeoff is managed?"
Examples:
1. F10: minimize quarantine scope while preserving trace confidence
2. F8: balance false alarms vs missed anomalies vs downtime cost
3. F2/F3: minimize lateness and flow time under dynamic capacity loss

---

## Rubric Attack Plan (Section-by-Section)

1. System overview: make every function statement EARC-specific.
2. Schema: verify all PK/FK references are valid and consistent naming is used.
3. Algorithms: run the 6-item completeness checklist for all 11 functions.
4. Integration: each function must name at least 2 cross-function exchanges with table+field names.
5. Timeline: include >=10 events and ensure all three mandatory events appear:
   - quality alarm cascade
   - maintenance/failure event
   - traceability trigger
6. Roadmap: Week 11 table build + seed sizes, Week 12 algorithm list (4-6), Week 13 demo script.
7. Cross-reference table: no algorithm without function + week + HW mapping.
8. Complexity: keep >=3 resources, >=4 roles, meaningful lot/batch traceability.

---

## High-Scoring Self-Check (Final Pass)
Before submission, answer yes/no:
1. Does every function have business role, tables, math, and integration notes?
2. Does every algorithm include objective, variables, constraints, constants, citation, read/write tables?
3. Did I add revision-control workflow beneath crypto verification in F4?
4. Did I explicitly connect Trust Decay to course EWMA/F8 framing?
5. Did I list 4-6 Week 12 algorithms including at least one standard quality and one maintenance algorithm?
6. Did I include both required visuals (ERD + data flow)?
7. Are dashboard outputs defined in enough detail to drive schema design?
8. Can Week 11 database be built directly from this document with no guesswork?

If any answer is no, fix before submission.

---

## Suggested "Best Submission" Positioning (short paragraph)
Use this style in your intro/conclusion:
"This design intentionally combines course-standard MES controls (scheduling, SPC, MTBF PM, OEE) with EARC-specific cyber-physical resilience layers (trust-decay anomaly handling, cryptographic document integrity, and constrained DIL operations). The document is structured as an implementation blueprint: every function defines tables, equations, integration points, and measurable KPIs so Week 11-13 execution can proceed without schema ambiguity."

---

## Optional Next Upgrade
If you want, I can generate a second file that is a strict fill-in template for all 11 functions with placeholders so you can complete/revise faster and avoid missing rubric items.