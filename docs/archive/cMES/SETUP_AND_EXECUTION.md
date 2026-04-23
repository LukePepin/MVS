# HOW TO — Pharma MES Prototype
**ISE 573 Week 7 | Connor Sheridan | University of Rhode Island**

A plain-English guide to what this project is, what everything means, and how the pieces fit together.

---

## What is this project?

This is a **Manufacturing Execution System (MES) prototype** for a pharmaceutical facility that produces sterile injectable drugs. It simulates how batches of medicine move through a factory — from raw materials all the way to finished, approved product.

The system was built for an ISE 573 (Manufacturing Systems) assignment and demonstrates five things:

1. **Queueing Theory** — mathematical analysis of how lines form at each station
2. **Simulation** — a virtual factory you can run and watch
3. **Statistics** — running the simulation many times to get reliable numbers
4. **What-If Analysis** — testing changes (like adding a machine) before doing it for real
5. **MES Integration** — connecting the simulation to a real database with scheduling and planning

---

## The Two Types of Simulation

This is the most important thing to understand:

### 📊 The Statistical Simulation (runs once before you open the browser)
- Run by `des_simulation.py` (or via ⚙ Run Analysis in the dashboard)
- Runs **15 complete replications** of the factory, each lasting 15,000 simulated minutes (~10 days)
- Used for **science** — getting statistically reliable numbers, confidence intervals, comparing scenarios
- Produces the 6 PNG charts in the `outputs/` folder
- Takes ~3 minutes to run

### 🟢 The Live Dashboard Simulation (runs while the browser is open)
- Runs continuously inside the dashboard
- You can watch **individual batches** (colored dots) move through the factory in real time
- Used for **visualization** — seeing how the factory behaves, testing dispatch rules live
- This is NOT used for the statistical analysis — it's a teaching/demo tool

**Think of it this way:** The statistical simulation is like running a lab experiment 15 times and averaging the results. The live simulation is like a fishbowl you can watch.

---

## The Factory Process (Step by Step)

Every batch of injectable drug goes through exactly these stations, in this order:

| Step | Station | What happens | Approx. time |
|------|---------|-------------|-------------|
| ① | **Raw Material Staging** | Incoming materials are logged and held | 30 min |
| ② | **Quarantine Hold** | Materials are tested and held pending results | 120 min (fixed) |
| ③ | **Dispensing & Weighing** | APIs and excipients are weighed out precisely | 45 min |
| ④ | **Compounding / Solution Prep** | Drug is dissolved and mixed with water (WFI) | 90 min |
| ⑤ | **Sterile Filtration** | Solution is passed through a 0.22µm filter | 60 min |
| ⑥ | **Aseptic Filling** ⚡ | Solution is filled into vials in a cleanroom | 120 min ← **BOTTLENECK** |
| ⑦ | **Inspection & Packaging** | Each vial is visually inspected; cartons assembled | 45 min |
| ⑧ | **QA Release Hold** | Quality team reviews the batch record | 180 min (fixed) |
| ⑨ | **Released ✓** | Batch approved for shipment | — |

The **bottleneck** is Aseptic Filling — it takes the longest and is the most constrained. Most of the mathematical analysis focuses on this station.

---

## The Dashboard — Tab by Tab

### Factory Floor Tab
The main view. Shows a diagram of the factory with **colored dots** representing individual batches moving through the stations.

- **Blue dot** = Injectable-A (100mg/mL)
- **Green dot** = Injectable-B (50mg/mL)
- **Orange dot** = Injectable-C (25mg/mL)

Station border colors:
- **Green border** = idle (waiting for a batch)
- **Orange border** = busy (processing a batch)
- **Red border** = breakdown or alarm

Below the factory floor you'll see two panels with **live graphs** showing how the WFI water system and cleanroom environment (HVAC) are behaving over time.

### Analytics Tab
Contains four charts:
- **WIP Over Time** — how many batches are inside the factory at any moment. If this keeps rising, the factory is overloaded.
- **Queue at Filling** — how many batches are waiting for the filling machine. This is the key congestion point.
- **Station Utilization** — how busy each station is on average. These are analytical values from queueing math (not the live sim). Filling is at 50% utilization theoretically.
- **Cumulative Throughput** — total batches released over time (from the live sim).

### MRP / WO Tab
Shows data from the **database** (Sheridan_573):
- **Work Orders** — production jobs created for the factory (which product, how many, when needed)
- **MRP Planned Orders** — materials to order and when, based on the Work Orders and Bill of Materials
- **EDD Schedule** — the planned sequence for the filling machine, sorted by earliest deadline

### Events Tab
A live log of everything happening in the simulation — batch arrivals, station starts, machine breakdowns, and releases.

---

## The Controls Bar

| Control | What it does |
|---------|-------------|
| **▶ Start** | Begins the factory floor simulation. The dots start moving. |
| **⏸ Pause / ▶ Resume** | Freezes or unfreeze the simulation |
| **↺ Reset** | Clears everything and returns to a fresh state (does NOT auto-start) |
| **⚡ Finish Instantly** | Runs the simulation at maximum speed until 30 batches are released, then auto-pauses |
| **Speed slider** | Controls how fast simulated time passes. 30× means 30 simulated minutes per real second. |
| **Dispatch Rule** | How the factory decides which batch to process next when a machine becomes free |
| **Filling Lines** | How many filling machines are running in parallel |
| **⚙ Run Analysis** | Opens a panel to re-run the database setup, queueing calculations, simulation, or MRP scheduling |

