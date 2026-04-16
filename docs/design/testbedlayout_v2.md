```mermaid
flowchart LR
  %% Zone 1: Source
  subgraph SRC[Source and Infeed]
    direction LR
    ir[Initial Inventory]
    r0(Robot Arm R0)
    r1(Robot Arm R1)
    c0(Conveyor Belt c0)
    c1(Conveyor Belt c1)
  end

  %% Zone 2: Fabrication Branches
  subgraph FAB[Fabrication Branches]
    direction TB

    subgraph FAB_MILL[Branch 1: CNC Mill Section]
      direction TB
      r2(Robot Arm R2)
      cncm[CNC Mill]
      c2(Conveyor Belt c2)
      c4(Conveyor Belt c4)
    end

    subgraph FAB_LASER[Branch 2: Laser Section]
      direction TB
      r3(Robot Arm R3)
      lz[Dual Laser Cutters]
      c3(Conveyor Belt c3)
      c5(Conveyor Belt c5)
    end

    subgraph FAB_LATHE[Branch 3: CNC Lathe Section]
      direction TB
      r4(Robot Arm R4)
      cncl[CNC Lathe]
      c6(Conveyor Belt c6)
      c7(Conveyor Belt c7)
    end
  end

  %% Zone 3: Merge, Inspection, and Output
  subgraph OUT[Merge, QA, and Output]
    direction TB
    r5(Robot Arm R5)
    r6(Robot Arm R6)

    qia[Quality Inspection A]
    c8(Conveyor Belt c8)
    c9(Conveyor Belt c9)
    c10(Conveyor Belt c10)
    qib[Quality Inspection B]

    oba[Output Spot A]
    obb[Output Spot B]
    tra[Trash]
  end

  %% Source to branch entry
  ir --> r0
  ir --> r1
  r0 <--> c0
  r1 <--> c1

  %% Top branch: CNC Mill
  c0 <--> r2
  r2 <--> cncm
  r2 <--> c2
  r2 <--> c4

  %% Middle branch: Laser
  c1 <--> r3
  r3 <--> lz
  r3 <--> c2
  r3 <--> c3
  r3 <--> c5

  %% Bottom branch: Lathe
  c4 <--> r4
  r4 <--> cncl
  r4 <--> c3
  r4 <--> c6
  r4 <--> c7

  %% Merge to QA
  c6 <--> r5
  c5 <--> r6
  c7 <--> r6
  r5 <--> qia
  r6 <--> c10
  c10 <--> qib

  %% QA to outputs/reject
  r5 <--> c8
  r5 <--> c9
  r6 <--> c9

  c8 <--> oba
  qib <--> obb
  c9 <--> tra
```

## Notes on this v2 layout
- Preserves your triangular branch-and-merge intent.
- Removes duplicate links and normalizes spacing.
- Splits the graph into clear operational zones for readability.
- Breaks fabrication into three explicit branch sections (mill, laser, lathe).
- Positions Quality Inspection B beneath c10 by linking `c10 <--> qib`.
- Keeps conveyors as explicit nodes so you can later assign occupancy state per belt.
