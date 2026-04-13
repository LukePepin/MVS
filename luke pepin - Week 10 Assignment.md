# Luke Pepin - Week 10 Assignment: MES Design Prototype Document

## Section 1: System Overview

### Business Context
The Expeditionary Automated Repair Cell (EARC) is a decentralized, highly automated manufacturing execution system designed for Disconnected, Intermittent, and Limited (DIL) environments (such as forward-deployed logistics). The system produces "repair geometries" distributed across four distinct product families: gaskets, shafts, housings, and brackets. To achieve operations, the EARC relies on 5 primary physical resource types: initial infeed robots (R0), material verification nodes, CNC Mills, Dual Laser Cutters, CNC Lathes, and outfeed merge robots (R1). 

Despite heavy automation, the EARC requires specialized human intervention to sustain continuous operation, utilizing 4 critical worker roles:
1. **Operations Commander**: Oversees system-wide dispatching and resolves production bottlenecks.
2. **Field Service Engineer**: Maintains CNCs, robotic arms, and corrects edge ML anomalies.
3. **Logistics Technician**: Loads raw material stock, manages infeed, and unloads finished pallets.
4. **Quality Assurance Inspector**: Manages exception handling for parts that fail automated verification.
The system routinely processes approximately 50-75 discrete repair jobs per shift under strict constraints and high-mix variables.

### MESA-11 Summary Table

| Function | Role in your system | Key tables | Key algorithm | Primary KPI |
| :--- | :--- | :--- | :--- | :--- |
| **F1** Resource Allocation | Assigns jobs to specific machines based on tooling and capacity. | Resources, ResourceStatus, ResourceAssignment | Integer Programming | Utilization Rate |
| **F2** Operations Scheduling | Determines overall sequence of the daily repair jobs based on priority constraints. | WorkOrders, Schedule, Products | Earliest Due Date (EDD) | Total Tardiness |
| **F3** Dispatching | Dynamically selects the next job from a station's queue to clear bottlenecks rapidly. | DispatchQueue, DispatchLog | Shortest Processing Time (SPT) | Mean Time in System |
| **F4** Document Control | Maintains version-controlled G-Code recipes and 3D print models for repair geometries. | Documents, Revisions, Acknowledgments | Version Hashing (ZKP) | Audit Compliance |
| **F5** Data Collection | Gathers 6-axis IMU telemetry from robots to feed the anomaly detection Autoencoder. | Sensors, SensorReadings, Events | Threshold Alarm Logic | Packet Success Rate |
| **F6** Labour Management | Schedules human technicians for setup, teardown, and maintenance during shifts. | Workers, SkillMatrix, Shifts, TimeEvents | Integer Programming (IP Rostering) | Labour Efficiency |
| **F7** Quality Management | Tracks automated dimensional verification and rejects defective parts. | QualitySpecs, InspResults, NCRecords | $X$-bar and $R$ charts | Defect Rate / $C_{pk}$ |
| **F8** Process Management | Monitors kinematic toolpaths for tampering using autoencoder reconstruction error. | RecipeParams, ProcessEvents, Deviations | Trust Equation Decay | Anomaly Hit Rate |
| **F9** Maintenance | Triggers fail-safe disconnects and schedules preventative maintenance on robotic joints. | Equipment, MaintenanceLog, FailureLog | MTBF-based PM | MTTR / Availability |
| **F10** Product Tracking | Manages backward and forward genealogy for each batch through the Tri-branch topology. | Lots, Genealogy, LotEvents | Backwards/Forwards Genealogy Trace | Trace Time |
| **F11** Performance Analysis | Aggregates all cell data to summarize overall expeditionary mission readiness. | KPILog, OEELog, ShiftReports | Overall Equipment Effectiveness (OEE) | OEE |

---

## Section 2: Database Schema — All 11 Functions

### F1 — Resource Allocation
**Business Role**: F1 identifies available physical resources (robots, mills, lathes) and assigns them to awaiting tasks that match equipment routing requirements, ensuring no resource is double-booked.

