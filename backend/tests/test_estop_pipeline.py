import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add backend directory to sys.path to import the modules
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

import phase2_datalogger
import MVS_data_collection

class TestEStopPipeline(unittest.TestCase):
    def setUp(self):
        # Make sure the flag doesn't exist before testing
        self.flag_path = backend_dir / "estop.flag"
        if self.flag_path.exists():
            self.flag_path.unlink()
            
        # Ensure tests dir exists for dummy output
        self.tests_dir = backend_dir / "tests"
        self.tests_dir.mkdir(exist_ok=True)

    def tearDown(self):
        # Cleanup the flag after tests
        if self.flag_path.exists():
            self.flag_path.unlink()

    @patch('phase2_datalogger.serial.Serial')
    @patch('phase2_datalogger.time.time')
    def test_datalogger_estop_flag_creation(self, mock_time, mock_serial_class):
        def mock_time_func():
            mock_time_func.val += 0.1
            return mock_time_func.val
        mock_time_func.val = 0.0
        mock_time.side_effect = mock_time_func
        
        # Setup mock serial instance
        mock_serial_instance = MagicMock()
        mock_serial_class.return_value.__enter__.return_value = mock_serial_instance
        
        def mock_readline():
            mock_readline.call_count += 1
            if mock_readline.call_count == 2:
                return b"ESTOP:COLLISION\n"
            return b"0.1,0.2,0.3,0.4,0.5,0.6\n"
        mock_readline.call_count = 0
        mock_serial_instance.readline.side_effect = mock_readline
        
        out_csv = self.tests_dir / "dummy_out.csv"
        if out_csv.exists():
            out_csv.unlink()
            
        phase2_datalogger.run_datalogger(
            port="COM_DUMMY",
            port_candidates=["COM_DUMMY"],
            baud=115200,
            out_csv=out_csv,
            node_id="test-node",
            duration_s=2.0,
            startup_wait_s=0.0,
            axes=6,
            reconnect_wait_s=0.0,
            max_reconnects=0,
            no_data_timeout_s=5.0
        )
        
        # Assertion: estop.flag should have been created by the logger receiving ESTOP
        self.assertTrue(self.flag_path.exists(), "estop.flag should be created by datalogger when ESTOP is received")

    @patch('MVS_data_collection.move_to_pose_name')
    @patch('MVS_data_collection.time.sleep')
    def test_data_collection_stops_on_estop_flag(self, mock_sleep, mock_move):
        # Manually create the flag to simulate an active E-STOP
        self.flag_path.touch()
        
        robot_mock = MagicMock()
        
        # Run sequence with expected 3 repeats
        MVS_data_collection.run_sequence(
            robot=robot_mock,
            repeats=3,
            sleep_s=0,
            dry_run=False,
            group1=["1v1"],
            group2=["2v1"],
            group3=["3v1"],
            group4=["4v1"]
        )
        
        # Assertion: Sequence should have immediately broken out; zero moves requested.
        mock_move.assert_not_called()
        
        # Clean up flag and test the nominal case
        self.flag_path.unlink()
        
        MVS_data_collection.run_sequence(
            robot=robot_mock,
            repeats=1,
            sleep_s=0,
            dry_run=False,
            group1=["1v1"],
            group2=["2v1"],
            group3=["3v1"],
            group4=["4v1"]
        )
        
        # Assertion: With 1 repeat and no E-STOP, we expect exactly 5 moves (Home + 4 poses)
        self.assertEqual(mock_move.call_count, 5)

if __name__ == '__main__':
    unittest.main()
