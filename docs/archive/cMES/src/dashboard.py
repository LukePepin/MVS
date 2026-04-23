"""
dashboard.py — Pharma MES Live Dashboard

Pure Python HTTP server (no Flask) — RITE MES style.
Runs a SimPy discrete-event simulation in a background thread.
The factory floor shows animated batch tokens moving through all
pharma process stations in real time.

Run:  python3 dashboard.py
Open: http://localhost:8090
"""

import json
import os
import sys
import threading
import time
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse
from typing import Dict, Optional
import math

# Ensure sibling modules (db_setup, des_simulation, etc.) are importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np
import simpy
import psycopg2
import psycopg2.extras

# ── Configuration ──────────────────────────────────────────────────────────────
HTTP_PORT = 8090
TEMPLATE_DIR  = os.path.join(os.path.dirname(__file__), "templates")
OUTPUTS_DIR   = os.path.join(os.path.dirname(__file__), "..", "outputs")

DB_CFG = dict(
    host="100.115.213.16", port=5432, dbname="Sheridan_573",
    user="twin_mes_db", password="postgres", connect_timeout=5,
)

# ── Station definitions (match project proposal process flow) ──────────────────
STATION_ORDER = [
    "raw_material", "quarantine", "dispensing",
    "compounding", "filtration", "filling",
    "inspection", "qa_hold",
]
STATION_LABELS = {
    "raw_material": "Raw Material\n& Quarantine Staging",
    "quarantine":   "Quarantine\nHold",
    "dispensing":   "Dispensing\n& Weighing",
    "compounding":  "Compounding /\nSolution Prep",
    "filtration":   "Sterile\nFiltration",
    "filling":      "Aseptic\nFilling",
    "inspection":   "Inspection\n& Packaging",
    "qa_hold":      "QA Release\nHold",
}
STATION_MEANS = {
    "raw_material": 30, "quarantine": 120,
    "dispensing": 45,   "compounding": 90,
    "filtration": 60,   "filling": 120,
    "inspection": 45,   "qa_hold": 180,
}
PRODUCT_MULT = {"Injectable-A": 1.00, "Injectable-B": 0.88, "Injectable-C": 0.74}
PRODUCT_COLOR = {
    "Injectable-A": "#3498db",
    "Injectable-B": "#27ae60",
    "Injectable-C": "#e67e22",
}
PRODUCTS = ["Injectable-A", "Injectable-B", "Injectable-C"]

MTTF = 480.0
MTTR = 30.0
MEAN_INTERARRIVAL = 240.0

# WFI/HVAC initial values
WFI_INIT = dict(conductivity=0.82, temperature=80.0, flow_rate=15.0,
                toc=248.0, pressure=45.0, status="Normal")
HVAC_INIT = dict(temp_c=22.0, humidity_pct=45.0, pressure_pa=15.0,
                 particles=2000, status="Normal")


# ── Shared simulation state ────────────────────────────────────────────────────

class SimState:
    """Thread-safe shared state between SimPy thread and HTTP thread."""
    def __init__(self):
        self._lock = threading.Lock()
        self._data = {
            "running":     False,
            "paused":      False,
            "speed":       30,        # sim-minutes per real second
            "sim_time":    0.0,
            "dispatch_rule": "FIFO",
            "num_filling": 1,
            # Batch tokens: {batch_id: {station, product, color, arrival_time}}
            "batches":     {},
            # Station current occupant + queue
            "stations":    {s: {"occupant": None, "queue": []} for s in STATION_ORDER},
            "stations":    {s: {"occupant": None, "queue": []} for s in
                            list(STATION_ORDER) + ["released"]},
            "metrics": {
                "throughput": 0.0,
                "wip": 0,
                "avg_flow_min": 0.0,
                "util_filling": 0.0,
                "n_released": 0,
                "n_breakdowns": 0,
            },
            "wip_history":    [],   # [(sim_min, wip), ...]
            "q_fill_history": [],
            "events":         [],   # last 80 events
            "wfi": dict(WFI_INIT),
            "hvac": dict(HVAC_INIT),
        }

    def read(self) -> dict:
        with self._lock:
            return json.loads(json.dumps(self._data, default=str))

    def update(self, updates: dict):
        with self._lock:
            _deep_update(self._data, updates)

    def get(self, key):
        with self._lock:
            return self._data.get(key)

    def set_station_occupant(self, station: str, batch_id: Optional[str]):
        with self._lock:
            self._data["stations"][station]["occupant"] = batch_id

    def add_to_queue(self, station: str, batch_id: str):
        with self._lock:
            q = self._data["stations"][station]["queue"]
            if batch_id not in q:
                q.append(batch_id)

    def remove_from_queue(self, station: str, batch_id: str):
        with self._lock:
            q = self._data["stations"][station]["queue"]
            if batch_id in q:
                q.remove(batch_id)

    def add_event(self, level: str, msg: str, batch_id: str = ""):
        with self._lock:
            ts = datetime.now().strftime("%H:%M:%S")
            self._data["events"].insert(0, {
                "ts": ts, "level": level,
                "message": msg, "batch_id": batch_id,
            })
            self._data["events"] = self._data["events"][:80]

    def set_batch_station(self, batch_id: str, station: str):
        with self._lock:
            if batch_id in self._data["batches"]:
                self._data["batches"][batch_id]["station"] = station

    def append_history(self, wip: int, q_fill: int, sim_time: float):
        with self._lock:
            self._data["wip_history"].append([round(sim_time / 60, 1), wip])
            self._data["q_fill_history"].append([round(sim_time / 60, 1), q_fill])
            # Keep last 300 points
            self._data["wip_history"]    = self._data["wip_history"][-300:]
            self._data["q_fill_history"] = self._data["q_fill_history"][-300:]


