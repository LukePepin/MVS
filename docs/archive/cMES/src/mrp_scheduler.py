"""
mrp_scheduler.py — Part 5: First Prototype Demonstration (15 pts)

Integrates:
  1. Database (Sheridan_573) — populated tables from db_setup.py
  2. Scheduling — EDD (Earliest Due Date) and SPT (Shortest Processing Time)
  3. Optimization — PuLP multi-product batch production planning
  4. MRP — BOM explosion + netting + lot-sizing + lead-time offsetting
  5. Data flow demo — work order → MRP → scheduling → dispatch sequence

Run standalone:  python3 mrp_scheduler.py
"""

import math
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

import psycopg2
import psycopg2.extras
from pulp import (LpProblem, LpVariable, LpMinimize, lpSum,
                  LpStatus, value, PULP_CBC_CMD)

DB_CFG = dict(
    host="100.115.213.16", port=5432, dbname="Sheridan_573",
    user="twin_mes_db", password="postgres", connect_timeout=8,
)

# Processing time (minutes) per product per total batch flow
# Used for SPT ordering (total flow time through all stations)
PRODUCT_FLOW_MIN: Dict[str, float] = {
    "INJ_A": 390,   # 30+45+90+60+120+45 = 390 min × 1.00 product mult
    "INJ_B": 343,   # × 0.88
    "INJ_C": 289,   # × 0.74
}
PRODUCT_NAMES: Dict[str, str] = {
    "INJ_A": "Injectable-A 100mg/mL",
    "INJ_B": "Injectable-B 50mg/mL",
    "INJ_C": "Injectable-C 25mg/mL",
}


def get_conn():
    return psycopg2.connect(**DB_CFG)


# ── 1. MRP Engine ──────────────────────────────────────────────────────────────

