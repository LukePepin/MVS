import React, { useMemo } from "react";

const fallbackNodes = [];
const fallbackConnectors = [];

// Base mapping to convert relative arbitrary units to fixed pixel bases
const SCALE = 8; 

const typeStyles = {
  robot: "bg-red-500/90 border-2 border-dashed border-red-950 text-white rounded-full flex flex-col items-center justify-center font-bold shadow-[0_0_15px_rgba(239,68,68,0.4)]",
  conveyor: "bg-[#b48600] border-2 border-[#5a4300] text-[#4d3900] font-bold flex items-center justify-center shadow-md",
  machine: "bg-[#1e3a8a] border-2 border-[#0b1b44] text-white rounded-xl flex flex-col items-center justify-center font-bold shadow-[0_0_15px_rgba(30,58,138,0.35)]",
  station: "bg-orange-500/90 border-2 border-orange-900 text-white rounded-xl flex flex-col items-center justify-center font-bold shadow-[0_0_15px_rgba(249,115,22,0.3)]",
  inventory: "bg-[#a3d9a5] border-2 border-[#1d4f20] text-[#1d4f20] rounded-xl flex items-center justify-center font-bold shadow-md",
  output: "bg-[#a3d9a5] border-2 border-[#1d4f20] text-[#1d4f20] rounded-xl flex items-center justify-center font-bold shadow-md"
};

