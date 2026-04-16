"""
slide33.py
==========
ISE 573 -- Manufacturing Execution Systems  |  Week 9
Creates buffers.csv for the reference serial line.

HOW TO RUN
----------
    python slide33.py

WHAT IT DOES
------------
Computes B_min and B* for all three buffers in the
reference line (B_in, B_12, B_23) and writes them
to buffers.csv in the current folder.

WHAT TO DO NEXT
---------------
1. Open buffers.csv in Excel
2. Confirm B* = 11 for all three buffers
3. Go to slide 34: change B_12 capacity to 5 in Excel,
   then re-run des_tkinter.py Experiment 2 to observe
   the effect of a tight buffer on Stn 2 Wq.

FILES NEEDED IN THE SAME FOLDER
--------------------------------
    week9_helper.py

Dr. Manbir Sodhi -- University of Rhode Island -- Spring 2026
"""

import os, sys

if not os.path.isfile('week9_helper.py'):
    print("ERROR: week9_helper.py not found.")
    print(f"Make sure it is in: {os.getcwd()}")
    sys.exit(1)

from week9_helper import load_equipment_defaults, size_all_buffers_csv

CSV_PATH = 'buffers.csv'

print("=" * 55)
print("Slide 33 -- Creating buffers.csv for the reference line")
print("=" * 55)
print()
print("Reference line equipment:")
print("  M01  CNC Lathe    mu=10  MTBF=200hr  MTTR=45min")
print("  M02  CNC Lathe    mu=10  MTBF=180hr  MTTR=45min")
print("  M03  Grinder      mu=10  MTBF=300hr  MTTR=30min")
print(f"  lambda = 8 jobs/hr   service level = 95%")
print()

equip   = load_equipment_defaults()
results = size_all_buffers_csv(equip, lam=8.0, csv_path=CSV_PATH)

print()
print("=" * 55)
print("WHAT THESE NUMBERS MEAN")
print("=" * 55)
for r in results:
    label  = r['label']
    B_min  = r['B_min']
    B_star = r['B_star']
    tdrain = r['t_drain_hr']
    print(f"\n  {label}:")
    print(f"    B_min = {B_min}  "
          f"(minimum slots to absorb one average repair)")
    print(f"    B*    = {B_star}  "
          f"(slots for 95% confidence -- no starvation)")
    print(f"    t_drain = {tdrain} hr  "
          f"(how long after repair to clear the queue burst)")

print()
print("=" * 55)
print("NEXT STEPS")
print("=" * 55)
print()
print("1. Open buffers.csv in Excel -- confirm three rows,")
print("   B* = 11, capacity = 11 for all buffers.")
print()
print("2. SLIDE 34 EXERCISE:")
print("   - In Excel, change B_12 capacity from 11 to 5")
print("   - Save and close Excel")
print("   - Open des_tkinter.py")
print("   - Set: n=3, Station 1 breaks, MTBF=3hr, MTTR=0.5hr")
print("   - Click Run")
print("   - Observe: does Stn 2 Wq increase compared to")
print("     Experiment 2 (where capacity was 11)?")
print()
print(f"Output file: {os.path.abspath(CSV_PATH)}")
print("=" * 55)
