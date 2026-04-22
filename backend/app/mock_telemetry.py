import asyncio
import random
import math
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

from .config import HYBRID_SCHEMA_VERSION
from .database import AsyncSessionLocal
from .models import WorkOrders, MachineStatus, RawInventory, LotEvents, Genealogy
from sqlalchemy import delete


@dataclass(slots=True)
class MockJob:
    job_id: str
    part_family: str
    requesting_unit: str
    due_date_iso: str
    route: list[str]
    step_index: int
    step_remaining_s: float
    status: str
    total_processing_time: float


class MockTelemetryEngine:
    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        self.routing_algorithm = "SPT"
        self.dil_config = {"r6_offline": False, "packet_loss": 0, "latency": 0, "jitter": 0}
        self._pending_lot_events = []
        self._rng = random.Random(573)
        self._tick = 0
        self._sequence = 1000
        self._max_jobs = 10
        self._spawn_probability = 0.30
        self._jobs: list[MockJob] = []
        self._in_transition: dict[str, tuple[str, str]] = {}
        self._inventory_kg = {
            "PLA-3": 24.5,
            "AL-6061": 39.2,
            "STEEL-17": 17.8,
        }
        self._status_overrides = {
            "r5": "Idle",  # Merge Robot R5
            "qia": "Idle", # QA A
        }
        self._node_capacity = {
            "ir": 10,
            "r0": 1, "r1": 1,
            "c0": 2, "c1": 2, "c2": 2, "c3": 2, "c4": 2, "c5": 2, "c6": 2, "c7": 2, "c8": 2, "c9": 2, "c10": 2,
            "r2": 1, "r3": 1, "r4": 1, "r5": 1, "r6": 1,
            "inv_cncm": 5, "inv_lz": 5, "inv_cncl": 5,
            "cncm": 1, "lz": 2, "cncl": 1,
            "inv_qia": 1, "inv_qib": 1,
            "qia": 1, "qib": 1,
            "inv_oba": 5, "inv_obb": 5, "inv_tra": 5,
            "oba": 5, "obb": 5, "tra": 5,
        }

        # Sparse coordinates to expand canvas later
        self._node_definitions = {
            "ir": {"label": "Input", "type": "inventory", "x": 10, "y": 65, "w": 10, "h": 10, "rot": 0},
            "r0": {"label": "R0", "type": "robot", "x": 5, "y": 50, "w": 8, "h": 8, "rot": 0},
            "r1": {"label": "R1", "type": "robot", "x": 14, "y": 65, "w": 8, "h": 8, "rot": 0},
            "c0": {"label": "C0", "type": "conveyor", "x": 12, "y": 38, "w": 10, "h": 4, "rot": -35},
            "c1": {"label": "C1", "type": "conveyor", "x": 24, "y": 65, "w": 14, "h": 4, "rot": 0},
            "r2": {"label": "R2", "type": "robot", "x": 20, "y": 28, "w": 8, "h": 8, "rot": 0},
            "inv_cncm": {"label": "Q-M1", "type": "inventory", "x": 20, "y": 18, "w": 8, "h": 8, "rot": 0},
            "cncm": {"label": "CNC", "type": "machine", "x": 20, "y": 8, "w": 12, "h": 10, "rot": 0},
            "c2": {"label": "C2", "type": "conveyor", "x": 27, "y": 46, "w": 28, "h": 4, "rot": 65},
            "c4": {"label": "C4", "type": "conveyor", "x": 34, "y": 28, "w": 18, "h": 4, "rot": 0},
            "r3": {"label": "R3", "type": "robot", "x": 34, "y": 65, "w": 8, "h": 8, "rot": 0},
            "inv_lz": {"label": "Q-M2", "type": "inventory", "x": 34, "y": 75, "w": 8, "h": 8, "rot": 0},
            "lz": {"label": "Laser", "type": "machine", "x": 34, "y": 85, "w": 12, "h": 10, "rot": 0},
            "c3": {"label": "C3", "type": "conveyor", "x": 41, "y": 46, "w": 28, "h": 4, "rot": -65},
            "c5": {"label": "C5", "type": "conveyor", "x": 50, "y": 60, "w": 25, "h": 4, "rot": -18},
            "r4": {"label": "R4", "type": "robot", "x": 48, "y": 28, "w": 8, "h": 8, "rot": 0},
            "inv_cncl": {"label": "Q-M3", "type": "inventory", "x": 48, "y": 18, "w": 8, "h": 8, "rot": 0},
            "cncl": {"label": "Lathe", "type": "machine", "x": 48, "y": 8, "w": 12, "h": 10, "rot": 0},
            "c6": {"label": "C6", "type": "conveyor", "x": 56, "y": 28, "w": 10, "h": 4, "rot": 0},
            "c7": {"label": "C7", "type": "conveyor", "x": 56, "y": 41, "w": 18, "h": 4, "rot": 60},
            "r5": {"label": "R5", "type": "robot", "x": 64, "y": 28, "w": 8, "h": 8, "rot": 0},
            "r6": {"label": "R6", "type": "robot", "x": 64, "y": 55, "w": 8, "h": 8, "rot": 0},
            "inv_qia": {"label": "Q-IA", "type": "inventory", "x": 64, "y": 18, "w": 6, "h": 6, "rot": 0},
            "qia": {"label": "Inspection A", "type": "machine", "x": 64, "y": 8, "w": 14, "h": 10, "rot": 0},
            "c10": {"label": "C10", "type": "conveyor", "x": 75, "y": 60, "w": 12, "h": 4, "rot": 0},
            "inv_qib": {"label": "Q-IB", "type": "inventory", "x": 64, "y": 65, "w": 6, "h": 6, "rot": 0},
            "qib": {"label": "Inspection B", "type": "machine", "x": 64, "y": 75, "w": 14, "h": 10, "rot": 0},
            "c8": {"label": "C8", "type": "conveyor", "x": 75, "y": 22, "w": 12, "h": 4, "rot": 0},
            "c9": {"label": "C9", "type": "conveyor", "x": 75, "y": 42, "w": 12, "h": 4, "rot": 0},
            "inv_oba": {"label": "Q-OBA", "type": "inventory", "x": 84, "y": 22, "w": 6, "h": 6, "rot": 0},
            "oba": {"label": "Output A", "type": "output", "x": 92, "y": 22, "w": 12, "h": 12, "rot": 0},
            "inv_obb": {"label": "Q-OBB", "type": "inventory", "x": 84, "y": 60, "w": 6, "h": 6, "rot": 0},
            "obb": {"label": "Output B", "type": "output", "x": 92, "y": 60, "w": 12, "h": 12, "rot": 0},
            "inv_tra": {"label": "Q-TRA", "type": "inventory", "x": 84, "y": 42, "w": 6, "h": 6, "rot": 0},
            "tra": {"label": "Trash", "type": "output", "x": 92, "y": 42, "w": 12, "h": 12, "rot": 0},
        }

        self._connector_pairs = [
            ("ir", "r0"), ("ir", "r1"),
            ("r0", "c0"), ("r1", "c1"),
            ("c0", "r2"), ("r2", "inv_cncm"), ("inv_cncm", "cncm"), ("r2", "c2"), ("r2", "c4"),
            ("c1", "r3"), ("r3", "inv_lz"), ("inv_lz", "lz"), ("r3", "c2"), ("r3", "c3"), ("r3", "c5"),
            ("c4", "r4"), ("r4", "inv_cncl"), ("inv_cncl", "cncl"), ("r4", "c3"), ("r4", "c6"), ("r4", "c7"),
            ("c6", "r5"), ("c5", "r6"), ("c7", "r6"),
            ("r5", "inv_qia"), ("inv_qia", "qia"), ("r6", "c10"), ("r6", "inv_qib"), ("inv_qib", "qib"),
            ("r5", "c8"), ("r5", "c9"), ("r6", "c9"),
            ("c8", "inv_oba"), ("inv_oba", "oba"),
            ("c10", "inv_obb"), ("inv_obb", "obb"),
            ("c9", "inv_tra"), ("inv_tra", "tra"),
        ]

    async def run(self, stop_event: asyncio.Event) -> None:
        tick_seconds = 0.5
        while not stop_event.is_set():
            await asyncio.sleep(tick_seconds)
            async with self._lock:
                self._tick += 1
                self._simulate_failures()
                self._dispatch_jobs(tick_seconds)
                self._spawn_jobs()
                self._consume_inventory()
                await self._sync_to_db()

    async def _sync_to_db(self) -> None:
        async with AsyncSessionLocal() as session:
            for row in self._build_machine_status(self._build_nodes()):
                await session.merge(MachineStatus(machine_id=row["machine_id"], current_state=row["current_state"], job_in_progress=row["job_in_progress"]))
            
            for row in self._build_inventory():
                await session.merge(RawInventory(material_id=row["material_id"], current_weight_kg=row["current_weight_kg"], last_updated=datetime.fromisoformat(row["last_updated"])))

            for job in self._jobs:
                await session.merge(WorkOrders(order_id=job.job_id, requesting_unit=job.requesting_unit, due_date=datetime.fromisoformat(job.due_date_iso), status=job.status))

            for ev in self._pending_lot_events:
                # We mock serial_id with job_id string
                session.add(LotEvents(serial_id=ev[0], station_point=ev[1], status=ev[2], timestamp=ev[3]))
            self._pending_lot_events.clear()
            
            await session.commit()

    async def snapshot(self) -> dict[str, Any]:
        async with self._lock:
            nodes = self._build_nodes()
            connectors = self._build_connectors()
            return {
                "schema_version": HYBRID_SCHEMA_VERSION,
                "mode": "mock",
                "cloud_status": True,
                "local_mesh_status": True,
                "latency_ms": 4.0,
                "telemetry_stats": {
                    "mock_tick": self._tick,
                    "jobs_active": len(self._jobs),
                },
                "work_orders": self._build_work_orders(),
                "machine_status": self._build_machine_status(nodes),
                "raw_inventory": self._build_inventory(),
                "schematic": {
                    "layout": "v2_branch_merge",
                    "nodes": nodes,
                    "connectors": connectors,
                },
            }

    def _simulate_failures(self) -> None:
        if self._status_overrides["r5"] == "Blocked":
            if self._rng.random() < 0.20:
                self._status_overrides["r5"] = "Idle"
        elif self._rng.random() < 0.025:
            self._status_overrides["r5"] = "Blocked"

        if self.dil_config.get("r6_offline"):
            self._status_overrides["r6"] = "Offline"
        else:
            if "r6" in self._status_overrides:
                del self._status_overrides["r6"]

        if self._status_overrides.get("qia", "") == "Offline":
            if self._rng.random() < 0.25:
                self._status_overrides["qia"] = "Idle"
        elif self._rng.random() < 0.02:
            self._status_overrides["qia"] = "Offline"

    def _spawn_jobs(self) -> None:
        if len(self._jobs) >= self._max_jobs:
            return
        if self._rng.random() > self._spawn_probability:
            return

        self._sequence += 1
        family = self._rng.choice(["gasket", "shaft", "housing", "bracket"])

        if family == "gasket":
            route = ["ir", "r1", "c1", "r3", "inv_lz", "lz", "r3", "c5", "r6", "c10", "inv_obb", "obb"]
        elif family == "shaft":
            route = ["ir", "r0", "c0", "r2", "c4", "r4", "inv_cncl", "cncl", "r4", "c6", "r5", "inv_qia", "qia", "r5", "c8", "inv_oba", "oba"]
        elif family == "housing":
            route = ["ir", "r0", "c0", "r2", "inv_cncm", "cncm", "r2", "c2", "r3", "c5", "r6", "c9", "inv_tra", "tra"]
        else:
            route = ["ir", "r1", "c1", "r3", "inv_lz", "lz", "r3", "c3", "r4", "inv_cncl", "cncl", "r4", "c7", "r6", "inv_qib", "qib"]

        total_time = sum(self._duration_for_node(n) for n in route)
        due_date = datetime.now(timezone.utc) + timedelta(hours=self._rng.randint(8, 36))
        job = MockJob(
            job_id=f"WO-{self._sequence}",
            part_family=family,
            requesting_unit=self._rng.choice(["CVN-68", "SSN-774", "DDG-51", "LCS-19"]),
            due_date_iso=due_date.isoformat(),
            route=route,
            step_index=0,
            step_remaining_s=self._duration_for_node(route[0]),
            status="Queued",
            total_processing_time=total_time,
        )
        self._jobs.append(job)
        self._pending_lot_events.append((job.job_id, route[0], 'Entered', datetime.now(timezone.utc)))

    def _dispatch_jobs(self, tick_s: float) -> None:
        self._in_transition = {}
        completed: list[MockJob] = []

        if self.routing_algorithm == "SPT":
            self._jobs.sort(key=lambda j: j.total_processing_time)
        elif self.routing_algorithm == "EDD":
            self._jobs.sort(key=lambda j: j.due_date_iso)

        processed_nodes = set()

        for job in self._jobs:
            current_node = job.route[job.step_index]
            if self._is_blocked(current_node):
                job.status = "Blocked"
                continue

            # Capacity constraint Check (O(1) approximation)
            if current_node in processed_nodes and self._node_capacity.get(current_node, 1) <= 1:
                job.status = "Queued"
                continue

            processed_nodes.add(current_node)
            job.status = "Busy"
            job.step_remaining_s -= tick_s

            if job.step_remaining_s > 0:
                continue

            prev_node = current_node
            if job.step_index + 1 < len(job.route):
                next_node = job.route[job.step_index + 1]
                
                # Check downstream capacity before transition
                next_jobs_count = sum(1 for j in self._jobs if j.route[j.step_index] == next_node)
                if next_jobs_count >= self._node_capacity.get(next_node, 1):
                    job.status = "Blocked by Capacity"
                    continue

                job.step_index += 1
                self._in_transition[job.job_id] = (prev_node, next_node)
                job.step_remaining_s = self._duration_for_node(next_node)
                self._pending_lot_events.append((job.job_id, prev_node, "Left", datetime.now(timezone.utc)))
                self._pending_lot_events.append((job.job_id, next_node, "Entered", datetime.now(timezone.utc)))
                
                # Rework Injection for Lathe -> Trash
                if prev_node == "cncl" and self._rng.random() < 0.05:
                    job.route = job.route[:job.step_index] + ["r4", "c6", "r5", "c9", "tra"]
            else:
                job.status = "Completed"
                completed.append(job)
                self._pending_lot_events.append((job.job_id, current_node, "Completed", datetime.now(timezone.utc)))

        if completed:
            completed_ids = {job.job_id for job in completed}
            self._jobs = [job for job in self._jobs if job.job_id not in completed_ids]

    def _is_blocked(self, node_id: str) -> bool:
        return self._status_overrides.get(node_id) in {"Blocked", "Offline"}

    def _duration_for_node(self, node_id: str) -> float:
        base = 1.0
        # Incorporate High Variance for Lathe (M/G/1 simulation)
        if node_id == "cncl":
            # Lognormal distribution: CV = 1.5
            mu = math.log(3.7) - 0.5 * math.log(1 + 1.5**2)
            sigma = math.sqrt(math.log(1 + 1.5**2))
            return max(1.0, self._rng.lognormvariate(mu, sigma))
            
        durations = {
            "ir": 0.6,
            "r0": 0.9, "r1": 0.9,
            "inv_cncm": 0.2, "inv_lz": 0.2, "inv_cncl": 0.2,
            "cncm": 4.8, "lz": 2.6,
            "c0": 0.5, "c1": 0.5, "c2": 0.5, "c3": 0.5, "c4": 0.5, "c5": 0.5, "c6": 0.5, "c7": 0.5, "c8": 0.5, "c9": 0.5, "c10": 0.5,
            "r2": 1.0, "r3": 1.0, "r4": 1.0, "r5": 1.0, "r6": 1.0,
            "inv_qia": 0.2, "inv_qib": 0.2,
            "qia": 3.0, "qib": 3.0,
            "inv_oba": 0.2, "inv_obb": 0.2, "inv_tra": 0.2,
            "oba": 1.0, "obb": 1.0, "tra": 1.0,
        }
        base = durations.get(node_id, 1.0)
        return max(0.2, base + self._rng.uniform(-0.25, 0.25))

    def _consume_inventory(self) -> None:
        active_cutting = sum(1 for job in self._jobs if job.route[job.step_index] in {"cncm", "cncl", "lz"})
        if active_cutting == 0:
            return

        self._inventory_kg["PLA-3"] = max(0.0, self._inventory_kg["PLA-3"] - 0.002 * active_cutting)
        self._inventory_kg["AL-6061"] = max(0.0, self._inventory_kg["AL-6061"] - 0.0015 * active_cutting)
        self._inventory_kg["STEEL-17"] = max(0.0, self._inventory_kg["STEEL-17"] - 0.001 * active_cutting)

    def reset(self) -> None:
        self._jobs.clear()
        self._in_transition.clear()

    def _node_status_map(self) -> dict[str, str]:
        status_map = {node_id: "Idle" for node_id in self._node_definitions}

        for node_id, forced in self._status_overrides.items():
            if forced in {"Blocked", "Offline"}:
                status_map[node_id] = forced

        for job in self._jobs:
            node_id = job.route[job.step_index]
            if status_map[node_id] in {"Blocked", "Offline"}:
                continue
            status_map[node_id] = "Busy"

        return status_map

    def _jobs_at_node(self, node_id: str) -> int:
        return sum(1 for job in self._jobs if job.route[job.step_index] == node_id)

    def _queue_depth_at_node(self, node_id: str) -> int:
        capacity = self._node_capacity.get(node_id, 1)
        active_jobs = self._jobs_at_node(node_id)
        return max(0, active_jobs - capacity)

    def _build_nodes(self) -> list[dict[str, Any]]:
        status_map = self._node_status_map()
        nodes = []

        for node_id, node_meta in self._node_definitions.items():
            active_jobs = self._jobs_at_node(node_id)
            nodes.append(
                {
                    "id": node_id,
                    "label": node_meta["label"],
                    "type": node_meta["type"],
                    "source": "mock",
                    "status": status_map[node_id],
                    "active_jobs": active_jobs,
                    "queue_depth": self._queue_depth_at_node(node_id),
                    "x": node_meta["x"],
                    "y": node_meta["y"],
                    "w": node_meta["w"],
                    "h": node_meta["h"],
                    "rot": node_meta["rot"],
                }
            )

        return nodes

    def _build_connectors(self) -> list[dict[str, Any]]:
        active_pairs = set(self._in_transition.values())
        reverse_pairs = {(to_node, from_node) for (from_node, to_node) in active_pairs}

        connectors = []
        for from_node, to_node in self._connector_pairs:
            connectors.append(
                {
                    "from": from_node,
                    "to": to_node,
                    "active": (from_node, to_node) in active_pairs or (from_node, to_node) in reverse_pairs,
                    "bidirectional": True,
                    "kind": "conveyor" if "c" in from_node or "c" in to_node else "robot",
                }
            )

        return connectors

    def _build_work_orders(self) -> list[dict[str, Any]]:
        rows = []
        for job in self._jobs[:15]:
            current_node = job.route[job.step_index]
            next_node = job.route[job.step_index + 1] if job.step_index + 1 < len(job.route) else None
            meta = "SPT Sorted" if job.total_processing_time < 5.0 else ""
            rows.append(
                {
                    "order_id": int(job.job_id.split("-")[-1]),
                    "requesting_unit": job.requesting_unit,
                    "due_date": job.due_date_iso,
                    "status": f"{job.part_family}:{current_node}:{job.status} {meta}",
                    "route": list(job.route),
                    "step_index": job.step_index,
                    "current_node": current_node,
                    "next_node": next_node,
                }
            )
        return rows

    def _build_machine_status(self, nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
        node_lookup = {node["id"]: node for node in nodes}

        def job_for(node_id: str) -> str | None:
            for job in self._jobs:
                if job.route[job.step_index] == node_id:
                    return job.job_id
            return None

        return [
            {
                "machine_id": "M1 (Mill)",
                "current_state": node_lookup["cncm"]["status"],
                "job_in_progress": job_for("cncm"),
                "est_completion": None,
            },
            {
                "machine_id": "M2 (Laser)",
                "current_state": node_lookup["lz"]["status"],
                "job_in_progress": job_for("lz"),
                "est_completion": None,
            },
            {
                "machine_id": "M3 (Lathe)",
                "current_state": node_lookup["cncl"]["status"],
                "job_in_progress": job_for("cncl"),
                "est_completion": None,
            },
        ]

    def _build_inventory(self) -> list[dict[str, Any]]:
        now = datetime.now(timezone.utc).isoformat()
        return [
            {
                "material_id": material,
                "current_weight_kg": round(weight, 3),
                "last_updated": now,
            }
            for material, weight in self._inventory_kg.items()
        ]
