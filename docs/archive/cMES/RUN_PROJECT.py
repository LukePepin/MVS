"""
RUN_PROJECT.py — Single-file launcher for the ISE 573 Week 7 MES Prototype
Connor Sheridan | University of Rhode Island

Just run:  python3 RUN_PROJECT.py
Then open: http://localhost:8090
"""

import subprocess
import sys
import os
import time
import webbrowser

HERE = os.path.dirname(os.path.abspath(__file__))
SRC  = os.path.join(HERE, "src")

# ── 1. Check / install dependencies ──────────────────────────────────────────

REQUIRED = ["psycopg2", "simpy", "numpy", "scipy", "matplotlib", "pulp"]

def check_deps():
    missing = []
    for pkg in REQUIRED:
        try:
            __import__(pkg)
        except ImportError:
            missing.append(pkg)
    if missing:
        print(f"\n  Installing missing packages: {', '.join(missing)}")
        subprocess.check_call([sys.executable, "-m", "pip", "install",
                               "psycopg2-binary", "simpy", "numpy",
                               "scipy", "matplotlib", "pulp", "-q"])
        print("  Packages installed.\n")

# ── 2. Run setup steps ────────────────────────────────────────────────────────

def run_step(label, module_name, func_name):
    print(f"  [{label}] ...", end=" ", flush=True)
    sys.path.insert(0, SRC)
    import importlib
    mod = importlib.import_module(module_name)
    fn  = getattr(mod, func_name)

    # Suppress noisy stdout from sub-modules
    import io, contextlib
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        fn()

    print("done")

# ── 3. Launch dashboard ───────────────────────────────────────────────────────

def launch_dashboard():
    print("\n  Launching dashboard at http://localhost:8090 ...")
    proc = subprocess.Popen(
        [sys.executable, os.path.join(SRC, "dashboard.py")],
        cwd=SRC,
    )
    time.sleep(3)
    webbrowser.open("http://localhost:8090")
    print("  Browser opened. Press Ctrl+C here to stop the server.\n")
    try:
        proc.wait()
    except KeyboardInterrupt:
        print("\n  Shutting down dashboard...")
        proc.terminate()

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print()
    print("=" * 60)
    print("  ISE 573 Week 7 — Pharma MES Prototype")
    print("  Connor Sheridan | University of Rhode Island")
    print("=" * 60)

    # Dependencies
    print("\n[1/4] Checking dependencies...")
    check_deps()
    print("  All packages ready.")

    # Database
    print("\n[2/4] Setting up database (Sheridan_573)...")
    run_step("db_setup",  "db_setup",  "setup_database")
    run_step("queueing",  "queueing_analysis", "run_queueing_analysis")
    run_step("mrp/sched", "mrp_scheduler",     "run_mrp_and_schedule")

    # Optional: full simulation (slow)
    print()
    print("  The full DES simulation (15 replications × 5 scenarios) takes ~3 min.")
    try:
        ans = input("  Run it now? [y/N]: ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        ans = "n"

    if ans == "y":
        print("\n[3/4] Running discrete-event simulation...")
        run_step("simulation", "des_simulation", "run_des_analysis")
        print("  Simulation plots saved to outputs/")
    else:
        print("[3/4] Simulation skipped. (You can run it later via ⚙ Run Analysis in the dashboard.)")

    # Dashboard
    print("\n[4/4] Starting dashboard...")
    launch_dashboard()


if __name__ == "__main__":
    main()