**Table Specifications**
| Field | Type | Role | Description |
| :--- | :--- | :--- | :--- |
| **Resources** | | | |
| ResourceID | VARCHAR(64) | PK | Unique identifier for the machine/robot. |
| ResourceType | VARCHAR(64) | - | Categorization (e.g., CNC Mill, Laser Cutter). |
| CapacityLimit | INT | - | Maximum concurrent jobs the resource can hold. |
| CurrentStatus | VARCHAR(32) | - | Defines if resource is Active, Idle, or Offline. |
| LastMaintenance | DATETIME | - | Timestamp of the last preventative check. |
| **ResourceStatus** | | | |
| StatusID | INT | PK | Unique log ID. |
| ResourceID | VARCHAR(64) | FK (Resources) | The resource this status belongs to. |
| State | VARCHAR(32) | - | Operational state (Idle, Busy, Error). |
| JobInProgress | VARCHAR(128) | FK (WorkOrders) | What is currently being worked on. |
| Timestamp | DATETIME | - | Time the status was recorded. |
| **ResourceAssignment** | | | |
| AssignmentID | INT | PK | Unique assignment ID. |
| ResourceID | VARCHAR(64) | FK (Resources) | Resource assigned to task. |
| TaskID | INT | FK (WorkOrders) | Work order being processed. |
| AssignedBy | VARCHAR(64) | FK (Workers) | Authorizer of the assignment. |
| ExpectedDuration | FLOAT | - | Forecasted minutes task will take. |

**Key Algorithm or Formula**
*Integer Programming Assignment (from Week 6 MILP Formulations)*
- **Objective function**: $\min Z = \sum_{i} \sum_{j} c_{ij} x_{ij}$ (minimize setup/transfer cost $c$ between machine $i$ and job $j$).
- **Decision variables**: $x_{ij} \in \{0, 1\}$, where $1$ if job $j$ is assigned to machine $i$.
- **Key constraint**: $\sum_{j} x_{ij} \le 1$ for all $i$ (A machine can only process one task at a time).
- **Source**: Week 6 Homework - MILP.

**Integration Notes**: F1 exchanges data with **F2 Operations Scheduling** by checking the priority of tasks. It writes updates to `ResourceStatus` which is continually read by **F11 Performance Analysis** to aggregate utilization metrics.

### F2 — Operations Scheduling
**Business Role**: F2 manages the overarching priority sequence of requested Work Orders, ensuring that critical repair units receive their parts before expeditionary deadlines expire.

**Table Specifications**
| Field | Type | Role | Description |
| :--- | :--- | :--- | :--- |
| **WorkOrders** | | | |
| OrderID | INT | PK | Unique auto-incrementing ID. |
| ProductID | VARCHAR(64) | FK (Products) | Foreign key pointing to part family recipe. |
| RequestingUnit | VARCHAR(128) | - | Name of expeditionary force requesting part. |
| DueDate | DATETIME | - | The hard deadline for completion. |
| Status | VARCHAR(32) | - | e.g., Pending, Scheduled, Complete. |
| **Schedule** | | | |
| ScheduleID | INT | PK | Unique schedule ID. |
| OrderID | INT | FK (WorkOrders) | Order referenced in this schedule permutation. |
| PlannedStart | DATETIME | - | Estimated start block. |
| PlannedEnd | DATETIME | - | Expected finish time. |
| SequenceRank | INT | - | Ordering priority for the shift. |
| **Products** | | | |
| ProductID | VARCHAR(64) | PK | Unique product string (e.g., 'Gasket_A'). |
| RoutingPath | VARCHAR(128) | - | Comma-separated required resources. |
| CycleTime | FLOAT | - | Theoretical minimum processing minutes. |
| BillOfMaterials | VARCHAR(255) | - | Consumable requirements per unit. |
| ApprovalStatus | VARCHAR(32) | - | Readiness flag. |

**Key Algorithm or Formula**
*Earliest Due Date (EDD) Scheduling*
- **Objective function**: $\min L_{max}$ (minimize the maximum lateness of the schedule).
- **Decision variables**: Sequence order permutation $\pi = (J_{(1)}, J_{(2)}, ..., J_{(n)})$.
- **Key constraint**: Processing time $p_j > 0$ restricts start of subsequent jobs (No preemption allowed). 
- **Parameter values**: Sorting relies on $d_j$ (due date of job $j$).
- **Source**: Week 3 - Single Machine Deterministic Scheduling.

