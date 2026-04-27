ISE 573: Manufacturing Execution Systems

**Final Project Rubric**

A Working MES — Software · Video Presentation · Report

Dr. Manbir Sodhi  ·  University of Rhode Island  ·  Spring 2026

| 1 — Software 40 pts | 2 — Video 25 pts | 3 — Report 20 pts | 4 — Optimization 10 pts | 5 — Scale-up 3 pts | 6 — Installation 2 pts |
| :---- | :---- | :---- | :---- | :---- | :---- |

# **Deliverables**

Submit all six together before the deadline.

| Item | What to submit |
| :---- | :---- |
| **1 — Software** | Zipped folder: .db file with seed data loaded, all .py scripts, requirements.txt, README with run instructions. Entry point: python mes.py. |
| **2 — Video** | Screen-recorded demo, 8–15 min, .mp4 or unlisted link. Must show live database state — not slides or screenshots. |
| **3 — Report** | Technical report 10–18 pages, PDF or Word. File name: LastName\_MES\_Final\_Report.pdf |
| **4 — Optimization** | Implemented and demonstrated in the video (see Section 4). |
| **5 — Scale-up** | One-page section in the report (see Section 5). |
| **6 — Installation** | README section or appendix (see Section 6). |

# **Section 1 — Working MES Software  (40 points)**

| Criterion | Full credit — what earns every point | Minimum / not acceptable |
| :---- | :---- | :---- |
| **Database — schema & seed data** 12 points | All Week 10 tables with correct PK/FK constraints Entity tables ≥20 rows; event/reading tables ≥50 rows PRAGMA foreign\_keys \= ON; no violations Seed data supports a complete end-to-end demo scenario | Fewer than half the design tables present Obviously synthetic data (sequential integers) No FK enforcement |
| **Algorithms — implementation (4–6 required)** 16 points | ≥4 algorithms in named functions, each reading/writing DB tables Scheduler (F2) runs against the live Schedule table SPC (F7) computes UCL/LCL from actual seed data OEE (F11) reads live FailureLog and InspResults All functions have docstrings citing source week and tables | Algorithms not connected to the database Fewer than 2 algorithms present |
| **Runnability & code quality** 7 points | Runs cleanly on fresh install via single entry point requirements.txt and step-by-step README included Functions clearly named; no dead commented-out code At least one assertion confirming output is plausible | Does not run without significant debugging No README; monolithic script with no functions |
| **Cross-function integration** 5 points | ≥1 chain: event in F-x writes a row that F-y reads and acts on Integration is database-driven, not direct function calls | All algorithms operate on isolated, unconnected data |
| **Section total  40 pts** |  |  |

# **Section 2 — Video Presentation  (25 points)**

| Criterion | Full credit — what earns every point | Minimum / not acceptable |
| :---- | :---- | :---- |
| **Demo scenario — live system response** 12 points | Both required events from live DB state: quality alarm and maintenance failure System visibly responds — a row is written, a flag is set, a schedule updates Before/after query result shown for at least one event | Only one event shown, or both are staged/mock Demo shows static or pre-computed data |
| **Clarity and pacing** 7 points | Narration explains each step before executing Terminal/query output readable on screen 8–15 minutes; no dead air or rushing | Narration absent or inaudible Viewer cannot follow what is happening |
| **End-of-shift output** 6 points | OEE shown as A × P × Q; FPY by station; one system-specific KPI At least one visual output (chart, formatted table, or report) Numbers reflect the demo events — failure appears in FPY | No end-of-shift output shown |
| **Section total  25 pts** |  |  |

# **Section 3 — Technical Report  (20 points)**

| Criterion | Full credit — what earns every point | Minimum / not acceptable |
| :---- | :---- | :---- |
| **System description & architecture** 5 points | One-page overview: what is produced, resources, worker roles ERD or schema diagram with tables grouped by MESA function Comparison to Week 10 design: what changed and why | Description is generic — could apply to any system No architecture documentation |
| **Algorithm documentation** 8 points | One section per algorithm: objective, variables, parameters, source week Each section includes a sample result from the actual database Explains what the algorithm does in the demo scenario | Algorithms in prose only — no mathematical notation Documentation does not match what was built |
| **Results & analysis** 5 points | Key KPIs reported: OEE, FPY, RTY, or system equivalent At least one result compared to a Week 10 expectation Each demo event has a documented outcome | No quantitative results reported |
| **AI-use reflection** 2 points | Distinguishes AI-generated from student-reviewed from student-decided Names a specific AI error caught and how it was fixed | No reflection, or fewer than one paragraph |
| **Section total  20 pts** |  |  |