def _deep_update(base: dict, updates: dict):
    for k, v in updates.items():
        if isinstance(v, dict) and isinstance(base.get(k), dict):
            _deep_update(base[k], v)
        else:
            base[k] = v


# ── SimPy Simulation ───────────────────────────────────────────────────────────

class PharmaDashboardSim:
    def __init__(self, state: SimState):
        self.state        = state
        self.rng          = np.random.default_rng(int(time.time()))
        self._dispatch    = state.get("dispatch_rule") or "FIFO"
        self._num_fill    = state.get("num_filling") or 1
        self.env          = simpy.Environment()
        self._current_wip = 0
        self._completed   = []
        self._flow_times  = []
        self._filling_busy = 0.0
        self._filling_broken = False
        self._n_breakdowns   = 0
        self._batch_count    = 0

        # Resources
        self.resources: Dict[str, simpy.PriorityResource] = {}
        for s in ["raw_material", "dispensing", "compounding",
                  "filtration", "filling", "inspection"]:
            cap = self._num_fill if s == "filling" else 1
            self.resources[s] = simpy.PriorityResource(self.env, capacity=cap)

        self.env.process(self._breakdown_proc())
        self.env.process(self._monitor_proc())
        self.env.process(self._wfi_hvac_proc())
        self.env.process(self._arrivals())

    def _priority(self, batch_id: str, product: str, arrival: float,
                  due: float, station: str) -> float:
        rule = self.state.get("dispatch_rule") or "FIFO"
        if rule == "SPT":
            return STATION_MEANS.get(station, 60) * PRODUCT_MULT.get(product, 1.0)
        elif rule == "EDD":
            return due
        return arrival  # FIFO

    def _sample(self, station: str, product: str) -> float:
        mean  = STATION_MEANS.get(station, 60)
        mult  = PRODUCT_MULT.get(product, 1.0)
        sigma = mean * mult * 0.15
        return float(max(1.0, self.rng.normal(mean * mult, sigma)))

    def _breakdown_proc(self):
        while True:
            yield self.env.timeout(float(self.rng.exponential(MTTF)))
            self._filling_broken = True
            self._n_breakdowns += 1
            self.state.add_event("ALARM", "Filling machine breakdown — repairing…")
            yield self.env.timeout(float(self.rng.exponential(MTTR)))
            self._filling_broken = False
            self.state.add_event("INFO", "Filling machine restored to service")

    def _monitor_proc(self):
        while True:
            yield self.env.timeout(60.0)
            q_fill = len(self.resources["filling"].queue)
            self.state.append_history(self._current_wip, q_fill, self.env.now)
            n = len(self._flow_times)
            avg_flow = float(np.mean(self._flow_times[-20:])) if self._flow_times else 0.0
            run_h = self.env.now / 60.0
            tput  = len(self._completed) / run_h if run_h > 0 else 0.0
            util  = self._filling_busy / self.env.now if self.env.now > 0 else 0.0
            self.state.update({
                "sim_time": round(self.env.now, 1),
                "metrics": {
                    "wip":           self._current_wip,
                    "throughput":    round(tput, 3),
                    "avg_flow_min":  round(avg_flow, 1),
                    "util_filling":  round(min(util, 1.0) * 100, 1),
                    "n_released":    len(self._completed),
                    "n_breakdowns":  self._n_breakdowns,
                },
            })

    def _wfi_hvac_proc(self):
        """Simulate WFI and HVAC with realistic variations."""
        rng = self.rng
        wfi_c = 0.82; wfi_t = 80.0; wfi_f = 15.0; wfi_toc = 248.0
        hvac_t = 22.0; hvac_h = 45.0; hvac_p = 2000

        while True:
            yield self.env.timeout(5.0)  # update every 5 sim-minutes

            wfi_c   = max(0.5, min(1.5, wfi_c   + rng.normal(0, 0.04) + (0.82 - wfi_c)*0.08))
            wfi_t   = max(75,  min(85,  wfi_t   + rng.normal(0, 0.2)  + (80.0 - wfi_t)*0.05))
            wfi_f   = max(10,  min(20,  wfi_f   + rng.normal(0, 0.15) + (15.0 - wfi_f)*0.05))
            wfi_toc = max(100, min(600, wfi_toc + rng.normal(0, 20)   + (250 - wfi_toc)*0.05))

            hvac_t  = max(19, min(25, hvac_t + rng.normal(0, 0.3) + (22.0 - hvac_t)*0.06))
            hvac_h  = max(30, min(60, hvac_h + rng.normal(0, 1.5) + (45.0 - hvac_h)*0.05))
            hvac_p  = max(1000, min(4500, int(hvac_p + rng.normal(0, 100) + (2000 - hvac_p)*0.1)))

            # Occasional spikes
            if rng.random() < 0.02:
                wfi_c += rng.uniform(0.15, 0.3)
                if wfi_c > 1.0:
                    self.state.add_event("WARNING", f"WFI conductivity spike: {wfi_c:.2f} µS/cm")

            wfi_status = ("ALARM" if wfi_c > 1.3 or wfi_toc > 500
                          else "WARNING" if wfi_c > 1.0 or wfi_toc > 400
                          else "Normal")
            hvac_status = ("ALARM"   if hvac_p > 3520 or hvac_t < 19.5 or hvac_t > 24.5
                           else "WARNING" if not (20 <= hvac_t <= 24) or not (35 <= hvac_h <= 55)
                           else "Normal")

            self.state.update({
                "wfi": {
                    "conductivity": round(wfi_c, 3),
                    "temperature":  round(wfi_t, 1),
                    "flow_rate":    round(wfi_f, 1),
                    "toc":          round(wfi_toc, 0),
                    "status":       wfi_status,
                },
                "hvac": {
                    "temp_c":      round(hvac_t, 1),
                    "humidity_pct": round(hvac_h, 1),
                    "particles":   hvac_p,
                    "status":      hvac_status,
                },
            })

    def _batch_proc(self, batch_id: str, product: str,
                    arrival: float, due: float):
        """Route one batch through all stations."""
        self._current_wip += 1

        # Register batch
        color = PRODUCT_COLOR.get(product, "#999")
        self.state.update({
            "batches": {
                batch_id: {
                    "station": "arriving",
                    "product": product,
                    "color":   color,
                    "arrival": arrival,
                }
            }
        })
        self.state.add_event("INFO", f"{batch_id} ({product}) arrived", batch_id)

        flow_def = [
            ("raw_material", False),
            ("quarantine",   True),   # fixed delay
            ("dispensing",   False),
            ("compounding",  False),
            ("filtration",   False),
            ("filling",      False),
            ("inspection",   False),
            ("qa_hold",      True),   # fixed delay
        ]

        filling_start: Optional[float] = None

        for station, is_delay in flow_def:
            if is_delay:
                self.state.set_batch_station(batch_id, station)
                self.state.add_to_queue(station, batch_id)
                self.state.add_event("INFO", f"{batch_id} → {station}", batch_id)
                yield self.env.timeout(self._sample(station, product))
                self.state.remove_from_queue(station, batch_id)
                continue

            prio = self._priority(batch_id, product, arrival, due, station)
            self.state.set_batch_station(batch_id, f"q_{station}")
            self.state.add_to_queue(station, batch_id)

            with self.resources[station].request(priority=prio) as req:
                yield req
                self.state.remove_from_queue(station, batch_id)
                self.state.set_station_occupant(station, batch_id)
                self.state.set_batch_station(batch_id, station)
                self.state.add_event(
                    "INFO", f"{batch_id} → processing at {STATION_LABELS.get(station, station).split(chr(10))[0]}",
                    batch_id,
                )

                if station == "filling":
                    filling_start = self.env.now

                proc = self._sample(station, product)

                if station == "filling":
                    remaining = proc
                    while remaining > 0:
                        if self._filling_broken:
                            yield self.env.timeout(1.0)
                        else:
                            step = min(remaining, 1.0)
                            yield self.env.timeout(step)
                            remaining -= step
                    if filling_start is not None:
                        self._filling_busy += self.env.now - filling_start
                else:
                    yield self.env.timeout(proc)

                self.state.set_station_occupant(station, None)

        # Released
        flow_time = self.env.now - arrival
        self._current_wip -= 1
        self._completed.append(batch_id)
        self._flow_times.append(flow_time)
        self.state.set_batch_station(batch_id, "released")
        self.state.add_event(
            "INFO",
            f"{batch_id} RELEASED  flow={flow_time/60:.1f} h",
            batch_id,
        )

    def _arrivals(self):
        count = 0
        while True:
            yield self.env.timeout(float(self.rng.exponential(MEAN_INTERARRIVAL)))
            count += 1
            self._batch_count = count
            product  = self.rng.choice(PRODUCTS)
            arrival  = self.env.now
            due      = arrival + float(self.rng.uniform(800, 1200))
            batch_id = f"B{count:03d}"
            self.env.process(
                self._batch_proc(batch_id, product, arrival, due)
            )