**Integration Notes**: F2 passes the optimized sequence list to **F3 Dispatching** to construct station-level queues. It also reads the routing definitions directly from **F4 Document Control** to understand required paths.

### F3 — Dispatching
**Business Role**: F3 operates locally at the Work Center level (e.g., Dual Laser Cutters). When a machine finishes a job, F3 overrides the master schedule if queue depth metrics dictate a high-velocity part is necessary to clear the bottleneck.

**Table Specifications**
| Field | Type | Role | Description |
| :--- | :--- | :--- | :--- |
| **DispatchQueue** | | | |
| QueueID | INT | PK | Primary Key. |
| ResourceID | VARCHAR(64) | FK (Resources) | Equipment this queue belongs to. |
| OrderID | INT | FK (WorkOrders) | Task pending execution. |
| LocalPriority | FLOAT | - | Calculated numeric priority weight. |
| TimeEntered | DATETIME | - | Moment job arrived buffering at this node. |
| **DispatchLog** | | | |
| LogID | INT | PK | Execution record identifier. |
| QueueID | INT | FK (DispatchQueue) | Original queue record. |
| DispatchedAt | DATETIME | - | Time the task was explicitly commanded to start. |
| AuthorizedBy | VARCHAR(64) | FK (Workers) | Verification signature (System or Commander). |
| Overridden | BOOLEAN | - | True if local SPT overrode F2 EDD schedule. |

**Key Algorithm or Formula**
*Shortest Processing Time (SPT)*
- **Objective function**: $\min \sum C_j$ (minimize total completion time and Mean Time in System).
- **Decision variables**: Next selected job $j \in \text{AvailableQueue}$.
- **Key constraint**: $Capacity \le Limits$.
- **Parameter values**: $p_j$, expected processing time for the pending geometries.
- **Source**: Week 4 - Dispatching / Sequencing Rules.

**Integration Notes**: F3 reads available queue depth data from the **F1 Resource Allocation** status tables. It pushes execution events into **F10 Product Tracking** to initiate the lot movement history.

### F4 — Document Control
**Business Role**: F4 ensures that only cryptographically verified G-Code paths and 3D print models are executed by the edge machines, mitigating the risk of adversarial tampering.

**Table Specifications**
| Field | Type | Role | Description |
| :--- | :--- | :--- | :--- |
| **Documents** | | | |
| DocID | VARCHAR(64) | PK | Unique document identifier. |
| ProductID | VARCHAR(64) | FK (Products) | Part family this document belongs to. |
| FileBlob | BLOB | - | Raw physical binary data or G-code payload. |
| CurrentRev | VARCHAR(16) | - | Current approved revision version. |
| DocumentType | VARCHAR(32) | - | e.g., 'G-Code', 'CAD', 'QA-Spec'. |
| **Revisions** | | | |
| RevID | INT | PK | Unique revision trace. |
| DocID | VARCHAR(64) | FK (Documents) | Original parent document. |
| HashKey | VARCHAR(256) | - | SHA-256 / Schnorr signature. |
| CreatedAt | DATETIME | - | Time of revision commit. |
| CreatedBy | VARCHAR(64) | FK (Workers) | Author of the engineering change. |
| **Acknowledgments** | | | |
| AckID | INT | PK | Internal index. |
| RevID | INT | FK (Revisions) | Which revision is being acknowledged. |
| WorkerID | VARCHAR(64) | FK (Workers) | Technician signing off. |
| SignatureTime | DATETIME | - | Timestamp. |
| Valid | BOOLEAN | - | State of validation context. |

**Key Algorithm or Formula**
*Zero-Knowledge Hash Verification (Represented as a Logic Match)*
- **Objective function**: $Match(H_{received}, H_{database})$.
- **Decision variables**: Allow execution (Boolean).
- **Key constraint**: $H(x) = H_{database}$ (Hash validation strict equality).
- **Source**: Week 8 / Week 10 Design.

