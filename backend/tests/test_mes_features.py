import pytest
import asyncio
from datetime import datetime, timezone
from app.mock_telemetry import MockTelemetryEngine

def test_dil_adversarial_settings():
    engine = MockTelemetryEngine()
    engine.dil_config = {"r6_offline": True, "packet_loss": 0, "latency": 0, "jitter": 0}
    engine._simulate_failures()
    
    status_map = engine._node_status_map()
    assert status_map["r6"] == "Offline", "DIL config should forcibly offline R6"

    # Turn it back on
    engine.dil_config = {"r6_offline": False, "packet_loss": 0, "latency": 0, "jitter": 0}
    engine._simulate_failures()
    status_map = engine._node_status_map()
    # It should not be forced offline anymore. It might remain something else or Idle
    assert status_map["r6"] != "Offline", "DIL config should lift offline restriction"


def test_spt_routing_algorithm():
    engine = MockTelemetryEngine()
    
    # Spawn explicitly multiple jobs so we can test routing behavior
    engine.routing_algorithm = "SPT"
    
    engine._spawn_jobs() # creates job 1
    engine._spawn_jobs() # creates job 2 
    engine._spawn_jobs() # creates job 3
    
    if len(engine._jobs) > 1:
        engine._dispatch_jobs(1.0)
        # Verify SPT sort
        for i in range(len(engine._jobs) - 1):
            assert engine._jobs[i].total_processing_time <= engine._jobs[i+1].total_processing_time, "Queue should be ordered by SPT"

def test_edd_routing_algorithm():
    engine = MockTelemetryEngine()
    engine.routing_algorithm = "EDD"
    
    # Spawn multiple jobs
    for _ in range(5):
        engine._spawn_jobs()
        
    if len(engine._jobs) > 1:
        engine._dispatch_jobs(1.0)
        for i in range(len(engine._jobs) - 1):
            date_a = datetime.fromisoformat(engine._jobs[i].due_date_iso)
            date_b = datetime.fromisoformat(engine._jobs[i+1].due_date_iso)
            assert date_a <= date_b, "Queue should be ordered by Earliest Due Date"
