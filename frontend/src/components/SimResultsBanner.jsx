import React from "react";

export default function SimResultsBanner({ simState, onReset }) {
  if (simState.sim_status !== "finished") return null;

  return (
    <div className="rounded-xl bg-blue-500/10 border border-blue-500/30 p-6 flex flex-col md:flex-row items-center justify-between gap-6 shadow-2xl animate-in fade-in zoom-in duration-500">
      <div className="flex items-center gap-4">
        <div className="w-12 h-12 rounded-full bg-blue-500 flex items-center justify-center text-2xl">
          🏆
        </div>
        <div>
          <h2 className="text-xl font-bold text-white">Simulation Complete</h2>
          <p className="text-sm text-blue-200/70">Performance metrics for algorithm: <span className="font-bold text-blue-300">{simState.algorithm}</span></p>
        </div>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-8">
        <div className="text-center">
          <div className="text-[10px] uppercase tracking-widest text-blue-300/60 mb-1">Throughput</div>
          <div className="text-2xl font-bold text-white">{simState.completed_jobs} <span className="text-sm font-normal text-slate-500">units</span></div>
        </div>
        <div className="text-center">
          <div className="text-[10px] uppercase tracking-widest text-blue-300/60 mb-1">Avg Flow Time</div>
          <div className="text-2xl font-bold text-white">{simState.avg_flow_time} <span className="text-sm font-normal text-slate-500">min</span></div>
        </div>
        <div className="text-center">
          <div className="text-[10px] uppercase tracking-widest text-blue-300/60 mb-1">Total Time</div>
          <div className="text-2xl font-bold text-white">{simState.sim_time} <span className="text-sm font-normal text-slate-500">min</span></div>
        </div>
        <div className="text-center">
          <div className="text-[10px] uppercase tracking-widest text-blue-300/60 mb-1">Est. OEE</div>
          <div className="text-2xl font-bold text-green-400">
            {((simState.completed_jobs * 15) / Math.max(1, simState.sim_time) * 0.95 * 100).toFixed(1)}%
          </div>
        </div>
      </div>

      <button
        onClick={onReset}
        className="px-6 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-sm font-bold text-white transition-all shadow-lg active:scale-95"
      >
        New Simulation
      </button>
    </div>
  );
}
