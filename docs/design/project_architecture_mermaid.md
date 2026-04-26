# MVS Project Architecture (Mermaid)

This diagram shows the primary runtime architecture and supporting delivery workflow for the MVS project.

```mermaid
flowchart LR
    %% External inputs
    RH[Robot Hardware Telemetry]

    subgraph SIM[Simulation Layer]
        MT[mock_telemetry.py]
        DE[des_engine.py]
        SD[seed_db.py]
    end

    subgraph BE[Backend Layer - FastAPI]
        UDP[UDP Listener 0.0.0.0:5005]
        Q[Async Queue + Writer]
        API[API Endpoints /dashboard_data /hybrid/dashboard_data /mock/dashboard_data]
    end

    subgraph DATA[Data Layer]
        SQL[(SQLite)]
        CSV[(CSV Artifacts)]
    end

    subgraph FE[Frontend Layer - React + Vite]
        DASH[Dashboard UI]
        POLL[Polling Hooks 1000ms]
    end

    subgraph OPS[Ops + Validation]
        PS[scripts/*.ps1]
        TESTS[backend/tests + frontend tests]
        DOCKER[Docker + Compose + GHCR Workflow]
    end

    RH --> UDP
    MT --> UDP
    DE --> API
    SD --> SQL

    UDP --> Q
    Q --> SQL
    Q --> CSV

    SQL --> API
    CSV --> API

    API --> POLL
    POLL --> DASH

    PS --> TESTS
    TESTS --> API
    DOCKER --> API
    DOCKER --> DASH
```

## Notes

- The backend receives both real and simulated telemetry, normalizes it, and persists to SQLite and CSV.
- The frontend dashboard polls backend endpoints, with hybrid mode as the primary operational mode.
- PowerShell scripts and automated tests validate behavior; Docker and CI support packaging and deployment.