**Integration Notes**: F4 receives check requests from **F8 Process Management**. Upon updating a recipe, it signals **F7 Quality Management** to refresh the expected quality dimensional tolerances.

### F5 — Data Collection
**Business Role**: F5 is a high-frequency polling engine that gathers physical robotic kinematics (accelerometer, gyroscope, magnetometer data) to ensure the system is physically executing the digital directive.

**Table Specifications**
| Field | Type | Role | Description |
| :--- | :--- | :--- | :--- |
| **Sensors** | | | |
| SensorID | VARCHAR(64) | PK | Identifier (e.g., 'IMU_Nano33'). |
| NodeID | VARCHAR(64) | FK (Resources) | Machine/Robot arm this is physically attached to. |
| PollingHz | INT | - | Required polling frequency (e.g., 100 Hz). |
| CalibrationDate| DATETIME | - | Last known zeroing offset process. |
| Status | VARCHAR(16) | - | Online, Error, Syncing. |
| **SensorReadings** | | | |
| LogID | INT | PK | Auto-increment PK. |
| SensorID | VARCHAR(64) | FK (Sensors) | Sensor sending the payload. |
| Accel_X | FLOAT | - | X-Axis Linear Acceleration. |
| Gyro_X | FLOAT | - | X-Axis Rotational Velocity. |
| Timestamp | DATETIME | - | UTC Time of physical event. |
| **Events** | | | |
| EventID | INT | PK | Primary Key. |
| SensorID | VARCHAR(64) | FK (Sensors) | Source. |
| EventType | VARCHAR(64) | - | 'Threshold Exceeded', 'Baseline Normal'. |
| AlertSeverity | INT | - | 1 (Low) to 5 (Critical). |
| Acknowledged | BOOLEAN | - | Whether an operator has cleared it. |

**Key Algorithm or Formula**
*Threshold Alarm Logic (Simple Control Bound)*
- **Objective function**: Identify $x_t > UCL$ or $x_t < LCL$.
- **Decision variables**: Trigger alert status $A \in \{0, 1\}$.
- **Parameter values**: $UCL = \mu + 3\sigma$.
- **Source**: Week 5 Data Processing & SPC Foundations.

**Integration Notes**: F5 directly populates tables which are consumed asynchronously by the TinyML Autoencoder in **F8 Process Management**. Sensor dropouts immediately notify **F9 Maintenance**.

### F6 — Labour Management
**Business Role**: F6 manages the complex rostering of the EARC's human support components given the extreme DIL conditions. Ensures coverage exists for manual QA verification and mechanical upkeep.

**Table Specifications**
| Field | Type | Role | Description |
| :--- | :--- | :--- | :--- |
| **Workers** | | | |
| WorkerID | VARCHAR(64) | PK | Employee ID / Rank ID. |
| Name | VARCHAR(128) | - | Full Name. |
| Role | VARCHAR(64) | - | E.g., 'Operations Commander', 'Logistics Tech'. |
| ActiveStatus | BOOLEAN | - | True if actively designated to the EARC shift. |
| Clearances | VARCHAR(256) | - | Authentication clearance level. |
| **SkillMatrix** | | | |
| MatrixID | INT | PK | PK. |
| WorkerID | VARCHAR(64) | FK (Workers) | Staff member. |
| ResourceType | VARCHAR(64) | FK (Resources) | Equipment they are certified on. |
| CertificationDate| DATETIME | - | When qualification was obtained. |
| ExpirationDate | DATETIME | - | Required recertification date. |
| **Shifts** | | | |
| ShiftID | INT | PK | Shift ID. |
| WorkerID | VARCHAR(64) | FK (Workers) | Staff Member scheduled. |
| StartTime | DATETIME | - | Start of shift limit. |
| EndTime | DATETIME | - | End of shift limit. |
| TotalHours | FLOAT | - | Total duration. |
| **TimeEvents** | | | |
| EventID | INT | PK | Event index. |
| WorkerID | VARCHAR(64) | FK (Workers) | Worker interacting. |
| Action | VARCHAR(64) | - | Clock-in, Clock-out, Break. |
| Timestamp | DATETIME | - | Temporal record. |

