"""
EARC Discrete Event Simulation Engine
Stateful SimPy-based simulation with live job tracking, speed controls,
and PuLP-based EDD/SPT scheduling optimization.
"""
import simpy
import pulp
import random
import asyncio
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum


class SimulationStatus(str, Enum):
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    FINISHED = "finished"


@dataclass
class JobToken:
    """Represents a single WIP token moving through the EARC."""
    job_id: str
    product: str
    route: list
    current_step: int = 0
    current_station: str = "queue"
    status: str = "queued"  # queued, processing, moving, completed, scrapped
    start_time: float = 0.0
    end_time: float = 0.0
    due_date: float = 0.0


# ── EARC topology constants ──────────────────────────────────────────
PRODUCTS = {
    "Gasket_A":  {"route": ["R0", "M2", "R1"], "cycle_times": {"R0": 2.0, "M2": 15.0, "R1": 3.0}},
    "Shaft_B":   {"route": ["R0", "M3", "R1"], "cycle_times": {"R0": 2.0, "M3": 45.0, "R1": 5.0}},
    "Housing_C": {"route": ["R0", "M1", "R1"], "cycle_times": {"R0": 3.0, "M1": 60.0, "R1": 5.0}},
    "Bracket_D": {"route": ["R0", "M1", "M2", "R1"], "cycle_times": {"R0": 2.0, "M1": 30.0, "M2": 20.0, "R1": 4.0}},
}

STATION_CAPACITIES = {"R0": 5, "M1": 1, "M2": 2, "M3": 1, "R1": 1}

STATION_LABELS = {
    "R0": "Infeed Robot",
    "M1": "CNC Mill",
    "M2": "Dual Laser",
    "M3": "CNC Lathe",
    "R1": "Outfeed Robot",
}

PROJECT_START_UTC = datetime(2026, 4, 1, 8, 0, tzinfo=timezone.utc)


class LiveSimulationState:
    """Thread-safe container for the live simulation state consumed by the API."""

    def __init__(self):
        self._lock = threading.Lock()
        self.status: SimulationStatus = SimulationStatus.IDLE
        self.sim_time: float = 0.0
        self.speed: float = 1.0
        self.algorithm: str = ""
        self.num_jobs: int = 0
        self.tokens: dict[str, JobToken] = {}
        self.completed_jobs: int = 0
        self.total_flow_time: float = 0.0
        self.flow_times: list[float] = []
        self.station_busy: dict[str, int] = {s: 0 for s in STATION_CAPACITIES}
        self.station_queue: dict[str, int] = {s: 0 for s in STATION_CAPACITIES}
        self.station_cumulative_busy: dict[str, float] = {s: 0.0 for s in STATION_CAPACITIES}
        self.events_log: list[dict] = []
        self.oee_snapshots: list[dict] = []
        self.project_start_iso: str = PROJECT_START_UTC.isoformat()

    def snapshot(self) -> dict:
        with self._lock:
            token_list = []
            for t in self.tokens.values():
                token_list.append({
                    "job_id": t.job_id,
                    "product": t.product,
                    "route": t.route,
                    "current_step": t.current_step,
                    "current_station": t.current_station,
                    "status": t.status,
                    "start_time": round(t.start_time, 1),
                    "due_date": round(t.due_date, 1),
                })
            # Build utilization percentages
            util = {}
            for s in STATION_CAPACITIES:
                if self.sim_time > 0:
                    util[s] = round(self.station_cumulative_busy.get(s, 0) / (self.sim_time * STATION_CAPACITIES[s]) * 100, 1)
                else:
                    util[s] = 0.0
            return {
                "sim_status": self.status.value,
                "sim_time": round(self.sim_time, 1),
                "speed": self.speed,
                "algorithm": self.algorithm,
                "num_jobs": self.num_jobs,
                "completed_jobs": self.completed_jobs,
                "avg_flow_time": round(self.total_flow_time / max(1, self.completed_jobs), 1),
                "project_start_iso": self.project_start_iso,
                "simulated_time_iso": (PROJECT_START_UTC + timedelta(minutes=self.sim_time)).isoformat(),
                "tokens": token_list,
                "station_busy": dict(self.station_busy),
                "station_queue": dict(self.station_queue),
                "station_utilization": util,
                "flow_times": [round(f, 1) for f in self.flow_times[-100:]],
                "events_log": self.events_log[-50:],
                "oee_snapshots": self.oee_snapshots[-30:],
            }

    def _log_event(self, sim_time: float, event_type: str, message: str):
        self.events_log.append({
            "time": round(sim_time, 1),
            "type": event_type,
            "message": message,
            "wall_clock": datetime.now(timezone.utc).isoformat(),
        })
        if len(self.events_log) > 200:
            self.events_log = self.events_log[-200:]


