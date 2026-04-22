Week 10 Homework: MES Design Prototype Document
📄 DESIGN DOCUMENT DUE
Major Milestone! This week you produce the complete specification that drives the rest of the term. Your MES Design Prototype Document covers all 11 MESA functions for a system of your choice — with table specifications, mathematical algorithms, an integration timeline, and a three-week implementation roadmap. No coding. No SQL. Pure design.

Objective
Create a complete MES Design Prototype Document for a manufacturing or production system of your choice. This document is not code — it is a detailed design specification of the kind a systems engineer writes before any database is created or any algorithm is coded. It will serve as the blueprint for your Week 11 database, Week 12 algorithm implementations, and Week 13 demo.

A complete worked example — the Lerici's Pizza MES Design Prototype — is posted on Brightspace. Read it carefully before starting. Your document should match its structure, level of detail, and specificity.

Connection to the Course
This assignment draws on every algorithm and framework introduced since Week 1. The scheduling rules (Weeks 3–4), LP and MILP formulations (Week 6), OEE and maintenance metrics (Week 9), and the four new functions covered this week — F6 Labour Management, F7 Quality Management, F8 Process Management, F10 Product Tracking — all appear in your design document as mathematically specified algorithms tied to specific database tables. The more precisely you specify them now, the faster and better the LLM will generate your Week 11 database.

What This Assignment Is NOT
This week is pure design. The following are explicitly out of scope:

No SQL. Do not write CREATE TABLE statements. Write table specifications in English: field name, data type, PK/FK role, and description. The SQL comes in Week 11.
No Python. Do not implement algorithms. Write out the mathematics — objective function, decision variables, constraints, parameter values. The code comes in Week 12.
No SQLite database file. You are producing a Word or PDF document, not a .db file.
No demo. The demo is Week 13. This week is pure design.
Think of this as an architectural blueprint. An architect does not pour concrete — they draw plans precise enough that a builder can pour concrete from the drawing alone. Your document must be precise enough that your Week 11 database can be built directly from it.

Choose Your System
Select any manufacturing or production system you find interesting. It must have physical resources, workers with different skills, a repeatable process, and trackable products or batches.

Craft brewery — batches, recipes, fermentation control, lot traceability
Hospital pharmacy — medication batches, staff certifications, quality checks, dispensing tracking
Electronics assembly — PCB build, component lot tracing, soldering temperature control, AOI inspection
Textile mill — yarn lots, loom scheduling, quality (defects per metre), dyeing process control
Automotive body shop — job scheduling, paint process control, quality inspection, parts traceability
University research lab — experiment scheduling, reagent lot tracking, instrument maintenance
Other — propose to instructor; must have sufficient complexity
Minimum complexity requirements: ≥3 resource types, ≥4 worker roles, and batch/lot identity that makes F10 traceability meaningful. A system without these is too simple for all 11 MESA functions to matter.

Assignment Requirements
Section 1: System Overview (10 points)
Write a one-page overview of your chosen system covering:

Business context: What does the system produce? How many resources, worker roles, and jobs per shift?
Why all 11 MESA functions are needed: 1–2 sentences per function explaining its specific role in your system. Do not copy generic MESA definitions — tie each function to your operational context.
MESA-11 Summary Table: One row per function with columns: Function, Role in your system, Key tables, Key algorithm, Primary KPI. Model this exactly on the Lerici example.
Section 2: Database Schema — All 11 Functions (25 points)
This is the main body of your document. Write one sub-section per MESA function, each containing:

Component A — Business Role (2–3 sentences): What does this function do in your specific system?
Component B — Table Specifications (2–4 tables per function): For each table, provide a specification table with four columns: Field, Type, Role (PK/FK), and Description. Every field must have a data type. Every foreign key must name the target table. Minimum 5 fields per table.
Component C — Key Algorithm or Formula: Write out the mathematics — objective function, decision variables, key constraints, and parameter values. Cite the course week where this algorithm was taught. See the checklist below.
Component D — Integration Notes (2–3 sentences): Name the other MESA functions this function exchanges data with, and specify the exact tables and fields involved.
Function	Minimum Tables	Required Algorithm
F1 — Resource Allocation	Resources, ResourceAssignment, ResourceStatus	LP or assignment heuristic
F2 — Operations Scheduling	Orders/Jobs, Schedule, Products	SPT, EDD, or MILP
F3 — Dispatching	DispatchQueue, DispatchLog	Priority dispatch rule with weights
F4 — Document Control	Documents/Recipes, Revisions, Acknowledgments	Version control + approval workflow
F5 — Data Collection	Sensors, SensorReadings, Events	Threshold alarm logic
F6 — Labour Management	Workers, SkillMatrix, Shifts, TimeEvents	IP rostering + labour efficiency KPI
F7 — Quality Management	QualitySpecs, InspResults, NCRecords	X̅-R chart, Cpk, NCR→CAPA
F8 — Process Management	RecipeParams, ProcessEvents, Deviations	PID and/or CUSUM + alarm rationalisation
F9 — Maintenance	Equipment, MaintenanceLog, FailureLog	MTBF-based PM scheduling
F10 — Product Tracking	Lots/Batches, Genealogy, LotEvents	Forward & backward genealogy trace (described mathematically, not coded)
F11 — Performance Analysis	KPILog, OEELog, ShiftReports	OEE = A × P × Q; FPY; RTY
Algorithm specification checklist — every algorithm in your document must include:

