"""
Test suite for the DES routing engine and PuLP scheduling.
Verifies EDD ordering, SPT ordering, simulation state transitions,
and EARC product route integrity.
"""
import unittest
import asyncio
import sys
import os

# Ensure backend is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from backend.simulation.des_engine import (
    optimize_schedule_edd,
    optimize_schedule_spt,
    run_headless_simulation,
    LiveSimulationState,
    EARCSimulation,
    SimulationStatus,
    PRODUCTS,
)


class TestEDDScheduling(unittest.TestCase):
    """Verify that PuLP-based EDD scheduling produces correct orderings."""

    def test_edd_orders_by_due_date(self):
        """EDD should schedule earlier due-date jobs first."""
        orders = [
            {"id": 0, "product": "Gasket_A", "route": ["R0", "M2", "R1"],
             "cycle_times": {"R0": 2, "M2": 15, "R1": 3}, "due": 500},
            {"id": 1, "product": "Shaft_B", "route": ["R0", "M3", "R1"],
             "cycle_times": {"R0": 2, "M3": 45, "R1": 5}, "due": 100},
            {"id": 2, "product": "Housing_C", "route": ["R0", "M1", "R1"],
             "cycle_times": {"R0": 3, "M1": 60, "R1": 5}, "due": 300},
        ]
        scheduled = optimize_schedule_edd(orders)
        ids = [wo["id"] for wo in scheduled]
        # Job 1 (due 100) should be first, Job 2 (due 300) second, Job 0 (due 500) third
        self.assertEqual(ids[0], 1, "Earliest due-date job should be scheduled first")
        self.assertEqual(ids[-1], 0, "Latest due-date job should be scheduled last")

    def test_edd_empty_list(self):
        """EDD should handle empty work order list gracefully."""
        result = optimize_schedule_edd([])
        self.assertEqual(result, [])

    def test_edd_single_job(self):
        """EDD should handle a single job."""
        orders = [{"id": 0, "product": "Gasket_A", "route": ["R0", "M2", "R1"],
                    "cycle_times": {"R0": 2, "M2": 15, "R1": 3}, "due": 100}]
        result = optimize_schedule_edd(orders)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["id"], 0)


class TestSPTScheduling(unittest.TestCase):
    """Verify SPT scheduling orders by total processing time."""

    def test_spt_shortest_first(self):
        """SPT should place shortest total processing time first."""
        orders = [
            {"id": 0, "product": "Housing_C", "route": ["R0", "M1", "R1"],
             "cycle_times": {"R0": 3, "M1": 60, "R1": 5}, "due": 500},  # total = 68
            {"id": 1, "product": "Gasket_A", "route": ["R0", "M2", "R1"],
             "cycle_times": {"R0": 2, "M2": 15, "R1": 3}, "due": 100},  # total = 20
            {"id": 2, "product": "Shaft_B", "route": ["R0", "M3", "R1"],
             "cycle_times": {"R0": 2, "M3": 45, "R1": 5}, "due": 300},  # total = 52
        ]
        scheduled = optimize_schedule_spt(orders)
        ids = [wo["id"] for wo in scheduled]
        self.assertEqual(ids[0], 1, "Shortest processing time job should be first")
        self.assertEqual(ids[-1], 0, "Longest processing time job should be last")


class TestHeadlessSimulation(unittest.TestCase):
    """Verify that the headless simulation runs to completion."""

    def test_headless_completes(self):
        """Headless simulation should return valid results."""
        result = asyncio.run(run_headless_simulation(10))
        self.assertIn("completed_jobs", result)
        self.assertIn("average_flow_time", result)
        self.assertIn("simulated_oee", result)
        self.assertGreater(result["completed_jobs"], 0, "Should complete at least 1 job")
        self.assertGreater(result["average_flow_time"], 0, "Flow time should be positive")


class TestSimulationState(unittest.TestCase):
    """Verify the LiveSimulationState container."""

    def test_initial_state(self):
        state = LiveSimulationState()
        self.assertEqual(state.status, SimulationStatus.IDLE)
        self.assertEqual(state.completed_jobs, 0)
        self.assertEqual(state.sim_time, 0.0)

    def test_snapshot_structure(self):
        state = LiveSimulationState()
        state.sim_time = 15.0
        state.num_jobs = 750
        snap = state.snapshot()
        self.assertIn("sim_status", snap)
        self.assertIn("tokens", snap)
        self.assertIn("station_busy", snap)
        self.assertIn("events_log", snap)
        self.assertIn("project_start_iso", snap)
        self.assertIn("simulated_time_iso", snap)
        self.assertIn("num_jobs", snap)
        self.assertEqual(snap["num_jobs"], 750)
        self.assertEqual(snap["sim_status"], "idle")


class TestProductRoutes(unittest.TestCase):
    """Verify EARC product topology definitions."""

    def test_all_products_have_routes(self):
        for name, info in PRODUCTS.items():
            self.assertIn("route", info, f"{name} missing route")
            self.assertIn("cycle_times", info, f"{name} missing cycle_times")
            self.assertGreater(len(info["route"]), 0, f"{name} has empty route")

    def test_routes_start_at_r0_end_at_r1(self):
        for name, info in PRODUCTS.items():
            self.assertEqual(info["route"][0], "R0", f"{name} should start at R0")
            self.assertEqual(info["route"][-1], "R1", f"{name} should end at R1")


if __name__ == "__main__":
    unittest.main()