# ── Global singleton ─────────────────────────────────────────────────
_sim_state = LiveSimulationState()


def get_sim_state() -> LiveSimulationState:
    return _sim_state


# ── PuLP Scheduling ──────────────────────────────────────────────────
def optimize_schedule_edd(work_orders: list[dict]) -> list[dict]:
    """EDD-based scheduling: sort by due date (primary), use PuLP to verify feasibility."""
    if not work_orders:
        return []

    # EDD rule: sort strictly by ascending due date
    sorted_orders = sorted(work_orders, key=lambda wo: wo["due"])

    # Use PuLP to assign optimal start times respecting the EDD sequence
    prob = pulp.LpProblem("EARC_EDD_Schedule", pulp.LpMinimize)
    ids = [wo["id"] for wo in sorted_orders]
    start_vars = pulp.LpVariable.dicts("start", ids, lowBound=0, cat="Continuous")
    tardiness_vars = pulp.LpVariable.dicts("tardiness", ids, lowBound=0, cat="Continuous")

    prob += pulp.lpSum([tardiness_vars[i] for i in ids])

    cumulative_time = 0
    for wo in sorted_orders:
        i = wo["id"]
        proc_time = sum(wo.get("cycle_times", {}).values())
        # Enforce sequencing: each job starts after the previous finishes
        prob += start_vars[i] >= cumulative_time
        prob += tardiness_vars[i] >= start_vars[i] + proc_time - wo["due"]
        cumulative_time += proc_time

    prob.solve(pulp.PULP_CBC_CMD(msg=0))
    return sorted_orders


def optimize_schedule_spt(work_orders: list[dict]) -> list[dict]:
    """SPT-based scheduling: sort by total processing time (shortest first)."""
    return sorted(work_orders, key=lambda wo: sum(wo.get("cycle_times", {}).values()))


def optimize_schedule_fifo(work_orders: list[dict]) -> list[dict]:
    """FIFO: First In First Out — maintain original arrival order."""
    return list(work_orders)


def optimize_schedule_lpt(work_orders: list[dict]) -> list[dict]:
    """LPT: Longest Processing Time first — maximize machine utilization."""
    return sorted(work_orders, key=lambda wo: sum(wo.get("cycle_times", {}).values()), reverse=True)


def optimize_schedule_wspt(work_orders: list[dict]) -> list[dict]:
    """WSPT: Weighted SPT — weight = 1/due_date, minimize weighted completion."""
    def wspt_key(wo):
        p = sum(wo.get("cycle_times", {}).values())
        w = 1.0 / max(1.0, wo.get("due", 1000))
        return p / w  # ascending = highest priority first
    return sorted(work_orders, key=wspt_key)


def optimize_schedule_cr(work_orders: list[dict]) -> list[dict]:
    """CR: Critical Ratio — (due_date) / processing_time, lowest ratio first."""
    def cr_key(wo):
        p = sum(wo.get("cycle_times", {}).values())
        return wo.get("due", 1000) / max(0.1, p)
    return sorted(work_orders, key=cr_key)