---

## The Three Dispatch Rules

When multiple batches are waiting for a machine, the system needs a rule to pick which one goes next:

| Rule | Full Name | How it works | Best for |
|------|-----------|-------------|---------|
| **FIFO** | First In, First Out | Oldest batch waiting goes first | Fairness, simplicity |
| **SPT** | Shortest Processing Time | Fastest-to-process batch goes first | Minimising average wait time |
| **EDD** | Earliest Due Date | Most urgent (closest deadline) batch first | Avoiding late orders |

Our statistical analysis showed **SPT** gives a statistically significant ~7 minute reduction in average flow time compared to FIFO (p = 0.04).

---

## Key Metrics Explained

| Metric | What it means | Good value |
|--------|--------------|-----------|
| **WIP Batches** | Batches currently inside the factory | Stable (not growing) |
| **Released** | Batches fully completed and approved | Should grow steadily |
| **Avg Flow Time** | Time from raw material entry to release | ~6.5 hours target |
| **Filling Util %** | How busy the filling machine is | ~50% theoretical |
| **Throughput/h** | Batches completed per hour | ~0.25 batches/h |
| **Breakdowns** | Times the filling machine broke down | Lower is better |

---

## The WFI System (Water for Injection)

WFI is ultra-pure water used to make the drug solution. It must meet strict pharmaceutical standards:

| Parameter | Limit | Why it matters |
|-----------|-------|---------------|
| **Conductivity** | < 1.3 µS/cm | Measures dissolved ions — too high means contamination |
| **TOC** | < 500 ppb | Measures organic contamination |
| **Temperature** | 70–85°C | Hot water loop prevents microbial growth |

If WFI goes out of spec, affected batches may need to be held for investigation.

---

## The HVAC Cleanroom System

Sterile injectables are filled in ISO Class 5 cleanrooms (the most stringent standard). The HVAC system controls:

| Parameter | Required Range | Why |
|-----------|---------------|-----|
| **Temperature** | 20–24°C | Prevents product degradation; operator comfort |
| **Humidity** | 35–55% | Prevents static buildup; protects hygroscopic drugs |
| **Particle Count** | ≤ 3,520 /m³ (ISO Class 5) | Sterile environment — particles can carry bacteria |

---

## The Queueing Theory (Part 1)

Before running the simulation, we calculated expected waiting times mathematically. This is useful because it gives exact theoretical answers without running the sim.

| Model | What it assumes | Key insight |
|-------|----------------|-------------|
| **M/M/1** | Random arrivals, one machine | Filling queue wait = 120 min |
| **M/M/2** | Random arrivals, two machines | Filling queue wait = 8 min (−93%!) |
| **M/G/1** | Random arrivals, realistic variability (CV=0.2) | Filling queue wait = 62 min |

**Key finding:** Adding a second filling machine is the single most impactful improvement possible. The M/M/2 analysis shows it reduces waiting time by 93%.

---

## The MRP System (Material Requirements Planning)

MRP answers the question: *"Given these work orders, what raw materials do I need to order and when?"*

It works backwards from the due date:
1. Start with Work Orders (what to make, when)
2. Explode the **Bill of Materials** (what components does each product need?)
3. Check what's already **on hand** in the warehouse
4. Calculate the **net requirement** (what's missing)
5. Apply **lead times** (how far in advance must you order?)
6. Create **planned orders**

A "past-due" planned order means you should have ordered already — it's a warning.

---

## File Overview

| File | What it does |
|------|-------------|
| `RUN_PROJECT.py` | **Start here.** Single-file launcher — installs packages, sets up DB, runs analysis, opens browser |
| `db_setup.py` | Creates the PostgreSQL database tables and fills them with test data |
| `queueing_analysis.py` | Calculates queueing theory metrics (M/M/1, M/M/c, M/G/1) |
| `des_simulation.py` | Runs the SimPy statistical simulation (15 reps, 5 scenarios) |
| `mrp_scheduler.py` | Runs MRP, scheduling algorithms, and production plan optimizer |
| `dashboard.py` | Runs the web server and live factory simulation |
| `templates/dashboard.html` | The browser interface |
| `outputs/` | 6 PNG charts generated by the statistical simulation |

---

## Frequently Asked Questions

**Q: Why doesn't the simulation start automatically?**
A: By design — so you can review the current factory state and settings before committing. Press ▶ Start when ready.

**Q: Why do the analytics charts look flat when I first open the dashboard?**
A: The live simulation needs to run for a while to collect data. The statistical analysis charts (Utilization) are pre-computed and show immediately.

**Q: What's the difference between "Quarantine Hold" (station ②) and "QA Release Hold" (station ⑧)?**
A: Station ② is an *incoming materials quarantine* — raw materials are held until tested. Station ⑧ is the *end-of-batch quality review* — a pharmacist or quality manager checks the completed batch record before releasing for distribution.

**Q: Why is Aseptic Filling the bottleneck?**
A: It has the longest processing time (120 min) relative to how often batches arrive (every 240 min on average). This gives it a utilization of 50% — higher than every other station — and means it builds up a queue first.

**Q: Why does adding a 2nd filling machine help so much?**
A: When you split the queue between 2 machines, each machine only needs to handle half the traffic. The queueing math shows this drops the wait time from 120 min to 8 min — a 93% reduction. This is a real-world insight: pooled parallel servers are dramatically more efficient than two separate queues.
