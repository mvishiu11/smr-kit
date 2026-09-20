"""Digital twin of gas-fired units (CCGT / OCGT / engines) with perfect-foresight unit commitment.

Each unit is modelled with:
* a two-parameter heat-input curve  H = a·P_max·u + b·g  (MWh_th per hour) fitted through the
  full-load efficiency and the efficiency at minimum stable load — this reproduces the strong
  part-load penalty of combined-cycle plants (e.g. 57 % → 45 % at 40–50 % load);
* on/off binary, minimum up/down times, start-up costs (wear + start fuel, hot/warm/cold by
  preceding off-time), minimum stable load, availability derate and a planned-outage window;
* variable cost = fuel (monthly gas price / η) + CO2 (EUA × 0.2006 t/MWh_th) + non-fuel VOM.

Weekly MILPs (168 h) are solved with HiGHS through :func:`scipy.optimize.milp`, chained through
the end-of-week state, so a full year is 52 small problems instead of one 8,760-h monolith.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp
from scipy.sparse import coo_matrix, csr_matrix, vstack


@dataclass
class GasUnit:
    name: str
    net_mw: float
    eta_full: float
    eta_min: float
    min_load: float
    min_up_h: int = 1
    min_down_h: int = 1
    start_cost_pln_per_mw: dict = field(default_factory=lambda: {"hot": 100, "warm": 100, "cold": 100})
    start_hot_max_off_h: int = 8
    start_warm_max_off_h: int = 48
    start_fuel_mwh_per_mw: float = 0.3
    vom_pln_per_mwh: float = 16.0
    availability: float = 0.925
    planned_outage_weeks: int = 3
    emission_factor_t_per_mwh_th: float = 0.2006

    # heat-input curve coefficients (per MW of capacity / per MWh generated)
    @property
    def b(self) -> float:  # incremental heat rate, MWh_th per MWh_e
        m = self.min_load
        return (1 / self.eta_full - m / self.eta_min) / (1 - m)

    @property
    def a(self) -> float:  # no-load heat, MWh_th per hour per MW of capacity while on
        return 1 / self.eta_full - self.b

    def heat_input(self, g: np.ndarray, u: np.ndarray, cap: np.ndarray) -> np.ndarray:
        return self.a * cap * u + self.b * g

    def start_type(self, off_hours: int) -> str:
        if off_hours <= self.start_hot_max_off_h:
            return "hot"
        if off_hours <= self.start_warm_max_off_h:
            return "warm"
        return "cold"


@dataclass
class GasDispatchResult:
    gen_mwh: np.ndarray            # (T,) total portfolio
    gen_by_unit: np.ndarray        # (n_units, T)
    on_by_unit: np.ndarray         # (n_units, T)
    price: np.ndarray
    revenue_pln: float
    fuel_cost_pln: float
    co2_cost_pln: float
    vom_cost_pln: float
    start_cost_pln: float
    starts: dict                   # per unit: {hot, warm, cold}
    fuel_mwh_th: float
    co2_t: float
    energy_mwh: float
    capture_price: float
    running_hours: np.ndarray      # per unit

    @property
    def var_cost_pln(self) -> float:
        return self.fuel_cost_pln + self.co2_cost_pln + self.vom_cost_pln + self.start_cost_pln

    @property
    def gross_margin_pln(self) -> float:
        return self.revenue_pln - self.var_cost_pln


def _week_milp(units: list[GasUnit], price: np.ndarray, gas: np.ndarray, eua_pln: np.ndarray,
               cap: np.ndarray, u_prev: np.ndarray, off_prev: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Solve one block.  Returns (g [n,T], u [n,T], s [n,T])."""
    n, T = len(units), len(price)
    nv = 3 * n * T                       # g, u, s stacked per unit
    idx_g = lambda i, t: (i * T + t)
    idx_u = lambda i, t: n * T + i * T + t
    idx_s = lambda i, t: 2 * n * T + i * T + t

    c = np.zeros(nv)
    lb = np.zeros(nv)
    ub = np.ones(nv)
    integrality = np.zeros(nv)
    rows, cols, vals, lo_c, hi_c = [], [], [], [], []
    r = 0

    for i, un in enumerate(units):
        ef = un.emission_factor_t_per_mwh_th
        # cost of heat per MWh_th (hourly): gas + CO2
        heat_price = gas + eua_pln * ef
        for t in range(T):
            # objective (minimise) = −(price − b·heat − vom)·g + a·cap·heat·u + start·s
            c[idx_g(i, t)] = -(price[t] - un.b * heat_price[t] - un.vom_pln_per_mwh)
            c[idx_u(i, t)] = un.a * cap[i, t] * heat_price[t]
            start_cost = (un.start_cost_pln_per_mw["warm"] + un.start_fuel_mwh_per_mw * gas[t]) * un.net_mw
            c[idx_s(i, t)] = start_cost
            ub[idx_g(i, t)] = max(cap[i, t], 0.0)
            integrality[idx_u(i, t)] = 1
            if cap[i, t] <= 0:
                ub[idx_u(i, t)] = 0
            # g − cap·u ≤ 0
            rows += [r, r]; cols += [idx_g(i, t), idx_u(i, t)]; vals += [1.0, -cap[i, t]]
            lo_c.append(-np.inf); hi_c.append(0.0); r += 1
            # g − min·cap·u ≥ 0
            rows += [r, r]; cols += [idx_g(i, t), idx_u(i, t)]; vals += [1.0, -un.min_load * cap[i, t]]
            lo_c.append(0.0); hi_c.append(np.inf); r += 1
            # s ≥ u_t − u_{t−1}
            if t == 0:
                rows += [r, r]; cols += [idx_s(i, t), idx_u(i, t)]; vals += [1.0, -1.0]
                lo_c.append(-u_prev[i]); hi_c.append(np.inf); r += 1
            else:
                rows += [r, r, r]; cols += [idx_s(i, t), idx_u(i, t), idx_u(i, t - 1)]; vals += [1.0, -1.0, 1.0]
                lo_c.append(0.0); hi_c.append(np.inf); r += 1
            # minimum up time: u_k ≥ s_t for k in [t, t+MU−1]
            for k in range(t + 1, min(T, t + un.min_up_h)):
                rows += [r, r]; cols += [idx_u(i, k), idx_s(i, t)]; vals += [1.0, -1.0]
                lo_c.append(0.0); hi_c.append(np.inf); r += 1
            # minimum down time: u_k ≤ 1 − (u_{t−1} − u_t)  → u_k + u_{t−1} − u_t ≤ 1, k in [t+1, t+MD−1]
            if t >= 1:
                for k in range(t + 1, min(T, t + un.min_down_h)):
                    rows += [r, r, r]; cols += [idx_u(i, k), idx_u(i, t - 1), idx_u(i, t)]; vals += [1.0, 1.0, -1.0]
                    lo_c.append(-np.inf); hi_c.append(1.0); r += 1
        # enforce remaining min-down from previous block
        if u_prev[i] == 0 and off_prev[i] < un.min_down_h:
            for k in range(0, min(T, un.min_down_h - int(off_prev[i]))):
                ub[idx_u(i, k)] = 0

    A = coo_matrix((vals, (rows, cols)), shape=(r, nv)).tocsr()
    res = milp(c, constraints=LinearConstraint(A, np.array(lo_c), np.array(hi_c)),
               integrality=integrality, bounds=Bounds(lb, ub),
               options={"disp": False, "mip_rel_gap": 1e-4, "time_limit": 60})
    if res.x is None:
        raise RuntimeError(f"gas UC MILP failed: {res.message}")
    x = res.x
    g = x[: n * T].reshape(n, T)
    u = np.round(x[n * T: 2 * n * T].reshape(n, T))
    s = x[2 * n * T:].reshape(n, T)
    return g, u, s


