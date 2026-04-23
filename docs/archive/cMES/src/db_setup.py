"""
db_setup.py — Create and seed the Sheridan_573 PostgreSQL database.

Tables created:
  products, items, bom, work_orders, materials_inventory,
  schedule, mrp_plan, dispatch_queue, batch_log, events_log,
  simulation_results

Run once before any other module.
"""

import psycopg2
import psycopg2.extras
from datetime import datetime, timedelta

DB_CFG = dict(
    host="100.115.213.16", port=5432,
    dbname="Sheridan_573", user="twin_mes_db", password="postgres",
    connect_timeout=8,
)


def get_conn():
    return psycopg2.connect(**DB_CFG)


DDL = """
-- ── Products ──────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS products (
    product_id          TEXT PRIMARY KEY,
    name                TEXT NOT NULL,
    description         TEXT,
    target_units_batch  INTEGER DEFAULT 10000,
    fill_volume_ml      REAL DEFAULT 10.0,
    unit_cost_usd       REAL DEFAULT 45000
);

-- ── Items (finished goods, components, raw materials) ─────────────
CREATE TABLE IF NOT EXISTS items (
    item_id       TEXT PRIMARY KEY,
    name          TEXT NOT NULL,
    bom_level     INTEGER NOT NULL,   -- 0=finished, 1=component, 2=raw
    lead_time_wk  INTEGER DEFAULT 1,
    lot_rule      TEXT DEFAULT 'L4L', -- L4L or FOQ
    lot_size      INTEGER,
    safety_stock  REAL DEFAULT 0,
    on_hand       REAL DEFAULT 0,
    unit          TEXT DEFAULT 'unit'
);

-- ── Bill of Materials ──────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS bom (
    parent_id  TEXT REFERENCES items(item_id),
    child_id   TEXT REFERENCES items(item_id),
    qty_per    REAL NOT NULL,
    PRIMARY KEY (parent_id, child_id)
);

-- ── Work Orders ────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS work_orders (
    wo_id        TEXT PRIMARY KEY,
    product_id   TEXT REFERENCES products(product_id),
    quantity     INTEGER NOT NULL,
    due_date     TIMESTAMP NOT NULL,
    release_date TIMESTAMP,
    priority     INTEGER DEFAULT 5,  -- 1=highest
    status       TEXT DEFAULT 'pending',
    created_at   TIMESTAMP DEFAULT NOW()
);

-- ── Materials Inventory ────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS materials_inventory (
    inventory_id  SERIAL PRIMARY KEY,
    item_id       TEXT REFERENCES items(item_id),
    lot_number    TEXT,
    quantity      REAL NOT NULL,
    location      TEXT DEFAULT 'Warehouse-A',
    status        TEXT DEFAULT 'approved',   -- quarantine | approved | consumed
    received_date TIMESTAMP DEFAULT NOW()
);

-- ── Schedule (work center assignments) ────────────────────────────
CREATE TABLE IF NOT EXISTS schedule (
    schedule_id   SERIAL PRIMARY KEY,
    wo_id         TEXT REFERENCES work_orders(wo_id),
    work_center   TEXT NOT NULL,
    planned_start TIMESTAMP,
    planned_end   TIMESTAMP,
    actual_start  TIMESTAMP,
    actual_end    TIMESTAMP,
    algorithm     TEXT DEFAULT 'EDD',
    status        TEXT DEFAULT 'scheduled'
);

-- ── MRP Planned Orders ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS mrp_plan (
    plan_id       SERIAL PRIMARY KEY,
    item_id       TEXT REFERENCES items(item_id),
    period_week   INTEGER NOT NULL,
    release_week  INTEGER,
    quantity      REAL NOT NULL,
    status        TEXT DEFAULT 'planned',  -- planned | past_due | released
    created_at    TIMESTAMP DEFAULT NOW()
);

-- ── Dispatch Queue ─────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS dispatch_queue (
    queue_id    SERIAL PRIMARY KEY,
    wo_id       TEXT REFERENCES work_orders(wo_id),
    work_center TEXT NOT NULL,
    priority    INTEGER DEFAULT 5,
    est_proc_min REAL,
    due_date    TIMESTAMP,
    enqueued_at TIMESTAMP DEFAULT NOW(),
    status      TEXT DEFAULT 'waiting'
);

-- ── Batch Execution Log ────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS batch_log (
    batch_id     TEXT PRIMARY KEY,
    wo_id        TEXT REFERENCES work_orders(wo_id),
    product_id   TEXT REFERENCES products(product_id),
    start_time   TIMESTAMP,
    end_time     TIMESTAMP,
    target_units INTEGER,
    actual_units INTEGER,
    reject_count INTEGER DEFAULT 0,
    yield_pct    REAL,
    status       TEXT DEFAULT 'in_progress',
    deviations   TEXT DEFAULT ''
);

-- ── Events / Alarms Log ────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS events_log (
    event_id  SERIAL PRIMARY KEY,
    ts        TIMESTAMP DEFAULT NOW(),
    level     TEXT NOT NULL,   -- INFO | WARNING | ALARM
    source    TEXT,
    message   TEXT NOT NULL,
    batch_id  TEXT
);

-- ── Simulation Results ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS simulation_results (
    run_id             SERIAL PRIMARY KEY,
    scenario           TEXT NOT NULL,
    dispatch_rule      TEXT DEFAULT 'FIFO',
    seed               INTEGER,
    replication        INTEGER,
    mean_flow_time_min REAL,
    std_flow_time_min  REAL,
    mean_wip           REAL,
    throughput_per_hr  REAL,
    util_filling_pct   REAL,
    mean_queue_filling REAL,
    ci_low_flow        REAL,
    ci_high_flow       REAL,
    created_at         TIMESTAMP DEFAULT NOW()
);
"""