✓ Objective function written out (what is being minimised or maximised?)
✓ Decision variables named (what does the solver change?)
✓ Key constraint stated (capacity, certification, coverage, spec limit)
✓ Parameter values given (e.g., k=0.5σ for CUSUM, A2=0.577 for n=5)
✓ Source week cited (e.g., "Week 10 F7 lecture — X̅-R chart")
✓ Which tables the algorithm reads from and writes to
Section 3: Integration Timeline (10 points)
Write a table showing at least 10 events from a single production day (or shift) in your system. Columns: Time, Event, Functions Triggered. Events must chain across functions — the output of one function is the input of the next. See Section 3 of the Lerici document ("A Day at Lerici's") for the exact format.

Your timeline must include at least:

one quality alarm that propagates across multiple functions
one maintenance event or resource failure
one traceability event (a suspect lot triggering a forward trace)
Section 4: Implementation Roadmap (10 points)
Even though you are not coding this week, you must plan ahead. Write three short paragraphs:

Week 11 — Database: Which tables you will create, how many seed rows per table (minimum 20 for major tables, 50+ for event/reading tables), and the 4 cross-function queries you will write and test.
Week 12 — Algorithms: Name 4–6 algorithms you will implement, specifying which MESA function each serves and which tables it reads from and writes to.
Week 13 — Demo: Your demo scenario in 3–4 sentences — how many jobs, what will go wrong, and what end-of-shift outputs you will show.
Section 5: Algorithm Cross-Reference Table (5 points)
Include a table mapping every algorithm in your document to: MESA function, course week where it was taught, and the homework problem where it was first practised. See Section 6 of the Lerici document for the exact format. This table becomes your implementation checklist for Weeks 12–13.

Using AI in This Assignment
You are encouraged to use AI language models (Claude, ChatGPT, Gemini, Copilot) to help draft your design. This is consistent with how modern engineers work.

AI is good at — use it freely for:	You must do yourself — AI cannot substitute for:
Suggesting column names, data types, and FK relationships you may have missed
Drafting table specifications from a verbal description of your system
Reviewing your schema for normalisation issues
Generating the MESA-11 summary table once you describe your system
Explaining mathematical formulas and SPC chart constants
Choosing which system to design and explaining why all 11 functions matter for it
Defining business logic: what does a quality failure mean in your context?
Writing the mathematical formulations before asking AI to refine them
Creating the integration timeline — only you know the operational story
Critically reviewing AI output for hallucinated column names, incorrect formulas, or generic definitions that don't match your system
Key principle: your design document is the prompt you will give the LLM in Week 11. If you let the LLM write a vague design now, you will get vague code later. The precision is the point.

Deliverables
MES Design Prototype Document — PDF (preferred) or Word, 15–25 pages
Must follow the six-section structure above in order
File name: LastName_MES_Design_Prototype.pdf
Upload to Brightspace under Assignment 10
This document becomes your specification for Weeks 11–13. You will hand it directly to an LLM to generate your database. Every vague sentence now is a debugging session later. Be precise.

Grading Rubric
Criterion	Points	What the Grader Checks
System Overview & Business Context	10	What the system produces, resource types, worker roles, jobs/shift. Why all 11 functions are needed (1–2 sentences each). MESA-11 summary table complete.
Database Schema — all 11 functions	25	2–4 tables per function. Each table: field name, data type, PK/FK annotation, description. Every FK references a real table. Schema is implementable directly in SQLite.
Algorithm / Formula per function	20	Objective function, decision variables, constraints, and parameter values written out mathematically — not just described in words. Course week cited for each algorithm.
Cross-function integration per section	10	Each function section states how it connects to at least 2 other functions, naming specific tables and fields exchanged.
Integration Timeline (≥10 events)	10	Production-day walkthrough showing which functions each event triggers. Events chain correctly. Includes quality alarm, maintenance event, and traceability event.
Implementation Roadmap (Wk 11–13)	10	Week 11: tables, seed rows, 4 queries. Week 12: 4–6 algorithms. Week 13: demo scenario. Specific enough to execute without further clarification.
Algorithm Cross-Reference Table	10	Every algorithm mapped to MESA function, course week, and HW problem. No algorithm appears in the design without a course source.
System Complexity	5	≥3 resource types, ≥4 worker roles, batch/lot traceability present. Not a trivially simple system.
Total	100	
Download Assignment
Assignment document

Example Report
Example MES Design Document
Due Date
Submit by: Before the Week 11 class session, 11:59 PM Eastern

Questions? sodhi@uri.edu  ·  Fascitelli 284·  Office hours: see syllabus