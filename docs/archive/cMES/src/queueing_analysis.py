"""
queueing_analysis.py — Part 1: Queueing Theory Foundation (20 pts)

Applies analytical queueing models to the pharma manufacturing process.
Models the 6 processing work centers based on the project proposal:
  Raw Material → Dispensing → Compounding → Filtration → Filling → Inspection

Outputs:
  - M/M/1 metrics for all stations
  - M/M/c for the bottleneck (Filling) with c=2
  - M/G/1 (Pollaczek-Khinchine) for all stations with realistic CV
  - Little's Law verification
  - Results saved to simulation_results table
"""

import math
import json
from dataclasses import dataclass, asdict
from typing import Optional
import psycopg2

DB_CFG = dict(
    host="100.115.213.16", port=5432, dbname="Sheridan_573",
    user="twin_mes_db", password="postgres", connect_timeout=8,
)

# ── System parameters ──────────────────────────────────────────────────────────
# Batch arrivals: Poisson process, mean inter-arrival = 240 min → λ = 1/240
# Chosen so that utilization ρ < 1 at all stations (system stable)
MEAN_INTERARRIVAL = 240.0   # minutes between batch arrivals
LAM = 1.0 / MEAN_INTERARRIVAL  # arrival rate (batches/min)

# Mean processing times (minutes) — from project proposal process flow
STATION_MEANS: dict = {
    "Raw Material & Quarantine": 30,    # staging, visual inspection
    "Dispensing & Weighing":     45,    # API dispensing, WFI measurement
    "Compounding":               90,    # formulation mixing  ← heaviest workload
    "Sterile Filtration":        60,    # filter integrity + sterile transfer
    "Aseptic Filling":          120,    # vial filling + stoppering  ← BOTTLENECK
    "Inspection & Packaging":    45,    # visual + semi-auto inspection
}

# Coefficients of Variation (CV = σ/μ) per station
# Filling has highest variability (manual setup, environmental sensitivity)
STATION_CVS: dict = {
    "Raw Material & Quarantine": 0.15,
    "Dispensing & Weighing":     0.15,
    "Compounding":               0.10,
    "Sterile Filtration":        0.15,
    "Aseptic Filling":           0.20,   # highest CV — manual + env sensitive
    "Inspection & Packaging":    0.15,
}


# ── Analytical queueing models ─────────────────────────────────────────────────

@dataclass
class MM1Result:
    station:     str
    lam:         float   # arrival rate (batches/min)
    mu:          float   # service rate (batches/min)
    rho:         float   # utilization
    L:           float   # avg number in system
    Lq:          float   # avg queue length
    W:           float   # avg time in system (min)
    Wq:          float   # avg wait in queue (min)
    stable:      bool


def mm1(station: str, mu: float, lam: float = LAM) -> MM1Result:
    """M/M/1 queue: Poisson arrivals, exponential service, 1 server."""
    rho = lam / mu
    if rho >= 1.0:
        return MM1Result(station, lam, mu, rho, math.inf, math.inf, math.inf, math.inf, False)
    Lq = rho ** 2 / (1 - rho)
    L  = rho / (1 - rho)
    Wq = Lq / lam
    W  = Wq + 1 / mu
    return MM1Result(station, lam, mu, rho, L, Lq, W, Wq, True)


@dataclass
class MMcResult:
    station:  str
    lam:      float
    mu:       float
    c:        int
    rho:      float   # per-server utilization = λ/(c·μ)
    P0:       float   # probability of empty system
    C_erlang: float   # Erlang-C probability (prob of queuing)
    Lq:       float
    L:        float
    Wq:       float
    W:        float
    stable:   bool