PRODUCTS = [
    ("INJ_A", "Injectable-A 100mg/mL",
     "Sterile injectable, 10 mL vials, 100 mg/mL concentration", 10000, 10.0, 52000),
    ("INJ_B", "Injectable-B 50mg/mL",
     "Sterile injectable, 10 mL vials, 50 mg/mL concentration",  10000, 10.0, 47000),
    ("INJ_C", "Injectable-C 25mg/mL",
     "Sterile injectable, 10 mL vials, 25 mg/mL concentration",  10000, 10.0, 41000),
]

# item_id, name, level, lead_time_wk, lot_rule, lot_size, safety_stock, on_hand, unit
ITEMS = [
    # Level 0 — finished products (make-to-order: no pre-stocked batches)
    ("INJ_A", "Injectable-A 100mg/mL", 0, 1, "L4L",  None,  0,  0, "batch"),
    ("INJ_B", "Injectable-B 50mg/mL",  0, 1, "L4L",  None,  0,  0, "batch"),
    ("INJ_C", "Injectable-C 25mg/mL",  0, 1, "L4L",  None,  0,  0, "batch"),
    # Level 1 — direct components (per batch)
    ("API_A",  "API-A (Active Ingredient A)",    1, 2, "FOQ", 5,   2, 8,    "kg"),
    ("API_B",  "API-B (Active Ingredient B)",    1, 2, "FOQ", 5,   2, 6,    "kg"),
    ("API_C",  "API-C (Active Ingredient C)",    1, 2, "FOQ", 5,   2, 10,   "kg"),
    ("WFI",    "Water for Injection",            1, 0, "L4L", None, 0, 9999, "kg"),  # utility
    ("VIAL10", "10 mL Glass Vials",              1, 1, "FOQ", 20000, 5000, 35000, "unit"),
    ("STOPPER","Rubber Stoppers 20mm",           1, 1, "FOQ", 25000, 5000, 40000, "unit"),
    ("ALUM",   "Aluminum Crimp Caps",            1, 1, "FOQ", 25000, 5000, 38000, "unit"),
    # Level 2 — raw materials for APIs
    ("RAW_A",  "API-A Raw Material",  2, 3, "FOQ", 20, 5, 25, "kg"),
    ("RAW_B",  "API-B Raw Material",  2, 3, "FOQ", 20, 5, 20, "kg"),
    ("RAW_C",  "API-C Raw Material",  2, 3, "FOQ", 20, 5, 30, "kg"),
    ("SOLV",   "Purified Solvent",    2, 2, "FOQ", 50, 10, 80, "kg"),
]

# parent, child, qty_per (per 1 batch of finished product)
BOM_ROWS = [
    ("INJ_A", "API_A",  0.12),   # 0.12 kg API per batch
    ("INJ_A", "WFI",   50.0),    # 50 kg WFI per batch
    ("INJ_A", "VIAL10", 10200),  # 10,200 vials (includes 2% overfill)
    ("INJ_A", "STOPPER",10500),
    ("INJ_A", "ALUM",   10500),
    ("INJ_B", "API_B",  0.06),
    ("INJ_B", "WFI",   50.0),
    ("INJ_B", "VIAL10", 10200),
    ("INJ_B", "STOPPER",10500),
    ("INJ_B", "ALUM",   10500),
    ("INJ_C", "API_C",  0.03),
    ("INJ_C", "WFI",   50.0),
    ("INJ_C", "VIAL10", 10200),
    ("INJ_C", "STOPPER",10500),
    ("INJ_C", "ALUM",   10500),
    # Level 2: raw materials for each API
    ("API_A", "RAW_A", 1.15),    # 1.15 kg raw per 1 kg API (15% process loss)
    ("API_A", "SOLV",  0.5),
    ("API_B", "RAW_B", 1.15),
    ("API_B", "SOLV",  0.5),
    ("API_C", "RAW_C", 1.15),
    ("API_C", "SOLV",  0.5),
]

