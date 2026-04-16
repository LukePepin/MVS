"""
des_tkinter.py
==============
ISE 573 -- Manufacturing Execution Systems
Week 9: Consequences of Breakdowns -- Interactive Serial Line DES

ZERO DEPENDENCIES -- uses only Python standard library.

RUN
---
    python des_tkinter.py

Dr. Manbir Sodhi - University of Rhode Island - Spring 2026
"""

import heapq
import math
import random
import statistics
import threading
import tkinter as tk
from tkinter import ttk, font as tkfont

# ══════════════════════════════════════════════════════════════════════════
#  DES engine
# ══════════════════════════════════════════════════════════════════════════

ARR, SVC, BRK, REP = "ARR", "SVC", "BRK", "REP"
UP,  DOWN           = "UP",  "DOWN"


def gamma_sample(mean: float, cv2: float, rng: random.Random) -> float:
    if cv2 < 1e-9:
        return mean
    return rng.gammavariate(1.0 / cv2, mean * cv2)


def sq_cv(data: list) -> float:
    if len(data) < 2:
        return float("nan")
    m = statistics.mean(data)
    return statistics.variance(data) / (m * m) if m > 0 else float("nan")


def run_serial_des(n_stn, lam, mu, Ca2, Cs2_nom,
                   brk_stn, mtbf, mttr, n_jobs, seed):
    rng    = random.Random(seed)
    warmup = max(n_jobs // 5, 200)

    state   = [UP]    * n_stn
    busy    = [False] * n_stn
    cur_arr = [None]  * n_stn
    cur_svc = [None]  * n_stn
    queues  = [[] for _ in range(n_stn)]

    waits    = [[] for _ in range(n_stn)]
    ideps    = [[] for _ in range(n_stn)]
    last_dep = [None] * n_stn
    bk_tot   = [0.0]  * n_stn
    bk_st    = [None] * n_stn
    bk_cnt   = [0]    * n_stn
    done     = [0]    * n_stn

    cal   = []
    seq   = 0
    clock = 0.0

    def push(t, et, si):
        nonlocal seq
        heapq.heappush(cal, (t, seq, et, si))
        seq += 1

    def try_start(i):
        if busy[i] or state[i] == DOWN or not queues[i]:
            return
        cur_arr[i] = queues[i].pop(0)
        cur_svc[i] = clock
        busy[i]    = True
        push(clock + gamma_sample(1.0 / mu, Cs2_nom, rng), SVC, i)

    push(gamma_sample(1.0 / lam, Ca2, rng), ARR, 0)
    if 0 <= brk_stn < n_stn and mtbf > 0 and mttr > 0:
        push(gamma_sample(mtbf, 1.0, rng), BRK, brk_stn)

    exits    = 0
    max_evts = n_jobs * n_stn * 500
    ev_count = 0

    while exits < n_jobs and cal and ev_count < max_evts:
        t, _, et, si = heapq.heappop(cal)
        clock = t
        ev_count += 1

        if et == ARR:
            push(clock + gamma_sample(1.0 / lam, Ca2, rng), ARR, 0)
            queues[0].append(clock)
            try_start(0)

        elif et == SVC:
            if not busy[si]:
                continue
            arr_t = cur_arr[si]
            svc_s = cur_svc[si]
            busy[si] = False; cur_arr[si] = None; cur_svc[si] = None
            if last_dep[si] is not None:
                ideps[si].append(clock - last_dep[si])
            last_dep[si] = clock
            done[si] += 1
            if done[si] > warmup:
                waits[si].append(svc_s - arr_t)
            if si < n_stn - 1:
                queues[si + 1].append(clock)
                try_start(si + 1)
            else:
                if done[si] > warmup:
                    exits += 1
            try_start(si)

        elif et == BRK:
            if state[si] == DOWN:
                continue
            state[si] = DOWN; bk_cnt[si] += 1; bk_st[si] = clock
            if busy[si]:
                queues[si].insert(0, cur_arr[si])
                busy[si] = False; cur_arr[si] = None; cur_svc[si] = None
            push(clock + gamma_sample(mttr, 1.0, rng), REP, si)

        elif et == REP:
            if state[si] == UP:
                continue
            state[si] = UP
            if bk_st[si] is not None:
                bk_tot[si] += clock - bk_st[si]; bk_st[si] = None
            push(clock + gamma_sample(mtbf, 1.0, rng), BRK, si)
            try_start(si)

    Ca2_arr = [Ca2] + [sq_cv(ideps[i]) for i in range(n_stn - 1)]
    return {
        "n_collected":   [len(waits[i])  for i in range(n_stn)],
        "Wq_sim":        [statistics.mean(waits[i]) if waits[i] else float("nan")
                          for i in range(n_stn)],
        "A_sim":         [(1.0 - bk_tot[i] / clock) if clock > 0 else 1.0
                          for i in range(n_stn)],
        "Ca2_arriving":  Ca2_arr,
        "Cd2_dep":       [sq_cv(ideps[i]) for i in range(n_stn)],
        "bk_count":      bk_cnt,
        "sim_time":      clock,
        "hit_limit":     ev_count >= max_evts,
        "warmup":        warmup,
    }


# ══════════════════════════════════════════════════════════════════════════
#  Analytics
# ══════════════════════════════════════════════════════════════════════════

def kingman_wq(lam, mu, Ca2, Cs2):
    rho = lam / mu
    return float("inf") if rho >= 1.0 else (rho / (1 - rho)) * ((Ca2 + Cs2) / 2) / mu


def station_analytics(mu, lam, mtbf, mttr, Cs2_nom, Ca2_in):
    tp = 1.0 / mu
    if mtbf and mttr and mtbf > 0 and mttr > 0:
        A      = mtbf / (mtbf + mttr)
        mu_eff = mu * A
        Cs2_eff = Cs2_nom + A * (1 - A) * (mttr / tp) ** 2
    else:
        A, mu_eff, Cs2_eff = 1.0, mu, Cs2_nom
    rho_eff = min(lam / mu_eff, 0.9999) if mu_eff > 0 else 0.9999
    Wq_pred = kingman_wq(lam, mu_eff, Ca2_in, Cs2_eff)
    Cd2     = (1 - rho_eff**2) * Ca2_in + rho_eff**2 * Cs2_eff
    return dict(A=A, mu_eff=mu_eff, rho_eff=rho_eff,
                Cs2_eff=Cs2_eff, Wq_pred=Wq_pred, Cd2=Cd2)


def buffer_sizing(lam, mttr):
    if not mttr or mttr <= 0:
        return None
    B_min  = math.ceil(lam * mttr)
    B_star = B_min + math.ceil(1.65 * math.sqrt(max(B_min, 1)))
    return B_min, B_star


def make_observations(sim, n_stn, lam, mu, Ca2, Cs2_nom, brk_stn, mtbf, mttr):
    obs = []
    Ca2_chain = Ca2
    for i in range(n_stn):
        is_brk = (i == brk_stn)
        an = station_analytics(mu, lam,
                               mtbf if is_brk else 0,
                               mttr if is_brk else 0,
                               Cs2_nom, Ca2_chain)
        if an["rho_eff"] > 0.93:
            obs.append(("warn",
                f"Stn {i+1}: rho_eff = {an['rho_eff']:.3f} — past the knee. "
                f"Small further lambda increase causes disproportionate Wq growth."))
        if is_brk and an["Cs2_eff"] > 2.0 * Cs2_nom:
            pct = round((an["Cs2_eff"] - Cs2_nom) / an["Cs2_eff"] * 100)
            obs.append(("info",
                f"Stn {i+1}: Cs2_eff = {an['Cs2_eff']:.2f} vs Cs2_nom = {Cs2_nom:.2f}. "
                f"Breakdowns account for {pct}% of variability. "
                f"Reducing MTTR beats tightening process precision."))
        if is_brk and i < n_stn - 1:
            Ca2_dn = sim["Ca2_arriving"][i + 1]
            if not math.isnan(Ca2_dn) and Ca2_dn > Ca2 * 1.15:
                an_dn = station_analytics(mu, lam, 0, 0, Cs2_nom, an["Cd2"])
                Wq_base = kingman_wq(lam, mu, Ca2, Cs2_nom) * 60
                obs.append(("info",
                    f"Ca2 cascade: Stn {i+2} sees Ca2_arriving = {Ca2_dn:.3f} "
                    f"(original: {Ca2:.2f}). Kingman Wq = {an_dn['Wq_pred']*60:.1f} min "
                    f"vs baseline {Wq_base:.1f} min. Stn {i+2} never broke."))
        if is_brk and i < n_stn - 1 and mttr > 0:
            B_min, B_star = buffer_sizing(lam, mttr)
            dr = mu - lam
            Lq = lam * an["Wq_pred"]
            t_d = Lq / dr if dr > 0 else float("inf")
            obs.append(("action",
                f"Buffer: place B* = {B_star} jobs between Stn {i+1} and Stn {i+2} "
                f"(B_min = {B_min} = ceil(lambda x MTTR)). "
                f"Burst drains in ~{t_d:.1f} hr at mu-lambda = {dr:.1f} jobs/hr."))
        if an["rho_eff"] >= 0.9999:
            obs.append(("error",
                f"Stn {i+1}: UNSTABLE — rho_eff >= 1. "
                f"Reduce lambda, increase mu, or improve MTBF."))
        Ca2_chain = an["Cd2"]

    if sim.get("hit_limit"):
        obs.append(("warn", "Hit event limit — system near-unstable."))
    if not obs:
        obs.append(("ok",
            "System stable. Try: enable breakdown at Stn 1, then "
            "observe Wq rise at downstream stations (Ca2 cascade)."))
    return obs


# ══════════════════════════════════════════════════════════════════════════
#  Colour palette
# ══════════════════════════════════════════════════════════════════════════

BG        = "#1e2d3d"   # dark navy  (window background)
PANEL_BG  = "#243447"   # slightly lighter (left panel)
CARD_BG   = "#f8fafc"   # near-white (right panel cards)
ACCENT    = "#3b82f6"   # blue
RED       = "#dc2626"
ORANGE    = "#d97706"
GREEN     = "#16a34a"
TEXT_DARK = "#1f2937"
TEXT_LITE = "#e2e8f0"
TEXT_MID  = "#94a3b8"
WARN_BG   = "#fffbeb"
INFO_BG   = "#eff6ff"
ERR_BG    = "#fef2f2"
OK_BG     = "#f0fdf4"
BRK_ROW   = "#fef2f2"
NRM_ROW   = "#ffffff"
HDR_BG    = "#1e3a5f"


# ══════════════════════════════════════════════════════════════════════════
#  Labeled slider widget
# ══════════════════════════════════════════════════════════════════════════

class LabeledSlider(tk.Frame):
    def __init__(self, parent, label, from_, to, resolution, initial,
                 fmt=None, command=None, **kw):
        super().__init__(parent, bg=PANEL_BG, **kw)
        self._fmt = fmt or (lambda v: f"{v:.2f}")
        self._cmd = command

        top = tk.Frame(self, bg=PANEL_BG)
        top.pack(fill="x")
        tk.Label(top, text=label, bg=PANEL_BG, fg=TEXT_LITE,
                 font=("Helvetica", 10)).pack(side="left")
        self._val_lbl = tk.Label(top, text=self._fmt(initial),
                                  bg=PANEL_BG, fg=ACCENT,
                                  font=("Helvetica", 10, "bold"))
        self._val_lbl.pack(side="right")

        self.var = tk.DoubleVar(value=initial)
        self.var.trace_add("write", self._on_change)
        self._slider = ttk.Scale(self, from_=from_, to=to,
                                  variable=self.var, orient="horizontal")
        self._slider.pack(fill="x", pady=(0, 4))
        self._res = resolution

    def _on_change(self, *_):
        raw = self.var.get()
        snapped = round(round(raw / self._res) * self._res, 10)
        self._val_lbl.config(text=self._fmt(snapped))
        if self._cmd:
            self._cmd(snapped)

    def get(self):
        raw = self.var.get()
        return round(round(raw / self._res) * self._res, 10)

    def set(self, v):
        self.var.set(v)


# ══════════════════════════════════════════════════════════════════════════
#  Section label helper
# ══════════════════════════════════════════════════════════════════════════

def section_label(parent, text):
    f = tk.Frame(parent, bg=PANEL_BG)
    f.pack(fill="x", pady=(10, 2))
    tk.Label(f, text=text.upper(), bg=PANEL_BG, fg=TEXT_MID,
             font=("Helvetica", 8, "bold")).pack(side="left")
    tk.Frame(f, bg=TEXT_MID, height=1).pack(side="left", fill="x",
                                             expand=True, padx=(6, 0))


# ══════════════════════════════════════════════════════════════════════════
#  Main application
# ══════════════════════════════════════════════════════════════════════════

class App(tk.Tk):
    # -- column definitions for the results treeview ----------------------
    ALWAYS_COLS = [
        ("station",  "Station",       70),
        ("role",     "Role",          90),
        ("wq_sim",   "Wq sim (min)",  90),
        ("a_sim",    "A (sim)",       75),
        ("rho_eff",  "rho_eff",       75),
        ("samples",  "Samples",       70),
        ("bk_count", "Breakdowns",    80),
    ]
    OPT_COLS = [
        ("kingman",  "Wq King (min)", 95),
        ("ca2",      "Ca2 arriving",  90),
        ("cd2",      "Cd2 depart",    90),
        ("cs2eff",   "Cs2_eff",       75),
        ("bstar",    "B_min / B*",    85),
        ("baseline", "Wq base (min)", 95),
    ]

    def __init__(self):
        super().__init__()
        self.title("ISE 573 — Serial Line Breakdown DES")
        self.configure(bg=BG)
        self.resizable(True, True)

        # -- ttk style ----------------------------------------------------
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TScale",    troughcolor=TEXT_MID, background=PANEL_BG)
        style.configure("Run.TButton",
                        background=ACCENT, foreground="white",
                        font=("Helvetica", 12, "bold"), padding=8)
        style.map("Run.TButton",
                  background=[("active", "#2563eb"), ("disabled", "#64748b")])
        style.configure("Treeview",
                        background=NRM_ROW, fieldbackground=NRM_ROW,
                        foreground=TEXT_DARK, rowheight=22,
                        font=("Courier", 10))
        style.configure("Treeview.Heading",
                        background=HDR_BG, foreground="white",
                        font=("Helvetica", 9, "bold"))
        style.map("Treeview", background=[("selected", "#bfdbfe")])

        self._build_ui()
        self._update_rho_label()

    # ── UI construction ──────────────────────────────────────────────────

    def _build_ui(self):
        # Top banner
        banner = tk.Frame(self, bg="#0f2850", pady=8)
        banner.pack(fill="x")
        tk.Label(banner,
                 text="ISE 573  —  Serial Line Breakdown DES",
                 bg="#0f2850", fg="white",
                 font=("Helvetica", 14, "bold")).pack(side="left", padx=14)
        tk.Label(banner,
                 text="URI · Dr. Manbir Sodhi · Spring 2026",
                 bg="#0f2850", fg=TEXT_MID,
                 font=("Helvetica", 9)).pack(side="right", padx=14)

        # Main pane: left (controls) + right (results)
        main = tk.Frame(self, bg=BG)
        main.pack(fill="both", expand=True, padx=8, pady=8)

        left  = tk.Frame(main, bg=PANEL_BG, width=270)
        left.pack(side="left", fill="y", padx=(0, 8))
        left.pack_propagate(False)

        right = tk.Frame(main, bg=CARD_BG)
        right.pack(side="left", fill="both", expand=True)

        self._build_left(left)
        self._build_right(right)
        # Both panels now exist -- safe to initialise state
        self._update_rho_label()
        self._update_breakdown_vis()
        self._draw_diagram()

    def _build_left(self, parent):
        # Scrollable left panel
        canvas = tk.Canvas(parent, bg=PANEL_BG, highlightthickness=0)
        sb = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        inner = tk.Frame(canvas, bg=PANEL_BG, padx=12)
        win   = canvas.create_window((0, 0), window=inner, anchor="nw")

        def _resize(e):
            canvas.configure(scrollregion=canvas.bbox("all"))
            canvas.itemconfig(win, width=canvas.winfo_width())
        inner.bind("<Configure>", _resize)
        canvas.bind("<MouseWheel>",
                    lambda e: canvas.yview_scroll(-1*(e.delta//120), "units"))

        self._build_controls(inner)

    def _build_controls(self, p):
        # ── System ───────────────────────────────────────────────────────
        section_label(p, "System")

        # n_stations
        nf = tk.Frame(p, bg=PANEL_BG)
        nf.pack(fill="x", pady=2)
        tk.Label(nf, text="Stations  n", bg=PANEL_BG, fg=TEXT_LITE,
                 font=("Helvetica", 10)).pack(side="left")
        self._n_var = tk.IntVar(value=3)
        for v in (2, 3, 4, 5):
            tk.Radiobutton(nf, text=str(v), variable=self._n_var, value=v,
                           bg=PANEL_BG, fg=TEXT_LITE, selectcolor=PANEL_BG,
                           activebackground=PANEL_BG,
                           command=self._on_n_change).pack(side="left", padx=4)

        self._sl_lam = LabeledSlider(p, "λ  arrival rate (jobs/hr)",
                                      1.0, 14.0, 0.5, 8.0,
                                      fmt=lambda v: f"{v:.1f}",
                                      command=lambda _: self._update_rho_label())
        self._sl_lam.pack(fill="x", pady=2)
        self._sl_mu = LabeledSlider(p, "μ  service rate (jobs/hr)",
                                     5.0, 20.0, 0.5, 10.0,
                                     fmt=lambda v: f"{v:.1f}",
                                     command=lambda _: self._update_rho_label())
        self._sl_mu.pack(fill="x", pady=2)

        self._rho_lbl = tk.Label(p, text="", bg=PANEL_BG,
                                  font=("Helvetica", 10, "bold"), anchor="w")
        self._rho_lbl.pack(fill="x", pady=(0, 4))

        # ── Variability ───────────────────────────────────────────────────
        section_label(p, "Variability")
        self._sl_ca2 = LabeledSlider(p, "Ca²  inter-arrivals",
                                      0.1, 3.0, 0.1, 1.0, fmt=lambda v: f"{v:.1f}")
        self._sl_ca2.pack(fill="x", pady=2)
        self._sl_cs2 = LabeledSlider(p, "Cs²  service (nominal)",
                                      0.1, 3.0, 0.1, 1.0, fmt=lambda v: f"{v:.1f}")
        self._sl_cs2.pack(fill="x", pady=2)
        tk.Label(p, text="0=deterministic · 1=exponential · >1=heavy tail",
                 bg=PANEL_BG, fg=TEXT_MID, font=("Helvetica", 8)).pack(anchor="w")

        # ── Breakdown ─────────────────────────────────────────────────────
        section_label(p, "Breakdown")
        bf = tk.Frame(p, bg=PANEL_BG)
        bf.pack(fill="x", pady=2)
        tk.Label(bf, text="Which station breaks?", bg=PANEL_BG, fg=TEXT_LITE,
                 font=("Helvetica", 10)).pack(side="left")
        self._brk_var = tk.StringVar(value="Station 1")
        self._brk_menu = ttk.Combobox(bf, textvariable=self._brk_var,
                                       state="readonly", width=12)
        self._brk_menu.pack(side="right")
        self._brk_menu.bind("<<ComboboxSelected>>",
                             lambda _: self._update_breakdown_vis())

        self._brk_frame = tk.Frame(p, bg=PANEL_BG)
        self._brk_frame.pack(fill="x")

        self._sl_mtbf = LabeledSlider(self._brk_frame, "MTBF (hr)",
                                       0.5, 20.0, 0.5, 3.0, fmt=lambda v: f"{v:.1f}",
                                       command=lambda _: self._refresh_brk_info())
        self._sl_mtbf.pack(fill="x", pady=2)
        self._sl_mttr = LabeledSlider(self._brk_frame, "MTTR (hr)",
                                       0.1,  5.0, 0.1, 0.5, fmt=lambda v: f"{v:.2f}",
                                       command=lambda _: self._refresh_brk_info())
        self._sl_mttr.pack(fill="x", pady=2)

        self._brk_info = tk.Label(self._brk_frame, text="",
                                   bg=PANEL_BG, fg="#fde68a",
                                   font=("Courier", 9), justify="left", anchor="w",
                                   wraplength=230)
        self._brk_info.pack(fill="x", pady=(0, 4))
        self._refresh_brk_info()

        # Now safe to call: _brk_frame exists
        self._update_brk_options()

        # ── Simulation ────────────────────────────────────────────────────
        section_label(p, "Simulation")
        jf = tk.Frame(p, bg=PANEL_BG)
        jf.pack(fill="x", pady=2)
        tk.Label(jf, text="Jobs (post warm-up)", bg=PANEL_BG, fg=TEXT_LITE,
                 font=("Helvetica", 10)).pack(side="left")
        self._jobs_var = tk.IntVar(value=2000)
        self._jobs_lbl = tk.Label(jf, text="2,000", bg=PANEL_BG, fg=ACCENT,
                                   font=("Helvetica", 10, "bold"))
        self._jobs_lbl.pack(side="right")
        jobs_sl = ttk.Scale(p, from_=500, to=5000, variable=self._jobs_var,
                             orient="horizontal")
        jobs_sl.pack(fill="x")
        self._jobs_var.trace_add("write", lambda *_: self._jobs_lbl.config(
            text=f"{int(round(self._jobs_var.get() / 500) * 500):,}"))

        sf = tk.Frame(p, bg=PANEL_BG)
        sf.pack(fill="x", pady=(6, 2))
        tk.Label(sf, text="Random seed", bg=PANEL_BG, fg=TEXT_LITE,
                 font=("Helvetica", 10)).pack(side="left")
        self._seed_var = tk.IntVar(value=42)
        tk.Spinbox(sf, from_=1, to=9999, textvariable=self._seed_var,
                   width=6, font=("Helvetica", 10)).pack(side="right")

        # ── Show columns ──────────────────────────────────────────────────
        section_label(p, "Show Columns")
        self._show_vars = {}
        opts = [
            ("kingman",  "Wq Kingman prediction",       True),
            ("ca2",      "Ca² arriving per station",    True),
            ("cd2",      "Cd² departure variability",   False),
            ("cs2eff",   "Cs²_eff (incl. breakdown)",   True),
            ("bstar",    "B_min / B* buffer sizing",     True),
            ("baseline", "Wq baseline (no breakdown)",  False),
        ]
        for key, label, default in opts:
            v = tk.BooleanVar(value=default)
            self._show_vars[key] = v
            cb = tk.Checkbutton(p, text=label, variable=v,
                                bg=PANEL_BG, fg=TEXT_LITE, selectcolor=PANEL_BG,
                                activebackground=PANEL_BG,
                                font=("Helvetica", 10))
            cb.pack(anchor="w", pady=1)

        # ── Run button ────────────────────────────────────────────────────
        tk.Frame(p, bg=PANEL_BG, height=8).pack()
        self._run_btn = ttk.Button(p, text="▶  Run Simulation",
                                    style="Run.TButton",
                                    command=self._on_run)
        self._run_btn.pack(fill="x", pady=4)

        self._status_lbl = tk.Label(p, text="", bg=PANEL_BG, fg=TEXT_MID,
                                     font=("Helvetica", 9), wraplength=230,
                                     justify="left")
        self._status_lbl.pack(fill="x", pady=2)

    def _build_right(self, parent):
        parent.configure(bg=CARD_BG)

        # ── Diagram row ───────────────────────────────────────────────────
        diag_frame = tk.Frame(parent, bg=CARD_BG, pady=6, padx=8)
        diag_frame.pack(fill="x")
        tk.Label(diag_frame, text="Serial Line", bg=CARD_BG,
                 fg=TEXT_DARK, font=("Helvetica", 11, "bold")).pack(anchor="w")
        self._diag_canvas = tk.Canvas(diag_frame, bg="#1e2d3d",
                                       height=110, highlightthickness=0)
        self._diag_canvas.pack(fill="x", pady=(4, 0))
        self._diag_canvas.bind("<Configure>", lambda _: self._draw_diagram())

        # ── Results treeview ──────────────────────────────────────────────
        res_frame = tk.Frame(parent, bg=CARD_BG, padx=8)
        res_frame.pack(fill="both", expand=False, pady=(6, 0))
        tk.Label(res_frame, text="Results", bg=CARD_BG,
                 fg=TEXT_DARK, font=("Helvetica", 11, "bold")).pack(anchor="w")

        tv_frame = tk.Frame(res_frame, bg=CARD_BG)
        tv_frame.pack(fill="both", expand=True)

        self._tree = ttk.Treeview(tv_frame, show="headings",
                                   selectmode="browse", height=6)
        xsb = ttk.Scrollbar(tv_frame, orient="horizontal",
                             command=self._tree.xview)
        self._tree.configure(xscrollcommand=xsb.set)
        self._tree.pack(fill="both", expand=True)
        xsb.pack(fill="x")
        self._tree.tag_configure("brk",  background="#fef2f2", foreground=RED)
        self._tree.tag_configure("norm", background=NRM_ROW,   foreground=TEXT_DARK)
        self._tree.tag_configure("alt",  background="#f8fafc",  foreground=TEXT_DARK)

        # Column key legend
        legend = (
            "Wq sim = DES mean queue wait  |  Wq King = Kingman G/G/1 prediction  |  "
            "Ca2 arriving = sq.CV of inter-arrivals at this station (= Cd2 of previous)  |  "
            "Cs2_eff = Cs2_nom + A(1-A)(MTTR/tp)^2"
        )
        tk.Label(res_frame, text=legend, bg=CARD_BG, fg=TEXT_MID,
                 font=("Helvetica", 8), wraplength=720,
                 justify="left").pack(anchor="w", pady=(2, 6))

        # ── Observations ──────────────────────────────────────────────────
        obs_frame = tk.Frame(parent, bg=CARD_BG, padx=8)
        obs_frame.pack(fill="both", expand=True)
        tk.Label(obs_frame, text="Key Observations", bg=CARD_BG,
                 fg=TEXT_DARK, font=("Helvetica", 11, "bold")).pack(anchor="w")

        self._obs_text = tk.Text(obs_frame, bg=CARD_BG, fg=TEXT_DARK,
                                  font=("Helvetica", 10), height=8,
                                  relief="flat", wrap="word",
                                  state="disabled")
        obs_sb = ttk.Scrollbar(obs_frame, orient="vertical",
                                command=self._obs_text.yview)
        self._obs_text.configure(yscrollcommand=obs_sb.set)
        obs_sb.pack(side="right", fill="y")
        self._obs_text.pack(fill="both", expand=True, pady=(2, 0))

        # Define text tags for colouring
        self._obs_text.tag_configure("warn",   foreground=ORANGE,
                                      font=("Helvetica", 10, "bold"))
        self._obs_text.tag_configure("info",   foreground="#1e40af",
                                      font=("Helvetica", 10))
        self._obs_text.tag_configure("action", foreground="#5b21b6",
                                      font=("Helvetica", 10))
        self._obs_text.tag_configure("error",  foreground=RED,
                                      font=("Helvetica", 10, "bold"))
        self._obs_text.tag_configure("ok",     foreground=GREEN,
                                      font=("Helvetica", 10))

        # ── Experiments expander ──────────────────────────────────────────
        exp_outer = tk.Frame(parent, bg=CARD_BG, padx=8, pady=4)
        exp_outer.pack(fill="x")
        self._exp_open = tk.BooleanVar(value=False)
        exp_btn = tk.Checkbutton(exp_outer,
                                  text="▶  Guided Experiments  (click to expand)",
                                  variable=self._exp_open,
                                  indicatoron=False,
                                  command=self._toggle_experiments,
                                  bg=HDR_BG, fg="white", selectcolor=HDR_BG,
                                  activebackground=HDR_BG,
                                  font=("Helvetica", 10, "bold"),
                                  relief="flat", padx=8, pady=4)
        exp_btn.pack(fill="x")
        self._exp_frame = tk.Frame(parent, bg=CARD_BG, padx=8)
        self._exp_text = tk.Text(self._exp_frame, bg="#f1f5f9", fg=TEXT_DARK,
                                  font=("Helvetica", 9), height=12,
                                  relief="flat", wrap="word", state="disabled")
        self._exp_text.pack(fill="both", expand=True)
        self._populate_experiments()

        self._draw_diagram()

    # ── Event handlers ────────────────────────────────────────────────────

    def _on_n_change(self):
        self._update_brk_options()
        self._draw_diagram()

    def _update_brk_options(self):
        n = self._n_var.get()
        opts = ["None"] + [f"Station {i+1}" for i in range(n)]
        cur  = self._brk_var.get()
        self._brk_menu["values"] = opts
        if cur not in opts:
            self._brk_var.set("Station 1")
        self._update_breakdown_vis()

    def _update_breakdown_vis(self):
        # Guard: may be called before _build_controls / _build_right finish
        if not hasattr(self, '_brk_frame') or not hasattr(self, '_diag_canvas'):
            return
        sel = self._brk_var.get()
        if sel == "None":
            self._brk_frame.pack_forget()
        else:
            self._brk_frame.pack(fill="x")
        self._refresh_brk_info()
        self._draw_diagram()

    def _refresh_brk_info(self):
        sel = self._brk_var.get()
        if sel == "None":
            self._brk_info.config(text="")
            return
        lam  = self._sl_lam.get()
        mu   = self._sl_mu.get()
        mtbf = self._sl_mtbf.get()
        mttr = self._sl_mttr.get()
        if mtbf <= 0 or mttr <= 0:
            return
        A       = mtbf / (mtbf + mttr)
        mu_eff  = mu * A
        rho_eff = lam / mu_eff if mu_eff > 0 else float("inf")
        tp      = 1.0 / mu
        Cs2_nom = self._sl_cs2.get()
        Cs2_eff = Cs2_nom + A * (1 - A) * (mttr / tp) ** 2
        self._brk_info.config(
            text=f"A={A:.3f}  rho_eff={min(rho_eff,9.99):.3f}\n"
                 f"Cs2_eff={Cs2_eff:.2f}  (nom: {Cs2_nom:.2f})"
        )

    def _update_rho_label(self):
        lam = self._sl_lam.get()
        mu  = self._sl_mu.get()
        rho = lam / mu
        if rho >= 1.0:
            self._rho_lbl.config(text=f"rho = {rho:.3f}  UNSTABLE", fg=RED)
        elif rho > 0.90:
            self._rho_lbl.config(text=f"rho = {rho:.3f}  (near knee)", fg=ORANGE)
        else:
            self._rho_lbl.config(text=f"rho = {rho:.3f}  (stable)", fg=GREEN)

    def _on_run(self):
        lam = self._sl_lam.get()
        mu  = self._sl_mu.get()
        if lam / mu >= 1.0:
            self._status("rho >= 1 — system unstable. Reduce lambda or increase mu.", RED)
            return
        self._run_btn.state(["disabled"])
        self._status("Simulating…", TEXT_MID)
        params = self._collect_params()
        thread = threading.Thread(target=self._run_thread, args=(params,), daemon=True)
        thread.start()

    def _run_thread(self, params):
        try:
            result = run_serial_des(**params)
            self.after(0, lambda: self._on_result(result, params))
        except Exception as e:
            self.after(0, lambda: self._status(f"Error: {e}", RED))
            self.after(0, lambda: self._run_btn.state(["!disabled"]))

    def _on_result(self, result, params):
        self._run_btn.state(["!disabled"])
        n  = params["n_stn"]
        ev = f"{result['sim_time']:.0f} hr simulated"
        hl = "  ⚠ hit event limit" if result["hit_limit"] else ""
        self._status(
            f"Done — warmup {result['warmup']:,} jobs{hl}  |  {ev}", GREEN
        )
        show = {k: v.get() for k, v in self._show_vars.items()}
        self._update_tree(result, params, show)
        obs  = make_observations(result, params["n_stn"], params["lam"],
                                 params["mu"], params["Ca2"], params["Cs2_nom"],
                                 params["brk_stn"], params["mtbf"], params["mttr"])
        self._update_obs(obs)
        self._last_result = result
        self._last_params  = params
        self._draw_diagram(result)

    def _collect_params(self):
        sel     = self._brk_var.get()
        brk_stn = -1 if sel == "None" else int(sel.split()[1]) - 1
        jobs    = int(round(self._jobs_var.get() / 500) * 500)
        return dict(
            n_stn   = self._n_var.get(),
            lam     = self._sl_lam.get(),
            mu      = self._sl_mu.get(),
            Ca2     = self._sl_ca2.get(),
            Cs2_nom = self._sl_cs2.get(),
            brk_stn = brk_stn,
            mtbf    = self._sl_mtbf.get(),
            mttr    = self._sl_mttr.get(),
            n_jobs  = jobs,
            seed    = int(self._seed_var.get()),
        )

    # ── Diagram ───────────────────────────────────────────────────────────

    def _draw_diagram(self, result=None):
        if not hasattr(self, '_diag_canvas'):
            return
        c      = self._diag_canvas
        c.delete("all")
        W      = c.winfo_width()
        if W < 10:
            W = 700
        H      = 110
        n      = self._n_var.get()
        sel    = self._brk_var.get()
        brk    = -1 if sel == "None" else int(sel.split()[1]) - 1
        mtbf   = self._sl_mtbf.get()
        mttr   = self._sl_mttr.get()
        lam    = self._sl_lam.get()
        A      = mtbf / (mtbf + mttr) if (brk >= 0 and mtbf > 0 and mttr > 0) else 1.0

        # Layout
        SRC_W  = 36
        SNK_W  = 42
        BUF_W  = 26
        GAP    = 10
        avail  = W - SRC_W - SNK_W - 16
        stn_w  = max(int((avail - n * (BUF_W + GAP * 2)) / n), 70)
        cy     = H // 2
        stn_h  = 46

        def stn_x(i):
            return SRC_W + 8 + i * (stn_w + BUF_W + GAP * 2)

        def buf_x(i):
            return stn_x(i) + stn_w + GAP

        # Arrow helper
        def arrow(x1, y1, x2, y2, color="#94a3b8"):
            c.create_line(x1, y1, x2, y2, fill=color, width=1.5,
                          arrow=tk.LAST, arrowshape=(8, 10, 3))

        # λ →
        c.create_text(4, cy, text="λ", fill="white",
                      font=("Helvetica", 11, "italic"), anchor="w")
        arrow(20, cy, stn_x(0), cy)

        for i in range(n):
            sx = stn_x(i)
            is_brk = (i == brk)
            fill   = "#4b1d1d" if is_brk else "#1e3a5f"
            border = RED       if is_brk else ACCENT
            lw     = 2         if is_brk else 1

            c.create_rectangle(sx, cy - stn_h//2,
                                sx + stn_w, cy + stn_h//2,
                                fill=fill, outline=border, width=lw)

            c.create_text(sx + stn_w//2, cy - 10,
                          text=f"Stn {i+1}",
                          fill="white", font=("Helvetica", 9, "bold"))

            role_txt = "BREAKDOWN" if is_brk else "normal"
            role_col = "#fca5a5"   if is_brk else TEXT_MID
            c.create_text(sx + stn_w//2, cy + 4,
                          text=role_txt,
                          fill=role_col, font=("Helvetica", 8))

            if is_brk:
                c.create_text(sx + stn_w//2, cy + 16,
                              text=f"A={A:.2f}",
                              fill="#fde68a", font=("Courier", 8))

            # Wq label below box
            if result:
                wq = result["Wq_sim"][i] * 60
                wq_txt = f"{wq:.1f} min" if not math.isnan(wq) else "…"
                wq_col = "#fca5a5" if is_brk else "#93c5fd"
                c.create_text(sx + stn_w//2, cy + stn_h//2 + 12,
                               text=f"Wq={wq_txt}",
                               fill=wq_col, font=("Courier", 9, "bold"))

            # Buffer between stations
            if i < n - 1:
                bx = buf_x(i)
                bs = buffer_sizing(lam, mttr) if (is_brk and mttr > 0) else None
                b_col = "#7c3aed" if bs else "#374151"
                c.create_rectangle(bx, cy - 14, bx + BUF_W, cy + 14,
                                    fill="#0f172a", outline=b_col,
                                    width=1, dash=(4, 3))
                if bs:
                    c.create_text(bx + BUF_W//2, cy - 18,
                                  text=f"B*={bs[1]}",
                                  fill="#c4b5fd", font=("Helvetica", 7, "bold"))
                arrow(sx + stn_w, cy, bx, cy)
                arrow(bx + BUF_W, cy, stn_x(i+1), cy)

        # Last → output
        last_x = stn_x(n - 1) + stn_w
        arrow(last_x, cy, W - 10, cy)
        c.create_text(W - 4, cy, text="→", fill="white",
                      font=("Helvetica", 11), anchor="e")

    # ── Results treeview ──────────────────────────────────────────────────

    def _update_tree(self, result, params, show):
        # Rebuild columns
        n_stn   = params["n_stn"]
        lam     = params["lam"]
        mu      = params["mu"]
        Ca2     = params["Ca2"]
        Cs2_nom = params["Cs2_nom"]
        brk_stn = params["brk_stn"]
        mtbf    = params["mtbf"]
        mttr    = params["mttr"]

        cols = [c for c, _, _ in self.ALWAYS_COLS]
        hdrs = {c: h for c, h, _ in self.ALWAYS_COLS}
        wids = {c: w for c, h, w in self.ALWAYS_COLS}
        for key, hdr, wid in self.OPT_COLS:
            if show.get(key):
                cols.append(key)
                hdrs[key] = hdr
                wids[key] = wid

        self._tree["columns"] = cols
        for col in cols:
            self._tree.heading(col, text=hdrs[col])
            self._tree.column(col, width=wids[col], anchor="center",
                               minwidth=wids[col], stretch=False)

        for row in self._tree.get_children():
            self._tree.delete(row)

        Ca2_chain = Ca2
        Wq_base   = kingman_wq(lam, mu, Ca2, Cs2_nom) * 60.0

        for i in range(n_stn):
            is_brk = (i == brk_stn)
            an = station_analytics(mu, lam,
                                   mtbf if is_brk else 0,
                                   mttr if is_brk else 0,
                                   Cs2_nom, Ca2_chain)
            s = result

            def v(x, d=2):
                if x is None or (isinstance(x, float) and math.isnan(x)):
                    return "—"
                return "∞" if math.isinf(x) else str(round(x, d))

            vals = {
                "station":  f"Stn {i+1}",
                "role":     "BREAKDOWN" if is_brk else "normal",
                "wq_sim":   v(s["Wq_sim"][i] * 60, 2),
                "a_sim":    v(s["A_sim"][i], 3),
                "rho_eff":  v(an["rho_eff"], 3),
                "samples":  f"{s['n_collected'][i]:,}",
                "bk_count": str(s["bk_count"][i]),
            }
            if show.get("kingman"):
                vals["kingman"]  = v(an["Wq_pred"] * 60, 2)
            if show.get("ca2"):
                vals["ca2"]      = v(s["Ca2_arriving"][i], 3)
            if show.get("cd2"):
                vals["cd2"]      = v(s["Cd2_dep"][i], 3)
            if show.get("cs2eff"):
                vals["cs2eff"]   = v(an["Cs2_eff"], 3)
            if show.get("bstar"):
                bs = buffer_sizing(lam, mttr) if (is_brk and i < n_stn-1) else None
                vals["bstar"]    = f"{bs[0]} / {bs[1]}" if bs else "—"
            if show.get("baseline"):
                vals["baseline"] = v(Wq_base, 2)

            tag  = "brk" if is_brk else ("norm" if i % 2 == 0 else "alt")
            self._tree.insert("", "end",
                               values=[vals.get(c, "—") for c in cols],
                               tags=(tag,))
            Ca2_chain = an["Cd2"]

    # ── Observations text widget ──────────────────────────────────────────

    def _update_obs(self, obs):
        t = self._obs_text
        t.config(state="normal")
        t.delete("1.0", "end")
        icons = {"warn": "⚠  ", "info": "📊  ", "action": "💡  ",
                 "error": "🚨  ", "ok": "✅  "}
        for kind, msg in obs:
            t.insert("end", f"\n{icons.get(kind,'')}{msg}\n", kind)
        t.config(state="disabled")

    # ── Experiments panel ─────────────────────────────────────────────────

    def _populate_experiments(self):
        exps = [
            ("1 — Baseline",
             "No breakdown. Run. All stations Wq ≈ 24 min. "
             "Simulation matches Kingman within ~10%."),
            ("2 — Ca² cascade",
             "Breakdown at Stn 1 (MTBF=3, MTTR=0.5). Run. "
             "Observe Wq rise at Stn 2 and 3 — zero breakdown there. "
             "Ca2 arriving column shows the propagation (Departure Theorem)."),
            ("3 — Saturation",
             "Increase MTTR to 2hr. rho_eff approaches 1. Wq explodes non-linearly. "
             "See the knee of the congestion curve."),
            ("4 — Precision wasted",
             "Set Cs2_nom = 0.1 (deterministic). Re-run with same breakdown. "
             "Wq barely improves — check Cs2_eff column: "
             "breakdowns dominate, process precision accounts for < 3%."),
            ("5 — Last station",
             "Move breakdown to the last station. No downstream cascade. "
             "Upstream stations unaffected, Wq stays near baseline."),
            ("6 — 5 stations",
             "Set n=5, breakdown at Stn 1. Watch Ca2 cascade and decay "
             "through 4 downstream stations. "
             "Cd2 = (1-rho^2)Ca2 + rho^2 * Cs2_eff smooths over distance."),
            ("7 — Buffer sizing",
             "After exp 2: read B_min / B* in the table. "
             "That is the buffer needed to prevent starvation in 95% of repairs. "
             "B_min = ceil(lambda x MTTR). "
             "Increasing MTTR raises B* — another reason to minimise repair time."),
        ]
        t = self._exp_text
        t.config(state="normal")
        for title, desc in exps:
            t.insert("end", f"\n{title}\n", "title")
            t.insert("end", f"{desc}\n\n")
        t.tag_configure("title", font=("Helvetica", 9, "bold"),
                         foreground=ACCENT)
        t.config(state="disabled")

    def _toggle_experiments(self):
        if self._exp_open.get():
            self._exp_frame.pack(fill="x", padx=8, pady=(0, 6))
        else:
            self._exp_frame.pack_forget()

    # ── Status bar ────────────────────────────────────────────────────────

    def _status(self, msg, color=TEXT_MID):
        self._status_lbl.config(text=msg, fg=color)


# ══════════════════════════════════════════════════════════════════════════
#  Entry point
# ══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    app = App()
    app.geometry("1100x720")
    app.minsize(900, 600)
    app.mainloop()