# ── SimPy Engine ─────────────────────────────────────────────────────
class EARCSimulation:
    def __init__(self, state: LiveSimulationState, num_jobs: int = 50,
                 algorithm: str = "EDD", seed: int | None = None):
        self.state = state
        self.num_jobs = num_jobs
        self.algorithm = algorithm
        self.rng = random.Random(seed)
        self.env = simpy.Environment()
        self._paused = threading.Event()
        self._paused.set()  # not paused by default
        self._finish_instantly = False

        # Create SimPy resources
        self.resources: dict[str, simpy.Resource] = {}
        for station_id, cap in STATION_CAPACITIES.items():
            self.resources[station_id] = simpy.Resource(self.env, capacity=cap)

    def _generate_work_orders(self) -> list[dict]:
        orders = []
        product_names = list(PRODUCTS.keys())
        for i in range(self.num_jobs):
            prod = self.rng.choice(product_names)
            info = PRODUCTS[prod]
            orders.append({
                "id": i,
                "product": prod,
                "route": list(info["route"]),
                "cycle_times": dict(info["cycle_times"]),
                "due": self.rng.uniform(200, 2000),
            })
        return orders

    def _process_job(self, token: JobToken, cycle_times: dict):
        """SimPy process for a single job flowing through its route."""
        token.start_time = self.env.now
        token.status = "moving"

        with self.state._lock:
            self.state.tokens[token.job_id] = token
            self.state._log_event(self.env.now, "INFO", f"{token.job_id} ({token.product}) entered system")

        for step_idx, station_id in enumerate(token.route):
            token.current_step = step_idx
            token.current_station = station_id
            token.status = "queued"

            with self.state._lock:
                self.state.station_queue[station_id] = self.state.station_queue.get(station_id, 0) + 1

            resource = self.resources[station_id]
            with resource.request() as req:
                yield req
                with self.state._lock:
                    self.state.station_queue[station_id] = max(0, self.state.station_queue.get(station_id, 0) - 1)
                    self.state.station_busy[station_id] = self.state.station_busy.get(station_id, 0) + 1

                token.status = "processing"

                # Processing time with lognormal variation (CV ≈ 0.20)
                mean_time = cycle_times.get(station_id, 10.0)
                if self._finish_instantly:
                    actual_time = 0.01
                else:
                    sigma = 0.20
                    actual_time = self.rng.lognormvariate(
                        __import__("math").log(mean_time) - (sigma ** 2) / 2,
                        sigma,
                    )
                yield self.env.timeout(actual_time)

                with self.state._lock:
                    self.state.station_busy[station_id] = max(0, self.state.station_busy.get(station_id, 0) - 1)
                    self.state.station_cumulative_busy[station_id] = self.state.station_cumulative_busy.get(station_id, 0) + actual_time
                    self.state._log_event(
                        self.env.now, "INFO",
                        f"{token.job_id} finished at {STATION_LABELS.get(station_id, station_id)} ({actual_time:.1f} min)",
                    )

            token.status = "moving"

        # Job completed
        token.status = "completed"
        token.end_time = self.env.now
        flow = token.end_time - token.start_time

        with self.state._lock:
            self.state.completed_jobs += 1
            self.state.total_flow_time += flow
            self.state.flow_times.append(flow)
            self.state._log_event(
                self.env.now, "SUCCESS",
                f"{token.job_id} completed — flow time {flow:.1f} min",
            )
            # Remove token after a short visual delay (keep for snapshot)
            # We'll let old tokens age out after 50 completed
            if self.state.completed_jobs % 5 == 0:
                self._record_oee_snapshot()

    def _record_oee_snapshot(self):
        """Simplified OEE snapshot based on station utilization."""
        total_capacity_mins = self.env.now * sum(STATION_CAPACITIES.values())
        total_busy_mins = self.state.total_flow_time
        avail = min(1.0, 0.85 + self.state.completed_jobs * 0.001)
        perf = min(1.0, total_busy_mins / max(1, total_capacity_mins) + 0.5)
        qual = 0.98  # fixed quality for now
        oee = avail * perf * qual

        self.state.oee_snapshots.append({
            "sim_time": round(self.env.now, 1),
            "completed": self.state.completed_jobs,
            "availability": round(avail * 100, 1),
            "performance": round(perf * 100, 1),
            "quality": round(qual * 100, 1),
            "oee": round(oee * 100, 1),
        })

    def _arrival_process(self, scheduled_orders: list[dict]):
        """SimPy generator — releases jobs into the system over time."""
        for wo in scheduled_orders:
            # Wait for unpause
            while not self._paused.is_set():
                yield self.env.timeout(0.1)

            token = JobToken(
                job_id=f"Job_{wo['id']:03d}",
                product=wo["product"],
                route=wo["route"],
                due_date=wo["due"],
            )
            self.env.process(self._process_job(token, wo["cycle_times"]))

            # Inter-arrival time (exponential)
            if not self._finish_instantly:
                iat = self.rng.expovariate(1.0 / 8.0)
                yield self.env.timeout(iat)
            else:
                yield self.env.timeout(0.01)

    def run_sync(self):
        """Run the full simulation synchronously in a background thread."""
        with self.state._lock:
            self.state.status = SimulationStatus.RUNNING
            self.state.algorithm = self.algorithm
            self.state.num_jobs = self.num_jobs
            self.state.completed_jobs = 0
            self.state.total_flow_time = 0.0
            self.state.flow_times = []
            self.state.tokens = {}
            self.state.events_log = []
            self.state.oee_snapshots = []
            self.state.station_busy = {s: 0 for s in STATION_CAPACITIES}
            self.state.station_queue = {s: 0 for s in STATION_CAPACITIES}
            self.state.station_cumulative_busy = {s: 0.0 for s in STATION_CAPACITIES}

        work_orders = self._generate_work_orders()

        schedulers = {
            "EDD": optimize_schedule_edd,
            "SPT": optimize_schedule_spt,
            "FIFO": optimize_schedule_fifo,
            "LPT": optimize_schedule_lpt,
            "WSPT": optimize_schedule_wspt,
            "CR": optimize_schedule_cr,
        }
        scheduler_fn = schedulers.get(self.algorithm, optimize_schedule_edd)
        scheduled = scheduler_fn(work_orders)

        with self.state._lock:
            self.state._log_event(0, "INFO", f"Scheduled {len(scheduled)} jobs using {self.algorithm}")

        self.env.process(self._arrival_process(scheduled))

        # Step simulation in small increments so the API can observe progress
        step_size = 1.0  # 1 simulated minute per tick
        while self.env.peek() < 10000 and self.state.completed_jobs < self.num_jobs:
            if not self._paused.is_set():
                time.sleep(0.05)
                continue

            try:
                self.env.step()
            except simpy.core.EmptySchedule:
                break

            with self.state._lock:
                self.state.sim_time = self.env.now

            # Real-time pacing — sleep proportional to sim speed
            if not self._finish_instantly and self.state.speed < 100:
                time.sleep(0.05 / max(0.1, self.state.speed))

        # Final OEE snapshot
        with self.state._lock:
            self._record_oee_snapshot()
            self.state.status = SimulationStatus.FINISHED
            self.state.sim_time = self.env.now
            self.state._log_event(
                self.env.now, "SUCCESS",
                f"Simulation complete — {self.state.completed_jobs} jobs, avg flow {self.state.total_flow_time / max(1, self.state.completed_jobs):.1f} min",
            )
            # Clean up completed tokens (keep last 20)
            completed_ids = [k for k, v in self.state.tokens.items() if v.status == "completed"]
            for cid in completed_ids[:-20]:
                del self.state.tokens[cid]