def run_mrp_explosion(conn, horizon_weeks: int = 6, verbose: bool = True) -> List[dict]:
    """
    Full MRP explosion following the algorithm from the Week 7 lecture:
      For each BOM level (0 → 1 → 2):
        For each item at that level:
          1. Get gross requirements (MPS demand or parent planned releases × qty_per)
          2. Net requirements = max(0, gross - on_hand)
          3. Lot sizing (L4L or FOQ)
          4. Planned release = receipt week - lead_time

    Uses the work_orders table as the MPS (Level 0 demand).
    Saves results to mrp_plan table.
    """
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    # Clear old plan
    cur.execute("DELETE FROM mrp_plan")

    # ── Convert work orders to weekly MPS demand ───────────────────────────────
    now = datetime.now()
    cur.execute("""
        SELECT wo_id, product_id, quantity, due_date, priority
        FROM work_orders
        WHERE status IN ('pending','released')
        ORDER BY due_date
    """)
    work_orders = cur.fetchall()

    # Group by product and week (weeks from today, 1-indexed)
    demand: Dict[str, Dict[int, float]] = {}  # item_id -> week -> batches
    for wo in work_orders:
        delta_days = (wo["due_date"] - now).days
        week = max(1, math.ceil(delta_days / 7))
        if week > horizon_weeks:
            continue
        pid = wo["product_id"]
        demand.setdefault(pid, {})
        demand[pid][week] = demand[pid].get(week, 0) + 1  # 1 WO = 1 batch

    # ── Fetch items ────────────────────────────────────────────────────────────
    cur.execute("""
        SELECT item_id, name, bom_level, lead_time_wk, lot_rule,
               lot_size, safety_stock, on_hand
        FROM items ORDER BY bom_level
    """)
    items_raw = cur.fetchall()
    items: Dict[str, dict] = {r["item_id"]: dict(r) for r in items_raw}

    # ── Fetch BOM ──────────────────────────────────────────────────────────────
    cur.execute("SELECT parent_id, child_id, qty_per FROM bom")
    bom_rows = cur.fetchall()
    bom_children: Dict[str, List[Tuple[str, float]]] = {}  # parent -> [(child, qty)]
    bom_parents:  Dict[str, List[Tuple[str, float]]] = {}  # child -> [(parent, qty)]
    for row in bom_rows:
        bom_children.setdefault(row["parent_id"], []).append((row["child_id"], row["qty_per"]))
        bom_parents.setdefault(row["child_id"],  []).append((row["parent_id"], row["qty_per"]))

    # ── Planned releases (accumulated as we process levels) ────────────────────
    planned_releases: Dict[str, Dict[int, float]] = {}  # item_id -> week -> qty

    def get_gross(item_id: str, level: int) -> Dict[int, float]:
        if level == 0:
            return dict(demand.get(item_id, {}))
        gross: Dict[int, float] = {}
        for parent_id, qty_per in bom_parents.get(item_id, []):
            for wk, rel_qty in planned_releases.get(parent_id, {}).items():
                gross[wk] = gross.get(wk, 0) + rel_qty * qty_per
        return gross

    def mrp_item(item: dict) -> List[dict]:
        iid     = item["item_id"]
        level   = item["bom_level"]
        lt      = item["lead_time_wk"]
        rule    = item["lot_rule"]
        lot_sz  = item["lot_size"] or 1
        ss      = item["safety_stock"] or 0
        oh      = float(item["on_hand"])

        gross   = get_gross(iid, level)
        if not gross:
            return []

        orders  = []
        for wk in sorted(range(1, horizon_weeks + 1)):
            gq = gross.get(wk, 0)
            projected = oh - gq
            if projected < ss:
                net = ss - projected
                # Lot sizing
                if rule == "FOQ":
                    qty = math.ceil(net / lot_sz) * lot_sz
                else:  # L4L
                    qty = net
                oh = projected + qty
                rel_wk = wk - lt
                status = "past_due" if rel_wk < 1 else "planned"
                orders.append(dict(item_id=iid, period_week=wk,
                                   release_week=rel_wk, quantity=qty,
                                   status=status))
                planned_releases.setdefault(iid, {})
                planned_releases[iid][rel_wk] = (
                    planned_releases[iid].get(rel_wk, 0) + qty
                )
            else:
                oh = projected

        return orders

    # ── Process level by level ─────────────────────────────────────────────────
    all_orders: List[dict] = []
    level_groups: Dict[int, List[dict]] = {}
    for item in items.values():
        level_groups.setdefault(item["bom_level"], []).append(item)

    for level in sorted(level_groups):
        for item in level_groups[level]:
            orders = mrp_item(item)
            all_orders.extend(orders)

    # ── Persist to mrp_plan ────────────────────────────────────────────────────
    for o in all_orders:
        cur.execute(
            """INSERT INTO mrp_plan (item_id, period_week, release_week, quantity, status)
               VALUES (%s, %s, %s, %s, %s)""",
            (o["item_id"], o["period_week"],
             o["release_week"], float(o["quantity"]), o["status"]),
        )
    conn.commit()

    if verbose:
        _print_mrp_table(all_orders, items, horizon_weeks)

    return all_orders


def _print_mrp_table(orders: List[dict], items: Dict[str, dict], horizon: int):
    sep = "─" * 72
    print(f"\n{sep}")
    print("MRP EXPLOSION RESULTS")
    print(sep)
    by_item: Dict[str, List[dict]] = {}
    for o in orders:
        by_item.setdefault(o["item_id"], []).append(o)
    for iid in sorted(by_item, key=lambda x: items[x]["bom_level"]):
        item    = items[iid]
        iorders = sorted(by_item[iid], key=lambda r: r["period_week"])
        print(f"\n  {iid} — {item['name']}  (Level {item['bom_level']}, "
              f"LT={item['lead_time_wk']} wk, Rule={item['lot_rule']})")
        print(f"    {'Wk':>3}  {'Release Wk':>11}  {'Qty':>8}  {'Status'}")
        print(f"    {'─'*3}  {'─'*11}  {'─'*8}  {'─'*10}")
        for o in iorders:
            flag = " ⚠ PAST DUE" if o["status"] == "past_due" else ""
            print(f"    {o['period_week']:>3}  {str(o['release_week']):>11}  "
                  f"{o['quantity']:>8.1f}  {o['status']}{flag}")


