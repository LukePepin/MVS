import React from "react";

export default function EventsLog({ events }) {
  if (!events || events.length === 0) {
    return (
      <div className="rounded-xl glass-panel p-5 border border-white/10 shadow-lg">
        <h3 className="mb-4 text-base font-semibold text-white tracking-wide border-b border-white/10 pb-2">
          Events Log (Live)
        </h3>
        <div className="text-center py-8 text-slate-500 text-sm">No events yet — start a simulation.</div>
      </div>
    );
  }

  const typeColor = {
    INFO: "text-blue-300 bg-blue-500/10",
    SUCCESS: "text-green-300 bg-green-500/10",
    WARNING: "text-yellow-300 bg-yellow-500/10",
    ALARM: "text-red-300 bg-red-500/10",
  };

  return (
    <div className="rounded-xl glass-panel p-5 border border-white/10 shadow-lg">
      <h3 className="mb-4 text-base font-semibold text-white tracking-wide border-b border-white/10 pb-2">
        Events Log — {events.length} events
      </h3>
      <div className="overflow-y-auto max-h-80 custom-scrollbar rounded-lg border border-white/5 bg-black/20">
        <table className="min-w-full divide-y divide-white/5 text-xs font-mono">
          <thead className="bg-white/5 sticky top-0 backdrop-blur-sm">
            <tr>
              <th className="px-3 py-2 text-left text-[10px] font-semibold tracking-wide text-slate-400">T (min)</th>
              <th className="px-3 py-2 text-left text-[10px] font-semibold tracking-wide text-slate-400">Type</th>
              <th className="px-3 py-2 text-left text-[10px] font-semibold tracking-wide text-slate-400">Message</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-white/5">
            {[...events].reverse().map((ev, i) => (
              <tr key={i} className="hover:bg-white/5 transition-colors">
                <td className="px-3 py-1.5 text-slate-400 whitespace-nowrap">{ev.time}</td>
                <td className="px-3 py-1.5 whitespace-nowrap">
                  <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${typeColor[ev.type] || "text-slate-300"}`}>
                    {ev.type}
                  </span>
                </td>
                <td className="px-3 py-1.5 text-slate-300">{ev.message}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