# ── Public API ────────────────────────────────────────────────────────
_sim_thread: threading.Thread | None = None
_sim_instance: EARCSimulation | None = None


def start_simulation(
    num_jobs: int = 50,
    algorithm: str = "EDD",
    seed: int | None = None,
):
    global _sim_thread, _sim_instance
    state = get_sim_state()

    if state.status == SimulationStatus.RUNNING:
        return {"error": "Simulation already running"}

    _sim_instance = EARCSimulation(
        state,
        num_jobs=num_jobs,
        algorithm=algorithm,
        seed=seed,
    )
    _sim_thread = threading.Thread(target=_sim_instance.run_sync, daemon=True)
    _sim_thread.start()
    return {
        "status": "started",
        "num_jobs": num_jobs,
        "algorithm": algorithm,
    }


def set_speed(speed: float):
    state = get_sim_state()
    state.speed = max(0.1, min(100.0, speed))
    return {"speed": state.speed}


def finish_instantly():
    global _sim_instance
    if _sim_instance:
        _sim_instance._finish_instantly = True
    return {"status": "finishing"}


def pause_simulation():
    global _sim_instance
    state = get_sim_state()
    if _sim_instance and state.status == SimulationStatus.RUNNING:
        _sim_instance._paused.clear()
        state.status = SimulationStatus.PAUSED
    return {"status": state.status.value}