**Key Algorithm or Formula**
*Integer Programming Rostering*
- **Objective function**: $\min \sum (\text{OvertimePenalty}_{w} \cdot y_w)$
- **Decision variables**: $x_{w,t} \in \{0, 1\}$ assigned worker $w$ on time block $t$.
- **Key constraint**: $\sum_{w \in Skilled} x_{w,t} \ge \text{Demand}_t$ (Coverage Constraint).
- **Source**: Week 6 - Integer/MILP Formulations.

**Integration Notes**: F6 intersects with **F1 Resource Allocation** when assigning manual QA verification roles, requiring validation of certifications from the `SkillMatrix` table before allowing dispatching of tasks via **F3**.

### F7 — Quality Management
**Business Role**: F7 aggregates results from the automated inspection station and manually flags out-of-tolerance (OOT) parts for rework based on statistical process control limits.

**Table Specifications**
| Field | Type | Role | Description |
| :--- | :--- | :--- | :--- |
| **QualitySpecs** | | | |
| SpecID | INT | PK | Spec Sheet ID. |
| ProductID | VARCHAR(64) | FK (Products) | Part configuration. |
| DimensionName | VARCHAR(64) | - | Target feature (e.g., 'Outer Diameter'). |
| TargetValue | FLOAT | - | Ideal nominal value (mm). |
| Tolerance | FLOAT | - | $\pm$ allowable bound. |
| **InspResults** | | | |
| ResultID | INT | PK | Unique measurement log. |
| SerialID | VARCHAR(128) | FK (Genealogy) | Physical batch / serial traced. |
| SpecID | INT | FK (QualitySpecs) | What was measured against. |
| MeasuredValue| FLOAT | - | The raw numeric measurement. |
| Passed | BOOLEAN | - | Programmatic pass/fail true. |
| **NCRecords** | | | |
| NcrID | INT | PK | Non-conforming record ID. |
| ResultID | INT | FK (InspResults) | Failed inspection trace. |
| Severity | VARCHAR(32) | - | Minor, Major, Critical. |
| CAPA_Action | VARCHAR(128) | - | Corrective Action implemented. |
| ReworkRoute | VARCHAR(128) | - | E.g. 'Route back to CNC Mill'. |

**Key Algorithm or Formula**
*Statistical Process Control: X-bar and R Charts*
- **Formulation ($\bar{X}$)**: $UCL_{\bar{x}} = \bar{\bar{X}} + A_2 \bar{R}$, $LCL_{\bar{x}} = \bar{\bar{X}} - A_2 \bar{R}$
- **Formulation (R)**: $UCL_R = D_4 \bar{R}$, $LCL_R = D_3 \bar{R}$
- **Parameter values**: Sample size $n=5$ yields constants $A_2 = 0.577, D_3 = 0, D_4 = 2.114$.
- **Source**: Week 10 - F7 Quality Lecture.

**Integration Notes**: F7 initiates rework events affecting **F2 Operations Scheduling**. If parts are scrapped, F7 notifies **F10 Product Tracking** to close the lot and updates the First Pass Yield (FPY) metric in **F11 Performance Analysis**.

### F8 — Process Management
**Business Role**: F8 acts as the intelligence layer, executing edge TinyML Autoencoders against real-time data to verify that the toolpath isn't being spoofed or deviating dangerously from nominal norms.

**Table Specifications**
| Field | Type | Role | Description |
| :--- | :--- | :--- | :--- |
| **RecipeParams** | | | |
| ParamID | INT | PK | Recipe logic block. |
| DocID | VARCHAR(64) | FK (Documents) | Target operation. |
| NominalTrust | FLOAT | - | Starting Trust Scalar. |
| AnomalyThresh | FLOAT | - | Value beyond which the system isolates. |
| **ProcessEvents** | | | |
| EventID | INT | PK | Log trace. |
| SerialID | VARCHAR(128) | FK (Genealogy) | Target batch. |
| ReconError | FLOAT | - | Autoencoder loss distance. |
| CurrentTrust | FLOAT | - | Calculated decaying trust value. |
| Timestamp | DATETIME | - | Local capture time. |
| **Deviations** | | | |
| DevID | INT | PK | Incident log. |
| EventID | INT | FK (ProcessEvents) | Originating anomaly. |
| SystemAction | VARCHAR(128) | - | E.g. 'Safety Cutoff Activated'. |
| ClearanceID | VARCHAR(64) | FK (Workers) | Staff validating the isolate event. |