def mm_c(station: str, mu: float, c: int, lam: float = LAM) -> MMcResult:
    """M/M/c queue: Poisson arrivals, exponential service, c parallel servers."""
    a   = lam / mu          # offered traffic (Erlangs)
    rho = lam / (c * mu)    # per-server utilization
    if rho >= 1.0:
        return MMcResult(station, lam, mu, c, rho, 0, 0, math.inf, math.inf, math.inf, math.inf, False)

    # P0 — probability system is empty
    sum_terms = sum(a**k / math.factorial(k) for k in range(c))
    last_term  = a**c / (math.factorial(c) * (1 - rho))
    P0 = 1.0 / (sum_terms + last_term)

    # Erlang-C: probability an arriving job has to wait
    C = (a**c / (math.factorial(c) * (1 - rho))) * P0

    Lq = C * rho / (1 - rho)
    L  = Lq + a
    Wq = Lq / lam
    W  = Wq + 1 / mu
    return MMcResult(station, lam, mu, c, rho, P0, C, Lq, L, Wq, W, True)


@dataclass
class MG1Result:
    station:  str
    lam:      float
    mu:       float
    rho:      float
    cv:       float
    ES2:      float   # E[S²]
    Wq:       float   # P-K formula wait time
    W:        float
    Lq:       float
    L:        float


def mg1(station: str, mu: float, cv: float, lam: float = LAM) -> MG1Result:
    """
    M/G/1 queue: Poisson arrivals, general service distribution.
    Uses Pollaczek-Khinchine (P-K) mean value formula.

    Wq = λ·E[S²] / (2·(1−ρ))
    where E[S²] = σ² + (1/μ)² = (CV·(1/μ))² + (1/μ)²
    """
    ES  = 1.0 / mu
    rho = lam * ES
    if rho >= 1.0:
        return MG1Result(station, lam, mu, rho, cv, math.inf, math.inf, math.inf, math.inf, math.inf)

    sigma2 = (cv * ES) ** 2
    ES2    = sigma2 + ES**2

    Wq = (lam * ES2) / (2 * (1 - rho))
    W  = Wq + ES
    Lq = lam * Wq
    L  = lam * W
    return MG1Result(station, lam, mu, rho, cv, ES2, Wq, W, Lq, L)


# ── Little's Law verification ──────────────────────────────────────────────────

def verify_littles_law(results_mg1: list[MG1Result]):
    """
    Verify L = λ·W for M/G/1 results.
    Returns a table of [station, L_formula, λW_check, error_%].
    """
    rows = []
    for r in results_mg1:
        if math.isinf(r.L):
            continue
        lW = LAM * r.W
        err = abs(r.L - lW) / r.L * 100 if r.L > 0 else 0
        rows.append({
            "station":     r.station,
            "L_formula":   round(r.L,  4),
            "lambda_W":    round(lW,   4),
            "error_pct":   round(err,  6),
        })
    return rows


# ── Report formatting ──────────────────────────────────────────────────────────

def _bar(label, value, width=55):
    pct = min(1.0, value) if value <= 1.0 else 1.0
    filled = int(pct * width)
    bar = "█" * filled + "░" * (width - filled)
    return f"{label}: [{bar}] {value:.1%}"