# ── Simulation background thread ───────────────────────────────────────────────

_sim_thread: Optional[threading.Thread] = None
_state = SimState()

# ── Analysis task state ───────────────────────────────────────────────────────
_analysis_lock  = threading.Lock()
_analysis_state = {"running": False, "step": "", "progress": 0, "log": [], "done": False, "error": ""}


def _run_sim_thread():
    global _state
    sim = PharmaDashboardSim(_state)
    _state.update({"running": True})
    tick_real = 0.05  # 50 ms real-time between ticks

    while _state.get("running"):
        if _state.get("paused"):
            time.sleep(0.1)
            continue

        speed = _state.get("speed") or 30
        sim_tick = speed * tick_real  # sim-minutes per real tick

        try:
            sim.env.run(until=sim.env.now + sim_tick)
        except Exception:
            pass

        _state.update({"sim_time": round(sim.env.now, 1)})
        time.sleep(tick_real)


def finish_instantly(target_batches: int = 30):
    """Run the sim at warp speed until target_batches are released, then pause."""
    global _state
    _state.update({"speed": 9999, "paused": False})
    _state.add_event("INFO", f"Finish Instantly — running to {target_batches} released batches…")

    def _warp():
        while _state.get("running"):
            released = (_state.read().get("metrics") or {}).get("n_released", 0)
            if released >= target_batches:
                _state.update({"paused": True, "speed": 30})
                _state.add_event("INFO", f"Finish Instantly complete — {released} batches released")
                return
            time.sleep(0.05)

    t = threading.Thread(target=_warp, daemon=True)
    t.start()


