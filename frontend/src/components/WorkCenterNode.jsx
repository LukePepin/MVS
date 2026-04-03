import React from "react";
import StatusBadge from "./StatusBadge";

const NODE_RING = {
  Idle: "border-slate-700/60 bg-slate-900/40",
  Busy: "border-blue-500/50 bg-blue-900/20 shadow-[0_0_15px_rgba(59,130,246,0.15)]",
  Blocked: "border-amber-500/50 bg-amber-900/20 shadow-[0_0_15px_rgba(245,158,11,0.1)]",
  Offline: "border-red-500/50 bg-red-900/20 shadow-[0_0_15px_rgba(239,68,68,0.1)]",
};

const WorkCenterNode = ({ label, status, activeJobs, queueDepth, subtitle }) => {
  const ring = NODE_RING[status] || NODE_RING.Idle;

  return (
    <div className={`relative flex flex-col justify-center min-h-[70px] rounded-md border backdrop-blur-sm p-2 transition-all duration-300 ${ring}`}>
      <div className="flex items-center justify-between gap-1 mb-1.5">
        <h4 className="text-[11px] font-semibold text-slate-100 leading-tight truncate max-w-[90px]" title={label}>{label}</h4>
        <StatusBadge status={status} />
      </div>
      <div className="flex items-center gap-1 text-[10px] text-slate-300">
        <span className="rounded bg-black/50 px-1.5 py-0.5 border border-white/5">A: {activeJobs}</span>
        <span className="rounded bg-black/50 px-1.5 py-0.5 border border-white/5">Q: {queueDepth}</span>
      </div>
      {activeJobs > 0 && (
        <div className="absolute -right-1.5 -top-1.5 flex h-4 min-w-4 items-center justify-center rounded-full bg-blue-500 text-[9px] font-bold text-white shadow-[0_0_8px_rgba(59,130,246,0.5)] animate-pulse">
          {activeJobs}
        </div>
      )}
    </div>
  );
};

export default WorkCenterNode;
