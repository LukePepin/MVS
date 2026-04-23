import React from "react";
import { describe, it, expect, vi } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import "@testing-library/jest-dom";
import SimulationControls from "../components/SimulationControls";

const mockSimState = {
  sim_status: "idle",
  sim_time: 0,
  speed: 1.0,
  completed_jobs: 0,
  avg_flow_time: 0,
  simulated_time_iso: "2026-04-01T08:30:00.000Z",
  num_jobs: 200,
  tokens: [],
  station_busy: {},
  station_queue: {},
  events_log: [],
  oee_snapshots: [],
};

describe("SimulationControls", () => {
  it("displays idle status", () => {
    render(<SimulationControls simState={mockSimState} />);
    expect(screen.getByText("idle")).toBeInTheDocument();
  });

  it("renders Start button", () => {
    render(<SimulationControls simState={mockSimState} />);
    expect(screen.getByText("START")).toBeInTheDocument();
  });

  it("renders instant finish and reset buttons", () => {
    render(<SimulationControls simState={mockSimState} />);
    expect(screen.getByText("INSTANT")).toBeInTheDocument();
    expect(screen.getByText("RESET")).toBeInTheDocument();
  });

  it("renders speed buttons", () => {
    render(<SimulationControls simState={mockSimState} />);
    expect(screen.getByText("1x")).toBeInTheDocument();
    expect(screen.getByText("5x")).toBeInTheDocument();
    expect(screen.getByText("20x")).toBeInTheDocument();
  });

  it("shows running status with green text", () => {
    const runningState = { ...mockSimState, sim_status: "running" };
    render(<SimulationControls simState={runningState} />);
    const status = screen.getByText("running");
    expect(status).toHaveClass("text-green-400");
  });

  it("shows completed jobs and simulated datetime", () => {
    const state = { ...mockSimState, completed_jobs: 42 };
    render(<SimulationControls simState={state} />);
    expect(screen.getByText("42")).toBeInTheDocument();
    expect(screen.getByText(/Sim Date\/Time/i)).toBeInTheDocument();
  });

  it("shows algorithm select with EDD and SPT options", () => {
    render(<SimulationControls simState={mockSimState} />);
    expect(screen.getByText("EDD (Due Date)")).toBeInTheDocument();
    expect(screen.getByText("SPT (Shortest Time)")).toBeInTheDocument();
  });

  it("sends job count + algorithm on start", async () => {
    const fetchMock = vi.fn().mockResolvedValue({ ok: true });
    global.fetch = fetchMock;

    render(<SimulationControls simState={mockSimState} />);
    fireEvent.change(screen.getByLabelText("Jobs"), { target: { value: "750" } });
    fireEvent.click(screen.getByText("START"));

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledTimes(1);
    });

    const [, options] = fetchMock.mock.calls[0];
    expect(options.method).toBe("POST");
    expect(options.body).toContain('"algorithm":"EDD"');
    expect(options.body).toContain('"num_jobs":750');
  });
});