def _run_analysis_thread(steps: list):
    global _analysis_state
    import io, contextlib

    def _log(msg):
        with _analysis_lock:
            _analysis_state["log"].append(msg)
            _analysis_state["log"] = _analysis_state["log"][-200:]

    def _set(step, progress):
        with _analysis_lock:
            _analysis_state["step"]     = step
            _analysis_state["progress"] = progress

    with _analysis_lock:
        _analysis_state.update({"running": True, "done": False, "error": "", "log": [], "progress": 0})

    try:
        total = len(steps)
        for i, step in enumerate(steps):
            _set(step, int(i / total * 100))
            _log(f"▶ Starting: {step}")

            buf = io.StringIO()
            try:
                with contextlib.redirect_stdout(buf):
                    if step == "db_setup":
                        import db_setup
                        db_setup.setup_database()
                    elif step == "queueing":
                        import queueing_analysis
                        queueing_analysis.run_queueing_analysis()
                    elif step == "simulation":
                        import des_simulation
                        des_simulation.run_des_analysis()
                    elif step == "mrp":
                        import mrp_scheduler
                        mrp_scheduler.run_mrp_and_schedule()

                for line in buf.getvalue().splitlines():
                    if line.strip():
                        _log(line)

            except Exception as exc:
                _log(f"ERROR in {step}: {exc}")
                with _analysis_lock:
                    _analysis_state["error"] = str(exc)

            _log(f"✓ Done: {step}")

        with _analysis_lock:
            _analysis_state.update({"done": True, "running": False, "progress": 100, "step": "complete"})

    except Exception as exc:
        with _analysis_lock:
            _analysis_state.update({"running": False, "done": True, "error": str(exc)})


