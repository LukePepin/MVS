import React from "react";
import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import Dashboard from "../dashboard";

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
  it("renders the Machine Status table", () => {
    render(<Dashboard />);
    expect(screen.getAllByText("Machine Status").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Time Left").length).toBeGreaterThan(0);
  });

  it("renders Work Orders and Analytics sections", () => {
    render(<Dashboard />);
    expect(screen.getByText("Work Orders")).toBeInTheDocument();
    expect(screen.getByText("Testbed Analytics")).toBeInTheDocument();
  });
});
