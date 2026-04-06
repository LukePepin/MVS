import argparse
import os
import sys
import time

import serial
from serial.tools import list_ports


def get_available_ports() -> list[str]:
    return [port.device for port in list_ports.comports()]


def print_available_ports() -> None:
    ports = get_available_ports()
    if not ports:
        print("No serial ports detected.")
        return

    print("Detected serial ports:")
    for port in ports:
        print(f"  - {port}")


def run_test(port: str, baud: int, duration_s: float) -> None:
    print(f"Opening {port} at {baud} baud...")

    if os.name != "nt" and port.upper().startswith("COM"):
        print(
            "Invalid port for Linux container: COM ports are Windows-only. "
            "Use /dev/ttyUSB0 or /dev/ttyACM0, or run this script on the Windows host."
        )
        print_available_ports()
        raise SystemExit(2)

    try:
        with serial.Serial(port=port, baudrate=baud, timeout=1) as ser:
            # Some boards reset when the port opens; give it a moment to boot.
            time.sleep(2)

            print("Connected. Reading initial messages...")
            start = time.time()
            ping_count = 0

            while time.time() - start < duration_s:
                ping_count += 1
                payload = f"PING {ping_count}".encode("utf-8")
                ser.write(payload + b"\n")

                line = ser.readline().decode("utf-8", errors="replace").strip()
                if line:
                    print(f"< {line}")

                time.sleep(0.5)
    except serial.SerialException as exc:
        print(f"Serial open/read failed: {exc}")
        print_available_ports()
        if os.name != "nt":
            print("Tip: if running in Docker, pass through the USB device to the container.")
        raise SystemExit(1) from exc

    print("Serial test complete.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Arduino Nano serial connection test")
    parser.add_argument("--port", default="COM15", help="Serial port, e.g. COM15")
    parser.add_argument("--baud", type=int, default=115200, help="Baud rate")
    parser.add_argument("--duration", type=float, default=10.0, help="Test duration in seconds")
    parser.add_argument(
        "--list-ports",
        action="store_true",
        help="List detected serial ports and exit",
    )
    args = parser.parse_args()

    if args.list_ports:
        print_available_ports()
        return

    run_test(port=args.port, baud=args.baud, duration_s=args.duration)


if __name__ == "__main__":
    main()