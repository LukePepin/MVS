import React from "react";
import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import Dashboard from "../dashboard";

vi.mock("../hooks/useSimState", () => ({
  useSimState: () => ({
    sim_status: "idle",
    sim_time: 0,
    speed: 1,
    simulated_time_iso: "2026-04-01T08:00:00.000Z",
    duration_scalar: 1.0,
    completed_jobs: 0,
    avg_flow_time: 0,
    tokens: [],
    station_busy: {},
    station_queue: {},
    events_log: [],
    oee_snapshots: [],
  }),
}));

vi.mock("../components/ControlPlaneSections", () => ({
  default: () => <div>Cyber-Physical Control Plane</div>,
}));

vi.mock("../hooks/useTelemetry", () => ({
  useTelemetry: () => ({
    mode: "mock",
    setMode: vi.fn(),
    data: {
      mode: "mock",
      cloud_status: false,
      local_mesh_status: false,
      work_orders: [],
      machine_status: [
        {
          machine_id: "M1 (Mill)",
          current_state: "Idle",
          job_in_progress: null,
          est_completion: null
        }
      ],
      raw_inventory: [],
      schematic: { nodes: [], connectors: [] },
      telemetry_stats: {},
      latency_ms: 0
    },
    error: "",
    endpoint: "http://localhost:8000/mock/dashboard_data"
  })
}));

describe("Dashboard", () => {
  it("renders factory title and top-row operational stats", () => {
    render(<Dashboard />);
    expect(screen.getByText("Factory Floor")).toBeInTheDocument();
    expect(screen.getByText("Active Jobs")).toBeInTheDocument();
    expect(screen.getByText("Bottleneck")).toBeInTheDocument();
    expect(screen.getByText(/Simulated Project Time:/)).toBeInTheDocument();
  });

  it("renders moved control plane below factory graph", () => {
    render(<Dashboard />);
    expect(screen.getByText("Physical Layout Visualization")).toBeInTheDocument();
    expect(screen.getByText("Cyber-Physical Control Plane")).toBeInTheDocument();
  });
});
