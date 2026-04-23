import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter, Routes, Route, NavLink, Navigate } from "react-router-dom";
import Dashboard from "./dashboard";
import AnalyticsPage from "./pages/AnalyticsPage";
import "./index.css";

function NavBar() {
  const linkBase = "px-3 py-2 rounded-lg text-sm font-semibold transition-colors";
  const activeClass = "bg-blue-500/20 text-blue-200 ring-1 ring-blue-500/50";
  const inactiveClass = "text-slate-400 hover:text-white hover:bg-white/5";

  return (
    <nav className="sticky top-0 z-50 backdrop-blur-xl bg-slate-950/80 border-b border-white/10 px-4 py-2">
      <div className="mx-auto max-w-[1920px] flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-lg font-bold text-white tracking-tight">MVS</span>
          <span className="text-xs text-slate-500 font-medium hidden md:inline">Expeditionary MES</span>
        </div>
        <div className="flex gap-1">
          <NavLink to="/factory" className={({ isActive }) => `${linkBase} ${isActive ? activeClass : inactiveClass}`}>
            Factory
          </NavLink>
          <NavLink to="/analytics" className={({ isActive }) => `${linkBase} ${isActive ? activeClass : inactiveClass}`}>
            Analytics
          </NavLink>
        </div>
      </div>
    </nav>
  );
}

function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-slate-950 bg-[radial-gradient(ellipse_80%_80%_at_50%_-20%,rgba(30,58,138,0.25),rgba(255,255,255,0))] text-slate-100 font-inter">
        <NavBar />
        <main className="px-2 py-4 md:px-3 lg:px-4">
          <div className="mx-auto max-w-[1920px]">
            <Routes>
              <Route path="/" element={<Navigate to="/factory" replace />} />
              <Route path="/factory" element={<Dashboard />} />
              <Route path="/analytics" element={<AnalyticsPage />} />
              <Route path="/settings" element={<Navigate to="/factory" replace />} />
            </Routes>
          </div>
        </main>
      </div>
    </BrowserRouter>
  );
}

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