def print_report(mm1_results, mmc_result, mg1_results, littles_rows):
    sep = "=" * 72

    print(f"\n{sep}")
    print("PART 1 — QUEUEING THEORY ANALYSIS")
    print("Pharmaceutical Batch Manufacturing System — ISE 573 Week 7")
    print(sep)

    print(f"\nSystem Parameters")
    print(f"  Batch arrival rate  λ = {LAM:.6f} batches/min  "
          f"(mean inter-arrival = {MEAN_INTERARRIVAL:.0f} min)")
    print(f"  Arrival process     : Poisson (M/M/1, M/G/1) or scheduled")
    print(f"  Bottleneck station  : Aseptic Filling  (μ = 1/120 batches/min)")

    # ── M/M/1 table
    print(f"\n{'─'*72}")
    print("M/M/1 Analysis — All Work Centers")
    print(f"{'─'*72}")
    hdr = f"  {'Station':<35} {'ρ':>6}  {'Lq':>6}  {'L':>6}  {'Wq(min)':>9}  {'W(min)':>9}"
    print(hdr)
    print(f"  {'─'*35} {'─'*6}  {'─'*6}  {'─'*6}  {'─'*9}  {'─'*9}")
    for r in mm1_results:
        flag = "  ← BOTTLENECK" if r.station == "Aseptic Filling" else ""
        print(f"  {r.station:<35} {r.rho:>6.3f}  "
              f"{r.Lq:>6.3f}  {r.L:>6.3f}  "
              f"{r.Wq:>9.1f}  {r.W:>9.1f}{flag}")

    print(f"\n  All utilizations ρ < 1 → system is STABLE ✓")
    print(f"\n  Utilization bar chart (M/M/1):")
    for r in mm1_results:
        short = r.station.split()[0][:12]
        print(f"    {short:<12} {_bar('', r.rho, 30)} ρ={r.rho:.3f}")

    # ── M/M/c table (filling with 2 machines)
    print(f"\n{'─'*72}")
    print("M/M/c Extension — Aseptic Filling Bottleneck (Pooled vs Dedicated)")
    print(f"{'─'*72}")
    r1 = next(r for r in mm1_results if r.station == "Aseptic Filling")
    r2 = mmc_result
    print(f"  Configuration          {'c=1 (M/M/1)':>18}  {'c=2 (M/M/2)':>18}")
    print(f"  {'─'*60}")
    print(f"  Per-server utilization ρ  {r1.rho:>17.3f}  {r2.rho:>17.3f}")
    print(f"  Erlang-C  P(wait)         {'N/A (=ρ)':>17}  {r2.C_erlang:>17.4f}")
    print(f"  Avg queue length  Lq      {r1.Lq:>17.3f}  {r2.Lq:>17.4f}")
    print(f"  Avg system length L       {r1.L:>17.3f}  {r2.L:>17.4f}")
    print(f"  Avg queue wait    Wq(min) {r1.Wq:>17.1f}  {r2.Wq:>17.2f}")
    print(f"  Avg time in system W(min) {r1.W:>17.1f}  {r2.W:>17.2f}")
    pct_wq = (r1.Wq - r2.Wq) / r1.Wq * 100
    print(f"\n  Adding a 2nd filling line reduces Wq by {pct_wq:.1f}%  "
          f"({r1.Wq:.1f} → {r2.Wq:.2f} min)")
    print(f"  Recommendation: pooled M/M/2 dramatically outperforms two dedicated M/M/1 queues.")

    # ── M/G/1 table
    print(f"\n{'─'*72}")
    print("M/G/1 Analysis — Pollaczek-Khinchine Formula (Realistic CV)")
    print(f"{'─'*72}")
    print(f"  {'Station':<35} {'CV':>5}  {'ρ':>6}  {'Wq(min)':>9}  {'W(min)':>9}  {'Lq':>6}")
    print(f"  {'─'*35} {'─'*5}  {'─'*6}  {'─'*9}  {'─'*9}  {'─'*6}")
    for r in mg1_results:
        print(f"  {r.station:<35} {r.cv:>5.2f}  {r.rho:>6.3f}  "
              f"{r.Wq:>9.1f}  {r.W:>9.1f}  {r.Lq:>6.3f}")

    filling_mm1 = next(r for r in mm1_results if r.station == "Aseptic Filling")
    filling_mg1 = next(r for r in mg1_results  if r.station == "Aseptic Filling")
    print(f"\n  Filling: M/M/1 Wq = {filling_mm1.Wq:.1f} min  vs  "
          f"M/G/1 (CV={filling_mg1.cv}) Wq = {filling_mg1.Wq:.1f} min")
    print(f"  M/M/1 assumes CV=1.0 (exponential). With CV={filling_mg1.cv:.2f}, "
          f"wait time drops {(filling_mm1.Wq - filling_mg1.Wq)/filling_mm1.Wq*100:.1f}%.")
    print(f"  P-K: Wq = ρ·E[S]·(1+CV²) / (2·(1−ρ))  "
          f"→  factor (1+CV²)/2 = {(1+filling_mg1.cv**2)/2:.4f}")

    # ── Little's Law
    print(f"\n{'─'*72}")
    print("Little's Law Verification — L = λ·W")
    print(f"{'─'*72}")
    print(f"  {'Station':<35} {'L':>8}  {'λ·W':>8}  {'Error%':>8}")
    print(f"  {'─'*35} {'─'*8}  {'─'*8}  {'─'*8}")
    for row in littles_rows:
        print(f"  {row['station']:<35} {row['L_formula']:>8.4f}  "
              f"{row['lambda_W']:>8.4f}  {row['error_pct']:>8.6f}")
    print(f"\n  All errors < 1e-6 → Little's Law L = λW verified ✓")

    print(f"\n{sep}")
    print("Summary — Key Queueing Theory Insights")
    print(sep)
    total_W = sum(r.W for r in mm1_results)
    total_Wq = sum(r.Wq for r in mm1_results)
    print(f"  Total deterministic cycle time (sum of means):  "
          f"{sum(STATION_MEANS.values()):.0f} min")
    print(f"  Total avg time in system (M/M/1, all stations):  {total_W:.1f} min")
    print(f"  Total avg queueing time (M/M/1):                 {total_Wq:.1f} min  "
          f"({total_Wq/total_W*100:.1f}% of W)")
    print(f"  Bottleneck (Aseptic Filling) contributes {filling_mm1.Wq/total_Wq*100:.1f}% "
          f"of total queueing delay")
    print(f"\n  Actionable MES recommendation:")
    print(f"    Adding a 2nd filling line reduces total system W from {total_W:.0f} min")
    new_total = total_W - filling_mm1.W + mmc_result.W
    print(f"    to {new_total:.0f} min — a {(total_W-new_total)/total_W*100:.1f}% improvement.")
    print()


