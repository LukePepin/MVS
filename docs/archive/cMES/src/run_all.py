"""
run_all.py — End-to-end runner for the Sheridan_573 MES prototype (ISE 573 Week 7).

Execution order:
  1. db_setup        — drop/recreate and seed all tables
  2. queueing_analysis — M/M/1, M/M/c, M/G/1 + Little's Law; saves to simulation_results
  3. des_simulation  — SimPy DES, Welch warm-up, 15 reps, CI, paired t-test, what-if; saves PNGs
  4. mrp_scheduler   — MRP explosion, EDD/SPT scheduling, PuLP optimization, dispatch queue

Usage:
    python run_all.py [--skip-sim]   # --skip-sim skips the long DES run (~3 min)
    python run_all.py --only step    # run a single step (db/queueing/sim/mrp)
"""

import sys
import os
import time
import traceback

# Ensure src/ modules are importable regardless of working directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ── helpers ───────────────────────────────────────────────────────────────────

def section(title: str):
    bar = "=" * 60
    print(f"\n{bar}")
    print(f"  {title}")
    print(bar)


def elapsed(t0: float) -> str:
    s = time.time() - t0
    return f"{s:.1f}s" if s < 60 else f"{int(s//60)}m {int(s%60)}s"


# ── step runners ──────────────────────────────────────────────────────────────

def run_db_setup():
    section("Step 1 / 4 — Database Setup (Sheridan_573)")
    t0 = time.time()
    import db_setup
    db_setup.setup_database()
    print(f"\n  Completed in {elapsed(t0)}")


def run_queueing():
    section("Step 2 / 4 — Queueing Theory Analysis")
    t0 = time.time()
    import queueing_analysis
    queueing_analysis.run_queueing_analysis()
    print(f"\n  Completed in {elapsed(t0)}")


def run_simulation():
    section("Step 3 / 4 — Discrete-Event Simulation (SimPy)")
    print("  [!] This step runs 15 replications × 5 scenarios — may take 2-4 minutes.\n")
    t0 = time.time()
    import des_simulation
    des_simulation.run_des_analysis()
    print(f"\n  Completed in {elapsed(t0)}")


def run_mrp():
    section("Step 4 / 4 — MRP Explosion + Scheduling + Optimization")
    t0 = time.time()
    import mrp_scheduler
    mrp_scheduler.run_mrp_and_schedule()
    print(f"\n  Completed in {elapsed(t0)}")


# ── main ──────────────────────────────────────────────────────────────────────

STEPS = {
    "db":       run_db_setup,
    "queueing": run_queueing,
    "sim":      run_simulation,
    "mrp":      run_mrp,
}

STEP_ORDER = ["db", "queueing", "sim", "mrp"]


def main():
    args = sys.argv[1:]
    skip_sim = "--skip-sim" in args
    only_step = None
    if "--only" in args:
        idx = args.index("--only")
        if idx + 1 < len(args):
            only_step = args[idx + 1]
            if only_step not in STEPS:
                print(f"[ERROR] Unknown step '{only_step}'. Choose from: {', '.join(STEPS)}")
                sys.exit(1)

    total_t0 = time.time()
    print("\n" + "=" * 60)
    print("  Sheridan_573 — Week 7 MES Prototype  (ISE 573)")
    print("  Connor Sheridan  |  University of Rhode Island")
    print("=" * 60)

    run_order = [only_step] if only_step else STEP_ORDER

    errors = []
    for key in run_order:
        if skip_sim and key == "sim":
            section("Step 3 / 4 — Discrete-Event Simulation [SKIPPED]")
            print("  (pass without --skip-sim to run)")
            continue
        try:
            STEPS[key]()
        except Exception as exc:
            errors.append((key, exc))
            print(f"\n  [ERROR in {key}]: {exc}")
            traceback.print_exc()
            print("  Continuing to next step...\n")

    # ── final summary ────────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("  Run Summary")
    print("=" * 60)
    for key in run_order:
        if skip_sim and key == "sim":
            print(f"  {'sim':<12} SKIPPED")
        elif any(k == key for k, _ in errors):
            print(f"  {key:<12} FAILED")
        else:
            print(f"  {key:<12} OK")

    print(f"\n  Total wall time: {elapsed(total_t0)}")

    if not only_step and not skip_sim and not errors:
        print("\n  All steps complete. Start the dashboard with:")
        print("    python RUN_PROJECT.py   (from the project root)")
        print("  then open http://localhost:8090 in your browser.")
    elif errors:
        print(f"\n  {len(errors)} step(s) failed — see output above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