# **Section 4 — Optimization & Insight  (10 points)**

| Criterion | Full credit — what earns every point | Minimum / not acceptable |
| :---- | :---- | :---- |
| **Going beyond the specification** 10 points | ≥1 feature not in the Week 10 rubric but genuinely useful operationally Examples: Weibull PM, Bayesian supplier quality, bottleneck-aware dispatch, EVM, Crawford learning curve Feature is implemented and demonstrated in the video Brief justification explains why it matters for this system | Nothing beyond the base rubric requirements Feature added but not connected to the running system |
| **Section total  10 pts** |  |  |

# **Section 5 — Scaling Up  (3 points)**

| Criterion | Full credit — what earns every point | Minimum / not acceptable |
| :---- | :---- | :---- |
| **Scale-up analysis** 3 points | Identifies 2–3 bottlenecks that would emerge at 10× data volume Names specific tables and queries most likely to slow first Proposes one concrete remedy per bottleneck (index, partitioning, caching, batch job) | Only generic statements ('a real database would be needed') No specific tables or queries named |
| **Section total  3 pts** |  |  |

# **Section 6 — Installation & Deployment  (2 points)**

| Criterion | Full credit — what earns every point | Minimum / not acceptable |
| :---- | :---- | :---- |
| **Installation documentation** 2 points | OS requirements, Python version, and dependency install commands Steps to initialise the database and load seed data from scratch One-paragraph note on what production deployment would require (e.g. PostgreSQL, authentication, scheduled ETL) | No instructions beyond requirements.txt Instructions assume database is already loaded |
| **Section total  2 pts** |  |  |

# **Grade bands**

| Band | Score | What this level looks like |
| :---- | :---- | :---- |
| **A  93–100** | **93–100** | System runs cleanly. Both demo events fire from live DB state. ≥4 algorithms read/write correct tables. OEE and ≥1 additional KPI shown live. Each algorithm documented with formula and sample result. Genuine above-rubric capability implemented and demonstrated. Scale-up and installation sections complete. |
| **A− 90–92** | **90–92** | All of the above with one minor gap — one event slightly staged, one algorithm partially hardcoded, or above-rubric addition described but not fully demonstrated. |
| **B+ 87–89** | **87–89** | System runs. Both events shown. ≥4 algorithms connected to the database. Report with algorithm documentation. No above-rubric addition, or addition not demonstrated. Scale-up section thin. |
| **B  83–86** | **83–86** | System runs with minor fixes. Core algorithms present but one or two read hardcoded values. One event simulated rather than live. Report covers the system but results section is thin. |
| **B− 80–82** | **80–82** | System runs but 2–3 algorithms are stubs or disconnected from DB. Video shows some functionality. Report present but no quantitative results. |
| **C  70–79** | **70–79** | Partial system. Fewer than 4 algorithms or no cross-function integration. Video shows static data. Report describes the design rather than the built system. |
| **\< 70** | **\< 70** | System does not run, fewer than 2 algorithms, or video absent. |

# **Submission checklist**

Confirm all items before uploading:

**Software**

* Zipped folder runs via python mes.py on a clean machine

* requirements.txt and README included

* Database file with seed data already loaded

* All algorithms in named functions with docstrings

**Video**

* Quality alarm demonstrated from live database state

* Maintenance failure and resource reallocation shown

* End-of-shift OEE and at least one other KPI shown

* 8–15 minutes; output readable on screen

**Report**

* ERD or schema diagram included

* One section per algorithm with formula, parameters, and sample result

* Quantitative results with OEE, FPY, and demo event outcomes

* AI-use reflection with specific examples

* Scale-up bottleneck analysis present

* Installation instructions present

* File named LastName\_MES\_Final\_Report.pdf

*Questions? sodhi@uri.edu  ·  Fascitelli 284  ·  Office hours: see syllabus*