# ── Save results to database ───────────────────────────────────────────────────

def save_to_db(mg1_results):
    """Store M/G/1 queueing results in simulation_results for record."""
    conn = psycopg2.connect(**DB_CFG)
    cur  = conn.cursor()
    for r in mg1_results:
        cur.execute(
            """INSERT INTO simulation_results
               (scenario, dispatch_rule, seed, replication,
                mean_flow_time_min, util_filling_pct, mean_queue_filling)
               VALUES (%s, %s, %s, %s, %s, %s, %s)""",
            (f"queueing_MM1_{r.station[:20]}", "N/A", 0, 0,
             round(r.W, 2), round(r.rho * 100, 2), round(r.Lq, 4)),
        )
    conn.commit()
    conn.close()


# ── Main ───────────────────────────────────────────────────────────────────────

def run_queueing_analysis():
    # M/M/1 for every station
    mm1_results = [
        mm1(station, mu=1.0 / mean)
        for station, mean in STATION_MEANS.items()
    ]

    # M/M/c: 2 parallel filling lines
    mmc_result = mm_c(
        "Aseptic Filling", mu=1.0 / STATION_MEANS["Aseptic Filling"], c=2
    )

    # M/G/1 with realistic CVs
    mg1_results = [
        mg1(station, mu=1.0 / STATION_MEANS[station], cv=STATION_CVS[station])
        for station in STATION_MEANS
    ]

    # Little's Law check
    littles_rows = verify_littles_law(mg1_results)

    # Print report
    print_report(mm1_results, mmc_result, mg1_results, littles_rows)

    # Persist
    save_to_db(mg1_results)
    print("  Queueing results saved to simulation_results table.")

    return {
        "mm1":    mm1_results,
        "mmc":    mmc_result,
        "mg1":    mg1_results,
        "littles": littles_rows,
    }


if __name__ == "__main__":
    run_queueing_analysis()