const SchematicVisualizer = ({ schematic, selectedRoute, selectedStepIndex }) => {
  const nodes = schematic?.nodes?.length ? schematic.nodes : fallbackNodes;
  const connectors = schematic?.connectors?.length ? schematic.connectors : fallbackConnectors;

  const nodeMap = useMemo(() => {
    const map = new Map();
    for (const node of nodes) {
      map.set(node.id, node);
    }
    return map;
  }, [nodes]);

  const edgeLines = useMemo(() => {
    return connectors
      .map((edge) => {
        const from = nodeMap.get(edge.from);
        const to = nodeMap.get(edge.to);
        if (!from || !to) return null;
        return {
          ...edge,
          x1: from.x,
          y1: from.y,
          x2: to.x,
          y2: to.y,
        };
      })
      .filter(Boolean);
  }, [connectors, nodeMap]);

  const pathEdges = useMemo(() => {
    if (!selectedRoute || selectedRoute.length < 2) {
      return new Set();
    }
    const startIndex = typeof selectedStepIndex === "number" ? selectedStepIndex : 0;
    const remaining = selectedRoute.slice(Math.max(0, startIndex));
    const edges = new Set();
    for (let i = 0; i < remaining.length - 1; i += 1) {
      edges.add(`${remaining[i]}|${remaining[i + 1]}`);
    }
    return edges;
  }, [selectedRoute, selectedStepIndex]);

  const pathNodes = useMemo(() => {
    if (!selectedRoute || selectedRoute.length === 0) {
      return new Set();
    }
    const startIndex = typeof selectedStepIndex === "number" ? selectedStepIndex : 0;
    return new Set(selectedRoute.slice(Math.max(0, startIndex)));
  }, [selectedRoute, selectedStepIndex]);

  return (
    <section className="rounded-xl glass-panel p-5">
      <div className="mb-4 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
            <h3 className="text-xl font-bold text-white tracking-tight">Physical Layout Visualization</h3>
            <p className="text-xs text-slate-400">Custom shape mapping mimicking physical architecture</p>
        </div>
        <span className="rounded border border-blue-500/30 bg-blue-500/10 px-2.5 py-1 text-xs font-semibold tracking-widest uppercase text-blue-300">Live Telemetry</span>
      </div>

      {nodes.length === 0 ? (
          <div className="h-[600px] w-full flex items-center justify-center border border-white/10 rounded-xl bg-[#060b13]">
              <span className="text-slate-500">Awaiting Testbed Initialization...</span>
          </div>
      ) : (
        <div className="relative min-h-[850px] w-full rounded-xl border border-white/10 bg-[#060b13] shadow-inner overflow-hidden">
            {/* Blueprint Grid */}
            <div className="absolute inset-0 bg-[linear-gradient(to_right,#1e293b_1px,transparent_1px),linear-gradient(to_bottom,#1e293b_1px,transparent_1px)] bg-[size:40px_40px] opacity-20"></div>

            {/* Connecting Edges and Active WIP Animations */}
            <svg className="pointer-events-none absolute inset-0 h-full w-full opacity-60">
                {edgeLines.map((edge) => (
                <React.Fragment key={`edge-group-${edge.from}-${edge.to}`}>
                    <line
                        x1={`${edge.x1}%`}
                        y1={`${edge.y1}%`}
                        x2={`${edge.x2}%`}
                        y2={`${edge.y2}%`}
                      className={pathEdges.has(`${edge.from}|${edge.to}`) ? "stroke-blue-200" : "stroke-slate-500"}
                      strokeWidth={pathEdges.has(`${edge.from}|${edge.to}`) ? "3" : "2"}
                        strokeDasharray="4 4"
                    />
                    {edge.active && (
                        <circle r="6" className="fill-blue-300 drop-shadow-[0_0_8px_rgba(147,197,253,0.9)]">
                        <animate attributeName="cx" values={`${edge.x1}%;${edge.x2}%`} dur="3.6s" repeatCount="indefinite" />
                        <animate attributeName="cy" values={`${edge.y1}%;${edge.y2}%`} dur="3.6s" repeatCount="indefinite" />
                        </circle>
                    )}
                </React.Fragment>
                ))}
            </svg>

            {/* Custom Nodal Shapes */}
            {nodes.map((node) => {
                const widthPx = (node.w || 10) * SCALE;
                const heightPx = (node.h || 10) * SCALE;
                const baseClass = typeStyles[node.type] || typeStyles.machine;
                const isPathNode = pathNodes.has(node.id);
                
                // Dim nodes that are offline or error
                const opacityAttr = (node.status === "Offline" || node.status === "Blocked" || node.status === "Disconnected")
                  ? "opacity-50 grayscale"
                  : "opacity-100";

                return (
                    <div
                        key={node.id}
                        className={`absolute -translate-x-1/2 -translate-y-1/2 flex items-center justify-center transition-all duration-300 ${opacityAttr}`}
                        style={{ 
                            left: `${node.x}%`, 
                            top: `${node.y}%`, 
                            width: `${widthPx}px`, 
                            height: `${heightPx}px`,
                            transform: `translate(-50%, -50%) rotate(${node.rot || 0}deg)`
                        }}
                        title={`${node.label} (${node.status})`}
                    >
                        <div className={`w-full h-full ${baseClass} ${isPathNode ? "ring-2 ring-blue-200/70" : ""}`}>
                            {/* Counter-rotate label so text remains horizontally legible if conveyor is tilted */}
                            <span 
                                className="block text-center whitespace-pre-wrap leading-tight text-[11px]" 
                                style={{ transform: `rotate(${-(node.rot || 0)}deg)` }}
                            >
                                {node.label}
                            </span>
                        </div>

                        {/* Active jobs badge rendered specifically if active. Conveyors show no badges natively unless requested */}
                        {node.active_jobs > 0 && node.type !== "conveyor" && (
                            <div className="absolute -right-2 -top-2 flex h-5 min-w-5 items-center justify-center rounded-full bg-blue-500 text-[10px] font-bold text-white shadow-[0_0_8px_rgba(59,130,246,0.6)] animate-pulse border border-blue-200">
                                {node.active_jobs}
                            </div>
                        )}

                        {/* Queue backlog warning specifically for inventory buffers */}
                        {node.type === "inventory" && node.queue_depth > 0 && (
                            <div className="absolute -left-2 -top-2 flex h-5 min-w-5 items-center justify-center rounded-full bg-red-600 text-[10px] font-bold text-white shadow-[0_0_8px_rgba(220,38,38,0.8)] animate-bounce border border-red-300" title="Queue Backlog!">
                                !{node.queue_depth}
                            </div>
                        )}
                    </div>
                );
            })}
        </div>
      )}
    </section>
  );
};

export default SchematicVisualizer;
