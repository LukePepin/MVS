# Implementation Plan: Testbed Inventory and Physical Telemetry Collection

Date: 2026-04-03

Based on your feedback regarding the MVS Thesis and ISE572 ML Project Proposal requirements, you need a high-quality physical IMU dataset (accelerometer, gyroscope, magnetometer) to train your TinyML Autoencoder for anomaly detection. Since synthesizing this accurately via the digital twin is challenging and unnecessary for your core ML goals, we will bypass the mock IMU generator entirely. Instead, I will provide a step-by-step physical hardware collection plan.

Additionally, we need to update the digital twin testbed to include explicit inventory queues for the machining centers and outputs to prevent backlogs.

## User Review Required

> [!IMPORTANT]
> Please review the physical hardware step-by-step and the testbed schematic adjustments. Should the added testbed inventory queues have an explicit capacity limit (e.g., maximum 5 items) before they trigger a "Blocked" state upstream?

## Proposed Changes

### 1. Testbed Inventory Updates (Digital Twin)

We will modify the schematic layout in the mock testbed to explicitly visualize the buffer/inventory queues before the machining operations and outputs.

#### [MODIFY] [backend/app/mock_telemetry.py](backend/app/mock_telemetry.py)
- **Add Inventory Nodes**: Introduce new nodes representing inventory buffers next to each machining operation (`cncm`, `lz`, `cncl`) and output spots (`oba`, `obb`, `tra`).
  - E.g., `inv_m1`, `inv_m2`, `inv_m3`, `inv_oba`, etc.
- **Update Routing & Routing Display**: Adjust the standard job routing array to pass through these inventory nodes prior to hitting the machine or terminating at the output. 
- **Queue Logic**: Ensure `queue_depth` calculates appropriately for these buffers so backlogs can be visually monitored and mitigated before upstream starvation/blocking occurs.

### 2. Physical Hardware Telemetry Collection (Step-by-Step)

To fulfill the dataset requirements for the TinyML Autoencoder Model on the Arduino Nano 33 BLE, follow this guide setup to get your physical `training_data.csv`:

#### Step 1: Arduino Nano 33 BLE Setup
1. Mount the Arduino securely to the end-effector (or moving arm) of your physical robot.
2. Flash the Arduino with a C++ sketch utilizing the `Arduino_LSM9DS1` library to poll the 9-axis IMU (accel `x,y,z`, gyro `x,y,z`, mag `x,y,z`) at a fixed frequency (e.g., 50 Hz).
3. Have the Arduino serialize and print these readings directly to the Serial port as comma-separated values.

#### Step 2: Raspberry Pi / Laptop Datalogger
1. Connect the Arduino via USB to your Raspberry Pi or laptop.
2. We will run a simple Python script (using the `pyserial` and `csv` libraries) on the Pi that listens to the Arduino's serial port.
3. The script will append each row directly to a `.csv` file alongside a host-generated ISO-8601 Timestamp.

*(Optional: If the Arduino lacks a tether, it can stream via BLE, but USB Serial is the most deterministic method for gathering the training baseline.)*

#### Step 3: Loop Execution & Baseline Capture
1. Start the Python Datalogger script.
2. Command your physical robot to execute its **nominal, standardized kinematic loop** repeatedly.
3. Run the loop for several hours to collect a sufficient baseline (e.g., 50,000+ samples).
4. **Data Verification**: End the script. The resulting CSV will contain the 10 exact columns your ML Proposal expects, ready for training the Autoencoder.

## Verification Plan

### Automated Tests
- Refresh the frontend testbed visualization to ensure the new inventory nodes render appropriately and have lines flowing into them.

### Manual Verification
- Review the digital twin testbed to ensure that inventory levels accumulate realistically when downstream machines are "Busy".
- Review the generated physical IMU CSV to ensure no dropped frames/missing timestamps.