now = datetime.now()

WORK_ORDERS = [
    ("WO-001", "INJ_A", 10000, now + timedelta(days=2),  now,              1, "released"),
    ("WO-002", "INJ_B", 10000, now + timedelta(days=3),  now,              2, "released"),
    ("WO-003", "INJ_C", 10000, now + timedelta(days=4),  now,              3, "pending"),
    ("WO-004", "INJ_A", 10000, now + timedelta(days=5),  now,              2, "pending"),
    ("WO-005", "INJ_B", 10000, now + timedelta(days=6),  now + timedelta(days=1), 3, "pending"),
    ("WO-006", "INJ_C", 10000, now + timedelta(days=8),  now + timedelta(days=2), 1, "pending"),
    ("WO-007", "INJ_A", 10000, now + timedelta(days=10), now + timedelta(days=3), 2, "pending"),
    ("WO-008", "INJ_B", 10000, now + timedelta(days=12), now + timedelta(days=4), 3, "pending"),
]

MATERIALS_INVENTORY = [
    ("API_A",  "API-A-LOT-2601", 8.0,   "Cold-Storage-1",  "approved"),
    ("API_B",  "API-B-LOT-2602", 6.0,   "Cold-Storage-1",  "approved"),
    ("API_C",  "API-C-LOT-2603", 10.0,  "Cold-Storage-2",  "approved"),
    ("WFI",    "WFI-LOOP-LIVE",  9999.0,"WFI-Loop",        "approved"),
    ("VIAL10", "VIAL-LOT-5501",  35000, "Warehouse-A",     "approved"),
    ("STOPPER","STOP-LOT-4401",  40000, "Warehouse-A",     "approved"),
    ("ALUM",   "ALUM-LOT-3301",  38000, "Warehouse-A",     "approved"),
    ("RAW_A",  "RAWA-LOT-1001",  25.0,  "Warehouse-B",     "quarantine"),
    ("RAW_B",  "RAWB-LOT-1002",  20.0,  "Warehouse-B",     "approved"),
    ("RAW_C",  "RAWC-LOT-1003",  30.0,  "Warehouse-B",     "approved"),
    ("SOLV",   "SOLV-LOT-0901",  80.0,  "Chemical-Store",  "approved"),
]


def setup_database():
    print("=" * 60)
    print("Sheridan_573 — Database Setup")
    print("=" * 60)

    conn = get_conn()
    cur = conn.cursor()

    # Drop operational tables for a clean reset.
    # simulation_results is preserved — the full DES run takes ~3 minutes and
    # those results should survive re-runs that skip the simulation step.
    drop_order = [
        "events_log", "batch_log", "dispatch_queue",
        "mrp_plan", "schedule", "materials_inventory", "work_orders",
        "bom", "items", "products",
    ]
    for tbl in drop_order:
        cur.execute(f"DROP TABLE IF EXISTS {tbl} CASCADE")
    conn.commit()
    print("  Dropped operational tables (simulation_results preserved).")

    # Create tables
    cur.execute(DDL)
    conn.commit()
    print("  Created all tables.")

    # Products
    cur.executemany(
        "INSERT INTO products VALUES (%s,%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING",
        PRODUCTS,
    )

    # Items
    cur.executemany(
        "INSERT INTO items VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING",
        ITEMS,
    )

    # BOM
    cur.executemany(
        "INSERT INTO bom VALUES (%s,%s,%s) ON CONFLICT DO NOTHING",
        BOM_ROWS,
    )

    # Work orders
    cur.executemany(
        "INSERT INTO work_orders(wo_id,product_id,quantity,due_date,release_date,priority,status) "
        "VALUES (%s,%s,%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING",
        WORK_ORDERS,
    )

    # Materials inventory
    cur.executemany(
        "INSERT INTO materials_inventory(item_id,lot_number,quantity,location,status) "
        "VALUES (%s,%s,%s,%s,%s)",
        MATERIALS_INVENTORY,
    )

    conn.commit()
    conn.close()

    print(f"  Seeded: {len(PRODUCTS)} products, {len(ITEMS)} items, {len(BOM_ROWS)} BOM rows")
    print(f"          {len(WORK_ORDERS)} work orders, {len(MATERIALS_INVENTORY)} inventory lots")
    print("\nDatabase setup complete.")


if __name__ == "__main__":
    setup_database()
