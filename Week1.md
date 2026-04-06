# 90-Minute Deep Work Session: MVS ROS & Hardware Setup
Date: 2026-04-04

## Progress Update
Date: 2026-04-06

- Arduino serial connectivity test completed successfully on Windows host using COM15 at 115200 baud.
- Host-side Python test confirmed stable heartbeat and ACK ping responses end-to-end.
- Git workflow is configured and operational.
- Docker environment is installed, running, and containers are starting successfully for development.
- Development plan status transitioned from Week 1 Phase 1 to Week 1 Phase 2 (Physical Hardware Assembly).

Week 1 Phase 1 completed on 2026-04-06. Completed serial checklist archived under `docs_archive/`.

## Phase 2: Physical Hardware Assembly (30 Minutes)

> [!IMPORTANT]
> **Goal:** Secure physical setup of the Arduino Nano 33 BLE onto the end-effector.

1. **Mounting:** Use zip-ties or a 3D-printed fixture to attach the Arduino Nano 33 BLE firmly to the moving arm of the physical robot. *Do not leave it dangling by the wire, as cable whip will corrupt your IMU baseline.*
2. **Flashing the BLE:** 
   - Open Arduino IDE.
   - Flash `backend/arduino_nano_serial_test/arduino_nano_serial_test.ino`.
3. **Network Decision (Niryo):**
   - Yes, use the same network when you need direct Niryo control/ROS2 state integration.
   - No, same network is not required for USB-only Arduino serial logging on one machine.
4. **Joint/Location Decision:**
   - Mount at the wrist-side end-effector region (tool flange area, near final joint), not on base or shoulder joints.
5. **Connectivity Verification:**
   - Open Serial Monitor at 115200 baud and confirm each line is 9 comma-separated IMU values: `ax,ay,az,gx,gy,gz,mx,my,mz`.

## Phase 4: Baseline Execution & Validation (20 Minutes)

> [!CAUTION]
> **Goal:** Gathering real data. Stay clear of the robotic envelope while the nominal loop executes.

1. **Execution Loop:** Command your robot (via ROS or its native pendant) to execute the standardized kinematic loop continuously.
2. **Data Logging:** Track the loop for 15 minutes, allowing your Datalogger to accumulate a solid starting baseline (a few thousand rows).
3. **Teardown & Verification:** After stopping the robot, open `training_data.csv` and ensure all rows have 10 columns and timestamps are incrementing as expected.
