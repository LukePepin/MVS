"""
week9_helper.py
===============
ISE 573 -- Manufacturing Execution Systems
Week 9: Consequences of Breakdowns -- Helper Functions

Two main functions, referenced from the lecture slides:

    compute_breakdown_impact(event_id, conn, ...)
        Joins DowntimeEvents -> Equipment -> JobAssignments -> SchedulingJobs.
        Runs the Kingman analysis for a single breakdown event.
        Returns a dict with queueing metrics and dollar impact.

    compute_buffer_size(upstream_id, conn, lam, ...)
        Queries Equipment for MTBF/MTTR/mu.
        Computes B_min and B* for the downstream buffer.
        Creates the Buffers table if needed, then upserts the result.
        Returns a dict with all sizing quantities.

    setup_schema(conn)
        Creates all required tables if they do not exist.
        Safe to call every time -- uses CREATE TABLE IF NOT EXISTS.

USAGE
-----
    import sqlite3
    from week9_helper import setup_schema, compute_breakdown_impact, compute_buffer_size

    conn = sqlite3.connect('scheduling.db')
    conn.row_factory = sqlite3.Row
    setup_schema(conn)

    # Analyse one breakdown event
    impact = compute_breakdown_impact(event_id=47, conn=conn, lam=8.0)
    print(impact)

    # Size the buffer downstream of M01
    buf = compute_buffer_size('M01', conn, lam=8.0)
    print(buf)

Dr. Manbir Sodhi -- University of Rhode Island -- Spring 2026
"""

import math
import sqlite3
import datetime
from typing import Optional


# ══════════════════════════════════════════════════════════════════════════
#  Section 1 -- Schema DDL
#  All tables needed for Week 9.  Call setup_schema(conn) once at startup.
# ══════════════════════════════════════════════════════════════════════════

_DDL = """
-- Core equipment table (extended for Week 9)
CREATE TABLE IF NOT EXISTS Equipment (
    equipment_id   TEXT PRIMARY KEY,
    name           TEXT,
    mu_nominal     REAL NOT NULL,      -- service rate  (jobs / hr)
    tp_min         REAL,               -- mean processing time (min)
    MTBF_min       REAL,               -- mean time between failures (min)
    MTTR_avg_min   REAL,               -- mean time to repair (min)
    shift_min      REAL DEFAULT 480.0, -- planned shift duration (min)
    state          TEXT DEFAULT 'UP',  -- UP / DOWN / PM
    A_rolling_8hr  REAL,               -- rolling 8-hr availability
    rho_eff_now    REAL                -- current effective utilisation
);

-- Downtime event log (one row per failure event)
CREATE TABLE IF NOT EXISTS DowntimeEvents (
    event_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    equipment_id   TEXT    NOT NULL REFERENCES Equipment(equipment_id),
    start_time     TEXT    NOT NULL,   -- ISO-8601
    end_time       TEXT,
    duration_min   REAL    NOT NULL,
    reason_code    TEXT,
    loss_category  TEXT    DEFAULT 'Breakdown'
);

-- Job master
CREATE TABLE IF NOT EXISTS SchedulingJobs (
    job_id         TEXT PRIMARY KEY,
    due_date       TEXT,
    priority       INTEGER DEFAULT 3,
    penalty_per_hr REAL    DEFAULT 0.0,
    margin_per_job REAL    DEFAULT 50.0
);

-- Job-machine assignments
CREATE TABLE IF NOT EXISTS JobAssignments (
    assignment_id  INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id         TEXT NOT NULL REFERENCES SchedulingJobs(job_id),
    machine_id     TEXT NOT NULL REFERENCES Equipment(equipment_id),
    start_time     TEXT NOT NULL,
    end_time       TEXT
);

-- Buffer inventory between stations
CREATE TABLE IF NOT EXISTS Buffers (
    buffer_id               INTEGER PRIMARY KEY AUTOINCREMENT,
    upstream_id             TEXT NOT NULL REFERENCES Equipment(equipment_id),
    downstream_id           TEXT,                  -- NULL for B_in (no upstream machine)
    label                   TEXT,                  -- e.g. 'B_in', 'B_12', 'B_23'
    capacity                INTEGER NOT NULL DEFAULT 0,
    current_wip             INTEGER DEFAULT 0,
    B_min                   INTEGER,
    B_star                  INTEGER,
    holding_cost_per_job_hr REAL    DEFAULT 0.0,
    last_computed           TEXT,
    UNIQUE(upstream_id, downstream_id)
);

-- Breakdown cost log (one row per compute_breakdown_impact() call)
CREATE TABLE IF NOT EXISTS BreakdownCostLog (
    log_id                INTEGER PRIMARY KEY AUTOINCREMENT,
    run_date              TEXT,
    event_id              INTEGER REFERENCES DowntimeEvents(event_id),
    equipment_id          TEXT,
    duration_min          REAL,
    A_shift               REAL,
    rho_eff               REAL,
    Cs2_eff               REAL,
    Wq_base_hr            REAL,
    Wq_bkdn_hr            REAL,
    delta_Wq_min          REAL,
    jobs_affected_count   INTEGER,
    total_penalty_cost    REAL,
    total_throughput_loss REAL,
    total_event_cost      REAL
);

-- DES simulation results
CREATE TABLE IF NOT EXISTS BreakdownSimResults (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    run_date     TEXT,
    scenario     TEXT,
    label        TEXT,
    Wq_sim_min   REAL,
    Wq_pred_min  REAL,
    A_sim        REAL,
    Cs2_eff      REAL,
    breakdowns   INTEGER,
    params_json  TEXT
);
"""


