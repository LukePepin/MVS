import React from "react";
import SettingsPanel from "./SettingsPanel";
import TraceabilityTab from "./TraceabilityTab";

export default function ControlPlaneSections() {
  return (
    <>
      <header className="rounded-xl glass-panel p-6 border border-white/10">
        <h1 className="text-3xl font-bold text-white tracking-tight">Cyber-Physical Control Plane</h1>
        <p className="mt-1 text-sm text-slate-400 font-medium">
          Adversarial Configuration, Production Optimization, and Genealogy Traceability
        </p>
      </header>

      <section>
        <SettingsPanel />
      </section>

      <section className="space-y-4">
        <div className="flex items-center gap-2 px-2">
          <div className="w-1.5 h-6 bg-blue-500 rounded-full"></div>
          <h2 className="text-xl font-bold text-white">Product Genealogy (F10)</h2>
        </div>
        <TraceabilityTab />
      </section>

      <section className="rounded-xl glass-panel p-6 border border-white/10 bg-black/40">
        <h3 className="text-lg font-bold text-white mb-4">Scheduling Algorithm Reference (MESA-11)</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="space-y-2">
            <h4 className="text-sm font-bold text-blue-400">Time-Based (SPT/LPT)</h4>
            <p className="text-xs text-slate-400 leading-relaxed">
              <strong>SPT:</strong> Minimizes average completion time and WIP levels. Best for steady-state throughput.<br/>
              <strong>LPT:</strong> Maximizes utilization of bottleneck resources by front-loading complex tasks.
            </p>
          </div>
          <div className="space-y-2">
            <h4 className="text-sm font-bold text-orange-400">Due-Date Based (EDD/CR)</h4>
            <p className="text-xs text-slate-400 leading-relaxed">
              <strong>EDD:</strong> Minimizes maximum lateness. Essential for meeting customer service level agreements.<br/>
              <strong>CR:</strong> Dynamic ratio of time remaining to work remaining. Prioritizes jobs falling behind schedule.
            </p>
          </div>
          <div className="space-y-2">
            <h4 className="text-sm font-bold text-purple-400">Weighted / Logical (WSPT/FIFO)</h4>
            <p className="text-xs text-slate-400 leading-relaxed">
              <strong>WSPT:</strong> Incorporates job priority (weights) into processing order. Minimizes total weighted completion time.<br/>
              <strong>FIFO:</strong> Default fairness-based arrival sequence.
            </p>
          </div>
        </div>
      </section>
    </>
  );
}
