import { useEffect, useState } from "react";

const SIM_STATE_URL = "http://localhost:8000/api/sim/state";

const initialSimState = {
  sim_status: "idle",
  sim_time: 0,
  simulated_time_iso: null,
  project_start_iso: null,
  speed: 1.0,
  num_jobs: 50,
  completed_jobs: 0,
  avg_flow_time: 0,
  tokens: [],
  station_busy: {},
  station_queue: {},
  events_log: [],
  oee_snapshots: [],
};

export const useSimState = () => {
  const [simState, setSimState] = useState(initialSimState);

  useEffect(() => {
    let active = true;

    const fetchState = async () => {
      try {
        const res = await fetch(SIM_STATE_URL);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        if (active) setSimState(data);
      } catch {
        // silent — sim may not be running
      }
    };

    fetchState();
    const iv = setInterval(fetchState, 500);
    return () => {
      active = false;
      clearInterval(iv);
    };
  }, []);

  return simState;
};