**Key Algorithm or Formula**
*Trust Equation Decay (Exponential Smoothing variant)*
- **Formula**: $\Gamma(t+1) = \alpha \cdot \Gamma(t) + (1-\alpha) \cdot N_0$
- **Decision variables**: Network decay state $\Gamma(t)$.
- **Key constraint**: If $\Gamma(t) \le 0.30$, trigger hardware electrical fail-safe ($\le 500ms$).
- **Parameter values**: $\alpha$ decay constant based on network noise.
- **Source**: MVS Project Cyber-Physical Design / Week 8 Process Algorithms.

**Integration Notes**: F8 reads live bounds from **F5 Data Collection**. Any deviation that triggers an isolation forces a write to **F9 Maintenance**, effectively taking a node offline.

### F9 — Maintenance
**Business Role**: F9 captures involuntary degradation failures (like adversarial disconnects from F8) and uses historical Mean Time Between Failures (MTBF) to schedule preventative swap-outs of robotic joints.

**Table Specifications**
| Field | Type | Role | Description |
| :--- | :--- | :--- | :--- |
| **Equipment** | | | |
| EquipID | VARCHAR(64) | PK | Asset ID. |
| AssetClass | VARCHAR(64) | - | Component class (e.g. Servo Motor). |
| MTBF_Hrs | FLOAT | - | Historical Mean Time Between Failure. |
| OperatingHrs | FLOAT | - | Spindle / Move time counter. |
| **MaintenanceLog** | | | |
| MaintID | INT | PK | Event ID. |
| EquipID | VARCHAR(64) | FK (Equipment) | Target machine component. |
| WorkerID | VARCHAR(64) | FK (Workers) | Executing technician. |
| ActionType | VARCHAR(64) | - | PM (Preventative), CM (Corrective). |
| DurationMins | FLOAT | - | Time to fix. |
| **FailureLog** | | | |
| FailID | INT | PK | Log trace. |
| EquipID | VARCHAR(64) | FK (Equipment) | Downed asset. |
| CauseMode | VARCHAR(128) | - | e.g. Adversarial Jamming, Bearing Wear. |
| TimeDown | DATETIME | - | Recorded offline time. |
| TimeUp | DATETIME | - | Recorded return-to-service time. |

**Key Algorithm or Formula**
*Component Reliability & MTBF*
- **Mathematical Formula**: Reliability $R(t) = e^{-\lambda t}$, where failure rate $\lambda = 1 / \text{MTBF}$.
- **Objective function**: Maximize operational Availability $A = \frac{\text{MTBF}}{\text{MTBF} + \text{MTTR}}$.
- **Parameter values**: Target Availability $A \ge 0.95$. 
- **Source**: Week 9 - Maintenance and OEE.

**Integration Notes**: F9 updates equipment status in **F1 Resource Allocation** when machines enter downtime, instantly forcing a recalculation of the master schedule in **F2 Operations Scheduling**.

### F10 — Product Tracking
**Business Role**: F10 manages the intricate genealogy of high-end parts, capturing precise routing logs through the network (Initial Inventory $\rightarrow$ Divergence $\rightarrow$ Merge Robot $\rightarrow$ Quality) so that any failed part can trigger a backward trace to isolated CNC tool-wear issues.

**Table Specifications**
| Field | Type | Role | Description |
| :--- | :--- | :--- | :--- |
| **Lots** | | | |
| LotID | VARCHAR(128) | PK | Unique batch or lot identity. |
| ProductID | VARCHAR(64) | FK (Products) | SKU relation. |
| OriginalQty | INT | - | Initial quantity initiated. |
| CurrentQty | INT | - | Inventory minus shrinkage. |
| **Genealogy** | | | |
| SerialID | VARCHAR(128) | PK | Specific individual child serial number. |
| LotID | VARCHAR(128) | FK (Lots) | Parent batch. |
| MaterialID | VARCHAR(64) | FK (RawInventory) | Mapped raw stock consumption. |
| WorkOrderID| INT | FK (WorkOrders) | Traced execution order. |
| Status | VARCHAR(32) | - | 'WIP', 'Finished', 'Scrap'. |
| **LotEvents** | | | |
| EventID | INT | PK | Trace node log. |
| SerialID | VARCHAR(128) | FK (Genealogy) | Target product. |
| StationPoint | VARCHAR(64) | FK (Resources) | Where it arrived (e.g. Robot Merge R1). |
| Timestamp | DATETIME | - | When it crossed the node constraint. |