def setup_schema(conn: sqlite3.Connection) -> None:
    """
    Create all ISE 573 Week 9 tables if they do not already exist.
    Safe to call every time the application starts.
    """
    conn.executescript(_DDL)
    conn.commit()
    print("schema ready -- all tables created or already present")


# ══════════════════════════════════════════════════════════════════════════
#  Section 2 -- Internal helpers
# ══════════════════════════════════════════════════════════════════════════

def _kingman_wq(rho: float, Ca2: float, Cs2: float, mu_rate: float) -> float:
    """Kingman G/G/1 mean queue wait (hours). Caps rho at 0.999."""
    rho = min(rho, 0.999)
    return (rho / (1.0 - rho)) * ((Ca2 + Cs2) / 2.0) / mu_rate


def _infer_lam(equipment_id: str, ref_time: str,
               conn: sqlite3.Connection,
               window_hr: float = 4.0) -> float:
    """
    Estimate arrival rate from JobAssignments in the window before ref_time.
    Falls back to mu * 0.80 (rho = 0.80) if no records found.
    """
    sql = """
        SELECT COUNT(*) AS n
        FROM   JobAssignments
        WHERE  machine_id = :mid
          AND  start_time BETWEEN
               datetime(:t0, :back) AND :t0
    """
    row = conn.execute(sql, {
        'mid' : equipment_id,
        't0'  : ref_time,
        'back': f'-{int(window_hr * 60)} minutes'
    }).fetchone()

    n = row[0] if row else 0
    if n > 0 and window_hr > 0:
        return n / window_hr
    # fallback: use nominal rho = 0.80
    eq = conn.execute(
        "SELECT mu_nominal FROM Equipment WHERE equipment_id = ?",
        (equipment_id,)
    ).fetchone()
    return (eq['mu_nominal'] if eq else 10.0) * 0.80


def _margin_per_job(conn: sqlite3.Connection) -> float:
    """Average margin per job from SchedulingJobs. Falls back to 50.0."""
    row = conn.execute(
        "SELECT AVG(margin_per_job) AS m FROM SchedulingJobs"
    ).fetchone()
    return float(row['m']) if (row and row['m']) else 50.0


# ══════════════════════════════════════════════════════════════════════════
#  Section 3 -- compute_breakdown_impact()
# ══════════════════════════════════════════════════════════════════════════

