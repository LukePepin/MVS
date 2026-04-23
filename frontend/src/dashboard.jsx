import React, { useMemo } from "react";
import SchematicVisualizer from "./components/SchematicVisualizer";
import StatusBadge from "./components/StatusBadge";
import SimulationControls from "./components/SimulationControls";
import EventsLog from "./components/EventsLog";
import SimResultsBanner from "./components/SimResultsBanner";
import ControlPlaneSections from "./components/ControlPlaneSections";
import { useTelemetry } from "./hooks/useTelemetry";
import { useSimState } from "./hooks/useSimState";

const Dashboard = () => {
  const { mode, setMode, data } = useTelemetry();
  const simState = useSimState();

  const r6Node = useMemo(
    () => data?.schematic?.nodes?.find((node) => node.id === "r6"),
    [data]
  );
  const r6Imu = r6Node?.raw_imu || null;

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

  const handleReset = async () => {
    try {
      await fetch("http://localhost:8000/api/sim/reset", { method: "POST" });
    } catch (e) {
      console.error(e);
    }
  };

  const activeJobs = data.work_orders?.length || 0;

  const simulatedDateTime = useMemo(() => {
    if (!simState?.simulated_time_iso) {
      return "N/A";
    }
    const dt = new Date(simState.simulated_time_iso);
    if (Number.isNaN(dt.getTime())) {
      return "N/A";
    }
    return dt.toLocaleString();
  }, [simState?.simulated_time_iso]);

  return (
    <div className="space-y-6 pb-12">
      {/* Simulation Result Highlight */}
      <SimResultsBanner simState={simState} onReset={handleReset} />

      {/* Header & Global Toolbar */}
      <div className="grid grid-cols-1 xl:grid-cols-[minmax(0,1.15fr)_minmax(0,1.85fr)] items-stretch gap-4">
        <header className="rounded-xl glass-panel p-5 border border-white/10 shadow-lg h-full flex flex-col justify-between gap-4">
          <div className="flex items-center justify-between gap-3">
            <div className="space-y-1">
              <h1 className="text-2xl font-bold text-white tracking-tight">Factory Floor</h1>
              <p className="text-xs text-slate-400 font-medium">EARC Live Digital Twin & MES Executor</p>
              <p className="text-[11px] text-blue-300 font-mono">Simulated Project Time: {simulatedDateTime}</p>
            </div>
            <div className="flex items-center gap-2">
              <div className="flex rounded-lg bg-black/40 p-1 border border-white/5">
                <button
                  onClick={() => setMode("hybrid")}
                  className={`px-3 py-1.5 text-[10px] font-bold rounded-md transition-all ${mode === "hybrid" ? "bg-blue-600 text-white shadow-lg" : "text-slate-500 hover:text-slate-300"}`}
                >
                  HYBRID
                </button>
                <button
                  onClick={() => setMode("mock")}
                  className={`px-3 py-1.5 text-[10px] font-bold rounded-md transition-all ${mode === "mock" ? "bg-blue-600 text-white shadow-lg" : "text-slate-500 hover:text-slate-300"}`}
                >
                  MOCK
                </button>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div className="glass-panel px-4 py-2 rounded-lg border border-white/10 bg-black/60 backdrop-blur-md">
              <div className="text-[9px] uppercase font-bold text-slate-500 tracking-widest">Active Jobs</div>
              <div className="text-lg font-bold text-white leading-tight">{activeJobs}</div>
            </div>
            <div className="glass-panel px-4 py-2 rounded-lg border border-white/10 bg-black/60 backdrop-blur-md">
              <div className="text-[9px] uppercase font-bold text-slate-500 tracking-widest">Bottleneck</div>
              <div className={`text-lg font-bold leading-tight ${bottleneckNode ? "text-red-400" : "text-green-400"}`}>
                {bottleneckNode ? bottleneckNode.toUpperCase() : "NONE"}
              </div>
            </div>
          </div>
        </header>

        <div className="h-full">
          <SimulationControls simState={simState} />
        </div>
      </div>

      {/* Schematic Full Width */}
      <div className="rounded-xl overflow-hidden border border-white/10 shadow-2xl relative">
        <SchematicVisualizer
          schematic={data.schematic}
          machineStatus={data.machine_status}
          bottleneckNode={bottleneckNode}
          simTokens={[
            ...(simState.tokens || []),
            ...(data.work_orders || []).filter(wo => wo.current_node).map(wo => ({
              job_id: `WO-${wo.order_id}`,
              product: wo.status?.split(":")[0] || "",
              current_station: wo.current_node,
              status: wo.status?.split(":")[2]?.trim() || "Busy",
            })),
          ]}
        />
      </div>

      <section className="space-y-8">
        <ControlPlaneSections />
      </section>

      {/* Detailed Data View */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Station Utilization */}
        <div className="lg:col-span-2 space-y-6">
          <section className="rounded-xl glass-panel p-5 border border-white/10 shadow-lg bg-black/20">
            <h3 className="mb-4 text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
              <span className="w-1.5 h-4 bg-green-500 rounded-full"></span>
              Work Center Utilization
            </h3>
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-4">
              {Object.entries(simState.station_busy || {}).map(([station, busy]) => {
                const queue = (simState.station_queue || {})[station] || 0;
                const labels = { R0: "Infeed", M1: "CNC Mill", M2: "Laser", M3: "Lathe", R1: "Outfeed" };
                return (
                  <div key={station} className="rounded-xl border border-white/5 bg-black/40 p-4 text-center transition-all hover:border-white/20">
                    <div className="text-[10px] uppercase font-bold tracking-widest text-slate-500 mb-1">{labels[station] || station}</div>
                    <div className={`text-xl font-black ${busy > 0 ? "text-green-400" : "text-slate-600"}`}>
                      {busy > 0 ? "BUSY" : "IDLE"}
                    </div>
                    <div className="mt-2 h-1 w-full bg-white/5 rounded-full overflow-hidden">
                      <div className={`h-full transition-all duration-1000 ${busy > 0 ? "bg-green-500 w-full" : "w-0"}`}></div>
                    </div>
                    <div className="text-[10px] text-slate-500 mt-2 font-mono">Q-DEPTH: {queue}</div>
                  </div>
                );
              })}
            </div>
          </section>

          {/* Active Work Orders */}
          <section className="rounded-xl glass-panel p-5 border border-white/10 bg-black/20 overflow-hidden">
             <h3 className="mb-4 text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
              <span className="w-1.5 h-4 bg-blue-500 rounded-full"></span>
              Active Shop Floor Orders
            </h3>
            <div className="overflow-x-auto rounded-lg border border-white/5 bg-black/40">
              <table className="min-w-full divide-y divide-white/5 text-xs font-mono">
                <thead className="bg-white/5">
                  <tr>
                    <th className="px-4 py-3 text-left text-slate-400">ORDER_ID</th>
                    <th className="px-4 py-3 text-left text-slate-400">UNIT</th>
                    <th className="px-4 py-3 text-left text-slate-400">STATUS</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/5 text-slate-300">
                  {data.work_orders.map((order) => (
                    <tr key={order.order_id} className="hover:bg-white/5 transition-colors">
                      <td className="px-4 py-3 font-bold text-blue-400">#{order.order_id}</td>
                      <td className="px-4 py-3">{order.requesting_unit}</td>
                      <td className="px-4 py-3">
                        <span className="px-2 py-0.5 rounded-full bg-white/5 text-[10px]">
                          {order.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        </div>

        {/* Live Telemetry Feed */}
        <div className="space-y-6">
           <section className="rounded-xl glass-panel p-5 border border-white/10 bg-black/20 h-full">
            <h3 className="mb-4 text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
              <span className="w-1.5 h-4 bg-red-500 rounded-full"></span>
              R6 IMU Telemetry
            </h3>
            
            <div className="space-y-6">
              <div className="p-4 rounded-xl bg-black/40 border border-white/5 flex items-center justify-between">
                <div>
                  <div className="text-[10px] text-slate-500 font-bold uppercase mb-1">State</div>
                  <StatusBadge status={r6Node?.status || "Offline"} />
                </div>
                <div className="text-right">
                  <div className="text-[10px] text-slate-500 font-bold uppercase mb-1">Source</div>
                  <div className="text-xs font-bold text-white">{r6Node?.source?.toUpperCase() || "MOCK"}</div>
                </div>
              </div>

              {r6Imu ? (
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-3">
                    <div className="text-[10px] text-blue-400 font-bold uppercase border-b border-blue-400/20 pb-1">Accelerometer</div>
                    <div className="space-y-1 font-mono text-xs">
                      <div className="flex justify-between"><span>AX:</span> <span style={{ color: colorForValue(r6Imu.ax, 2) }}>{r6Imu.ax.toFixed(4)}</span></div>
                      <div className="flex justify-between"><span>AY:</span> <span style={{ color: colorForValue(r6Imu.ay, 2) }}>{r6Imu.ay.toFixed(4)}</span></div>
                      <div className="flex justify-between"><span>AZ:</span> <span style={{ color: colorForValue(r6Imu.az, 2) }}>{r6Imu.az.toFixed(4)}</span></div>
                    </div>
                  </div>
                  <div className="space-y-3">
                    <div className="text-[10px] text-purple-400 font-bold uppercase border-b border-purple-400/20 pb-1">Gyroscope</div>
                    <div className="space-y-1 font-mono text-xs">
                      <div className="flex justify-between"><span>GX:</span> <span style={{ color: colorForValue(r6Imu.gx, 30) }}>{r6Imu.gx.toFixed(4)}</span></div>
                      <div className="flex justify-between"><span>GY:</span> <span style={{ color: colorForValue(r6Imu.gy, 30) }}>{r6Imu.gy.toFixed(4)}</span></div>
                      <div className="flex justify-between"><span>GZ:</span> <span style={{ color: colorForValue(r6Imu.gz, 30) }}>{r6Imu.gz.toFixed(4)}</span></div>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="py-12 text-center text-slate-600 text-xs font-medium border-2 border-dashed border-white/5 rounded-xl">
                  WAITING FOR DATA PACKETS...
                </div>
              )}

              <EventsLog events={simState.events_log} />
            </div>
          </section>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
