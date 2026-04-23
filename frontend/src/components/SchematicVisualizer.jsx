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

const STATION_TO_NODE = {
  R0: "r0",
  M1: "cncm",
  M2: "lz",
  M3: "cncl",
  R1: "r6",
};

const normalizeStationToNode = (station) => {
  if (!station) return null;
  if (STATION_TO_NODE[station]) return STATION_TO_NODE[station];
  return String(station).toLowerCase();
};

const SchematicVisualizer = ({ schematic, machineStatus, selectedRoute, selectedStepIndex, bottleneckNode, simTokens }) => {
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

  const nodePartCounts = useMemo(() => {
    const counts = new Map();
    for (const token of simTokens || []) {
      const station = token.current_station || token.current_node;
      const nodeId = normalizeStationToNode(station);
      if (!nodeId) continue;
      counts.set(nodeId, (counts.get(nodeId) || 0) + 1);
    }
    return counts;
  }, [simTokens]);

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

          {/* Connecting Edges with usage-based highlighting */}
            <svg className="pointer-events-none absolute inset-0 h-full w-full opacity-60">
                {edgeLines.map((edge) => (
                <React.Fragment key={`edge-group-${edge.from}-${edge.to}`}>
              {(() => {
                const fromCount = nodePartCounts.get(edge.from) || 0;
                const toCount = nodePartCounts.get(edge.to) || 0;
                const edgeInUse = Boolean(edge.active) || fromCount > 0 || toCount > 0;
                return (
                    <line
                        x1={`${edge.x1}%`}
                        y1={`${edge.y1}%`}
                        x2={`${edge.x2}%`}
                        y2={`${edge.y2}%`}
                className={edgeInUse || pathEdges.has(`${edge.from}|${edge.to}`) ? "stroke-emerald-300" : "stroke-slate-700"}
                strokeWidth={edgeInUse || pathEdges.has(`${edge.from}|${edge.to}`) ? "3" : "2"}
                        strokeDasharray="4 4"
                    />
                );
              })()}
                </React.Fragment>
                ))}
            </svg>

            {/* Custom Nodal Shapes */}
            {nodes.map((node) => {
                const widthPx = (node.w || 10) * SCALE;
                const heightPx = (node.h || 10) * SCALE;
                const baseClass = typeStyles[node.type] || typeStyles.machine;
                const isPathNode = pathNodes.has(node.id);
                const partCount = nodePartCounts.get(node.id) || 0;
                const nodeInUse = partCount > 0 || node.active_jobs > 0;
                
                // Dim nodes that are offline or error
                const opacityAttr = (node.status === "Offline" || node.status === "Blocked" || node.status === "Disconnected")
                  ? "opacity-50 grayscale"
                  : "opacity-100";
                  
                const isBottleneck = bottleneckNode && node.id === bottleneckNode;
                const bottleneckClass = isBottleneck ? "ring-4 ring-red-500/80 shadow-[0_0_35px_rgba(239,68,68,0.9)] animate-pulse z-40 scale-110" : "";

                return (
                    <div
                        key={node.id}
                        className={`absolute -translate-x-1/2 -translate-y-1/2 flex items-center justify-center transition-all duration-300 ${opacityAttr} ${isBottleneck ? "z-40" : "z-10"}`}
                        style={{ 
                            left: `${node.x}%`, 
                            top: `${node.y}%`, 
                            width: `${widthPx}px`, 
                            height: `${heightPx}px`,
                            transform: `translate(-50%, -50%) rotate(${node.rot || 0}deg)`
                        }}
                        title={`${node.label} (${node.status})`}
                    >
                        <div
                          className={`w-full h-full ${baseClass} ${bottleneckClass} ${isPathNode ? "ring-2 ring-blue-200/70" : ""} ${nodeInUse ? "ring-4 ring-emerald-300/90 shadow-[0_0_35px_rgba(16,185,129,0.8)] brightness-125" : ""}`}
                        >
                            {/* Counter-rotate label so text remains horizontally legible if conveyor is tilted */}
                            <span 
                                className="block text-center whitespace-pre-wrap leading-tight text-[11px]" 
                                style={{ transform: `rotate(${-(node.rot || 0)}deg)` }}
                            >
                                {node.label}
                            </span>
                        </div>

                        {/* Compact parts-count indicator above active nodes */}
                        {partCount > 0 && (
                          <div className="absolute left-1/2 -translate-x-1/2 -top-3 flex h-5 min-w-5 items-center justify-center rounded-full bg-emerald-500 text-[10px] font-bold text-white shadow-[0_0_8px_rgba(16,185,129,0.7)] border border-emerald-200">
                            {partCount}
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