def dispatch_portfolio(units: list[GasUnit], price: np.ndarray, gas_pln_per_mwh_th: np.ndarray,
                       eua_pln_per_t: np.ndarray, block_hours: int = 168,
                       outage_start_hour: int | None = None) -> GasDispatchResult:
    """Yearly perfect-foresight unit commitment of a gas portfolio (chained weekly MILPs)."""
    n, T = len(units), len(price)
    cap = np.zeros((n, T))
    for i, un in enumerate(units):
        c = np.full(T, un.net_mw * un.availability)
        # planned outage: consecutive weeks in the lowest-price part of the year (default: start of April)
        st = 24 * 90 if outage_start_hour is None else outage_start_hour
        c[st: st + un.planned_outage_weeks * 168] = 0.0
        cap[i] = c
    g_all = np.zeros((n, T)); u_all = np.zeros((n, T)); s_all = np.zeros((n, T))
    u_prev = np.zeros(n); off_prev = np.full(n, 1000)
    for b0 in range(0, T, block_hours):
        b1 = min(T, b0 + block_hours)
        g, u, s = _week_milp(units, price[b0:b1], gas_pln_per_mwh_th[b0:b1], eua_pln_per_t[b0:b1],
                             cap[:, b0:b1], u_prev, off_prev)
        g_all[:, b0:b1] = g; u_all[:, b0:b1] = u; s_all[:, b0:b1] = s
        u_prev = u[:, -1]
        for i in range(n):
            if u[i, -1] == 1:
                off_prev[i] = 0
            else:
                run = 0
                for k in range(b1 - 1, -1, -1):
                    if u_all[i, k] == 1:
                        break
                    run += 1
                off_prev[i] = run
    # ---- post-processing: exact start classification and costs ------------------------
    gen = g_all.sum(axis=0)
    revenue = float((gen * price).sum())
    fuel_cost = co2_cost = vom_cost = start_cost = 0.0
    fuel_th_total = co2_total = 0.0
    starts = {}
    run_h = np.zeros(n)
    for i, un in enumerate(units):
        heat = un.heat_input(g_all[i], u_all[i], cap[i])
        fuel_th_total += float(heat.sum())
        fuel_cost += float((heat * gas_pln_per_mwh_th).sum())
        co2 = heat * un.emission_factor_t_per_mwh_th
        co2_total += float(co2.sum())
        co2_cost += float((co2 * eua_pln_per_t).sum())
        vom_cost += float(g_all[i].sum() * un.vom_pln_per_mwh)
        run_h[i] = u_all[i].sum()
        cnt = {"hot": 0, "warm": 0, "cold": 0}
        off = 1000
        for t in range(T):
            if u_all[i, t] == 1 and (t == 0 or u_all[i, t - 1] == 0):
                typ = un.start_type(off)
                cnt[typ] += 1
                start_cost += (un.start_cost_pln_per_mw[typ] + un.start_fuel_mwh_per_mw * gas_pln_per_mwh_th[t]) * un.net_mw
                fuel_th_total += un.start_fuel_mwh_per_mw * un.net_mw
                co2_total += un.start_fuel_mwh_per_mw * un.net_mw * un.emission_factor_t_per_mwh_th
            off = 0 if u_all[i, t] == 1 else off + 1
        starts[un.name] = cnt
    e = float(gen.sum())
    return GasDispatchResult(gen, g_all, u_all, price, revenue, fuel_cost, co2_cost, vom_cost, start_cost,
                             starts, fuel_th_total, co2_total, e, revenue / max(e, 1e-9), run_h)


