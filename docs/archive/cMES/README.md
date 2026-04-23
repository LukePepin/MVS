# Pharma MES Prototype — ISE 573 Week 7
**Connor Sheridan | University of Rhode Island**

A fully integrated Manufacturing Execution System (MES) prototype for a sterile injectable pharmaceutical facility. The system combines queueing theory, discrete-event simulation, statistical analysis, what-if scenario testing, and a live MES database — all presented through an interactive web dashboard.

---

## Quick Start

```
python3 RUN_PROJECT.py
```

Open **http://localhost:8090** in your browser. The launcher installs any missing Python packages, sets up the database, runs the scheduling pipeline, and opens the dashboard automatically. See [SETUP_AND_EXECUTION.md](SETUP_AND_EXECUTION.md) for step-by-step instructions.

---

## Project Overview

This prototype simulates how batches of medicine move through a pharmaceutical manufacturing line — from incoming raw materials through sterile filling and QA release. It demonstrates five core manufacturing systems concepts:

| Part | Topic | Method |
|------|-------|--------|
| 1 | Queueing Theory | M/M/1, M/M/c (Erlang-C), M/G/1 (Pollaczek-Khinchine), Little's Law |
| 2 | Discrete-Event Simulation | SimPy 4, PriorityResource queues, machine breakdowns, 3 product types |
| 3 | Statistical Analysis | 15 replications, Welch warm-up, 95% CI via Student's t, paired t-test with CRN |
| 4 | What-If Scenario Analysis | 5 scenarios × 15 reps: baseline, 2nd filling machine, low variability, SPT, EDD |
| 5 | MES Integration | PostgreSQL, MRP explosion, EDD/SPT scheduling, PuLP LP optimisation, ISA-95 Level 3 |

---

## The Factory Process

Every batch of sterile injectable drug passes through nine stations in sequence:

| Step | Station | Processing Time |
|------|---------|----------------|
| ① | Raw Material Staging | ~30 min (Lognormal) |
| ② | Quarantine Hold | 120 min (fixed regulatory dwell) |
| ③ | Dispensing & Weighing | ~45 min (Lognormal) |
| ④ | Compounding / Solution Prep | ~90 min (Lognormal) |
| ⑤ | Sterile Filtration | ~60 min (Lognormal) |
| ⑥ | **⚡ Aseptic Filling ← BOTTLENECK** | ~120 min (Lognormal) |
| ⑦ | Inspection & Packaging | ~45 min (Lognormal) |
| ⑧ | QA Release Hold | 180 min (fixed regulatory dwell) |
| ⑨ | Released ✓ | — |

Batch inter-arrival time: **Exponential(mean = 240 min)**. Three product types (Injectable-A/B/C) with processing time multipliers 1.00 / 0.88 / 0.74.

The **Aseptic Filling station** is the system bottleneck — highest utilisation (ρ = 0.50), longest queue, and the focus of all improvement scenarios.

---

## Part 1 — Queueing Theory Analysis

`src/queueing_analysis.py` models each station analytically before any simulation is run.

**Models applied:**

- **M/M/1** — Poisson arrivals, exponential service, single server. Key result: Filling queue wait Wq = 120 min.
- **M/M/c (Erlang-C)** — Adding a second filling machine (c = 2). Wq drops from 120 min to **8 min** (−93%). Probability of waiting drops from 50% to 10%.
- **M/G/1 (Pollaczek-Khinchine)** — Realistic lognormal service variability (CV = 0.20). Filling Wq = 62.4 min. Confirms adding a server dominates reducing variability.
- **Little's Law** — L = λW verified to < 0.000001 error for all stations.

Results are stored in the `simulation_results` database table and displayed on the **📊 Sim Results** tab.

---

## Part 2 — Discrete-Event Simulation Model

`src/des_simulation.py` builds a SimPy discrete-event simulation of the full nine-station factory.

**Model structure:**
- Each variable station is a `simpy.PriorityResource`. Priority is set by dispatch rule: FIFO (arrival time), SPT (service time), EDD (due-date timestamp).
- Three product types arrive in the same Poisson stream (40% / 35% / 25%), with lognormal service times (CV 0.10–0.20 per station).
- Machine breakdowns at Aseptic Filling: exponential MTTF = 480 min, exponential MTTR = 30 min, implemented via 1-min polling loops that interrupt the current job.
- Quarantine (step ②) and QA Release (step ⑧) use fixed-duration timeouts with no resource — they model mandatory regulatory hold times.
- WFI water quality (conductivity, TOC, temperature) and HVAC cleanroom conditions (temperature, humidity, particle count) are modelled as mean-reverting stochastic processes. Out-of-spec excursions generate ALARM events.

