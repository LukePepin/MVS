import React from "react";
import SchematicVisualizer from "./components/SchematicVisualizer";
import StatusBadge from "./components/StatusBadge";
import { useTelemetry } from "./hooks/useTelemetry";

const Dashboard = () => {
  const { mode, setMode, data, error, endpoint } = useTelemetry();

  return (
    <div className="min-h-screen bg-slate-950 bg-[radial-gradient(ellipse_80%_80%_at_50%_-20%,rgba(30,58,138,0.25),rgba(255,255,255,0))] p-6 text-slate-100 font-inter">
      <div className="mx-auto max-w-[1500px] space-y-6">
        <header className="rounded-xl glass-panel p-5">
          <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
            <div>
              <h1 className="text-2xl font-bold text-white tracking-tight">MVS Dashboard</h1>
              <p className="mt-1 text-sm text-slate-400 font-medium">Decentralized MES & Kinematic Anomaly Simulator</p>
            </div>

            <div className="inline-flex rounded-lg border border-blue-900/70 bg-gray-900 p-1">
              <button
                type="button"
                onClick={() => setMode("live")}
                className={`rounded-md px-3 py-1.5 text-sm font-medium transition ${
                  mode === "live"
                    ? "bg-blue-500/20 text-blue-200 ring-1 ring-blue-500/50"
                    : "text-slate-300 hover:text-blue-200"
                }`}
              >
                Live Mode
              </button>
              <button
                type="button"
                onClick={() => setMode("mock")}
                className={`rounded-md px-3 py-1.5 text-sm font-medium transition ${
                  mode === "mock"
                    ? "bg-blue-500/20 text-blue-200 ring-1 ring-blue-500/50"
                    : "text-slate-300 hover:text-blue-200"
                }`}
              >
                Mock Testbed Mode
              </button>
            </div>
          </div>

          <div className="mt-4 grid grid-cols-1 gap-4 md:grid-cols-3">
            <div className="rounded-lg border border-white/5 bg-black/20 p-4 shadow-inner">
              <p className="text-[10px] font-bold uppercase tracking-widest text-slate-500">Cloud Status</p>
              <div className="mt-2">
                <StatusBadge status={data.cloud_status ? "Busy" : "Offline"} />
              </div>
            </div>
            <div className="rounded-lg border border-white/5 bg-black/20 p-4 shadow-inner">
              <p className="text-[10px] font-bold uppercase tracking-widest text-slate-500">Local Mesh Status</p>
              <div className="mt-2">
                <StatusBadge status={data.local_mesh_status ? "Busy" : "Offline"} />
              </div>
            </div>
            <div className="rounded-lg border border-white/5 bg-black/20 p-4 shadow-inner">
              <p className="text-[10px] font-bold uppercase tracking-widest text-slate-500">Endpoint</p>
              <a
                href={endpoint}
                target="_blank"
                rel="noreferrer"
                className="mt-2 inline-block text-sm font-medium text-blue-400 hover:text-blue-300 transition-colors"
              >
                Open Raw Dashboard Data
              </a>
            </div>
          </div>

          {error ? (
            <p className="mt-4 rounded-md border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-200 backdrop-blur-sm">
              Telemetry error: {error}
            </p>
          ) : null}
        </header>

        <SchematicVisualizer schematic={data.schematic} machineStatus={data.machine_status} />

        <section className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          <div className="rounded-xl glass-panel p-5">
            <h3 className="mb-4 text-base font-semibold text-white">Work Orders</h3>
            <div className="overflow-x-auto rounded-lg border border-white/5 bg-black/20">
              <table className="min-w-full divide-y divide-white/5 text-sm">
                <thead className="bg-white/5">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-semibold tracking-wide text-slate-300">OrderID</th>
                    <th className="px-4 py-3 text-left text-xs font-semibold tracking-wide text-slate-300">Requesting Unit</th>
                    <th className="px-4 py-3 text-left text-xs font-semibold tracking-wide text-slate-300">Due Date</th>
                    <th className="px-4 py-3 text-left text-xs font-semibold tracking-wide text-slate-300">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/5 text-slate-300">
                  {data.work_orders.map((order) => (
                    <tr key={order.order_id} className="hover:bg-white/5 transition-colors">
                      <td className="px-4 py-2.5 font-medium">{order.order_id}</td>
                      <td className="px-4 py-2.5">{order.requesting_unit}</td>
                      <td className="px-4 py-2.5 text-slate-400">{order.due_date}</td>
                      <td className="px-4 py-2.5">{order.status}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          <div className="rounded-xl glass-panel p-5">
            <h3 className="mb-4 text-base font-semibold text-white">Machine Status</h3>
            <div className="overflow-x-auto rounded-lg border border-white/5 bg-black/20">
              <table className="min-w-full divide-y divide-white/5 text-sm">
                <thead className="bg-white/5">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-semibold tracking-wide text-slate-300">MachineID</th>
                    <th className="px-4 py-3 text-left text-xs font-semibold tracking-wide text-slate-300">Current State</th>
                    <th className="px-4 py-3 text-left text-xs font-semibold tracking-wide text-slate-300">Job In Progress</th>
                    <th className="px-4 py-3 text-left text-xs font-semibold tracking-wide text-slate-300">Est Completion</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/5 text-slate-300">
                  {data.machine_status.map((machine) => (
                    <tr key={machine.machine_id} className="hover:bg-white/5 transition-colors">
                      <td className="px-4 py-2.5 font-medium">{machine.machine_id}</td>
                      <td className="px-4 py-2.5">{machine.current_state}</td>
                      <td className="px-4 py-2.5">{machine.job_in_progress || "-"}</td>
                      <td className="px-4 py-2.5 text-slate-400">{machine.est_completion || "-"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
};

export default Dashboard;