# ── 2. Scheduling Algorithms ───────────────────────────────────────────────────

def edd_schedule(conn) -> List[dict]:
    """
    EDD — Earliest Due Date.
    Sort work orders by due_date ascending.
    Assign sequential start/end times (non-overlapping, 1 filling suite).
    """
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("""
        SELECT wo_id, product_id, quantity, due_date, priority, release_date
        FROM work_orders
        WHERE status IN ('pending', 'released')
        ORDER BY due_date ASC
    """)
    wos = cur.fetchall()

    now = datetime.now()
    schedule = []
    current_start = now

    for wo in wos:
        pid      = wo["product_id"]
        proc_min = PRODUCT_FLOW_MIN.get(pid, 390)
        end      = current_start + timedelta(minutes=proc_min)
        schedule.append({
            "wo_id":       wo["wo_id"],
            "product_id":  pid,
            "due_date":    wo["due_date"],
            "planned_start": current_start,
            "planned_end":   end,
            "proc_min":    proc_min,
            "algorithm":   "EDD",
            "work_center": "Filling_Suite_1",
            "tardiness":   max(0, (end - wo["due_date"]).total_seconds() / 60),
        })
        current_start = end

    return schedule


def spt_schedule(conn) -> List[dict]:
    """
    SPT — Shortest Processing Time.
    Sort by estimated total flow time (product-dependent).
    """
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("""
        SELECT wo_id, product_id, quantity, due_date, priority, release_date
        FROM work_orders
        WHERE status IN ('pending', 'released')
    """)
    wos = cur.fetchall()

    # Sort by processing time ascending (SPT rule)
    wos_sorted = sorted(wos, key=lambda r: PRODUCT_FLOW_MIN.get(r["product_id"], 390))

    now = datetime.now()
    schedule = []
    current_start = now

    for wo in wos_sorted:
        pid      = wo["product_id"]
        proc_min = PRODUCT_FLOW_MIN.get(pid, 390)
        end      = current_start + timedelta(minutes=proc_min)
        schedule.append({
            "wo_id":       wo["wo_id"],
            "product_id":  pid,
            "due_date":    wo["due_date"],
            "planned_start": current_start,
            "planned_end":   end,
            "proc_min":    proc_min,
            "algorithm":   "SPT",
            "work_center": "Filling_Suite_1",
            "tardiness":   max(0, (end - wo["due_date"]).total_seconds() / 60),
        })
        current_start = end

    return schedule


def save_schedule(conn, schedule: List[dict]):
    cur = conn.cursor()
    cur.execute("DELETE FROM schedule")
    for s in schedule:
        cur.execute(
            """INSERT INTO schedule
               (wo_id, work_center, planned_start, planned_end, algorithm, status)
               VALUES (%s, %s, %s, %s, %s, 'scheduled')""",
            (s["wo_id"], s["work_center"],
             s["planned_start"], s["planned_end"], s["algorithm"]),
        )
    conn.commit()


