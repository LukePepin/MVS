import React, { useState, useEffect, useMemo } from "react";
import { 
  LineChart, Line, AreaChart, Area, BarChart, Bar, XAxis, YAxis, 
  CartesianGrid, Tooltip, ResponsiveContainer, Legend
} from "recharts";
import { useSimState } from "../hooks/useSimState";

export default function AnalyticsPage() {
  const simState = useSimState();
  const [oeeData, setOeeData] = useState([]);

  useEffect(() => {
    fetch("http://localhost:8000/analytics/oee")
      .then(r => r.json())
      .then(setOeeData)
      .catch(console.error);
  }, []);

  const flowTimeHistogram = useMemo(() => {
    if (!simState.flow_times?.length) return [];
    const bins = {};
    simState.flow_times.forEach(ft => {
      const bin = Math.floor(ft / 5) * 5;
      bins[bin] = (bins[bin] || 0) + 1;
    });
    return Object.entries(bins).map(([bin, count]) => ({ bin: `${bin}-${parseInt(bin)+5}m`, count })).sort((a, b) => parseInt(a.bin) - parseInt(b.bin));
  }, [simState.flow_times]);

  const utilizationData = useMemo(() => {
    return Object.entries(simState.station_utilization || {}).map(([id, val]) => ({
      name: { R0: "Infeed", M1: "Mill", M2: "Laser", M3: "Lathe", R1: "Outfeed" }[id] || id,
      utilization: val,
      idle: 100 - val
    }));
  }, [simState.station_utilization]);

  return (
    <div className="space-y-8 pb-12">
      <header className="rounded-xl glass-panel p-6 border border-white/10 flex justify-between items-end">
        <div>
          <h1 className="text-3xl font-bold text-white tracking-tight">Advanced Analytics</h1>
          <p className="mt-1 text-sm text-slate-400 font-medium">Discrete Event Simulation Metrics & OEE Performance Tracking</p>
        </div>
        <div className="text-right">
          <div className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">Active Algorithm</div>
          <div className="text-lg font-bold text-blue-400">{simState.algorithm || "NONE"}</div>
        </div>
      </header>

      {/* High Level Metrics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <MetricCard title="Completed Jobs" value={simState.completed_jobs} sub="Units" color="text-blue-400" />
        <MetricCard title="Avg Flow Time" value={`${simState.avg_flow_time}m`} sub="Per Unit" color="text-purple-400" />
        <MetricCard title="Simulation Time" value={`${simState.sim_time}m`} sub="Total Elapsed" color="text-emerald-400" />
        <MetricCard title="Est. Throughput" value={(simState.completed_jobs / Math.max(1, simState.sim_time)).toFixed(2)} sub="Jobs/Min" color="text-amber-400" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        
        {/* OEE Trend Chart */}
        <div className="rounded-xl glass-panel p-6 border border-white/10 bg-black/20 shadow-xl">
          <h3 className="text-sm font-bold text-slate-300 uppercase tracking-wider mb-6 flex items-center gap-2">
            <span className="w-1.5 h-4 bg-blue-500 rounded-full"></span>
            Session OEE Trend
          </h3>
          <div className="h-[300px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={simState.oee_snapshots}>
                <defs>
                  <linearGradient id="colorOee" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
                <XAxis dataKey="sim_time" stroke="#64748b" fontSize={10} tickFormatter={(v) => `${v}m`} />
                <YAxis stroke="#64748b" fontSize={10} domain={[0, 100]} />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#0f172a', border: '1px solid #334155', borderRadius: '8px' }}
                  itemStyle={{ fontSize: '12px' }}
                />
                <Area type="monotone" dataKey="oee" stroke="#3b82f6" strokeWidth={3} fillOpacity={1} fill="url(#colorOee)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Station Utilization Bar Chart */}
        <div className="rounded-xl glass-panel p-6 border border-white/10 bg-black/20 shadow-xl">
          <h3 className="text-sm font-bold text-slate-300 uppercase tracking-wider mb-6 flex items-center gap-2">
            <span className="w-1.5 h-4 bg-emerald-500 rounded-full"></span>
            Work Center Utilization (%)
          </h3>
          <div className="h-[300px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={utilizationData} layout="vertical" margin={{ left: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" horizontal={false} />
                <XAxis type="number" hide domain={[0, 100]} />
                <YAxis dataKey="name" type="category" stroke="#94a3b8" fontSize={12} width={80} />
                <Tooltip cursor={{fill: 'transparent'}} contentStyle={{ backgroundColor: '#0f172a', border: '1px solid #334155' }} />
                <Bar dataKey="utilization" stackId="a" fill="#10b981" radius={[0, 4, 4, 0]} />
                <Bar dataKey="idle" stackId="a" fill="#1e293b" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Flow Time Distribution */}
        <div className="rounded-xl glass-panel p-6 border border-white/10 bg-black/20 shadow-xl">
          <h3 className="text-sm font-bold text-slate-300 uppercase tracking-wider mb-6 flex items-center gap-2">
            <span className="w-1.5 h-4 bg-purple-500 rounded-full"></span>
            Cycle Time Distribution
          </h3>
          <div className="h-[300px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={flowTimeHistogram}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
                <XAxis dataKey="bin" stroke="#64748b" fontSize={10} />
                <YAxis stroke="#64748b" fontSize={10} />
                <Tooltip cursor={{fill: 'rgba(255,255,255,0.05)'}} contentStyle={{ backgroundColor: '#0f172a', border: '1px solid #334155' }} />
                <Bar dataKey="count" fill="#a855f7" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* OEE Component Breakdown */}
        <div className="rounded-xl glass-panel p-6 border border-white/10 bg-black/20 shadow-xl">
          <h3 className="text-sm font-bold text-slate-300 uppercase tracking-wider mb-6 flex items-center gap-2">
            <span className="w-1.5 h-4 bg-amber-500 rounded-full"></span>
            OEE Components (A-P-Q)
          </h3>
          <div className="h-[300px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={simState.oee_snapshots}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
                <XAxis dataKey="sim_time" hide />
                <YAxis stroke="#64748b" fontSize={10} domain={[0, 100]} />
                <Tooltip contentStyle={{ backgroundColor: '#0f172a', border: '1px solid #334155' }} />
                <Legend verticalAlign="top" height={36} wrapperStyle={{ fontSize: '10px', textTransform: 'uppercase' }} />
                <Line type="monotone" dataKey="availability" stroke="#10b981" strokeWidth={2} dot={false} name="Avail" />
                <Line type="monotone" dataKey="performance" stroke="#3b82f6" strokeWidth={2} dot={false} name="Perf" />
                <Line type="monotone" dataKey="quality" stroke="#f43f5e" strokeWidth={2} dot={false} name="Qual" />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

      </div>
    </div>
  );
}

function MetricCard({ title, value, sub, color }) {
  return (
    <div className="rounded-xl glass-panel p-6 border border-white/10 bg-black/40 shadow-lg transition-transform hover:scale-[1.02]">
      <div className="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-2">{title}</div>
      <div className={`text-3xl font-black ${color} mb-1`}>{value}</div>
      <div className="text-xs text-slate-500 font-medium">{sub}</div>
    </div>
  );
}


