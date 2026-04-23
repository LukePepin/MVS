import React from "react";
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import "@testing-library/jest-dom";
import EventsLog from "../components/EventsLog";

describe("EventsLog", () => {
  it("shows empty message when no events", () => {
    render(<EventsLog events={[]} />);
    expect(screen.getByText(/No events yet/)).toBeInTheDocument();
  });

  it("renders events when provided", () => {
    const events = [
      { time: 10.5, type: "INFO", message: "Job_001 entered system" },
      { time: 25.3, type: "SUCCESS", message: "Job_001 completed" },
    ];
    render(<EventsLog events={events} />);
    expect(screen.getByText("Job_001 entered system")).toBeInTheDocument();
    expect(screen.getByText("Job_001 completed")).toBeInTheDocument();
  });

  it("displays event count in heading", () => {
    const events = [
      { time: 1, type: "INFO", message: "test" },
      { time: 2, type: "INFO", message: "test2" },
    ];
    render(<EventsLog events={events} />);
    expect(screen.getByText(/2 events/)).toBeInTheDocument();
  });
});
