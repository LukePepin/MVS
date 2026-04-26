import unittest
from datetime import datetime, timezone
from backend.app.mock_telemetry import MockTelemetryEngine

class TestMesFeatures(unittest.TestCase):
    def test_dil_adversarial_settings(self):
        engine = MockTelemetryEngine()
        engine.dil_config = {"r6_offline": True, "packet_loss": 0, "latency": 0, "jitter": 0}
        engine._simulate_failures()
        
        status_map = engine._node_status_map()
        self.assertEqual(status_map["r6"], "Offline", "DIL config should forcibly offline R6")

        # Turn it back on.
        engine.dil_config = {"r6_offline": False, "packet_loss": 0, "latency": 0, "jitter": 0}
        engine._simulate_failures()
        status_map = engine._node_status_map()
        self.assertNotEqual(status_map["r6"], "Offline", "DIL config should lift offline restriction")


    def test_spt_routing_algorithm(self):
        engine = MockTelemetryEngine()
        engine.routing_algorithm = "SPT"

        engine._spawn_jobs()
        engine._spawn_jobs()
        engine._spawn_jobs()

        if len(engine._jobs) > 1:
            engine._dispatch_jobs(1.0)
            for i in range(len(engine._jobs) - 1):
                self.assertLessEqual(
                    engine._jobs[i].total_processing_time,
                    engine._jobs[i + 1].total_processing_time,
                    "Queue should be ordered by SPT",
                )

    def test_edd_routing_algorithm(self):
        engine = MockTelemetryEngine()
        engine.routing_algorithm = "EDD"

        for _ in range(5):
            engine._spawn_jobs()

        if len(engine._jobs) > 1:
            engine._dispatch_jobs(1.0)
            for i in range(len(engine._jobs) - 1):
                date_a = datetime.fromisoformat(engine._jobs[i].due_date_iso)
                date_b = datetime.fromisoformat(engine._jobs[i + 1].due_date_iso)
                self.assertLessEqual(date_a, date_b, "Queue should be ordered by Earliest Due Date")


if __name__ == "__main__":
    unittest.main()
