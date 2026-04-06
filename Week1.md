# 90-Minute Deep Work Session: MVS ROS & Hardware Setup
Date: 2026-04-04

This schedule is optimized for a focused 90-minute block to get your Docker ROS environment mapped, your hardware (Arduino Nano 33 BLE) wired and mounted, and your initial IMU telemetry baseline logging.

## Phase 1: Environment & File Cleanup (15 Minutes)

> [!TIP]
> **Goal:** Archiving old files so your workspace is clean, then setting up an isolated Docker Linux environment for ROS to avoid Windows host pathing issues.

1. **File Movement:** Move all legacy, non-MVP test scripts and PDF outputs into `docs_archive/`. Ensure nothing clutters the root of `MVS/`.
2. **Docker Network & Volume Prep:** 
   - Write a quick `docker-compose.yml` (or use a raw `docker run` script) to pull a `ros:noetic-ros-base` or `ros:humble-ros-base` (depending on your ROS version).
   - Mount your serial devices (e.g., `--device=/dev/ttyUSB0` or the Windows equivalent if using WSL2 USB Passthrough) into the container so the Datalogger can see the Arduino.
3. **Workspace Initialization:** Spin up the container and initialize your catkin or colcon workspace. 

## Phase 2: Physical Hardware Assembly (30 Minutes)

> [!IMPORTANT]
> **Goal:** Secure physical setup of the Arduino Nano 33 BLE onto the end-effector.

1. **Mounting:** Use zip-ties or a 3D-printed fixture to attach the Arduino Nano 33 BLE firmly to the moving arm of the physical robot. *Do not leave it dangling by the wire, as cable whip will corrupt your IMU baseline.*
2. **Flashing the BLE:** 
   - Open Arduino IDE.
   - Flash the `Arduino_LSM9DS1` baseline sketch (polling at ~50 Hz, outputting raw comma-separated values to `Serial.print`).
3. **Connectivity Verification:** Open the Serial Monitor on your laptop to verify you are getting a clean stream of `x,y,z` for the accelerometer, gyroscope, and magnetometer.

## Phase 3: Build & Test the Datalogger (25 Minutes)

> [!NOTE]
> **Goal:** Routing data through your Python logger to get the exact 10 columns needed for your ML proposal.

1. **Script Placement:** Put your Python Datalogger script inside the new ROS Docker container (or run natively if Docker USB mapping fights you today).
2. **Library Checks:** Ensure `pyserial` is installed via `pip`.
3. **Dry Run:** Boot the script and ensure it successfully detects the COM port, appends an ISO-8601 timestamp, and writes cleanly to `training_data.csv` without throwing Unicode or port busy errors.

## Phase 4: Baseline Execution & Validation (20 Minutes)

> [!CAUTION]
> **Goal:** Gathering real data. Stay clear of the robotic envelope while the nominal loop executes.

1. **Execution Loop:** Command your robot (via ROS or its native pendant) to execute the standardized kinematic loop continuously.
2. **Data Logging:** Track the loop for 15 minutes, allowing your Datalogger to accumulate a solid starting baseline (a few thousand rows).
3. **Teardown & Verification:** After stopping the robot, open `training_data.csv` and ensure all rows have 10 columns and timestamps are incrementing as expected.
