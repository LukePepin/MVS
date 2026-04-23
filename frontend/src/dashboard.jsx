import React, { useMemo, useState } from "react";
import SchematicVisualizer from "./components/SchematicVisualizer";
import StatusBadge from "./components/StatusBadge";
import SettingsPanel from "./components/SettingsPanel";
import AnalyticsTab from "./components/AnalyticsTab";
import TraceabilityTab from "./components/TraceabilityTab";
import { useTelemetry } from "./hooks/useTelemetry";

const Dashboard = () => {
  const { mode, setMode, data, error, endpoint } = useTelemetry();
  const [activeTab, setActiveTab] = useState("overview");
  const r6Node = useMemo(
    () => data?.schematic?.nodes?.find((node) => node.id === "r6"),
    [data]
  );
  const r6Imu = r6Node?.raw_imu || null;

  const accelMag = useMemo(() => {
    if (!r6Imu) {
      return 0;
    }
    return Math.sqrt(r6Imu.ax ** 2 + r6Imu.ay ** 2 + r6Imu.az ** 2);
  }, [r6Imu]);

  const gyroMag = useMemo(() => {
    if (!r6Imu) {
      return 0;
    }
    return Math.sqrt(r6Imu.gx ** 2 + r6Imu.gy ** 2 + r6Imu.gz ** 2);
  }, [r6Imu]);

  const bottleneckNode = useMemo(() => {
    if (!data?.schematic?.nodes) return null;
    let maxQueue = 0;
    let bNode = null;
    for (const n of data.schematic.nodes) {
        if (n.queue_depth > maxQueue) {
            maxQueue = n.queue_depth;
            bNode = n.id;
        }
    }
    return bNode;
  }, [data]);

  const colorForValue = (value, maxAbs) => {
    const intensity = Math.min(1, Math.abs(value) / maxAbs);
    const red = Math.round(200 + 55 * intensity);
    const green = Math.round(220 - 140 * intensity);
    const blue = Math.round(220 - 160 * intensity);
    return `rgb(${red}, ${green}, ${blue})`;
  };

  const formatCountdown = (isoDate) => {
    if (!isoDate) {
      return "-";
    }
    const target = new Date(isoDate).getTime();
    if (Number.isNaN(target)) {
      return "-";
    }
    const now = Date.now();
    const remainingMs = Math.max(0, target - now);
    const totalSeconds = Math.floor(remainingMs / 1000);
    const minutes = Math.floor(totalSeconds / 60);
    const seconds = totalSeconds % 60;
    return `${minutes}:${String(seconds).padStart(2, "0")}`;
  };


  return (
    <div className="min-h-screen bg-slate-950 bg-[radial-gradient(ellipse_80%_80%_at_50%_-20%,rgba(30,58,138,0.25),rgba(255,255,255,0))] px-2 py-4 text-slate-100 font-inter md:px-3 lg:px-4">
      <div className="mx-auto max-w-[1920px] space-y-6">
        <header className="rounded-xl glass-panel p-5">
          <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
            <div>
              <h1 className="text-2xl font-bold text-white tracking-tight">MVS Dashboard</h1>
              <p className="mt-1 text-sm text-slate-400 font-medium">Decentralized MES & Kinematic Anomaly Simulator</p>
            </div>

            <div className="flex flex-col gap-2 md:flex-row md:items-center">
              <div className="inline-flex rounded-lg border border-blue-900/70 bg-gray-900 p-1">
                <button
                  type="button"
                  onClick={() => setMode("hybrid")}
                  className={`rounded-md px-3 py-1.5 text-sm font-medium transition ${
                    mode === "hybrid"
                      ? "bg-blue-500/20 text-blue-200 ring-1 ring-blue-500/50"
                      : "text-slate-300 hover:text-blue-200"
                  }`}
                >
                  Hybrid Live Mode
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
              <button
                onClick={async () => {
                  try {
                    await fetch("http://localhost:8000/api/start", { method: "POST" });
                    alert("MES Execution Started! (Headless Simulation Running)");
                  } catch (e) {
                    console.error("Start failed", e);
                  }
                }}
                className="rounded-lg border border-green-500 bg-green-600 px-4 py-2 text-sm font-bold text-white shadow-lg transition-colors hover:bg-green-500"
              >
                ▶ START EXECUTION
              </button>
            </div>
          </div>

          <div className="mt-4 flex gap-6 border-b border-white/10 pb-4">
            <button onClick={() => setActiveTab("overview")} className={`text-sm font-semibold transition ${activeTab === 'overview' ? 'text-blue-400 border-b-2 border-blue-400 pb-1' : 'text-slate-400 hover:text-white'}`}>Overview</button>
            <button onClick={() => setActiveTab("analytics")} className={`text-sm font-semibold transition ${activeTab === 'analytics' ? 'text-blue-400 border-b-2 border-blue-400 pb-1' : 'text-slate-400 hover:text-white'}`}>Analytics & Trends</button>
            <button onClick={() => setActiveTab("traceability")} className={`text-sm font-semibold transition ${activeTab === 'traceability' ? 'text-blue-400 border-b-2 border-blue-400 pb-1' : 'text-slate-400 hover:text-white'}`}>Traceability</button>
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

        <div className="grid grid-cols-1 gap-6 lg:grid-cols-12">
          
          {activeTab === "overview" && (
            <>
          <div className="lg:col-span-9">
            <SchematicVisualizer schematic={data.schematic} machineStatus={data.machine_status} bottleneckNode={bottleneckNode} />

            <section className="mt-6 rounded-xl glass-panel p-5">
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
            </section>

            <section className="mt-6 rounded-xl glass-panel p-5">
              <div className="flex flex-col gap-1">
                <h3 className="text-base font-semibold text-white">R6 Live Telemetry</h3>
                <p className="text-xs text-slate-400">
                  Raw 6-axis IMU metrics are shown when Hybrid mode is active.
                </p>
              </div>
              <div className="mt-4 grid grid-cols-1 gap-4 md:grid-cols-2">
                <div className="rounded-lg border border-white/5 bg-black/20 p-4">
                  <p className="text-[10px] font-bold uppercase tracking-widest text-slate-500">Status</p>
                  <div className="mt-2 flex items-center gap-2">
                    <StatusBadge status={r6Node?.status || "Offline"} />
                    <span className="text-xs text-slate-400">Source: {r6Node?.source || "mock"}</span>
                  </div>
                  <div className="mt-3 text-xs text-slate-400">
                    <div>Host time: {r6Node?.host_time || "-"}</div>
                    <div>Device time: {r6Node?.device_time || "-"}</div>
                  </div>
                  <div className="mt-4 text-xs text-slate-300">
                    <div>Accel magnitude: {accelMag.toFixed(3)}</div>
                    <div>Gyro magnitude: {gyroMag.toFixed(3)}</div>
                  </div>
                </div>
                <div className="rounded-lg border border-white/5 bg-black/20 p-4">
                  <p className="text-[10px] font-bold uppercase tracking-widest text-slate-500">Raw IMU</p>
                  {r6Imu ? (
                    <div className="mt-3 grid grid-cols-3 gap-3 text-sm font-semibold">
                      <div style={{ color: colorForValue(r6Imu.ax, 2) }}>ax: {r6Imu.ax.toFixed(4)}</div>
                      <div style={{ color: colorForValue(r6Imu.ay, 2) }}>ay: {r6Imu.ay.toFixed(4)}</div>
                      <div style={{ color: colorForValue(r6Imu.az, 2) }}>az: {r6Imu.az.toFixed(4)}</div>
                      <div style={{ color: colorForValue(r6Imu.gx, 30) }}>gx: {r6Imu.gx.toFixed(4)}</div>
                      <div style={{ color: colorForValue(r6Imu.gy, 30) }}>gy: {r6Imu.gy.toFixed(4)}</div>
                      <div style={{ color: colorForValue(r6Imu.gz, 30) }}>gz: {r6Imu.gz.toFixed(4)}</div>
                    </div>
                  ) : (
                    <div className="mt-2 text-xs text-slate-400">No live sample yet.</div>
                  )}
                </div>
              </div>

            </section>
          </div>

          <section className="rounded-xl p-5 lg:col-span-3 space-y-6">
            <SettingsPanel />

            <div className="glass-panel p-5 rounded-xl border border-white/10 shadow-lg">
              <h3 className="mb-4 text-base font-semibold text-white">Testbed Analytics</h3>
              <div className="grid grid-cols-1 gap-3 text-xs text-slate-300">
                <div className="rounded-lg border border-white/5 bg-black/20 p-3">
                  <div className="text-[10px] uppercase tracking-widest text-slate-500">Jobs Active</div>
                  <div className="mt-1 text-base font-semibold text-white">{data.work_orders.length}</div>
                </div>
                <div className="rounded-lg border border-white/5 bg-black/20 p-3 flex justify-between items-center">
                  <div>
                    <div className="text-[10px] uppercase tracking-widest text-slate-500">Bottleneck</div>
                    <div className="mt-1 text-base font-semibold text-red-400">{bottleneckNode ? bottleneckNode.toUpperCase() : "None"}</div>
                  </div>
                  {bottleneckNode && <span className="animate-pulse w-3 h-3 bg-red-500 rounded-full"></span>}
                </div>
              </div>
            </div>

            <div className="mt-6">
              <h3 className="mb-4 text-base font-semibold text-white">Machine Status</h3>
              <div className="overflow-x-auto rounded-lg border border-white/5 bg-black/20">
                <table className="min-w-full divide-y divide-white/5 text-sm">
                  <thead className="bg-white/5">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-semibold tracking-wide text-slate-300">MachineID</th>
                      <th className="px-4 py-3 text-left text-xs font-semibold tracking-wide text-slate-300">Current State</th>
                      <th className="px-4 py-3 text-left text-xs font-semibold tracking-wide text-slate-300">Job In Progress</th>
                      <th className="px-4 py-3 text-left text-xs font-semibold tracking-wide text-slate-300">Est Completion</th>
                      <th className="px-4 py-3 text-left text-xs font-semibold tracking-wide text-slate-300">Time Left</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-white/5 text-slate-300">
                    {data.machine_status.map((machine) => (
                      <tr key={machine.machine_id} className="hover:bg-white/5 transition-colors">
                        <td className="px-4 py-2.5 font-medium">{machine.machine_id}</td>
                        <td className="px-4 py-2.5">{machine.current_state}</td>
                        <td className="px-4 py-2.5">{machine.job_in_progress || "-"}</td>
                        <td className="px-4 py-2.5 text-slate-400">{machine.est_completion || "-"}</td>
                        <td className="px-4 py-2.5 text-slate-300">
                          {formatCountdown(machine.est_completion)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </section>
          </>
          )}

          {activeTab === "analytics" && (
            <div className="lg:col-span-12">
                <AnalyticsTab workOrders={data.work_orders} machineStatus={data.machine_status} telemetryStats={data.telemetry_stats} />
            </div>
          )}

          {activeTab === "traceability" && (
            <div className="lg:col-span-12">
                <TraceabilityTab />
            </div>
          )}

        </div>
      </div>
    </div>
  );
};

export default Dashboard;