**Parameters:** 15,000 min run length (~10 days), 15 independent seeds (0–14).

---

## Part 3 — Statistical Analysis

**Warm-up (Welch method):** Rolling-average WIP across replications shows the system reaches steady state at ~2,000 min. All statistics exclude the warm-up period.

**Baseline 95% Confidence Intervals (Student's t, n = 15):**

| Metric | Mean | 95% CI |
|--------|------|--------|
| Flow time | 703.6 min (~11.7 h) | ± ~6 min |
| WIP | 2.9 batches | ± ~0.3 |
| Filling utilisation | 50.2% | ± ~1% |
| Throughput | 0.213 batches/h | ± ~0.01 |

**Paired t-test (FIFO vs SPT, Common Random Numbers):**
Using the same 15 seeds for both rules controls replication-to-replication noise:
- Difference = **7.0 min**, 95% CI [0.5, 13.5], t ≈ 2.3, **p ≈ 0.04**
- SPT dispatching produces a statistically significant reduction in flow time at α = 0.05.

Charts: `outputs/fig1_welch_warmup.png`, `fig2_wip_replications.png`, `fig3_queue_filling.png`.

---

## Part 4 — What-If Scenario Analysis

Five scenarios, each with 15 replications. Results stored in the `simulation_results` table and shown in the **📊 Sim Results** tab (best scenario highlighted green, % change from baseline shown).

| Scenario | Change from Baseline | Key Result |
|----------|---------------------|------------|
| Baseline | FIFO, 1 filling machine, CV × 1.0 | Mean flow 703.6 min — reference |
| 2nd Filling Machine | Add parallel filling machine | ~90% queue wait reduction — largest single improvement |
| Low Variability | Halve service-time CV (× 0.5) | Moderate improvement; confirms capacity > variability |
| SPT Dispatching | Change rule to Shortest Processing Time | −7 min (p = 0.04); statistically significant |
| EDD Dispatching | Change rule to Earliest Due Date | 0 late jobs; similar average flow to FIFO |

Charts: `outputs/fig4_dispatching_boxplot.png`, `fig5_scenario_comparison.png`, `fig6_utilization.png`.

---

## Part 5 — MES Integration

### Database Schema (PostgreSQL — Sheridan_573)

| Table | Contents |
|-------|---------|
| `products` | Injectable-A, B, C product master records |
| `items` | Finished goods, sub-components, raw materials (14 items) |
| `bom` | Bill of Materials — parent/child quantities (21 rows, 3 levels) |
| `work_orders` | Production requests with quantities and due dates |
| `materials_inventory` | On-hand lots (approved / quarantine status) |
| `mrp_plan` | Planned orders from MRP explosion + PuLP optimisation |
| `schedule` | EDD/SPT work centre sequence assignments |
| `dispatch_queue` | Priority-ordered production sequence from MRP scheduler (not currently consumed by live sim) |
| `batch_log` | Batch execution records — populated when live sim is connected to DB (currently unused) |
| `events_log` | INFO / WARNING / ALARM event stream — populated when live sim is connected to DB (currently unused) |
| `simulation_results` | All queueing and DES scenario outputs |

### MRP Pipeline (`src/mrp_scheduler.py`)

1. **Work Order Entry** — 9 work orders across three products with a 4-week due-date horizon.
2. **BOM Explosion** — Level-by-level gross-to-net calculation. Net = gross − on-hand − scheduled receipts.
3. **Lot Sizing** — L4L (Lot for Lot) for finished goods. FOQ (Fixed Order Quantity) for components and raw materials.
4. **Lead-time offsetting** — Release date = need date − lead time. Past-due orders are flagged as warnings.
5. **Scheduling** — EDD and SPT both sequence work at the Aseptic Filling work centre. The lower-tardiness schedule is selected and saved to `schedule`.
6. **PuLP LP Optimisation** — Multi-product, multi-period LP minimises total production + holding cost subject to weekly capacity. Optimal plan written to `mrp_plan` (status = 'optimized'). Cost ≈ $431,000 / 4-week horizon.
7. **Dispatch Queue** — Optimised schedule converted to a prioritised queue in `dispatch_queue`; drives the live factory floor simulation.

### ISA-95 Level 3 Data Flow

```
Work Orders ──► MRP Explosion ──► Scheduling (EDD/SPT) ──► LP Optimisation ──► Dispatch Queue
                                                                                       │
                                                                               Live Simulation
                                                                                       │
Database ◄── events_log / batch_log ◄────────────────────────────────────── Factory Floor
```

---

## Scripts — What Each File Does

### `RUN_PROJECT.py` (root)
The single-entry-point launcher. Run this first. It checks for and installs missing pip packages, calls `db_setup.setup_database()`, `queueing_analysis.run_queueing_analysis()`, and `mrp_scheduler.run_mrp_and_schedule()` in sequence, optionally runs the full DES simulation, then launches `dashboard.py` as a subprocess and opens the browser. All module paths resolve relative to `src/` so it works from any working directory.

### `src/db_setup.py`
Creates and seeds the entire PostgreSQL database from scratch on every run (DROP + CREATE). Defines 11 tables covering the full ISA-95 Level 3 schema: product master, Bill of Materials (3 levels, 21 rows), work orders, materials inventory, MRP plan, schedule, dispatch queue, batch log, events log, and simulation results. Seeds pharmaceutical-realistic test data — three injectable products with realistic lead times, on-hand quantities, and a 9-order production plan. Called first by both `RUN_PROJECT.py` and `run_all.py`.

### `src/queueing_analysis.py`
Implements M/M/1, M/M/c (Erlang-C), and M/G/1 (Pollaczek-Khinchine) models for all six variable stations. Computes ρ, Lq, Wq, L, W, and verifies Little's Law. Results are written to the `simulation_results` table with scenario names prefixed `queueing_`. Runtime: ~1 second.

### `src/des_simulation.py`
Builds and runs the SimPy discrete-event simulation. Five scenario functions each run 15 independent replications (seeds 0–14) of 15,000 simulated minutes with a 2,000 min Welch warm-up. Applies Welch warm-up detection, computes 95% Student-t confidence intervals per metric, and performs a paired t-test (FIFO vs SPT) using Common Random Numbers. Saves batch-level results to the `simulation_results` table and writes six matplotlib PNG charts to `outputs/`. Runtime: ~3 minutes.

### `src/mrp_scheduler.py`
Implements the full MRP pipeline. Explodes the Bill of Materials level-by-level, calculates net requirements, applies L4L/FOQ lot sizing, offsets by lead time, and writes planned orders to `mrp_plan`. Runs both EDD and SPT scheduling algorithms at the Aseptic Filling work centre, selects the lower-tardiness schedule, and saves it to `schedule`. Then formulates and solves a multi-product multi-period linear programme using PuLP (CBC solver) to minimise production + holding cost over a 4-week horizon; writes the optimal plan back to `mrp_plan`. Finally builds the `dispatch_queue` representing the prioritised production sequence. Note: the `dispatch_queue` is stored in the database but is not currently consumed by the live dashboard simulation — it is available for display and future integration.

### `src/dashboard.py`
Pure Python HTTP server (`ThreadingHTTPServer + BaseHTTPRequestHandler` — no Flask or external web framework). Runs a SimPy simulation in a background daemon thread protected by a `threading.Lock`. The `SimState` dataclass holds all live state; `_deep_update` merges nested dict updates thread-safely. Key routes: `GET /` (serves the HTML template), `GET /api/state` (polled every second by the browser), `GET /api/sim_results` (scenario data from the database), `GET /outputs/<file>` (serves PNG charts), `POST /api/control` (start/stop/pause/reset/set_speed/set_rule/set_filling/finish_instantly), `POST /api/run_analysis` (triggers the full analysis pipeline in a background thread).

The live factory simulation runs **entirely in memory** and is independent of the database — it generates its own random batch arrivals and does not read from `dispatch_queue` or write to `batch_log`/`events_log`. The database is used only for the display tabs: the MRP/WO tab reads `work_orders`, `mrp_plan`, and `schedule`; the Sim Results tab reads `simulation_results`.

### `src/run_all.py`
A command-line runner for the four analysis steps without starting the dashboard. Useful for re-running individual steps during development. Supports `--skip-sim` (skips the 3-minute DES run) and `--only <step>` (runs only `db`, `queueing`, `sim`, or `mrp`). Prints a summary table with step status and total wall time.

---

## Database Connection

All Python scripts connect to the same PostgreSQL instance using these parameters, defined in `src/dashboard.py` and used consistently across all modules:

```python
DB_CFG = dict(
    host     = "100.115.213.16",
    port     = 5432,
    dbname   = "Sheridan_573",
    user     = "twin_mes_db",
    password = "postgres",
    connect_timeout = 5,
)
```

Connection is made via `psycopg2.connect(**DB_CFG)` with `RealDictCursor` for dictionary-style row access. The database must be reachable from your machine before running `RUN_PROJECT.py` — the launcher will fail at the `db_setup` step otherwise.

**Tables written by each script:**

| Script | Tables written |
|--------|---------------|
| `db_setup.py` | All 11 tables (creates schema + seeds data) |
| `queueing_analysis.py` | `simulation_results` (queueing_ rows) |
| `des_simulation.py` | `simulation_results` (scenario rows + t-test rows) |
| `mrp_scheduler.py` | `mrp_plan`, `schedule`, `dispatch_queue` |
| `dashboard.py` | reads `work_orders`, `mrp_plan`, `schedule`, `simulation_results` for display only — does not write to the database |

---

## Dashboard Pages

| Tab | Purpose |
|-----|---------|
| Factory Floor | Animated batch tokens on an SVG process diagram; live WFI and HVAC charts |
| Analytics | WIP, queue depth, utilisation, throughput — updates as live sim runs |
| 📊 Sim Results | All five assignment parts: queueing tables, figures, scenario comparison, ISA-95 flow |
| MRP / WO | Live database tables: Work Orders, MRP Planned Orders, EDD Schedule |
| Events | Real-time INFO / WARNING / ALARM log from the live simulation |
| ❓ Guide | Plain-language explanation of every page, control, and metric |

---

## File Structure

```
Week7_Submission/
├── RUN_PROJECT.py              ← Start here — single-file launcher
├── README.md                   ← This file
├── SETUP_AND_EXECUTION.md      ← Plain-language setup and execution guide
├── outputs/                    ← 6 PNG charts from the statistical simulation
│   ├── fig1_welch_warmup.png
│   ├── fig2_wip_replications.png
│   ├── fig3_queue_filling.png
│   ├── fig4_dispatching_boxplot.png
│   ├── fig5_scenario_comparison.png
│   └── fig6_utilization.png
└── src/                        ← All Python source files
    ├── db_setup.py             ← PostgreSQL schema + pharmaceutical seed data
    ├── queueing_analysis.py    ← Part 1: M/M/1, M/M/c, M/G/1, Little's Law
    ├── des_simulation.py       ← Parts 2–4: SimPy DES, warm-up, CI, scenarios
    ├── mrp_scheduler.py        ← Part 5: MRP, scheduling, PuLP optimisation
    ├── dashboard.py            ← HTTP server + live SimPy simulation engine
    ├── run_all.py              ← CLI runner for analysis steps without the dashboard
    └── templates/
        └── dashboard.html      ← Browser UI (Chart.js 4.4, SVG, vanilla JS)
```

---

## Dependencies

| Package | Purpose |
|---------|---------|
| `psycopg2-binary` | PostgreSQL driver |
| `simpy` | Discrete-event simulation engine |
| `numpy` / `scipy` | Statistics — CI, t-tests, distributions |
| `matplotlib` | PNG chart generation |
| `pulp` | Linear programming (CBC solver) |

Installed automatically by `RUN_PROJECT.py`. Requires Python 3.9+.

**Database:** PostgreSQL at `100.115.213.16:5432`, database `Sheridan_573`, user `twin_mes_db`. Must be reachable from your machine (via tailscale).

---

## Key Results Summary

| Finding | Value |
|---------|-------|
| System bottleneck | Aseptic Filling (ρ = 0.50) |
| Baseline mean flow time | 703.6 min (~11.7 h) |
| M/M/1 filling queue wait | 120.0 min |
| M/M/2 filling queue wait | 8.0 min (−93.3%) |
| SPT vs FIFO improvement | −7.0 min (p = 0.04, statistically significant) |
| Best single improvement | Add 2nd filling machine |
| EDD scheduling result | 0 late jobs in baseline |
| PuLP optimal cost | ~$431,000 / 4-week planning horizon |
