import React, { useEffect, useMemo, useState } from "react";

const API = "http://localhost:8000/api/sim";

export default function SimulationControls({ simState }) {
  const [algorithm, setAlgorithm] = useState("EDD");
  const [jobCount, setJobCount] = useState(200);
  const status = simState?.sim_status || "idle";

  useEffect(() => {
    const incoming = Number(simState?.num_jobs || 200);
    if (Number.isFinite(incoming)) {
      setJobCount(incoming);
    }
  }, [simState?.num_jobs]);

  const simulatedTimeLabel = useMemo(() => {
    if (!simState?.simulated_time_iso) {
      return "N/A";
    }
    const dt = new Date(simState.simulated_time_iso);
    if (Number.isNaN(dt.getTime())) {
      return "N/A";
    }
    return dt.toLocaleString();
  }, [simState?.simulated_time_iso]);

  const post = async (path) => {
    try { await fetch(`${API}/${path}`, { method: "POST" }); } catch (e) { console.error(e); }
  };

  const startSimulation = async () => {
    const sanitizedJobs = Math.max(50, Math.min(1000, Number(jobCount) || 50));
    try {
      await fetch(`${API}/start`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          algorithm,
          num_jobs: sanitizedJobs,
        }),
      });
      setJobCount(sanitizedJobs);
    } catch (e) {
      console.error(e);
    }
  };

  const throughput = useMemo(() => {
    const t = Number(simState?.sim_time || 0);
    if (t <= 0) return "0.00";
    return (Number(simState?.completed_jobs || 0) / t).toFixed(2);
  }, [simState?.sim_time, simState?.completed_jobs]);

  const activeWip = Number(simState?.tokens?.filter((t) => t.status !== "completed").length || 0);
  const totalQueue = useMemo(
    () => Object.values(simState?.station_queue || {}).reduce((acc, v) => acc + Number(v || 0), 0),
    [simState?.station_queue]
  );

  const statusColor = {
    idle: "text-slate-400",
    running: "text-green-400",
    paused: "text-yellow-400",
    finished: "text-blue-400",
  }[status] || "text-slate-400";

  return (
    <div className="glass-panel rounded-xl p-4 border border-white/10 shadow-lg h-full flex flex-col justify-between gap-4">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-6">
        <div className="flex flex-col">
          <span className="text-[10px] uppercase tracking-widest text-slate-500 font-bold">Status</span>
          <span className={`text-xs font-bold uppercase ${statusColor}`}>{status}</span>
        </div>

        <div className="flex flex-col">
          <span className="text-[10px] uppercase tracking-widest text-slate-500 font-bold">Time</span>
          <span className="text-xs font-bold text-white font-mono">{simState?.sim_time || 0}m</span>
        </div>

        <div className="flex flex-col">
          <span className="text-[10px] uppercase tracking-widest text-slate-500 font-bold">Units</span>
          <span className="text-xs font-bold text-green-400">{simState?.completed_jobs || 0}</span>
        </div>

        <div className="flex flex-col">
          <span className="text-[10px] uppercase tracking-widest text-slate-500 font-bold">Sim Date/Time</span>
          <span className="text-xs font-bold text-blue-300 font-mono">{simulatedTimeLabel}</span>
        </div>

        <div className="flex flex-col">
          <span className="text-[10px] uppercase tracking-widest text-slate-500 font-bold">Throughput</span>
          <span className="text-xs font-bold text-emerald-300 font-mono">{throughput} jobs/min</span>
        </div>

        <div className="flex flex-col">
          <span className="text-[10px] uppercase tracking-widest text-slate-500 font-bold">Active WIP</span>
          <span className="text-xs font-bold text-amber-300 font-mono">{activeWip}</span>
        </div>

        <div className="flex flex-col">
          <span className="text-[10px] uppercase tracking-widest text-slate-500 font-bold">Queued Parts</span>
          <span className="text-xs font-bold text-orange-300 font-mono">{totalQueue}</span>
        </div>
      </div>

      <div className="flex items-center gap-3 bg-white/5 p-1 rounded-lg border border-white/5">
        <select
          value={algorithm}
          onChange={(e) => setAlgorithm(e.target.value)}
          className="rounded-md bg-slate-900 border border-white/10 text-[11px] text-white px-2 py-1.5 focus:outline-none focus:ring-1 focus:ring-blue-500 w-40"
        >
          <option value="EDD">EDD (Due Date)</option>
          <option value="SPT">SPT (Shortest Time)</option>
          <option value="FIFO">FIFO (First In)</option>
          <option value="LPT">LPT (Longest Time)</option>
          <option value="WSPT">WSPT (Weighted SPT)</option>
          <option value="CR">CR (Critical Ratio)</option>
        </select>

        <div className="flex items-center gap-2 rounded-md bg-slate-900 border border-white/10 px-2 py-1.5">
          <label htmlFor="job-count" className="text-[10px] font-bold uppercase tracking-widest text-slate-400">
            Jobs
          </label>
          <input
            id="job-count"
            type="number"
            min="50"
            max="1000"
            step="1"
            value={jobCount}
            onChange={(e) => setJobCount(Number(e.target.value))}
            className="w-24 rounded-md bg-black/30 border border-white/10 text-[11px] text-white px-2 py-1 focus:outline-none focus:ring-1 focus:ring-blue-500"
          />
          <span className="text-[10px] font-bold text-blue-300 w-16 text-right">50-1000</span>
        </div>

        <button
          onClick={startSimulation}
          disabled={status === "running"}
          className="px-3 py-1.5 rounded-md bg-green-600 hover:bg-green-500 disabled:opacity-30 text-[11px] font-bold text-white transition shadow-md active:scale-95"
        >
          START
        </button>
      </div>
      </div>

      <div className="flex items-center gap-2">
        <button
          onClick={() => status === "paused" ? post("resume") : post("pause")}
          disabled={status === "idle" || status === "finished"}
          className="px-3 py-1.5 rounded-md bg-yellow-600 hover:bg-yellow-500 disabled:opacity-30 text-[11px] font-bold text-white transition active:scale-95"
        >
          {status === "paused" ? "RESUME" : "PAUSE"}
        </button>
        
        <div className="flex rounded-md overflow-hidden border border-white/10">
          <button
            onClick={() => post("speed/1")}
            className={`px-2 py-1.5 text-[10px] font-bold transition-colors ${simState.speed === 1 ? "bg-blue-600 text-white" : "bg-slate-800 text-slate-400 hover:bg-slate-700"}`}
          >
            1x
          </button>
          <button
            onClick={() => post("speed/5")}
            className={`px-2 py-1.5 text-[10px] font-bold border-l border-white/10 transition-colors ${simState.speed === 5 ? "bg-blue-600 text-white" : "bg-slate-800 text-slate-400 hover:bg-slate-700"}`}
          >
            5x
          </button>
          <button
            onClick={() => post("speed/20")}
            className={`px-2 py-1.5 text-[10px] font-bold border-l border-white/10 transition-colors ${simState.speed === 20 ? "bg-blue-600 text-white" : "bg-slate-800 text-slate-400 hover:bg-slate-700"}`}
          >
            20x
          </button>
        </div>

        <button
          onClick={() => post("finish")}
          disabled={status !== "running" && status !== "paused"}
          className="px-3 py-1.5 rounded-md bg-purple-600 hover:bg-purple-500 disabled:opacity-30 text-[11px] font-bold text-white transition active:scale-95"
        >
          INSTANT
        </button>
        
        <button
          onClick={() => post("reset")}
          className="px-3 py-1.5 rounded-md bg-slate-700 hover:bg-red-900/50 text-[11px] font-bold text-slate-300 transition active:scale-95"
        >
          RESET
        </button>
      </div>
    </div>
  );
}
