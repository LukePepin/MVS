"""
slide24.py
==========
ISE 573 -- Manufacturing Execution Systems  |  Week 9
Run this script to complete the two required DES experiments
and save des_results.csv for your worksheet submission.

HOW TO RUN
----------
    python slide24.py

WHAT IT DOES
------------
1. Runs Experiment 1 (baseline -- no breakdown)
2. Runs Experiment 2 (cascade -- Station 1 breaks)
3. Saves both to des_results.csv
4. Prints an analysis table to the screen

WORKSHEET CONNECTION
--------------------
Task 1 check:  find Wq_min in the exp1_baseline / Stn1 row.
               Write that number in the check box at the
               bottom of Task 1 and confirm it is within
               +/- 10% of your hand-calculated value.

Submit:  des_results.csv alongside your worksheet PDF.

FILES NEEDED IN THE SAME FOLDER
--------------------------------
    des_tkinter.py    -- the DES engine
    week9_helper.py   -- save_results_csv() helper

Dr. Manbir Sodhi -- University of Rhode Island -- Spring 2026
"""

import os
import sys

# ── Dependency check ──────────────────────────────────────────────────────
for fname in ('des_tkinter.py', 'week9_helper.py'):
    if not os.path.isfile(fname):
        print(f"ERROR: {fname} not found in current folder.")
        print("Make sure des_tkinter.py and week9_helper.py are in the")
        print(f"same directory as this script: {os.getcwd()}")
        sys.exit(1)

from des_tkinter  import run_serial_des
from week9_helper import save_results_csv

CSV_PATH = 'des_results.csv'

# ── Experiment parameters (reference line) ────────────────────────────────
BASE_PARAMS = dict(
    n_stn   = 3,
    lam     = 8.0,
    mu      = 10.0,
    Ca2     = 1.0,
    Cs2_nom = 1.0,
    n_jobs  = 2000,
    seed    = 42,
)

# ── Experiment 1: Baseline (no breakdown) ─────────────────────────────────
print("=" * 60)
print("Experiment 1 -- Baseline (no breakdown)")
print("  n=3, lambda=8, mu=10, Ca2=1, Cs2=1, no breakdown")
print("  Running 2000 jobs... ", end="", flush=True)

r1 = run_serial_des(**BASE_PARAMS, brk_stn=-1, mtbf=3.0, mttr=0.5)
save_results_csv(r1, 'exp1_baseline', CSV_PATH)
print("done")

# ── Experiment 2: Cascade (Station 1 breaks) ──────────────────────────────
print()
print("Experiment 2 -- Ca2 Cascade (Station 1 breaks)")
print("  MTBF=3hr, MTTR=0.5hr, Station 1 only")
print("  Running 2000 jobs... ", end="", flush=True)

r2 = run_serial_des(**BASE_PARAMS, brk_stn=0, mtbf=3.0, mttr=0.5)
save_results_csv(r2, 'exp2_cascade', CSV_PATH)
print("done")

# ── Analysis table ────────────────────────────────────────────────────────
print()
print("=" * 60)
print("RESULTS SUMMARY")
print("=" * 60)
print(f"{'Experiment':<18} {'Station':<8} {'Wq(min)':>8} "
      f"{'A':>7} {'Ca2_in':>8} {'Bkdowns':>8}")
print("-" * 60)

experiments = [
    ('exp1_baseline', r1),
    ('exp2_cascade',  r2),
]

for tag, r in experiments:
    for i in range(r['n_stn'] if 'n_stn' in r else len(r['Wq_sim'])):
        wq  = r['Wq_sim'][i] * 60
        a   = r['A_sim'][i]
        ca2 = r['Ca2_arriving'][i]
        bk  = r['bk_count'][i]
        stn = f"Stn {i+1}"
        print(f"{tag:<18} {stn:<8} {wq:>8.1f} {a:>7.3f} {ca2:>8.3f} {bk:>8d}")
    print()

# ── Interpretation prompts ─────────────────────────────────────────────────
print("=" * 60)
print("QUESTIONS TO ANSWER (for your worksheet)")
print("=" * 60)

wq_base = r1['Wq_sim'][0] * 60
wq_casc = r2['Wq_sim'][0] * 60
wq_stn2 = r2['Wq_sim'][1] * 60
ca2_stn2 = r2['Ca2_arriving'][1]

print(f"\n1. WORKSHEET TASK 1 CHECK")
print(f"   Exp 1 Wq at Stn 1 (simulation) = {wq_base:.1f} min")
print(f"   Write this in the Task 1 check box.")
print(f"   Your hand-calculated value should be within +/-10% of this.")
print(f"   Acceptable range: {wq_base*0.9:.1f} -- {wq_base*1.1:.1f} min")

print(f"\n2. CASCADE EFFECT (Departure Theorem)")
print(f"   Exp 2: Stn 1 Wq = {wq_casc:.1f} min  ({wq_casc/wq_base:.1f}x baseline)")
print(f"   Exp 2: Stn 2 Wq = {wq_stn2:.1f} min  (breakdowns at Stn 2 = 0)")
print(f"   Exp 2: Ca2 arriving at Stn 2 = {ca2_stn2:.3f}  (was 1.000 in Exp 1)")
print(f"   --> A breakdown at Stn 1 raised Stn 2 Wq by "
      f"{(wq_stn2/wq_base - 1)*100:.0f}% with NO breakdown at Stn 2.")
print(f"   --> The elevated Ca2 ({ca2_stn2:.2f}) is the cause.")

print(f"\n3. OUTPUT FILE")
print(f"   Saved to: {os.path.abspath(CSV_PATH)}")
print(f"   Open in Excel. Submit this file with your worksheet PDF.")
print("=" * 60)
