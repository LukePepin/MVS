# Arduino Serial Test Implementation Todo

## Scope
Complete the Arduino serial verification flow using:
- backend/arduino_nano_serial_test/arduino_nano_serial_test.ino
- backend/serial_test.py

## Preflight
- [x] Confirm Arduino IDE board and port are correct.
- [x] Close Arduino Serial Monitor before running Python (prevents port lock).
- [x] Install Python dependency:
  - pip install -r backend/requirements.txt
  - or pip install pyserial

## Upload Step
- [x] Open and upload:
  - backend/arduino_nano_serial_test/arduino_nano_serial_test.ino
- [x] Verify upload succeeds with no compile errors.

## Backend Script Step
- [x] Run host-side serial test:
  - python backend/serial_test.py --port COM15 --baud 115200 --duration 10
- [x] Expected output includes:
  - NANO_READY
  - HB <millis>
  - ACK:PING 1, ACK:PING 2, ...

## Troubleshooting
- [ ] If port open fails:
  - confirm COM port (or /dev/ttyUSB0, /dev/ttyACM0 on Linux)
  - close all tools using the serial port
  - unplug/replug board and rerun

## Optional Docker Note
- [ ] If testing in container, ensure USB serial device is passed through first.
- [ ] Then run:
  - python backend/serial_test.py --port /dev/ttyUSB0 --baud 115200 --duration 10

## Done Criteria
- [x] Sketch uploaded successfully.
- [x] Python script ran for full duration with heartbeat and ACK responses.
- [ ] Test can be repeated successfully after reconnecting the board.

## Current Status (2026-04-06)
- Week 1 Phase 1 complete.
- Transitioned to Week 1 Phase 2 (Physical Hardware Assembly).
