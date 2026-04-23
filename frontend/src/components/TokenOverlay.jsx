import React, { useMemo } from "react";

/**
 * Renders animated WIP tokens on the schematic overlay.
 * Maps DES engine station IDs to the actual mock_telemetry node coordinates.
 */

// Map DES station IDs to the actual schematic node coordinates (from mock_telemetry.py)
const STATION_TO_SCHEMATIC = {
  // DES Engine stations -> schematic node positions
  R0:    { x: 5,  y: 50,  label: "R0" },      // r0 robot
  M1:    { x: 20, y: 8,   label: "CNC" },      // cncm machine
  M2:    { x: 34, y: 85,  label: "Laser" },     // lz machine
  M3:    { x: 48, y: 8,   label: "Lathe" },     // cncl machine
  R1:    { x: 64, y: 55,  label: "R6" },        // r6 robot (outfeed merge)
  // Mock engine node IDs (direct mapping)
  ir:       { x: 10, y: 65 },
  r0:       { x: 5,  y: 50 },
  r1:       { x: 14, y: 65 },
  c0:       { x: 12, y: 38 },
  c1:       { x: 24, y: 65 },
  r2:       { x: 20, y: 28 },
  inv_cncm: { x: 20, y: 18 },
  cncm:     { x: 20, y: 8 },
  c2:       { x: 27, y: 46 },
  c4:       { x: 34, y: 28 },
  r3:       { x: 34, y: 65 },
  inv_lz:   { x: 34, y: 75 },
  lz:       { x: 34, y: 85 },
  c3:       { x: 41, y: 46 },
  c5:       { x: 50, y: 60 },
  r4:       { x: 48, y: 28 },
  inv_cncl: { x: 48, y: 18 },
  cncl:     { x: 48, y: 8 },
  c6:       { x: 56, y: 28 },
  c7:       { x: 56, y: 41 },
  r5:       { x: 64, y: 28 },
  r6:       { x: 64, y: 55 },
  inv_qia:  { x: 64, y: 18 },
  qia:      { x: 64, y: 8 },
  c10:      { x: 75, y: 60 },
  inv_qib:  { x: 64, y: 65 },
  qib:      { x: 64, y: 75 },
  c8:       { x: 75, y: 22 },
  c9:       { x: 75, y: 42 },
  inv_oba:  { x: 84, y: 22 },
  oba:      { x: 92, y: 22 },
  inv_obb:  { x: 84, y: 60 },
  obb:      { x: 92, y: 60 },
  inv_tra:  { x: 84, y: 42 },
  tra:      { x: 92, y: 42 },
  queue:    { x: 3,  y: 65 },
};

const PRODUCT_COLORS = {
  Gasket_A:  { bg: "bg-emerald-500", ring: "ring-emerald-300", text: "G" },
  Shaft_B:   { bg: "bg-amber-500",   ring: "ring-amber-300",   text: "S" },
  Housing_C: { bg: "bg-sky-500",     ring: "ring-sky-300",     text: "H" },
  Bracket_D: { bg: "bg-fuchsia-500", ring: "ring-fuchsia-300", text: "B" },
  gasket:    { bg: "bg-emerald-500", ring: "ring-emerald-300", text: "G" },
  shaft:     { bg: "bg-amber-500",   ring: "ring-amber-300",   text: "S" },
  housing:   { bg: "bg-sky-500",     ring: "ring-sky-300",     text: "H" },
  bracket:   { bg: "bg-fuchsia-500", ring: "ring-fuchsia-300", text: "B" },
};

export default function TokenOverlay({ tokens, schematicNodes }) {
  const nodePositions = useMemo(() => {
    const map = { ...STATION_TO_SCHEMATIC };
    if (schematicNodes) {
      for (const node of schematicNodes) {
        map[node.id] = { x: node.x, y: node.y };
      }
    }
    return map;
  }, [schematicNodes]);

  const groupedTokens = useMemo(() => {
    if (!tokens || tokens.length === 0) return [];

    const groups = {};
    for (const token of tokens) {
      if (token.status === "completed") continue;
      const station = token.current_station || token.current_node || "queue";
      if (!groups[station]) groups[station] = [];
      groups[station].push(token);
    }

    const positioned = [];
    for (const [station, stationTokens] of Object.entries(groups)) {
      const base = nodePositions[station] || { x: 50, y: 95 };
      stationTokens.forEach((token, idx) => {
        const col = idx % 3;
        const row = Math.floor(idx / 3);
        positioned.push({
          ...token,
          renderX: base.x + (col - 1) * 2.2,
          renderY: base.y - 6 - row * 3,
        });
      });
    }
    return positioned;
  }, [tokens, nodePositions]);

  if (groupedTokens.length === 0) return null;

  return (
    <>
      {groupedTokens.map((token) => {
        const prod = token.product || token.part_family || "";
        const colors = PRODUCT_COLORS[prod] || { bg: "bg-slate-500", ring: "ring-slate-300", text: "?" };
        const isProcessing = token.status === "processing" || token.status === "Busy";

        return (
          <div
            key={token.job_id}
            className="absolute z-50 flex flex-col items-center transition-all duration-700 ease-in-out"
            style={{
              left: `${token.renderX}%`,
              top: `${token.renderY}%`,
              transform: "translate(-50%, -50%)",
            }}
            title={`${token.job_id} (${prod}) — ${token.status} at ${token.current_station || token.current_node}`}
          >
            <div
              className={`
                w-5 h-5 rounded-full ${colors.bg} ring-2 ${colors.ring}
                flex items-center justify-center text-[8px] font-bold text-white
                shadow-[0_0_10px_rgba(255,255,255,0.25)]
                ${isProcessing ? "animate-pulse scale-110" : ""}
              `}
            >
              {colors.text}
            </div>
            <span className="text-[7px] font-mono text-slate-400 whitespace-nowrap mt-0.5 leading-none">
              {(token.job_id || "").replace("Job_", "#").replace("WO-", "#")}
            </span>
          </div>
        );
      })}
    </>
  );
}
