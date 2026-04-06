import argparse
import csv
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import serial
from serial.tools import list_ports

EXPECTED_COLUMNS = 9
CSV_HEADER = [
    "NodeID",
    "Accel_X",
    "Accel_Y",
    "Accel_Z",
    "Gyro_X",
    "Gyro_Y",
    "Gyro_Z",
    "Mag_X",
    "Mag_Y",
    "Mag_Z",
    "Timestamp",
]


def list_available_ports() -> list[str]:
    return [port.device for port in list_ports.comports()]


def print_available_ports() -> None:
    ports = list_available_ports()
    if not ports:
        print("No serial ports detected.")
        return

    print("Detected serial ports:")
    for port in ports:
        print(f"  - {port}")


def parse_imu_line(line: str) -> list[float] | None:
    parts = [part.strip() for part in line.split(",")]
    if len(parts) != EXPECTED_COLUMNS:
        return None

    values: list[float] = []
    try:
        for part in parts:
            values.append(float(part))
    except ValueError:
        return None

    return values


def ensure_csv_header(csv_path: Path) -> None:
    if csv_path.exists() and csv_path.stat().st_size > 0:
        return

    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(CSV_HEADER)


def run_datalogger(
    port: str,
    baud: int,
    out_csv: Path,
    node_id: str,
    duration_s: float,
    startup_wait_s: float,
) -> None:
    print(f"Opening {port} at {baud} baud...")

    if os.name != "nt" and port.upper().startswith("COM"):
        print(
            "Invalid port for Linux container: COM ports are Windows-only. "
            "Use /dev/ttyUSB0 or /dev/ttyACM0, or run this script on the Windows host."
        )
        print_available_ports()
        raise SystemExit(2)

    ensure_csv_header(out_csv)

    rows_written = 0
    invalid_rows = 0
    start = time.time()

    try:
        with serial.Serial(port=port, baudrate=baud, timeout=1) as ser, out_csv.open(
            "a", newline="", encoding="utf-8"
        ) as csv_file:
            writer = csv.writer(csv_file)

            # Nano 33 BLE may reset on port-open.
            time.sleep(startup_wait_s)

            print("Connected. Logging IMU stream...")
            print("Expected format: ax,ay,az,gx,gy,gz,mx,my,mz")

            while True:
                if duration_s > 0 and (time.time() - start) >= duration_s:
                    break

                raw = ser.readline().decode("utf-8", errors="replace").strip()
                if not raw:
                    continue

                parsed = parse_imu_line(raw)
                if parsed is None:
                    invalid_rows += 1
                    if invalid_rows <= 5:
                        print(f"Skipping non-IMU line: {raw}")
                    continue

                timestamp = datetime.now(timezone.utc).isoformat()
                row = [node_id, *parsed, timestamp]
                writer.writerow(row)
                csv_file.flush()
                rows_written += 1

                if rows_written % 50 == 0:
                    elapsed = time.time() - start
                    print(f"Logged {rows_written} rows in {elapsed:.1f}s")

    except serial.SerialException as exc:
        print(f"Serial open/read failed: {exc}")
        print_available_ports()
        if os.name != "nt":
            print("Tip: if running in Docker, pass through the USB device to the container.")
        raise SystemExit(1) from exc

    elapsed = time.time() - start
    rate = rows_written / elapsed if elapsed > 0 else 0.0
    print("Datalogger complete.")
    print(f"Rows written: {rows_written}")
    print(f"Invalid lines skipped: {invalid_rows}")
    print(f"Elapsed: {elapsed:.2f}s, approx rate: {rate:.2f} rows/s")
    print(f"Output: {out_csv}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Phase 2 IMU datalogger for Arduino Nano 33 BLE"
    )
    parser.add_argument("--port", default="COM15", help="Serial port, e.g. COM15 or /dev/ttyUSB0")
    parser.add_argument("--baud", type=int, default=115200, help="Baud rate")
    parser.add_argument(
        "--out",
        default="backend/training_data.csv",
        help="Output CSV file path",
    )
    parser.add_argument(
        "--node-id",
        default="niryo-wrist-imu",
        help="Node ID written to CSV NodeID column",
    )
    parser.add_argument(
        "--duration",
        type=float,
        default=900.0,
        help="Capture duration in seconds. Use 0 for indefinite logging.",
    )
    parser.add_argument(
        "--startup-wait",
        type=float,
        default=2.0,
        help="Seconds to wait after opening serial port before reading",
    )
    parser.add_argument(
        "--list-ports",
        action="store_true",
        help="List detected serial ports and exit",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.list_ports:
        print_available_ports()
        return

    out_csv = Path(args.out)
    out_csv.parent.mkdir(parents=True, exist_ok=True)

    run_datalogger(
        port=args.port,
        baud=args.baud,
        out_csv=out_csv,
        node_id=args.node_id,
        duration_s=args.duration,
        startup_wait_s=args.startup_wait,
    )


if __name__ == "__main__":
    main()