**Key Algorithm or Formula**
*Backwards Genealogy Trace (Relational Array Mapping)*
- **Mathematical Description**: Given a failed part $S_{fail}$, evaluate the inverse transitive closure over relations $S_{fail} \rightarrow M_{machine} \rightarrow L_{rawlot}$ to find all corresponding serials $\subset M_{machine}$.
- **Objective**: Identify the Root Node ($R_0$) of a branching failure network.
- **Source**: Week 10 - F10 Product Tracking.

**Integration Notes**: F10 consumes raw events recorded by **F3 Dispatching** to mark transition state points. It feeds final disposition status into **F11 Performance Analysis** for yield math.

### F11 — Performance Analysis
**Business Role**: F11 wraps up the execution logs into cohesive executive formats (OEE) validating the effectiveness of the EARC to high-command logic nodes.

**Table Specifications**
| Field | Type | Role | Description |
| :--- | :--- | :--- | :--- |
| **KPILog** | | | |
| KpiID | INT | PK | Unique log. |
| DateIndex | DATE | - | Calculated day matrix. |
| Value_A | FLOAT | - | Availability % |
| Value_P | FLOAT | - | Performance % |
| Value_Q | FLOAT | - | Quality % |
| **OEELog** | | | |
| OEEID | INT | PK | PK. |
| WorkCenter | VARCHAR(64) | FK (Resources) | Targeted node. |
| FinalOEE | FLOAT | - | Aggregate OEE metric. |
| **ShiftReports** | | | |
| ReportID | INT | PK | Finalized shift summary document. |
| ShiftID | INT | FK (Shifts) | Linked human block executing the work. |
| DefectRate | FLOAT | - | Total scrapped vs produced parts. |
| ReportTime | DATETIME | - | Final render time. |

**Key Algorithm or Formula**
*Overall Equipment Effectiveness (OEE)*
- **Equation**: $OEE = A \times P \times Q$
  - *Availability (A)* = Run Time / Planned Production Time
  - *Performance (P)* = (Ideal Cycle Time $\times$ Total Count) / Run Time
  - *Quality (Q)* = Good Count / Total Count
- **Parameter values**: Target World Class $OEE \ge 85\%$.
- **Source**: Week 9 - Maintenance and OEE.

**Integration Notes**: F11 is the ultimate sink, pulling data from **F2, F7, and F9** to generate the final analytical output factors.

---

## Section 3: Integration Timeline

**"A Day at the EARC" - Shift 1 Operations**