def srmc(unit: GasUnit, gas_pln: float, eua_pln: float, load: float = 1.0) -> float:
    """Short-run marginal cost at a given load (PLN/MWh_e), average-cost basis."""
    eta = unit.eta_full if load >= 1 else unit.eta_full - (unit.eta_full - unit.eta_min) * (1 - load) / (1 - unit.min_load)
    return (gas_pln + eua_pln * unit.emission_factor_t_per_mwh_th) / eta + unit.vom_pln_per_mwh


# ------------------------------------------------------------------------------------------
# Fast heuristic dispatch (for Monte Carlo / screening; validated against the MILP in tests)
# ------------------------------------------------------------------------------------------
def dispatch_heuristic(units: list[GasUnit], price: np.ndarray, gas_pln_per_mwh_th: np.ndarray,
                       eua_pln_per_t: np.ndarray, outage_start_hour: int | None = None) -> GasDispatchResult:
    """Daily-window commitment heuristic, per unit.

    For each day the unit is either off, or on for one contiguous window [t1, t2].  Inside the
    window it runs at full load in hours where price ≥ incremental cost b·h + vom, else at minimum
    load.  The window is the one maximising Σ margin − start cost (Kadane's algorithm on the
    "hourly margin while on" series, with the no-load heat a·cap·h charged per hour on).  Windows
    are merged across midnight when the overnight margin at minimum load beats a fresh start.
    """
    n, T = len(units), len(price)
    g_all = np.zeros((n, T)); u_all = np.zeros((n, T))
    for i, un in enumerate(units):
        capv = np.full(T, un.net_mw * un.availability)
        st = 24 * 90 if outage_start_hour is None else outage_start_hour
        capv[st: st + un.planned_outage_weeks * 168] = 0.0
        h = gas_pln_per_mwh_th + eua_pln_per_t * un.emission_factor_t_per_mwh_th
        inc = un.b * h + un.vom_pln_per_mwh                   # incremental cost per MWh_e
        noload = un.a * capv * h                                # PLN per hour while on
        full = (price - inc) * capv - noload                    # margin/h at full load
        minl = (price - inc) * un.min_load * capv - noload      # margin/h at min load
        best_h = np.maximum(full, minl)                         # margin/h if on (choose level)
        gen_if_on = np.where(full >= minl, capv, un.min_load * capv)
        start = (un.start_cost_pln_per_mw["warm"] + un.start_fuel_mwh_per_mw * gas_pln_per_mwh_th) * un.net_mw
        # Kadane over the whole year with a per-start penalty: dynamic programme on/off
        # state value: V_on[t], V_off[t]
        v_on = np.full(T, -np.inf); v_off = np.zeros(T)
        from_on = np.zeros(T, dtype=bool); from_off_on = np.zeros(T, dtype=bool)
        v_on_prev, v_off_prev = -np.inf, 0.0
        for t in range(T):
            if capv[t] <= 0:
                v_on[t] = -np.inf; v_off[t] = max(v_off_prev, v_on_prev); from_on[t] = v_on_prev > v_off_prev
                v_on_prev, v_off_prev = v_on[t], v_off[t]
                continue
            stay = v_on_prev + best_h[t]
            go = v_off_prev - start[t] + best_h[t]
            if stay >= go:
                v_on[t] = stay; from_off_on[t] = False
            else:
                v_on[t] = go; from_off_on[t] = True
            v_off[t] = max(v_off_prev, v_on_prev)
            from_on[t] = v_on_prev > v_off_prev
            v_on_prev, v_off_prev = v_on[t], v_off[t]
        # backtrack
        on = np.zeros(T, dtype=bool)
        state_on = v_on[T - 1] > v_off[T - 1]
        for t in range(T - 1, -1, -1):
            if state_on:
                on[t] = True
                state_on = not from_off_on[t]
            else:
                state_on = from_on[t]
        u_all[i] = on
        g_all[i] = np.where(on, gen_if_on, 0.0)
    # ---- costs (same post-processing as the MILP) --------------------------------------------
    gen = g_all.sum(axis=0)
    revenue = float((gen * price).sum())
    fuel_cost = co2_cost = vom_cost = start_cost = 0.0
    fuel_th_total = co2_total = 0.0
    starts = {}; run_h = np.zeros(n)
    for i, un in enumerate(units):
        capv = np.full(T, un.net_mw * un.availability)
        heat = un.heat_input(g_all[i], u_all[i], capv)
        fuel_th_total += float(heat.sum()); fuel_cost += float((heat * gas_pln_per_mwh_th).sum())
        co2 = heat * un.emission_factor_t_per_mwh_th
        co2_total += float(co2.sum()); co2_cost += float((co2 * eua_pln_per_t).sum())
        vom_cost += float(g_all[i].sum() * un.vom_pln_per_mwh)
        run_h[i] = u_all[i].sum()
        cnt = {"hot": 0, "warm": 0, "cold": 0}; off = 1000
        for t in range(T):
            if u_all[i, t] == 1 and (t == 0 or u_all[i, t - 1] == 0):
                typ = un.start_type(off); cnt[typ] += 1
                start_cost += (un.start_cost_pln_per_mw[typ] + un.start_fuel_mwh_per_mw * gas_pln_per_mwh_th[t]) * un.net_mw
                fuel_th_total += un.start_fuel_mwh_per_mw * un.net_mw
                co2_total += un.start_fuel_mwh_per_mw * un.net_mw * un.emission_factor_t_per_mwh_th
            off = 0 if u_all[i, t] == 1 else off + 1
        starts[un.name] = cnt
    e = float(gen.sum())
    return GasDispatchResult(gen, g_all, u_all, price, revenue, fuel_cost, co2_cost, vom_cost, start_cost,
                             starts, fuel_th_total, co2_total, e, revenue / max(e, 1e-9), run_h)
