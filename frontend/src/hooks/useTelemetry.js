import { useEffect, useMemo, useState } from "react";

const HYBRID_ENDPOINT = "http://localhost:8000/hybrid/dashboard_data";
const MOCK_ENDPOINT = "http://localhost:8000/mock/dashboard_data";

const initialData = {
  mode: "hybrid",
  cloud_status: false,
  local_mesh_status: false,
  work_orders: [],
  machine_status: [],
  raw_inventory: [],
  schematic: null,
  telemetry_stats: {},
  latency_ms: 0,
};

export const useTelemetry = () => {
  const [mode, setMode] = useState("hybrid");
  const [data, setData] = useState(initialData);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;

    const fetchTelemetry = async () => {
      const endpoint = mode === "mock" ? MOCK_ENDPOINT : HYBRID_ENDPOINT;

      try {
        const response = await fetch(endpoint, {
          method: "GET",
          headers: { "Content-Type": "application/json" },
        });

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }

        const payload = await response.json();
        if (!active) {
          return;
        }

        setData({
          ...initialData,
          ...payload,
          mode,
        });
        setError("");
      } catch (err) {
        if (!active) {
          return;
        }
        setError(err instanceof Error ? err.message : "Telemetry request failed");
        setData((prev) => ({
          ...prev,
          cloud_status: false,
          local_mesh_status: false,
        }));
      }
    };

    fetchTelemetry();
    const timerId = window.setInterval(fetchTelemetry, 1000);

    return () => {
      active = false;
      window.clearInterval(timerId);
    };
  }, [mode]);

  const endpoint = useMemo(
    () => (mode === "mock" ? MOCK_ENDPOINT : HYBRID_ENDPOINT),
    [mode]
  );

  return {
    mode,
    setMode,
    data,
    error,
    endpoint,
  };
};