def print_schedule_comparison(edd: List[dict], spt: List[dict]):
    sep = "─" * 72
    print(f"\n{sep}")
    print("SCHEDULING ALGORITHMS — EDD vs SPT")
    print(sep)

    def _print(sched: List[dict], label: str):
        total_tard = sum(s["tardiness"] for s in sched)
        late_cnt   = sum(1 for s in sched if s["tardiness"] > 0)
        makespan   = max((s["planned_end"] for s in sched), default=datetime.now())
        print(f"\n  {label} Schedule:")
        print(f"  {'#':>2}  {'WO':>6}  {'Product':<12}  {'Proc(min)':>9}  "
              f"{'Due':>12}  {'Tardiness(min)':>14}")
        print(f"  {'─'*2}  {'─'*6}  {'─'*12}  {'─'*9}  {'─'*12}  {'─'*14}")
        for i, s in enumerate(sched, 1):
            due_str = s["due_date"].strftime("%m/%d %H:%M")
            flag    = " ⚠" if s["tardiness"] > 0 else ""
            print(f"  {i:>2}  {s['wo_id']:>6}  "
                  f"{PRODUCT_NAMES.get(s['product_id'], s['product_id'])[:12]:<12}  "
                  f"{s['proc_min']:>9.0f}  {due_str:>12}  "
                  f"{s['tardiness']:>14.0f}{flag}")
        print(f"  Total tardiness: {total_tard:.0f} min  |  "
              f"Late jobs: {late_cnt}/{len(sched)}  |  "
              f"Makespan: {(makespan - sched[0]['planned_start']).total_seconds()/60:.0f} min")

    _print(edd, "EDD (Earliest Due Date)")
    _print(spt, "SPT (Shortest Processing Time)")

    edd_tard = sum(s["tardiness"] for s in edd)
    spt_tard = sum(s["tardiness"] for s in spt)
    winner   = "EDD" if edd_tard <= spt_tard else "SPT"
    print(f"\n  EDD total tardiness: {edd_tard:.0f} min  "
          f"|  SPT total tardiness: {spt_tard:.0f} min")
    print(f"  → Recommendation: {winner} minimizes total tardiness for this order set.")


# ── 3. PuLP Multi-Product Production Planning ──────────────────────────────────

def pulp_production_plan(conn, horizon_weeks: int = 4,
                          max_batches_per_week: int = 20) -> dict:
    """
    Multi-product, multi-period batch production planning.
    Minimizes total production + holding cost over 4-week horizon.

    Decision variables:
      x[p][t]  = batches of product p produced in week t
      I[p][t]  = ending inventory (batches) of product p after week t

    Constraints:
      Inventory balance:  I[p][t] = I[p][t-1] + x[p][t] - demand[p][t]
      Capacity:           sum_p x[p][t] <= max_batches_per_week
      Non-negativity:     x[p][t] >= 0,  I[p][t] >= 0

    Objective: minimize sum_pt [ prod_cost[p]*x[p][t] + hold_cost[p]*I[p][t] ]
    """
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    # Get current on-hand inventory (batches) and demand from work orders
    cur.execute("SELECT item_id, on_hand FROM items WHERE bom_level=0")
    start_inv = {r["item_id"]: float(r["on_hand"]) for r in cur.fetchall()}

    now = datetime.now()
    cur.execute("""
        SELECT product_id, due_date FROM work_orders
        WHERE status IN ('pending','released')
    """)
    demand: Dict[str, Dict[int, float]] = {}
    for wo in cur.fetchall():
        pid   = wo["product_id"]
        delta = (wo["due_date"] - now).days
        week  = max(1, min(horizon_weeks, math.ceil(delta / 7)))
        demand.setdefault(pid, {w: 0 for w in range(1, horizon_weeks + 1)})
        demand[pid][week] = demand[pid].get(week, 0) + 1

    products = ["INJ_A", "INJ_B", "INJ_C"]
    weeks    = list(range(1, horizon_weeks + 1))

    # Costs per batch
    prod_costs  = {"INJ_A": 52000, "INJ_B": 47000, "INJ_C": 41000}
    hold_costs  = {"INJ_A": 4000,  "INJ_B": 3800,  "INJ_C": 3200}

    # Ensure demand dict has all products/weeks
    for p in products:
        demand.setdefault(p, {})
        for t in weeks:
            demand[p].setdefault(t, 0)

    model = LpProblem("PharmaBatchPlan", LpMinimize)

    x = {(p, t): LpVariable(f"x_{p}_{t}", lowBound=0) for p in products for t in weeks}
    I = {(p, t): LpVariable(f"I_{p}_{t}", lowBound=0) for p in products for t in weeks}

    # Objective
    model += lpSum(
        prod_costs[p] * x[p, t] + hold_costs[p] * I[p, t]
        for p in products for t in weeks
    )

    # Inventory balance
    for p in products:
        for t in weeks:
            prev_inv = start_inv.get(p, 0) if t == 1 else I[p, t - 1]
            model += I[p, t] == prev_inv + x[p, t] - demand[p][t], f"InvBal_{p}_{t}"

    # Weekly capacity constraint
    for t in weeks:
        model += lpSum(x[p, t] for p in products) <= max_batches_per_week, f"Cap_{t}"

    model.solve(PULP_CBC_CMD(msg=0))

    status = LpStatus[model.status]
    obj    = value(model.objective) or 0.0

    plan: Dict[str, Dict] = {}
    for p in products:
        plan[p] = {}
        for t in weeks:
            plan[p][t] = {
                "produce": round(value(x[p, t]) or 0, 2),
                "inventory": round(value(I[p, t]) or 0, 2),
                "demand": demand[p][t],
            }

    return {"status": status, "total_cost": obj, "plan": plan,
            "products": products, "weeks": weeks,
            "prod_costs": prod_costs, "hold_costs": hold_costs,
            "max_cap": max_batches_per_week}