| Time | Event | Functions Triggered |
| :--- | :--- | :--- |
| 06:00 | **Shift Start**: Operations Commander logs into the terminal and authorizes the daily dispatch load. | **F6 (Labour Mgt)**, **F2 (Scheduling)** |
| 06:15 | **Routing Allocation**: The algorithm reads the EDD schedule and binds resources to Job 101 (Gasket Family). | **F1 (Resource)**, **F2 (Scheduling)** |
| 07:30 | **Production Launch**: Job reaches the Dual Laser Cutters. The G-Code recipe is cryptographically verified before cutting starts. | **F3 (Dispatching)**, **F4 (Doc Control)**, **F10 (Tracing)** |
| 08:45 | **Quality Alarm Trigger**: The automated inspection camera flags a housing piece from Job 104 as out of tolerance ($X$-bar limit breached). | **F7 (Quality Mgt)** |
| 08:46 | **Traceability Event**: The inspection failure triggers a backward trace, revealing the part originated from CNC Mill A. The operator flags Mill A as suspect. | **F10 (Product Tracking)**, **F1 (Resource)** |
| 09:10 | **Adversarial Anomaly Detected (Process Event)**: Edge IMU on Robot Arm R1 detects severe kinematic spoofing driving Autoencoder Reconstruction error above limit. | **F5 (Data Collection)**, **F8 (Process Mgt)** |
| 09:11 | **Cyber-Physical Disconnect (Maintenance Event)**: Trust score decays below 0.30, forcing an automatic fail-safe disconnect of R1. Asset marked offline. | **F8 (Process Mgt)**, **F9 (Maintenance)** |
| 09:15 | **Schedule Re-optimization**: With R1 totally disabled, the system dynamically reroutes all WIP parts back to manual infeed nodes, recalculating SPT. | **F1 (Resource)**, **F2 (Scheduling)**, **F3 (Dispatching)** |
| 11:30 | **Corrective Action**: Field Service Engineer swaps the compromised joint node on R1 and issues a return-to-service cryptographic sign-off. | **F6 (Labour Mgt)**, **F9 (Maintenance)**, **F4 (Doc Control)** |
| 14:00 | **End-of-Shift Analytics**: OEE metrics are computed taking into account the downtime hit on Availability ($A$) from the cyber-attack and the Quality ($Q$) hit. | **F11 (Performance)** |

---

## Section 4: Implementation Roadmap

**Week 11 — Database**
In Week 11, we will materialize all structural concepts using SQLite in the `backend`. I plan to instantiate the 20+ core tables using a Python seeding script. The seed will insert 50+ rows into historical event tables (`ResourceStatus`, `SensorReadings`, `ProcessEvents`) to provide an adequate dataset for dashboarding. Specifically, four cross-function queries will be written and tested: 
1. Joining `WorkOrders`, `Genealogy`, and `InspResults` to trace dimensional drift per job.
2. Joining `Equipment` and `FailureLog` to establish MTBF values.
3. Checking `SkillMatrix` against `DispatchQueue` to validate manual override permissions. 
4. Aggregating `ProcessEvents` to map trust degradation over time. 

**Week 12 — Algorithms**
In Week 12, mathematical frameworks will become executing functions in FastAPI:
1. **EDD Dispatcher** (F2): Sorts queued DB rows strictly filtering by shortest timeline due dates.
2. **Backwards Genealogy Resolver** (F10): Recursive SQL call fetching parent batches based on a queried serial number.
3. **Autoencoder Pipeline** (F8): Implementation of the Trust Decay equation translating IMU telemetry arrays into a singular decaying boolean.
4. **OEE Aggregator** (F11): End-of-day mathematical summary reading run times and defects from the database to generate an overarching system effectiveness percentage.

**Week 13 — Demo**
The final demonstration will focus on an "Adversarial DIL Operation" scenario processing 20 incoming repair geometries. The presentation will begin with normal MES operations before intentionally injecting a simulated IMU attack on a robotic node. The audience will observe the Autoencoder reconstruction error spike (F8), trigger a maintenance quarantine (F9), and force the system to successfully re-calculate the routing tables and SPT logic on the fly (F1, F2) to ensure completion of the remaining geometries.

---

## Section 5: Algorithm Cross-Reference Table

| Algorithm / Math Formulation | MESA Function | Course Source | Homework Origin |
| :--- | :--- | :--- | :--- |
| Integer Programming (Assignment Logic) | F1, F6 | Week 6 | LP/MILP Modeling |
| Earliest Due Date (EDD) Sequence | F2 | Week 3 | Single Machine Scheduling |
| Shortest Processing Time (SPT) Rule | F3 | Week 4 | Dispatching & Parallel Stations |
| Statistical Process Control ($X$-bar & $R$) | F7 | Week 10 | Quality Management (F7) |
| Threshold Value Alarm Bounds | F5 | Week 5 | MES Data Layer Processing |
| Component Reliability MTBF Calculation | F9 | Week 9 | Maintenance / Simulation |
| Overall Equipment Effectiveness (OEE) | F11 | Week 9 | OEE & KPIs |
| Transitive Genealogy Closure Logic | F10 | Week 10 | Product Tracking (F10) |

