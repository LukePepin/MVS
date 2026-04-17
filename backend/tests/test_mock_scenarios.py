import asyncio
import random
import sys
from pathlib import Path
import unittest

backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app.mock_telemetry import MockTelemetryEngine


def tick_engine(engine: MockTelemetryEngine, tick_s: float, steps: int) -> None:
    for _ in range(steps):
        engine._simulate_failures()
        engine._dispatch_jobs(tick_s)
        engine._spawn_jobs()
        engine._consume_inventory()
        engine._tick += 1


class TestMockScenarios(unittest.TestCase):
    def test_jobs_spawn_and_work_orders(self) -> None:
        engine = MockTelemetryEngine()
        engine._rng = random.Random(1)

        for _ in range(60):
            engine._spawn_jobs()

        self.assertGreater(len(engine._jobs), 0, "Expected mock engine to spawn jobs")

        nodes = engine._build_nodes()
        node_ids = {node["id"] for node in nodes}
        self.assertIn("r6", node_ids)
        self.assertIn("cncl", node_ids)

        work_orders = engine._build_work_orders()
        self.assertLessEqual(len(work_orders), 15)

    def test_transitions_mark_connectors(self) -> None:
        engine = MockTelemetryEngine()
        engine._rng = random.Random(2)

        for _ in range(25):
            engine._spawn_jobs()
            tick_engine(engine, tick_s=0.5, steps=1)

        connectors = engine._build_connectors()
        self.assertGreater(len(connectors), 0)
        keys = {"from", "to", "active", "kind", "bidirectional"}
        self.assertTrue(all(keys.issubset(connector.keys()) for connector in connectors))


if __name__ == "__main__":
    unittest.main()