def print_production_plan(result: dict):
    sep = "─" * 72
    print(f"\n{sep}")
    print("OPTIMIZATION — PuLP Multi-Product Batch Production Plan")
    print(sep)
    print(f"\n  Solver status: {result['status']}")
    print(f"  Optimal total cost: ${result['total_cost']:,.0f}")
    print(f"  Planning horizon:   {len(result['weeks'])} weeks")
    print(f"  Capacity:           {result['max_cap']} batches/week")

    print(f"\n  {'Product':<14}", end="")
    for t in result["weeks"]:
        print(f"  {'Wk'+str(t):>12}", end="")
    print()
    print(f"  {'─'*14}", end="")
    for _ in result["weeks"]: print(f"  {'─'*12}", end="")
    print()

    for p in result["products"]:
        name = PRODUCT_NAMES.get(p, p)[:14]
        print(f"\n  {name:<14}", end="")
        for t in result["weeks"]:
            v = result["plan"][p][t]
            print(f"  {'p='+str(int(v['produce']))+'/d='+str(int(v['demand']))+'/I='+str(int(v['inventory'])):>12}", end="")
        print(f"    (p=produce, d=demand, I=inv)")
        break  # just print header notation once
    print()

    for p in result["products"]:
        print(f"  {PRODUCT_NAMES.get(p, p)[:14]:<14}", end="")
        for t in result["weeks"]:
            v = result["plan"][p][t]
            print(f"  prod={int(v['produce']):>2} inv={int(v['inventory']):>2}", end="")
        print()

    # Weekly capacity usage
    print(f"\n  Weekly totals (vs {result['max_cap']} max):")
    for t in result["weeks"]:
        total = sum(result["plan"][p][t]["produce"] for p in result["products"])
        bar = "█" * int(total / result["max_cap"] * 20)
        print(f"    Week {t}: {total:>5.1f} batches  [{bar:<20}]")


def save_plan_to_db(conn, result: dict):
    cur = conn.cursor()
    cur.execute("DELETE FROM mrp_plan WHERE status='optimized'")
    for p in result["products"]:
        for t in result["weeks"]:
            v = result["plan"][p][t]
            if v["produce"] > 0:
                cur.execute(
                    """INSERT INTO mrp_plan (item_id, period_week, quantity, status)
                       VALUES (%s, %s, %s, 'optimized')""",
                    (p, t, float(v["produce"])),
                )
    conn.commit()


# ── 4. Dispatch Queue ──────────────────────────────────────────────────────────

def build_dispatch_queue(conn, schedule: List[dict]):
    cur = conn.cursor()
    cur.execute("DELETE FROM dispatch_queue")
    for s in schedule:
        cur.execute(
            """INSERT INTO dispatch_queue
               (wo_id, work_center, priority, est_proc_min, due_date, status)
               VALUES (%s, %s, %s, %s, %s, 'waiting')""",
            (s["wo_id"], s["work_center"], 1,
             float(s["proc_min"]), s["due_date"]),
        )
    conn.commit()


