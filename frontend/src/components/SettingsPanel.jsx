import React, { useState } from "react";

export default function SettingsPanel() {
  const [dil, setDil] = useState({ 
    r6_offline: false, 
    packet_loss: 0, 
    latency: 0, 
    jitter: 0,
    spoofed_node: null,
    bandwidth_kbps: 0.0,
    trust_override: null,
    isolated_nodes: []
  });
  const [routing, setRouting] = useState("SPT");
  const [statusMsg, setStatusMsg] = useState("");

  const applySettings = async (settings = dil) => {
    try {
      await fetch("http://localhost:8000/settings/dil", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(settings),
      });
      setStatusMsg("Configuration applied successfully.");
      setTimeout(() => setStatusMsg(""), 3000);
    } catch (e) {
      setStatusMsg("Failed to apply configuration");
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
      setStatusMsg(`Global routing updated to ${algo}`);
      setTimeout(() => setStatusMsg(""), 3000);
    } catch (e) {
      setStatusMsg("Failed to update routing");
    }
  };

  const setPreset = (preset) => {
    let newDil = { ...dil };
    if (preset === "nominal") {
      newDil = { r6_offline: false, packet_loss: 0, latency: 0, jitter: 0, spoofed_node: null, bandwidth_kbps: 10000, trust_override: 1.0, isolated_nodes: [] };
    } else if (preset === "degraded") {
      newDil = { r6_offline: false, packet_loss: 5, latency: 400, jitter: 100, spoofed_node: null, bandwidth_kbps: 128, trust_override: 0.7, isolated_nodes: [] };
    } else if (preset === "spoof") {
      newDil = { r6_offline: false, packet_loss: 0, latency: 0, jitter: 0, spoofed_node: "cncm", bandwidth_kbps: 10000, trust_override: 0.4, isolated_nodes: [] };
    } else if (preset === "attack") {
      newDil = { r6_offline: true, packet_loss: 20, latency: 1000, jitter: 500, spoofed_node: "r6", bandwidth_kbps: 10, trust_override: 0.1, isolated_nodes: ["cncm", "lz"] };
    }
    setDil(newDil);
    applySettings(newDil);
  };

  const toggleNodeIsolation = (nodeId) => {
    const newIsolated = dil.isolated_nodes.includes(nodeId) 
      ? dil.isolated_nodes.filter(n => n !== nodeId)
      : [...dil.isolated_nodes, nodeId];
    setDil({ ...dil, isolated_nodes: newIsolated });
  };

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Routing Controls */}
        <div className="rounded-xl glass-panel p-6 border border-white/10 shadow-xl bg-black/40">
          <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-blue-500"></span>
            Production Routing Logic
          </h3>
          <div className="space-y-4">
            <p className="text-sm text-slate-400">Select the active dispatching rule for real-time production optimization.</p>
            <div className="grid grid-cols-2 gap-3">
              {["SPT", "EDD", "FIFO", "LPT", "WSPT", "CR"].map(algo => (
                <button 
                  key={algo}
                  onClick={() => applyRouting(algo)}
                  className={`px-4 py-3 rounded-lg text-sm font-bold transition-all border ${routing === algo ? "bg-blue-600/20 border-blue-500 text-blue-200 shadow-[0_0_15px_rgba(59,130,246,0.3)]" : "bg-white/5 border-white/5 text-slate-400 hover:bg-white/10"}`}
                >
                  {algo}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Preset Attacks */}
        <div className="rounded-xl glass-panel p-6 border border-white/10 shadow-xl bg-black/40">
          <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-red-500"></span>
            Security & DIL Scenarios
          </h3>
          <div className="space-y-4">
            <p className="text-sm text-slate-400">Inject adversarial network conditions or cybersecurity attack signatures.</p>
            <div className="grid grid-cols-2 gap-3">
              <button onClick={() => setPreset("nominal")} className="p-3 rounded-lg bg-green-500/10 border border-green-500/30 text-green-400 text-xs font-bold hover:bg-green-500/20 transition-all">NOMINAL STATE</button>
              <button onClick={() => setPreset("degraded")} className="p-3 rounded-lg bg-yellow-500/10 border border-yellow-500/30 text-yellow-400 text-xs font-bold hover:bg-yellow-500/20 transition-all">DEGRADED COMMS</button>
              <button onClick={() => setPreset("spoof")} className="p-3 rounded-lg bg-orange-500/10 border border-orange-500/30 text-orange-400 text-xs font-bold hover:bg-orange-500/20 transition-all">SENSOR SPOOFING</button>
              <button onClick={() => setPreset("attack")} className="p-3 rounded-lg bg-red-500/10 border border-red-500/30 text-red-400 text-xs font-bold hover:bg-red-500/20 transition-all">FULL COMPROMISE</button>
            </div>
          </div>
        </div>
      </div>

      {/* Granular Adversarial Controls */}
      <div className="rounded-xl glass-panel p-6 border border-white/10 shadow-xl bg-black/40">
        <h3 className="text-lg font-bold text-white mb-6 border-b border-white/5 pb-2">Granular Adversarial Configuration</h3>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
          {/* Column 1: Network */}
          <div className="space-y-6">
            <h4 className="text-xs font-bold text-blue-400 uppercase tracking-widest">Network Layers</h4>
            <div className="space-y-4">
              <div className="flex flex-col gap-1">
                <label className="text-[10px] uppercase font-bold text-slate-500">Latency: {dil.latency}ms</label>
                <input type="range" min="0" max="2000" step="50" value={dil.latency} onChange={(e) => setDil({...dil, latency: parseInt(e.target.value)})} className="w-full accent-blue-500" />
              </div>
              <div className="flex flex-col gap-1">
                <label className="text-[10px] uppercase font-bold text-slate-500">Jitter: {dil.jitter}ms</label>
                <input type="range" min="0" max="1000" step="10" value={dil.jitter} onChange={(e) => setDil({...dil, jitter: parseInt(e.target.value)})} className="w-full accent-blue-500" />
              </div>
              <div className="flex flex-col gap-1">
                <label className="text-[10px] uppercase font-bold text-slate-500">Packet Loss: {dil.packet_loss}%</label>
                <input type="range" min="0" max="100" step="1" value={dil.packet_loss} onChange={(e) => setDil({...dil, packet_loss: parseInt(e.target.value)})} className="w-full accent-blue-500" />
              </div>
            </div>
          </div>

          {/* Column 2: Security */}
          <div className="space-y-6">
            <h4 className="text-xs font-bold text-red-400 uppercase tracking-widest">Cybersecurity</h4>
            <div className="space-y-4">
              <div className="flex flex-col gap-1">
                <label className="text-[10px] uppercase font-bold text-slate-500">Trust Decay Override: {dil.trust_override || "Auto"}</label>
                <input type="range" min="0" max="1" step="0.05" value={dil.trust_override || 1.0} onChange={(e) => setDil({...dil, trust_override: parseFloat(e.target.value)})} className="w-full accent-red-500" />
              </div>
              <div className="flex flex-col gap-1">
                <label className="text-[10px] uppercase font-bold text-slate-500">Spoof Node Target</label>
                <select 
                  value={dil.spoofed_node || "none"} 
                  onChange={(e) => setDil({...dil, spoofed_node: e.target.value === "none" ? null : e.target.value})}
                  className="bg-slate-900 border border-white/10 rounded-md p-1.5 text-xs text-white"
                >
                  <option value="none">None (Nominal)</option>
                  <option value="r6">R6 (Outfeed)</option>
                  <option value="cncm">CNC Mill</option>
                  <option value="lz">Laser Cutter</option>
                  <option value="cncl">Lathe</option>
                </select>
              </div>
            </div>
          </div>

          {/* Column 3: Isolation */}
          <div className="space-y-6">
            <h4 className="text-xs font-bold text-orange-400 uppercase tracking-widest">Node Isolation</h4>
            <div className="grid grid-cols-2 gap-2">
              {["r0", "r1", "r2", "r3", "r4", "r5", "r6", "cncm", "lz", "cncl"].map(node => (
                <button 
                  key={node}
                  onClick={() => toggleNodeIsolation(node)}
                  className={`px-2 py-1.5 rounded text-[10px] font-bold border transition-all ${dil.isolated_nodes.includes(node) ? "bg-orange-500 border-orange-400 text-white" : "bg-white/5 border-white/5 text-slate-500 hover:bg-white/10"}`}
                >
                  {node.toUpperCase()}
                </button>
              ))}
            </div>
          </div>

          {/* Column 4: Apply */}
          <div className="flex flex-col justify-end gap-3">
             <button 
                onClick={() => applySettings()}
                className="w-full bg-blue-600 hover:bg-blue-500 text-white text-xs font-bold py-3 rounded-lg transition-all shadow-lg shadow-blue-500/20 active:scale-95"
            >
              APPLY CUSTOM PROFILE
            </button>
            {statusMsg && <div className="text-center text-xs text-green-400 font-bold animate-pulse">{statusMsg}</div>}
          </div>
        </div>
      </div>
    </div>
  );
}