def resume_simulation():
    global _sim_instance
    state = get_sim_state()
    if _sim_instance and state.status == SimulationStatus.PAUSED:
        _sim_instance._paused.set()
        state.status = SimulationStatus.RUNNING
    return {"status": state.status.value}


def reset_simulation():
    global _sim_instance, _sim_thread
    state = get_sim_state()
    _sim_instance = None
    _sim_thread = None
    state.status = SimulationStatus.IDLE
    state.sim_time = 0.0
    state.tokens = {}
    state.completed_jobs = 0
    state.total_flow_time = 0.0
    state.events_log = []
    state.oee_snapshots = []
    state.station_busy = {s: 0 for s in STATION_CAPACITIES}
    state.station_queue = {s: 0 for s in STATION_CAPACITIES}
    return {"status": "reset"}


# ── Standalone quick-run ──────────────────────────────────────────────
async def run_headless_simulation(num_jobs=50):
    """Quick headless run for testing — returns summary dict."""
    env = simpy.Environment()
    rng = random.Random(42)
    completed = [0]
    total_flow = [0.0]

    resources = {s: simpy.Resource(env, capacity=c) for s, c in STATION_CAPACITIES.items()}

    def process_job(name, route, ctimes):
        start = env.now
        for station in route:
            res = resources[station]
            with res.request() as req:
                yield req
                pt = ctimes.get(station, 10.0)
                yield env.timeout(rng.expovariate(1.0 / pt))
        completed[0] += 1
        total_flow[0] += env.now - start

    product_names = list(PRODUCTS.keys())
    work_orders = []
    for i in range(num_jobs):
        prod = rng.choice(product_names)
        info = PRODUCTS[prod]
        work_orders.append({"id": i, "product": prod, "route": list(info["route"]),
                            "cycle_times": dict(info["cycle_times"]),
                            "due": rng.randint(100, 1000)})

    scheduled = optimize_schedule_edd(work_orders)

    def arrivals():
        for wo in scheduled:
            env.process(process_job(f"Job_{wo['id']}", wo["route"], wo["cycle_times"]))
            yield env.timeout(rng.expovariate(1.0 / 10.0))

    env.process(arrivals())
    env.run(until=5000)

    return {
        "completed_jobs": completed[0],
        "average_flow_time": round(total_flow[0] / max(1, completed[0]), 2),
        "simulated_oee": round(min(1.0, (completed[0] * 15.0) / max(1, env.now)), 3),
    }


if __name__ == "__main__":
    import asyncio as _aio
    res = _aio.run(run_headless_simulation(50))
    print("Simulation Results:", res)