# ── 5. End-to-End Data Flow Demo ───────────────────────────────────────────────

def demo_work_order_flow(conn):
    """
    Demonstrate the complete data flow:
    Work Order Entry → MRP Explosion → Scheduling → Optimization → Dispatch
    """
    sep = "=" * 72
    print(f"\n{sep}")
    print("PART 5 — FIRST PROTOTYPE: END-TO-END WORK ORDER FLOW DEMO")
    print(sep)

    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    # ── Step 1: Work Order Entry ───────────────────────────────────────────────
    print("\n  ┌─────────────────────────────────────────────────────────────┐")
    print("  │  STEP 1: Work Order Entry                                   │")
    print("  └─────────────────────────────────────────────────────────────┘")
    new_wo = {
        "wo_id":       "WO-DEMO-001",
        "product_id":  "INJ_A",
        "quantity":    10000,
        "due_date":    datetime.now() + timedelta(days=3),
        "release_date": datetime.now(),
        "priority":    1,
        "status":      "pending",
    }
    cur.execute("DELETE FROM schedule WHERE wo_id = 'WO-DEMO-001'")
    cur.execute("DELETE FROM dispatch_queue WHERE wo_id = 'WO-DEMO-001'")
    cur.execute("DELETE FROM batch_log WHERE wo_id = 'WO-DEMO-001'")
    cur.execute("DELETE FROM work_orders WHERE wo_id = 'WO-DEMO-001'")
    cur.execute(
        """INSERT INTO work_orders
           (wo_id, product_id, quantity, due_date, release_date, priority, status)
           VALUES (%(wo_id)s,%(product_id)s,%(quantity)s,%(due_date)s,
                   %(release_date)s,%(priority)s,%(status)s)""",
        new_wo,
    )
    conn.commit()

    print(f"\n  New Work Order Created:")
    print(f"    WO ID:    {new_wo['wo_id']}")
    print(f"    Product:  {PRODUCT_NAMES[new_wo['product_id']]} ({new_wo['product_id']})")
    print(f"    Quantity: {new_wo['quantity']:,} units (1 batch)")
    print(f"    Due Date: {new_wo['due_date'].strftime('%Y-%m-%d %H:%M')}")
    print(f"    Priority: {new_wo['priority']} (URGENT)")

    # ── Step 2: MRP Explosion ──────────────────────────────────────────────────
    print("\n  ┌─────────────────────────────────────────────────────────────┐")
    print("  │  STEP 2: MRP BOM Explosion                                  │")
    print("  └─────────────────────────────────────────────────────────────┘")

    # Show BOM tree for this product
    cur.execute("""
        SELECT b.child_id, i.name, b.qty_per, i.on_hand, i.unit,
               i.safety_stock, i.lead_time_wk
        FROM bom b JOIN items i ON b.child_id = i.item_id
        WHERE b.parent_id = %s
    """, (new_wo["product_id"],))
    bom_items = cur.fetchall()

    print(f"\n  BOM Explosion for {PRODUCT_NAMES[new_wo['product_id']]}:")
    print(f"  {'Component':<35}  {'Need':>8}  {'On-Hand':>8}  {'Net Req':>8}  {'Action'}")
    print(f"  {'─'*35}  {'─'*8}  {'─'*8}  {'─'*8}  {'─'*20}")
    for item in bom_items:
        need    = item["qty_per"] * 1  # 1 batch
        net_req = max(0, need - item["on_hand"])
        action  = "✓ Available" if net_req == 0 else f"⚠ Order {net_req:.1f} {item['unit']}"
        print(f"  {item['name'][:35]:<35}  {need:>8.1f}  "
              f"{item['on_hand']:>8.1f}  {net_req:>8.1f}  {action}")

    # Run full MRP
    print(f"\n  Running full MRP explosion (6-week horizon)…")
    orders = run_mrp_explosion(conn, horizon_weeks=6, verbose=False)
    n_past_due = sum(1 for o in orders if o["status"] == "past_due")
    n_planned  = sum(1 for o in orders if o["status"] == "planned")
    print(f"  MRP generated {len(orders)} planned orders "
          f"({n_planned} planned, {n_past_due} past-due alerts)")

    # ── Step 3: Scheduling ─────────────────────────────────────────────────────
    print("\n  ┌─────────────────────────────────────────────────────────────┐")
    print("  │  STEP 3: Work Order Scheduling                              │")
    print("  └─────────────────────────────────────────────────────────────┘")
    edd = edd_schedule(conn)
    spt = spt_schedule(conn)
    print_schedule_comparison(edd, spt)

    # Save EDD schedule (better for due-date compliance)
    save_schedule(conn, edd)
    print(f"\n  EDD schedule saved to schedule table ({len(edd)} work orders).")

    # ── Step 4: Optimization ───────────────────────────────────────────────────
    print("\n  ┌─────────────────────────────────────────────────────────────┐")
    print("  │  STEP 4: PuLP Batch Production Optimization                 │")
    print("  └─────────────────────────────────────────────────────────────┘")
    plan_result = pulp_production_plan(conn)
    print_production_plan(plan_result)
    save_plan_to_db(conn, plan_result)
    print(f"\n  Optimized plan saved to mrp_plan table (status='optimized').")

    # ── Step 5: Dispatch Queue ─────────────────────────────────────────────────
    print("\n  ┌─────────────────────────────────────────────────────────────┐")
    print("  │  STEP 5: Dispatch Queue                                     │")
    print("  └─────────────────────────────────────────────────────────────┘")
    build_dispatch_queue(conn, edd)

    cur.execute("""
        SELECT d.wo_id, d.work_center, d.est_proc_min, d.due_date, d.status,
               w.product_id
        FROM dispatch_queue d
        JOIN work_orders w ON d.wo_id = w.wo_id
        ORDER BY d.enqueued_at
    """)
    queue = cur.fetchall()

    print(f"\n  Filling Suite 1 — Dispatch Queue (EDD order):")
    print(f"  {'#':>2}  {'WO':>10}  {'Product':<12}  {'Proc(min)':>9}  {'Due':>16}  {'Status'}")
    print(f"  {'─'*2}  {'─'*10}  {'─'*12}  {'─'*9}  {'─'*16}  {'─'*10}")
    for i, q in enumerate(queue, 1):
        name = PRODUCT_NAMES.get(q["product_id"], q["product_id"])[:12]
        due  = q["due_date"].strftime("%Y-%m-%d %H:%M")
        print(f"  {i:>2}  {q['wo_id']:>10}  {name:<12}  "
              f"{q['est_proc_min']:>9.0f}  {due:>16}  {q['status']}")

    # ── Summary ────────────────────────────────────────────────────────────────
    print(f"\n{'─'*72}")
    print("  DATA FLOW SUMMARY")
    print(f"{'─'*72}")
    print(f"  1. Work Order → Created WO-DEMO-001 in work_orders table")
    print(f"  2. MRP        → Exploded BOM, {len(orders)} planned orders in mrp_plan")
    print(f"  3. Scheduling → EDD + SPT computed; EDD saved to schedule table")
    print(f"  4. Optimization → PuLP plan: ${plan_result['total_cost']:,.0f} total cost")
    print(f"  5. Dispatch   → {len(queue)} WOs queued at Filling Suite 1")
    print(f"\n  Prototype prototype demonstrates complete ISA-95 Level 3 data flow:")
    print(f"  Order Entry → MRP → Schedule → Optimize → Dispatch ✓")
    print()


# ── Main ───────────────────────────────────────────────────────────────────────

def run_mrp_and_schedule():
    conn = get_conn()
    try:
        demo_work_order_flow(conn)
    finally:
        conn.close()


if __name__ == "__main__":
    run_mrp_and_schedule()
