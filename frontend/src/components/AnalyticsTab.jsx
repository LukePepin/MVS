import React, { useState, useEffect } from "react";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, AreaChart, Area } from "recharts";

export default function AnalyticsTab({ workOrders, machineStatus, telemetryStats }) {
  const [history, setHistory] = useState([]);
  const [metrics, setMetrics] = useState({ avail: 100, perf: 100, qual: 100, oee: 100 });

  useEffect(() => {
    // Rudimentary OEE calculator for demo purposes:
    // Availability = (Running / (Running + Offline)).
    // Performance = (Expected Speed / Actual).
    // Quality = (Completed - scrap) / Completed.
    const offlineNodes = machineStatus.filter(m => m.current_state === "Offline" || m.current_state === "Error").length;
    const totalNodes = machineStatus.length || 3;
    const avail = Math.max(0, 100 - (offlineNodes / totalNodes) * 100);

    const completed = workOrders.filter(w => w.status.includes("Completed")).length;
    const scrapped = workOrders.filter(w => w.status.includes("Trash") || w.status.includes("tra")).length;
    
    let qual = 100;
    if (completed > 0) qual = ((completed - scrapped) / completed) * 100;

    // Performance based on Queue Depth (Bottlenecking hurts performance)
    const activeJobs = workOrders.filter(w => w.status.includes("Busy")).length;
    const perf = Math.max(20, Math.min(100, 100 - (activeJobs * 2))); 

    const oee = (avail/100) * (perf/100) * (qual/100) * 100;

    setMetrics({ avail, perf, qual, oee });

    setHistory(prev => {
        const newHist = [...prev, { time: new Date().toLocaleTimeString(), OEE: oee, Availability: avail, Performance: perf, Quality: qual }];
        if (newHist.length > 30) newHist.shift(); // Keep last 30 intervals
        return newHist;
    });

  }, [workOrders, machineStatus]);

  return (
    <div className="space-y-6 mt-6">
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="rounded-xl glass-panel p-5 border border-white/10 shadow-lg text-center">
            <h4 className="text-[10px] uppercase tracking-widest text-slate-400 font-bold mb-2">Availability (A)</h4>
            <div className={`text-4xl font-bold tracking-tighter ${metrics.avail < 80 ? 'text-red-400' : 'text-green-400'}`}>{metrics.avail.toFixed(1)}%</div>
            <p className="text-xs text-slate-500 mt-2">Uptime vs Downtime</p>
        </div>
        <div className="rounded-xl glass-panel p-5 border border-white/10 shadow-lg text-center">
            <h4 className="text-[10px] uppercase tracking-widest text-slate-400 font-bold mb-2">Performance (P)</h4>
            <div className={`text-4xl font-bold tracking-tighter ${metrics.perf < 80 ? 'text-orange-400' : 'text-green-400'}`}>{metrics.perf.toFixed(1)}%</div>
            <p className="text-xs text-slate-500 mt-2">Actual vs Target Speed</p>
        </div>
        <div className="rounded-xl glass-panel p-5 border border-white/10 shadow-lg text-center">
            <h4 className="text-[10px] uppercase tracking-widest text-slate-400 font-bold mb-2">Quality (Q)</h4>
            <div className={`text-4xl font-bold tracking-tighter ${metrics.qual < 95 ? 'text-red-400' : 'text-green-400'}`}>{metrics.qual.toFixed(1)}%</div>
            <p className="text-xs text-slate-500 mt-2">Good Parts Yield</p>
        </div>
        <div className="rounded-xl glass-panel p-5 border border-white/10 shadow-lg text-center bg-blue-900/10">
            <h4 className="text-[10px] uppercase tracking-widest text-blue-300 font-bold mb-2">Aggregate OEE (World Class ≥ 85%)</h4>
            <div className={`text-5xl font-bold tracking-tighter ${metrics.oee < 85 ? 'text-red-400' : 'text-blue-400'}`}>{metrics.oee.toFixed(1)}%</div>
            <p className="text-xs text-slate-500 mt-2">A × P × Q</p>
        </div>
      </div>

      <div className="rounded-xl glass-panel p-5 border border-white/10 shadow-lg">
        <h3 className="mb-4 text-base font-semibold text-white tracking-wide border-b border-white/10 pb-2">OEE Rolling Trend Line (F11 - Performance Metrics)</h3>
        <div className="h-64 mt-4 text-xs font-mono">
            <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={history} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                    <defs>
                        <linearGradient id="colorOee" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#60A5FA" stopOpacity={0.8}/>
                        <stop offset="95%" stopColor="#60A5FA" stopOpacity={0}/>
                        </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="#ffffff15" />
                    <XAxis dataKey="time" stroke="#94A3B8" />
                    <YAxis domain={[0, 100]} stroke="#94A3B8" />
                    <Tooltip contentStyle={{ backgroundColor: "#0f172a", borderColor: "#1e293b", color: "#f8fafc" }} />
                    <Legend />
                    <Area type="monotone" dataKey="OEE" stroke="#3B82F6" fillOpacity={1} fill="url(#colorOee)" isAnimationActive={false} />
                    <Line type="monotone" dataKey="Availability" stroke="#10B981" dot={false} isAnimationActive={false} />
                    <Line type="monotone" dataKey="Quality" stroke="#F59E0B" dot={false} isAnimationActive={false} />
                </AreaChart>
            </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
