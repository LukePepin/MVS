import React, { useState } from "react";

export default function SettingsPanel() {
  const [dil, setDil] = useState({ r6_offline: false, packet_loss: 0, latency: 0, jitter: 0 });
  const [routing, setRouting] = useState("SPT");
  const [statusMsg, setStatusMsg] = useState("");

  const applyDil = async () => {
    try {
      await fetch("http://localhost:8000/settings/dil", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(dil),
      });
      setStatusMsg("DIL settings applied.");
      setTimeout(() => setStatusMsg(""), 3000);
    } catch (e) {
      setStatusMsg("Failed to apply DIL");
    }
  };

  const applyRouting = async (algo) => {
    setRouting(algo);
    try {
      await fetch("http://localhost:8000/settings/routing", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ algorithm: algo }),
      });
      setStatusMsg(`Routing set to ${algo}`);
      setTimeout(() => setStatusMsg(""), 3000);
    } catch (e) {
      setStatusMsg("Failed to apply Routing");
    }
  };

  return (
    <div className="rounded-xl glass-panel p-5 space-y-4 shadow-xl border border-white/10 bg-black/40">
      <h3 className="text-base font-semibold text-white tracking-wide border-b border-white/10 pb-2">Control Panel</h3>
      
      <div className="space-y-3">
        <h4 className="text-sm font-semibold text-slate-300">Routing Algorithm (F2/F3)</h4>
        <div className="flex gap-2">
          <button 
            type="button"
            className={`px-3 py-1.5 text-xs font-semibold rounded transition-all ${routing === "SPT" ? "bg-blue-600 text-white shadow ring-2 ring-blue-500/50" : "bg-white/5 text-slate-300 hover:bg-white/10"}`}
            onClick={() => applyRouting("SPT")}
          >
            Shortest Processing Time (SPT)
          </button>
          <button 
            type="button"
            className={`px-3 py-1.5 text-xs font-semibold rounded transition-all ${routing === "EDD" ? "bg-orange-600 text-white shadow ring-2 ring-orange-500/50" : "bg-white/5 text-slate-300 hover:bg-white/10"}`}
            onClick={() => applyRouting("EDD")}
          >
            Earliest Due Date (EDD)
          </button>
        </div>
      </div>

      <div className="space-y-4 pt-2">
        <h4 className="text-sm font-semibold text-slate-300">DIL Adversarial Settings (R6)</h4>
        
        <label className="flex items-center gap-3 cursor-pointer">
          <div className="relative">
            <input type="checkbox" className="sr-only" checked={dil.r6_offline} onChange={(e) => setDil({...dil, r6_offline: e.target.checked})} />
            <div className={`block w-10 h-6 rounded-full transition-colors ${dil.r6_offline ? "bg-red-500" : "bg-slate-700"}`}></div>
            <div className={`absolute left-1 top-1 bg-white w-4 h-4 rounded-full transition-transform ${dil.r6_offline ? "transform translate-x-4" : ""}`}></div>
          </div>
          <span className="text-xs font-medium text-slate-300">Simulate R6 Compromise / Disconnect (Offline Mode)</span>
        </label>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="flex flex-col gap-1">
            <label className="text-[10px] uppercase font-bold text-slate-500 tracking-wider">Latency (ms): {dil.latency}</label>
            <input type="range" min="0" max="1500" step="50" value={dil.latency} onChange={(e) => setDil({...dil, latency: parseInt(e.target.value)})} className="w-full accent-blue-500" />
          </div>
          <div className="flex flex-col gap-1">
            <label className="text-[10px] uppercase font-bold text-slate-500 tracking-wider">Jitter (ms): {dil.jitter}</label>
            <input type="range" min="0" max="500" step="10" value={dil.jitter} onChange={(e) => setDil({...dil, jitter: parseInt(e.target.value)})} className="w-full accent-blue-500" />
          </div>
          <div className="flex flex-col gap-1">
            <label className="text-[10px] uppercase font-bold text-slate-500 tracking-wider">Packet Loss (%): {dil.packet_loss}</label>
            <input type="range" min="0" max="100" step="1" value={dil.packet_loss} onChange={(e) => setDil({...dil, packet_loss: parseInt(e.target.value)})} className="w-full accent-blue-500" />
          </div>
        </div>

        <button 
            type="button" 
            onClick={applyDil}
            className="w-full mt-2 bg-slate-800 hover:bg-slate-700 text-white text-xs font-semibold py-2 rounded border border-slate-600 transition-colors"
        >
          Apply DIL Profile
        </button>
      </div>
      
      {statusMsg && <div className="text-xs text-green-400 font-semibold mt-2">{statusMsg}</div>}
    </div>
  );
}
