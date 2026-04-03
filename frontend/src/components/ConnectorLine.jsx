import React from "react";

const ConnectorLine = ({ active = false }) => {
  return (
    <div className="relative h-0.5 w-14 bg-blue-900/50">
      <div className={`absolute inset-0 ${active ? "bg-blue-300/80" : "bg-blue-900/40"}`} />
      {active ? <span className="connector-dot" /> : null}
    </div>
  );
};

export default ConnectorLine;