def start_simulation():
    global _sim_thread, _state
    if _sim_thread and _sim_thread.is_alive():
        return
    _state = SimState()
    _state.update({
        "running": True, "paused": False,
        "speed": 30, "dispatch_rule": "FIFO", "num_filling": 1,
    })
    _sim_thread = threading.Thread(target=_run_sim_thread, daemon=True)
    _sim_thread.start()


def stop_simulation():
    global _state
    _state.update({"running": False})


# ── DB helpers ─────────────────────────────────────────────────────────────────

def _db_work_orders():
    try:
        conn = psycopg2.connect(**DB_CFG)
        cur  = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("""
            SELECT wo_id, product_id, quantity, due_date, priority, status
            FROM work_orders ORDER BY due_date LIMIT 20
        """)
        rows = [dict(r) for r in cur.fetchall()]
        for r in rows:
            r["due_date"] = r["due_date"].strftime("%Y-%m-%d %H:%M")
        conn.close()
        return rows
    except Exception as e:
        return [{"error": str(e)}]


def _db_mrp():
    try:
        conn = psycopg2.connect(**DB_CFG)
        cur  = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("""
            SELECT m.item_id, i.name, m.period_week, m.release_week,
                   m.quantity, m.status
            FROM mrp_plan m JOIN items i ON m.item_id = i.item_id
            ORDER BY m.bom_level DESC, m.period_week
            LIMIT 40
        """)
        return [dict(r) for r in cur.fetchall()]
    except Exception:
        try:
            conn = psycopg2.connect(**DB_CFG)
            cur  = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cur.execute("""
                SELECT m.item_id, m.period_week, m.release_week,
                       m.quantity, m.status
                FROM mrp_plan m ORDER BY m.period_week LIMIT 40
            """)
            return [dict(r) for r in cur.fetchall()]
        except Exception as e2:
            return [{"error": str(e2)}]


def _db_sim_results():
    """Return what-if scenario summaries from simulation_results table."""
    try:
        conn = psycopg2.connect(**DB_CFG)
        cur  = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("""
            SELECT scenario, dispatch_rule,
                   ROUND(AVG(mean_flow_time_min)::numeric, 1)  AS mean_flow,
                   ROUND(AVG(mean_wip)::numeric, 2)            AS mean_wip,
                   ROUND(AVG(throughput_per_hr)::numeric, 4)   AS mean_tput,
                   ROUND(AVG(util_filling_pct)::numeric, 1)    AS mean_util,
                   ROUND(AVG(mean_queue_filling)::numeric, 2)  AS mean_q,
                   ROUND(AVG(ci_low_flow)::numeric, 1)         AS ci_low,
                   ROUND(AVG(ci_high_flow)::numeric, 1)        AS ci_high,
                   COUNT(*)                                    AS n_reps
            FROM simulation_results
            WHERE scenario NOT LIKE 'queueing%%'
              AND scenario NOT LIKE 'ttest%%'
            GROUP BY scenario, dispatch_rule
            ORDER BY mean_flow
        """)
        scenarios = [dict(r) for r in cur.fetchall()]
        conn.close()
        return {"scenarios": scenarios, "has_data": len(scenarios) > 0}
    except Exception as e:
        return {"scenarios": [], "has_data": False, "error": str(e)}


def _db_schedule():
    try:
        conn = psycopg2.connect(**DB_CFG)
        cur  = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("""
            SELECT s.wo_id, s.work_center, s.algorithm,
                   s.planned_start, s.planned_end, s.status
            FROM schedule s ORDER BY s.planned_start LIMIT 20
        """)
        rows = [dict(r) for r in cur.fetchall()]
        for r in rows:
            for k in ["planned_start", "planned_end"]:
                if r.get(k):
                    r[k] = r[k].strftime("%m/%d %H:%M")
        conn.close()
        return rows
    except Exception as e:
        return [{"error": str(e)}]


# ── HTTP Handler ───────────────────────────────────────────────────────────────

