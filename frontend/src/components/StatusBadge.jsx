import React from "react";

const STATUS_STYLES = {
  Idle: "bg-slate-800/80 text-slate-400 border-slate-700/50",
  Busy: "bg-blue-500/20 text-blue-300 border-blue-500/30",
  Blocked: "bg-amber-500/20 text-amber-300 border-amber-500/30",
  Offline: "bg-red-500/20 text-red-300 border-red-500/30",
};

const StatusBadge = ({ status }) => {
  const style = STATUS_STYLES[status] || STATUS_STYLES.Idle;

  return (
    <span
      className={`inline-flex items-center rounded border px-1 py-[1px] text-[9px] font-bold uppercase tracking-wider backdrop-blur-md ${style}`}
    >
      {status}
    </span>
  );
};

export default StatusBadge;