def compute_breakdown_impact(
    event_id:          int,
    conn:              sqlite3.Connection,
    Ca2:               float = 1.0,
    lam:               Optional[float] = None,
    penalty_col:       str   = 'penalty_per_hr',
    window_before_min: float = 120.0,
    window_after_min:  float = 240.0,
    save_to_log:       bool  = True,
) -> dict:
    """
    Estimate the queueing and financial impact of a single breakdown event.

    Joins DowntimeEvents -> Equipment -> JobAssignments -> SchedulingJobs.
    Runs the Kingman G/G/1 analysis for both baseline and breakdown conditions.

    Parameters
    ----------
    event_id            Primary key in DowntimeEvents.
    conn                Open sqlite3 connection to scheduling.db.
    Ca2                 Squared CV of inter-arrivals (default 1.0 = Poisson).
    lam                 Arrival rate (jobs/hr). Inferred from JobAssignments
                        if None.
    penalty_col         Column in SchedulingJobs holding $/hr late penalty.
    window_before_min   How far before breakdown start to search for jobs.
    window_after_min    How far after breakdown start to search for jobs.
    save_to_log         Write result row to BreakdownCostLog if True.

    Returns
    -------
    dict with keys:
        event_id, equipment_id, duration_min,
        A_shift, mu_eff, rho_eff, Cs2_eff,
        Wq_base_hr, Wq_bkdn_hr, delta_Wq_min,
        jobs_affected  (list of dicts),
        total_penalty_cost, total_throughput_loss, total_event_cost
    """
    conn.row_factory = sqlite3.Row

    # -- Step 1: pull event + machine parameters ---------------------------
    row = conn.execute("""
        SELECT d.event_id, d.equipment_id, d.duration_min, d.start_time,
               e.mu_nominal, e.MTBF_min, e.MTTR_avg_min,
               e.tp_min,     e.shift_min
        FROM   DowntimeEvents d
        JOIN   Equipment      e ON d.equipment_id = e.equipment_id
        WHERE  d.event_id = ?
    """, (event_id,)).fetchone()

    if row is None:
        raise ValueError(f"event_id {event_id} not found in DowntimeEvents")

    mu        = row['mu_nominal']
    MTBF      = row['MTBF_min']
    MTTR      = row['MTTR_avg_min']
    tp        = row['tp_min'] or (60.0 / mu)   # fallback if NULL
    shift_min = row['shift_min'] or 480.0
    dur       = row['duration_min']

    # -- Step 2: queueing parameters ---------------------------------------
    A_shift  = max((shift_min - dur) / shift_min, 0.001)
    mu_eff   = mu * A_shift
    Cs2_nom  = 1.0
    A_hist   = MTBF / (MTBF + MTTR) if (MTBF and MTTR) else A_shift
    Cs2_eff  = Cs2_nom + A_hist * (1.0 - A_hist) * (MTTR / tp) ** 2

    if lam is None:
        lam = _infer_lam(row['equipment_id'], row['start_time'], conn)

    rho_base = lam / mu
    rho_eff  = min(lam / mu_eff, 0.999)

    # -- Step 3: Kingman Wq predictions ------------------------------------
    Wq_base     = _kingman_wq(rho_base, Ca2, Cs2_nom, mu)
    Wq_bkdn     = _kingman_wq(rho_eff,  Ca2, Cs2_eff, mu_eff)
    delta_Wq    = (Wq_bkdn - Wq_base) * 60.0          # hr -> min

    # -- Step 4: query affected jobs ---------------------------------------
    sql_jobs = f"""
        SELECT ja.job_id, sj.due_date, sj.priority,
               sj.{penalty_col} AS penalty_per_hr,
               ja.start_time    AS sched_start
        FROM   JobAssignments ja
        JOIN   SchedulingJobs sj ON ja.job_id = sj.job_id
        WHERE  ja.machine_id = :mid
          AND  ja.start_time BETWEEN
               datetime(:t0, '-{int(window_before_min)} minutes') AND
               datetime(:t0, '+{int(window_after_min)} minutes')
        ORDER  BY sj.priority ASC
    """
    jobs = conn.execute(sql_jobs, {
        'mid': row['equipment_id'],
        't0' : row['start_time']
    }).fetchall()

    # -- Step 5: cost roll-up ----------------------------------------------
    jobs_out       = []
    total_penalty  = 0.0
    for j in jobs:
        late_hr   = delta_Wq / 60.0
        pen_cost  = late_hr * (j['penalty_per_hr'] or 0.0)
        total_penalty += pen_cost
        jobs_out.append({
            'job_id'      : j['job_id'],
            'due_date'    : j['due_date'],
            'priority'    : j['priority'],
            'delta_Wq_min': round(delta_Wq, 1),
            'penalty_cost': round(pen_cost, 2),
        })

    throughput_loss = (dur / 60.0) * mu * _margin_per_job(conn)
    total_cost      = total_penalty + throughput_loss

    result = {
        'event_id'             : event_id,
        'equipment_id'         : row['equipment_id'],
        'duration_min'         : round(dur,            1),
        'A_shift'              : round(A_shift,         4),
        'mu_eff'               : round(mu_eff,          4),
        'rho_eff'              : round(rho_eff,         4),
        'Cs2_eff'              : round(Cs2_eff,         4),
        'Wq_base_hr'           : round(Wq_base,         4),
        'Wq_bkdn_hr'           : round(Wq_bkdn,         4),
        'delta_Wq_min'         : round(delta_Wq,        2),
        'jobs_affected'        : jobs_out,
        'total_penalty_cost'   : round(total_penalty,   2),
        'total_throughput_loss': round(throughput_loss, 2),
        'total_event_cost'     : round(total_cost,      2),
    }

    # -- Step 6: persist to BreakdownCostLog (optional) -------------------
    if save_to_log:
        conn.execute("""
            INSERT INTO BreakdownCostLog
              (run_date, event_id, equipment_id, duration_min,
               A_shift, rho_eff, Cs2_eff,
               Wq_base_hr, Wq_bkdn_hr, delta_Wq_min,
               jobs_affected_count,
               total_penalty_cost, total_throughput_loss, total_event_cost)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            datetime.date.today().isoformat(),
            event_id, row['equipment_id'], dur,
            result['A_shift'], result['rho_eff'], result['Cs2_eff'],
            result['Wq_base_hr'], result['Wq_bkdn_hr'], result['delta_Wq_min'],
            len(jobs_out),
            result['total_penalty_cost'],
            result['total_throughput_loss'],
            result['total_event_cost'],
        ))
        conn.commit()

    return result


# ══════════════════════════════════════════════════════════════════════════
#  Section 4 -- compute_buffer_size()
# ══════════════════════════════════════════════════════════════════════════

def compute_buffer_size(
    upstream_id:    str,
    conn:           sqlite3.Connection,
    lam:            float,
    downstream_id:  Optional[str]   = None,
    label:          Optional[str]   = None,
    service_level:  float           = 0.95,
    holding_cost:   float           = 0.0,
    update_table:   bool            = True,
) -> dict:
    """
    Compute the optimal buffer size B* for the buffer immediately
    downstream of upstream_id.

    Also handles B_in (the input buffer upstream of the first machine):
    pass upstream_id = 'SOURCE' and downstream_id = first machine id,
    or set label = 'B_in'.

    Parameters
    ----------
    upstream_id     Equipment.equipment_id of the upstream machine.
                    Use 'SOURCE' for the arrival-stream buffer B_in.
    conn            Open sqlite3 connection to scheduling.db.
    lam             External arrival rate (jobs/hr).
    downstream_id   Equipment.equipment_id of the downstream machine.
    label           Human-readable label e.g. 'B_in', 'B_12', 'B_23'.
    service_level   Target service level for safety stock (0.90/0.95/0.99).
    holding_cost    Holding cost per job per hour (for reporting).
    update_table    Write / update the Buffers row if True.

    Returns
    -------
    dict with keys:
        A, mu_eff, rho_eff, Cs2_eff,
        Wq_bkdn_min, Lq_bkdn, t_drain_hr,
        B_min, B_star
    """
    conn.row_factory = sqlite3.Row
    z_map = {0.90: 1.28, 0.95: 1.65, 0.99: 2.33}
    z = z_map.get(service_level, 1.65)

    # For B_in (input buffer before first machine), use downstream machine's
    # parameters -- it is the downstream station that is protected.
    query_id = downstream_id if upstream_id == 'SOURCE' else upstream_id

    row = conn.execute("""
        SELECT mu_nominal, MTBF_min, MTTR_avg_min, tp_min
        FROM   Equipment
        WHERE  equipment_id = ?
    """, (query_id,)).fetchone()

    if row is None:
        raise ValueError(f"equipment_id '{query_id}' not found in Equipment")

    mu   = row['mu_nominal']
    MTTR = row['MTTR_avg_min'] / 60.0      # min -> hr
    MTBF = row['MTBF_min']    / 60.0       # min -> hr
    tp   = (row['tp_min'] or 60.0 / mu) / 60.0

    # Kingman effective parameters
    A       = MTBF / (MTBF + MTTR)
    mu_eff  = mu * A
    rho_eff = min(lam / mu_eff, 0.999)
    Cs2_eff = 1.0 + A * (1.0 - A) * (MTTR / tp) ** 2

    # Queue length and drain during a repair
    Wq_bkdn = _kingman_wq(rho_eff, 1.0, Cs2_eff, mu_eff)   # Ca2 = 1 (Poisson)
    Lq_bkdn = lam * Wq_bkdn
    drain   = mu - lam
    t_drain = (Lq_bkdn / drain) if drain > 0 else float('inf')

    # Buffer sizing formulas
    B_min  = math.ceil(lam * MTTR)
    safety = math.ceil(z * math.sqrt(max(B_min, 1)))
    B_star = B_min + safety

    result = {
        'A'           : round(A,        4),
        'mu_eff'      : round(mu_eff,   4),
        'rho_eff'     : round(rho_eff,  4),
        'Cs2_eff'     : round(Cs2_eff,  4),
        'Wq_bkdn_min' : round(Wq_bkdn * 60, 1),
        'Lq_bkdn'     : round(Lq_bkdn, 2),
        't_drain_hr'  : round(t_drain,  2),
        'B_min'       : B_min,
        'B_star'      : B_star,
    }

    # -- Upsert into Buffers table ----------------------------------------
    if update_table:
        lbl = label or (
            'B_in' if upstream_id == 'SOURCE'
            else f'B_{upstream_id}_{downstream_id or "out"}'
        )
        # Use INSERT OR REPLACE so we can call this repeatedly
        conn.execute("""
            INSERT INTO Buffers
              (upstream_id, downstream_id, label,
               capacity, B_min, B_star,
               holding_cost_per_job_hr, last_computed)
            VALUES (?,?,?,?,?,?,?,date('now'))
            ON CONFLICT(upstream_id, downstream_id)
            DO UPDATE SET
               capacity                = excluded.capacity,
               B_min                  = excluded.B_min,
               B_star                 = excluded.B_star,
               holding_cost_per_job_hr= excluded.holding_cost_per_job_hr,
               last_computed          = excluded.last_computed
        """, (
            upstream_id, downstream_id or '', lbl,
            B_star, B_min, B_star,
            holding_cost,
        ))
        conn.commit()
        result['label']    = lbl
        result['saved_to'] = 'Buffers'

    return result


# ══════════════════════════════════════════════════════════════════════════
#  Section 5 -- Size all three reference-line buffers at once
# ══════════════════════════════════════════════════════════════════════════

def size_all_buffers(conn: sqlite3.Connection, lam: float = 8.0,
                     service_level: float = 0.95) -> list:
    """
    Convenience wrapper: compute and save B* for all three buffers in the
    reference line (B_in, B_12, B_23) in one call.

    Returns a list of three result dicts.
    """
    buffers = [
        # B_in: arrival stream -> M01  (protects M01 input during arrival burst)
        dict(upstream_id='SOURCE', downstream_id='M01', label='B_in'),
        # B_12: M01 -> M02
        dict(upstream_id='M01',    downstream_id='M02', label='B_12'),
        # B_23: M02 -> M03
        dict(upstream_id='M02',    downstream_id='M03', label='B_23'),
    ]
    results = []
    for b in buffers:
        r = compute_buffer_size(
            conn           = conn,
            lam            = lam,
            service_level  = service_level,
            update_table   = True,
            **b
        )
        results.append(r)
        print(f"  {b['label']}: B_min={r['B_min']}  B*={r['B_star']}"
              f"  t_drain={r['t_drain_hr']}hr")
    return results


# ══════════════════════════════════════════════════════════════════════════
#  Section 6 -- Kingman chain (used by worksheet Task 3)
# ══════════════════════════════════════════════════════════════════════════

def kingman_chain(stations: list, lam: float, Ca2_in: float = 1.0) -> list:
    """
    Propagate the Kingman G/G/1 analysis through a serial line.

    Parameters
    ----------
    stations   list of dicts, each with keys:
                   mu          service rate (jobs/hr)
                   mtbf_hr     mean time between failures (hr)
                   mttr_hr     mean time to repair (hr)
                   Cs2_nom     nominal squared CV of service time
    lam        external arrival rate (jobs/hr)
    Ca2_in     squared CV of the arrival stream (default 1.0 = Poisson)

    Returns
    -------
    list of dicts, one per station, with:
        A, mu_eff, rho_eff, Cs2_eff, Wq_pred_min, Cd2
    """
    results = []
    for stn in stations:
        mu   = stn['mu']
        tp   = 1.0 / mu
        mtbf = stn.get('mtbf_hr', 1e9)
        mttr = stn.get('mttr_hr', 0.0)

        A       = mtbf / (mtbf + mttr) if (mtbf and mttr) else 1.0
        mu_eff  = mu * A
        Cs2_nom = stn.get('Cs2_nom', 1.0)
        Cs2_eff = Cs2_nom + A * (1.0 - A) * (mttr / tp) ** 2

        rho_eff = min(lam / mu_eff, 0.9999) if mu_eff > 0 else 0.9999
        Wq_hr   = _kingman_wq(rho_eff, Ca2_in, Cs2_eff, mu_eff)
        Cd2     = (1.0 - rho_eff**2) * Ca2_in + rho_eff**2 * Cs2_eff

        results.append({
            'A'           : round(A,            4),
            'mu_eff'      : round(mu_eff,        4),
            'rho_eff'     : round(rho_eff,       4),
            'Cs2_eff'     : round(Cs2_eff,       4),
            'Wq_pred_min' : round(Wq_hr * 60,    2),
            'Cd2'         : round(Cd2,            4),
        })
        Ca2_in = Cd2    # Departure Theorem: Cd2 becomes next Ca2_in
    return results


# ══════════════════════════════════════════════════════════════════════════
#  Quick demo (run this file directly to verify)
# ══════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    import pprint

    # -- in-memory DB for demo --
    conn = sqlite3.connect(':memory:')
    conn.row_factory = sqlite3.Row
    setup_schema(conn)

    # Seed reference line equipment
    conn.executemany("""
        INSERT INTO Equipment
          (equipment_id, name, mu_nominal, tp_min, MTBF_min, MTTR_avg_min, shift_min)
        VALUES (?,?,?,?,?,?,?)
    """, [
        ('M01', 'CNC Lathe Alpha',   10, 6, 200*60, 45, 480),
        ('M02', 'CNC Lathe Beta',    10, 6, 180*60, 45, 480),
        ('M03', 'Surface Grinder',   10, 6, 300*60, 30, 480),
    ])
    conn.commit()

    print("\n=== Kingman chain (reference line, no breakdown) ===")
    line = [
        dict(mu=10, mtbf_hr=200, mttr_hr=45/60, Cs2_nom=1.0),
        dict(mu=10, mtbf_hr=180, mttr_hr=45/60, Cs2_nom=1.0),
        dict(mu=10, mtbf_hr=300, mttr_hr=30/60, Cs2_nom=1.0),
    ]
    for i, r in enumerate(kingman_chain(line, lam=8.0)):
        print(f"  M0{i+1}: {r}")

    print("\n=== Buffer sizing for all three buffers ===")
    size_all_buffers(conn, lam=8.0)

    print("\n=== Buffers table ===")
    for row in conn.execute("SELECT * FROM Buffers"):
        pprint.pprint(dict(row))


# ══════════════════════════════════════════════════════════════════════════
#  Section 7 -- CSV output functions  (no database required)
# ══════════════════════════════════════════════════════════════════════════

import csv
import os


def save_results_csv(sim_result: dict, scenario: str,
                     csv_path: str = 'des_results.csv') -> None:
    """
    Append DES simulation results to a CSV file --- one row per station.

    Parameters
    ----------
    sim_result  dict returned by run_serial_des() from des_tkinter.py
    scenario    short label e.g. 'exp1_baseline', 'exp2_cascade'
    csv_path    path to CSV file (created if absent, appended if present)

    CSV columns
    -----------
    scenario, station, Wq_min, A, Ca2_arriving, Cd2, breakdowns, n_samples

    Usage
    -----
        from des_tkinter import run_serial_des
        from week9_helper import save_results_csv

        r = run_serial_des(n_stn=3, lam=8, mu=10, Ca2=1.0,
                           Cs2_nom=1.0, brk_stn=-1,
                           mtbf=3.0, mttr=0.5, n_jobs=2000, seed=42)
        save_results_csv(r, 'exp1_baseline', 'des_results.csv')
    """
    import datetime

    fieldnames = ['run_date', 'scenario', 'station',
                  'Wq_min', 'A', 'Ca2_arriving', 'Cd2',
                  'breakdowns', 'n_samples']

    file_exists = os.path.isfile(csv_path)
    with open(csv_path, 'a', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        today = datetime.date.today().isoformat()
        stations = sim_result.get('stations',
                   # des_tkinter.py returns flat lists
                   [{'i': i,
                     'Wq_min':       sim_result['Wq_sim'][i] * 60,
                     'A':            sim_result['A_sim'][i],
                     'Ca2_arriving': sim_result['Ca2_arriving'][i],
                     'Cd2':          sim_result['Cd2_dep'][i],
                     'bk_count':     sim_result['bk_count'][i],
                     'n':            sim_result['n_collected'][i],
                    }
                    for i in range(len(sim_result['Wq_sim']))])
        for s in stations:
            i = s.get('i', s.get('station', 0))
            writer.writerow({
                'run_date':     today,
                'scenario':     scenario,
                'station':      f'Stn{i+1}',
                'Wq_min':       round(s.get('Wq_min',
                                 s.get('Wq_sim_min', float('nan'))), 2),
                'A':            round(s.get('A',
                                 s.get('A_sim', 1.0)), 4),
                'Ca2_arriving': round(s.get('Ca2_arriving',
                                 s.get('Ca2_in', float('nan'))), 4),
                'Cd2':          round(s.get('Cd2',
                                 s.get('Cd2_dep', float('nan'))), 4),
                'breakdowns':   s.get('bk_count', s.get('breakdowns', 0)),
                'n_samples':    s.get('n', s.get('n_collected', 0)),
            })
    print(f"  Saved {scenario} -> {csv_path}")


def load_equipment_defaults() -> list:
    """
    Return the ISE 573 reference line equipment parameters as a list of dicts.
    No file needed --- these are the Week 9 defaults.

    Returns
    -------
    list of dicts, one per station, with keys:
        equipment_id, name, mu, mtbf_hr, mttr_hr, tp_hr
    """
    return [
        dict(equipment_id='M01', name='CNC Lathe Alpha',
             mu=10.0, mtbf_hr=200.0, mttr_hr=45/60, tp_hr=1/10),
        dict(equipment_id='M02', name='CNC Lathe Beta',
             mu=10.0, mtbf_hr=180.0, mttr_hr=45/60, tp_hr=1/10),
        dict(equipment_id='M03', name='Surface Grinder',
             mu=10.0, mtbf_hr=300.0, mttr_hr=30/60, tp_hr=1/10),
    ]


def size_all_buffers_csv(
    equipment:     list,
    lam:           float = 8.0,
    service_level: float = 0.95,
    csv_path:      str   = 'buffers.csv',
) -> list:
    """
    Compute B* for all inter-station buffers and write to a CSV file.

    Buffers sized:
        B_in  : upstream of first machine  (SOURCE -> equipment[0])
        B_12  : between machine 0 and 1   (equipment[0] -> equipment[1])
        B_23  : between machine 1 and 2   (equipment[1] -> equipment[2])
        (and so on for longer lines)

    Parameters
    ----------
    equipment      list of dicts from load_equipment_defaults() or similar
    lam            arrival rate (jobs/hr)
    service_level  0.90 / 0.95 / 0.99
    csv_path       output CSV path (overwritten each call)

    Returns
    -------
    list of result dicts (one per buffer)
    """
    z_map = {0.90: 1.28, 0.95: 1.65, 0.99: 2.33}
    z = z_map.get(service_level, 1.65)

    def _size(eq):
        mu   = eq['mu']
        MTTR = eq['mttr_hr']
        MTBF = eq['mtbf_hr']
        tp   = eq['tp_hr']
        A       = MTBF / (MTBF + MTTR)
        mu_eff  = mu * A
        rho_eff = min(lam / mu_eff, 0.999)
        Cs2_eff = 1.0 + A * (1 - A) * (MTTR / tp) ** 2
        Wq_bkdn = _kingman_wq(rho_eff, 1.0, Cs2_eff, mu_eff)
        Lq      = lam * Wq_bkdn
        t_drain = Lq / (mu - lam) if mu > lam else float('inf')
        B_min   = math.ceil(lam * MTTR)
        B_star  = B_min + math.ceil(z * math.sqrt(max(B_min, 1)))
        return dict(A=round(A,4), rho_eff=round(rho_eff,4),
                    Cs2_eff=round(Cs2_eff,4),
                    Wq_bkdn_min=round(Wq_bkdn*60,1),
                    t_drain_hr=round(t_drain,2),
                    B_min=B_min, B_star=B_star, capacity=B_star)

    buffers = []
    # B_in: keyed to first machine
    b = _size(equipment[0])
    b.update(label='B_in', upstream='SOURCE',
             downstream=equipment[0]['equipment_id'])
    buffers.append(b)
    # Inter-station buffers
    for i in range(len(equipment) - 1):
        b = _size(equipment[i])
        b.update(label=f'B_{i+1}{i+2}',
                 upstream=equipment[i]['equipment_id'],
                 downstream=equipment[i+1]['equipment_id'])
        buffers.append(b)

    fieldnames = ['label', 'upstream', 'downstream',
                  'B_min', 'B_star', 'capacity',
                  'A', 'rho_eff', 'Cs2_eff',
                  'Wq_bkdn_min', 't_drain_hr']
    with open(csv_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames,
                                extrasaction='ignore')
        writer.writeheader()
        writer.writerows(buffers)

    for b in buffers:
        print(f"  {b['label']}: B_min={b['B_min']}  "
              f"B*={b['B_star']}  t_drain={b['t_drain_hr']}hr")
    print(f"  Written to {csv_path}")
    return buffers


def update_buffer_capacity(csv_path: str, label: str,
                           capacity: int) -> None:
    """
    Override the capacity field for one buffer in an existing buffers.csv.

    Parameters
    ----------
    csv_path   path to buffers.csv (must already exist)
    label      buffer label e.g. 'B_12'
    capacity   new physical capacity in jobs

    Usage
    -----
        update_buffer_capacity('buffers.csv', 'B_12', 5)
    """
    rows = []
    with open(csv_path, newline='') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        for row in reader:
            if row['label'] == label:
                row['capacity'] = str(capacity)
            rows.append(row)
    with open(csv_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"  {csv_path}: {label} capacity set to {capacity}")