class PharmaHandler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass  # suppress request logging

    def _send_json(self, data, status=200):
        body = json.dumps(data, default=str).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", len(body))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _send_html(self, body: bytes):
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", len(body))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urlparse(self.path)
        path   = parsed.path

        if path == "/" or path == "/index.html":
            html_path = os.path.join(TEMPLATE_DIR, "dashboard.html")
            with open(html_path, "rb") as f:
                self._send_html(f.read())

        elif path == "/api/state":
            self._send_json(_state.read())

        elif path == "/api/work_orders":
            self._send_json(_db_work_orders())

        elif path == "/api/mrp":
            self._send_json(_db_mrp())

        elif path == "/api/schedule":
            self._send_json(_db_schedule())

        elif path == "/api/station_config":
            cfg = {s: {"label": STATION_LABELS[s],
                       "mean_min": STATION_MEANS[s]}
                   for s in STATION_ORDER}
            self._send_json(cfg)

        elif path == "/api/analysis_status":
            with _analysis_lock:
                self._send_json(dict(_analysis_state))

        elif path == "/api/sim_results":
            self._send_json(_db_sim_results())

        elif path.startswith("/outputs/"):
            fname = os.path.basename(path)          # strip any path traversal
            fpath = os.path.join(OUTPUTS_DIR, fname)
            if fname.endswith(".png") and os.path.exists(fpath):
                with open(fpath, "rb") as f:
                    data = f.read()
                self.send_response(200)
                self.send_header("Content-Type", "image/png")
                self.send_header("Content-Length", len(data))
                self.send_header("Cache-Control", "no-cache")
                self.end_headers()
                self.wfile.write(data)
            else:
                self.send_response(404)
                self.end_headers()

        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        parsed = urlparse(self.path)
        length = int(self.headers.get("Content-Length", 0))
        body   = self.rfile.read(length) if length else b""
        try:
            payload = json.loads(body) if body else {}
        except Exception:
            payload = {}

        if parsed.path == "/api/control":
            global _state
            cmd = payload.get("cmd", "")
            if cmd == "start":
                start_simulation()
                self._send_json({"ok": True, "msg": "Simulation started"})
            elif cmd == "stop":
                stop_simulation()
                self._send_json({"ok": True, "msg": "Simulation stopped"})
            elif cmd == "pause":
                _state.update({"paused": True})
                self._send_json({"ok": True})
            elif cmd == "resume":
                _state.update({"paused": False})
                self._send_json({"ok": True})
            elif cmd == "reset":
                stop_simulation()
                time.sleep(0.3)
                _state = SimState()   # fresh state, NOT auto-started
                self._send_json({"ok": True, "msg": "Reset — press ▶ Start to begin"})
            elif cmd == "set_speed":
                _state.update({"speed": int(payload.get("speed", 30))})
                self._send_json({"ok": True})
            elif cmd == "set_rule":
                _state.update({"dispatch_rule": payload.get("rule", "FIFO")})
                self._send_json({"ok": True})
            elif cmd == "set_filling":
                _state.update({"num_filling": int(payload.get("n", 1))})
                self._send_json({"ok": True})
            elif cmd == "finish_instantly":
                target = int(payload.get("target_batches", 30))
                finish_instantly(target)
                self._send_json({"ok": True, "msg": f"Running to {target} released batches"})
            else:
                self._send_json({"ok": False, "msg": "Unknown command"}, 400)

        elif parsed.path == "/api/run_analysis":
            with _analysis_lock:
                already = _analysis_state.get("running", False)
            if already:
                self._send_json({"ok": False, "msg": "Analysis already running"})
                return
            steps = payload.get("steps", ["db_setup", "queueing", "mrp"])
            t = threading.Thread(target=_run_analysis_thread, args=(steps,), daemon=True)
            t.start()
            self._send_json({"ok": True, "msg": f"Started steps: {steps}"})
        else:
            self.send_response(404)
            self.end_headers()


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("Pharma MES Dashboard — ISE 573 Week 7")
    print("=" * 60)
    print(f"  Database : Sheridan_573 @ {DB_CFG['host']}")
    print(f"  Dashboard: http://localhost:{HTTP_PORT}")
    print(f"  Press Ctrl+C to stop")
    print()

    print("  Press ▶ Start in the browser to begin the simulation.")
    print()

    server = ThreadingHTTPServer(("", HTTP_PORT), PharmaHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down…")
        stop_simulation()
        server.shutdown()


if __name__ == "__main__":
    main()
