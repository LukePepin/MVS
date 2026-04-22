import React, { useEffect, useState } from "react";

export default function TraceabilityTab() {
  const [events, setEvents] = useState([]);

  useEffect(() => {
    const fetchGen = async () => {
      try {
        const res = await fetch("http://localhost:8000/analytics/genealogy");
        const data = await res.json();
        setEvents(data);
      } catch (e) {
        console.error(e);
      }
    };
    fetchGen();
    const iv = setInterval(fetchGen, 2000);
    return () => clearInterval(iv);
  }, []);

  return (
    <div className="rounded-xl glass-panel p-5 mt-6 border border-white/10 shadow-lg">
      <h3 className="mb-4 text-base font-semibold text-white tracking-wide border-b border-white/10 pb-2">Genealogy Trace (F10 - Product Tracking)</h3>
      <p className="text-xs text-slate-400 mb-4">Tracking individual unit movement across nodes mimicking the backward/forward trace logic.</p>
      
      <div className="overflow-x-auto rounded-lg border border-white/5 bg-black/20 max-h-96 overflow-y-auto custom-scrollbar">
        <table className="min-w-full divide-y divide-white/5 text-sm">
          <thead className="bg-white/5 sticky top-0 backdrop-blur-sm">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-semibold tracking-wide text-slate-300">Timestamp</th>
              <th className="px-4 py-3 text-left text-xs font-semibold tracking-wide text-slate-300">Serial ID (Lot)</th>
              <th className="px-4 py-3 text-left text-xs font-semibold tracking-wide text-slate-300">Station Point</th>
              <th className="px-4 py-3 text-left text-xs font-semibold tracking-wide text-slate-300">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-white/5 text-slate-300">
            {events.length === 0 && <tr><td colSpan="4" className="text-center py-6 text-slate-500">No events tracked yet.</td></tr>}
            {events.map((ev, i) => (
              <tr key={ev.event_id || i} className="hover:bg-white/5 transition-colors">
                <td className="px-4 py-2.5 whitespace-nowrap text-xs font-mono text-slate-400">{new Date(ev.timestamp).toISOString().substring(11, 23)}</td>
                <td className="px-4 py-2.5 font-medium text-blue-300">{ev.serial_id}</td>
                <td className="px-4 py-2.5 font-mono">{ev.station_point}</td>
                <td className="px-4 py-2.5 text-xs">
                    <span className={`px-2 py-0.5 rounded-full ${ev.status === 'Completed' ? 'bg-green-500/20 text-green-300' : ev.status === 'Entered' ? 'bg-blue-500/20 text-blue-300' : 'bg-orange-500/20 text-orange-300'}`}>
                        {ev.status}
                    </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
