"""Digital twin of a BWRX-300 unit: availability, part-load physics, marginal cost and
perfect-foresight dispatch against an hourly price vector.

Physics summarised (sources in ASSUMPTIONS.md):
* 870 MWt → 300 MWe net (η ≈ 34.5 %).  Load-following 50–100 % by reactor power reduction
  (control rods / feed-water temperature; natural circulation → no recirculation-flow control).
* Fuel *burn* scales with thermal power, so the fuel cost per MWh_e is ~constant under reactor
  power reduction; the un-burnt reactivity extends the cycle (energy banked).  A small turbine
  off-design efficiency penalty (≈1.5 pt at 50 %) raises fuel/MWh slightly at part load.
* Turbine bypass (steam dump) keeps the reactor at 100 % while electrical output falls — fuel
  is wasted; it is *not* used for economic dispatch here (only for minutes-scale balancing).
* Ramp: 0.5 %/min in 50–90 %, 2 %/min in 90–100 % → a 50→100 % ramp takes ≈85 min, so an
  hourly model needs a ramp limit of roughly 35 %·P per hour in the low band.
* No on/off cycling: the unit never goes below 50 % for price reasons (a trip/shutdown costs
  days, xenon transients, and the licence basis assumes baseload-with-load-following).

Marginal cost per MWh_e = fuel/η_rel + non-fuel VOM + statutory decommissioning-fund payment
(17.16 PLN/MWh, Dz.U. 2012 poz. 1213) — sustaining capex is treated as a fixed annual cost.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from scipy.optimize import linprog
from scipy.sparse import coo_matrix, csr_matrix, hstack, identity, vstack


@dataclass
class SMRUnit:
    net_mw: float = 300.0
    thermal_mwt: float = 870.0
    min_load: float = 0.5
    ramp_up_mw_per_h: float = 105.0     # 35 % of P per hour (0.5 %/min in the 50–90 % band)
    ramp_down_mw_per_h: float = 105.0
    fuel_pln_per_mwh: float = 31.0
    vom_pln_per_mwh: float = 11.0
    fund_pln_per_mwh: float = 17.16
    eff_penalty_pts_at_50: float = 1.5  # thermal efficiency points lost at 50 % load
    cycling_cost_pln_per_mw: float = 5.0

    # ---- derived -------------------------------------------------------------
    @property
    def eta_full(self) -> float:
        return self.net_mw / self.thermal_mwt

    def eta_rel(self, load: np.ndarray | float) -> np.ndarray | float:
        """Relative thermal efficiency vs full load (1.0 at 100 %, ~0.957 at 50 %)."""
        pts = self.eff_penalty_pts_at_50 * (1.0 - np.asarray(load)) / 0.5
        return (self.eta_full * 100 - pts) / (self.eta_full * 100)

    def marginal_cost(self, load: float = 1.0) -> float:
        """Short-run marginal cost of one more MWh_e at a given load level, PLN/MWh."""
        return self.fuel_pln_per_mwh / float(self.eta_rel(load)) + self.vom_pln_per_mwh + self.fund_pln_per_mwh

    def fuel_mwh_thermal(self, gen_mwh: np.ndarray, cap_mw: np.ndarray) -> np.ndarray:
        """Thermal energy burned for a generation vector (MWh_th), incl. part-load penalty."""
        load = np.divide(gen_mwh, cap_mw, out=np.zeros_like(gen_mwh), where=cap_mw > 0)
        return gen_mwh / (self.eta_full * self.eta_rel(np.clip(load, self.min_load, 1.0)))


# ------------------------------------------------------------------------------------------
# Availability
# ------------------------------------------------------------------------------------------
def availability_profile(year_index: int, hours: int = 8760, refuel_cycle_months: int = 18,
                         refuel_outage_days: float = 15, major_days_per_10yr: float = 25,
                         efor: float = 0.03, outage_month: int = 4, foak_extra_efor: float = 0.03,
                         foak_years: int = 3, month_of_hour: np.ndarray | None = None) -> np.ndarray:
    """Hourly available capacity fraction for operating year `year_index` (0-based).

    Planned refuelling outages follow an 18-month cycle → 2 outages every 3 years, placed in
    `outage_month` (April: historically the lowest Polish prices).  Forced outages are applied
    as an expected-value derate (EFOR) — a Monte-Carlo variant is in optimise.py.
    """
    if month_of_hour is None:
        month_of_hour = np.repeat(np.arange(1, 13), [744, 672, 744, 720, 744, 720, 744, 744, 720, 744, 720, 744])
    av = np.ones(hours)
    # refuelling: cycle in months; count outages whose end month falls in this year
    months_elapsed_start = year_index * 12
    outage_days = 0.0
    m = refuel_cycle_months
    while m <= months_elapsed_start + 12:
        if m > months_elapsed_start:
            outage_days += refuel_outage_days
        m += refuel_cycle_months
    if (year_index + 1) % 10 == 0:
        outage_days += major_days_per_10yr
    if outage_days > 0:
        idx = np.where(month_of_hour == outage_month)[0]
        n = int(min(len(idx), round(outage_days * 24)))
        av[idx[:n]] = 0.0
    e = efor + (foak_extra_efor if year_index < foak_years else 0.0)
    return av * (1.0 - e)


# ------------------------------------------------------------------------------------------
# Dispatch
# ------------------------------------------------------------------------------------------
@dataclass
class DispatchResult:
    gen_mwh: np.ndarray
    cap_mw: np.ndarray
    price: np.ndarray
    revenue_pln: float
    var_cost_pln: float
    cycling_cost_pln: float
    hours_at_min: int
    energy_mwh: float
    capture_price: float
    curtailed_mwh: float                    # energy foregone vs must-run at availability
    extra: dict = field(default_factory=dict)

    @property
    def gross_margin_pln(self) -> float:
        return self.revenue_pln - self.var_cost_pln - self.cycling_cost_pln


def dispatch_baseload(unit: SMRUnit, price: np.ndarray, avail: np.ndarray) -> DispatchResult:
    cap = unit.net_mw * avail
    gen = cap.copy()
    rev = float((gen * price).sum())
    var = float(gen.sum() * unit.marginal_cost(1.0))
    return DispatchResult(gen, cap, price, rev, var, 0.0, 0, float(gen.sum()),
                          rev / max(gen.sum(), 1e-9), 0.0)


def dispatch_flexible(unit: SMRUnit, price: np.ndarray, avail: np.ndarray,
                      ramp: bool = True) -> DispatchResult:
    """Perfect-foresight profit-maximising dispatch between min_load and available capacity.

    LP:  max Σ_t (p_t − mc) g_t − c_cyc Σ_t (u_t + d_t)
         s.t. g_t − g_{t−1} = u_t − d_t,  0 ≤ u_t ≤ R_up, 0 ≤ d_t ≤ R_dn,
              min_load·cap_t ≤ g_t ≤ cap_t   (cap_t = 0 during outages → g_t = 0)

    Without ramp/cycling terms the solution is the bang-bang rule g_t = cap if p_t > mc else
    min_load·cap; the LP adds the ramp coupling and the wear proxy.  Part-load efficiency is
    handled by using mc at full load (fuel/MWh differences at part load are <1 PLN/MWh).
    """
    T = len(price)
    cap = unit.net_mw * avail
    lo = unit.min_load * cap
    mc = unit.marginal_cost(1.0)
    if not ramp or unit.cycling_cost_pln_per_mw == 0 and unit.ramp_up_mw_per_h >= unit.net_mw:
        gen = np.where(price > mc, cap, lo)
        cyc = 0.0
    else:
        # variables: g (T), u (T), d (T)
        c = np.concatenate([-(price - mc), np.full(T, unit.cycling_cost_pln_per_mw),
                            np.full(T, unit.cycling_cost_pln_per_mw)])
        # equality: g_t − g_{t−1} − u_t + d_t = 0  (t ≥ 1)
        rows = np.arange(T - 1)
        A_g = coo_matrix((np.concatenate([np.ones(T - 1), -np.ones(T - 1)]),
                          (np.concatenate([rows, rows]), np.concatenate([rows + 1, rows]))), shape=(T - 1, T))
        A_u = coo_matrix((-np.ones(T - 1), (rows, rows + 1)), shape=(T - 1, T))
        A_d = coo_matrix((np.ones(T - 1), (rows, rows + 1)), shape=(T - 1, T))
        A_eq = hstack([A_g, A_u, A_d]).tocsr()
        b_eq = np.zeros(T - 1)
        bounds_g = list(zip(lo, cap))
        # ramp limits apply to economic manoeuvring; outage entries/exits (cap steps) are exempt
        dcap = np.diff(cap, prepend=cap[0])
        bounds_u = [(0, unit.ramp_up_mw_per_h + max(dcap[t], 0.0) + (cap[t] if cap[t] > 0 and (t > 0 and cap[t - 1] == 0) else 0.0)) for t in range(T)]
        bounds_d = [(0, unit.ramp_down_mw_per_h + max(-dcap[t], 0.0) + (cap[t - 1] if t > 0 and cap[t] == 0 and cap[t - 1] > 0 else 0.0)) for t in range(T)]
        res = linprog(c, A_eq=A_eq, b_eq=b_eq, bounds=bounds_g + bounds_u + bounds_d, method="highs")
        if res.status != 0:
            raise RuntimeError(f"SMR dispatch LP failed: {res.message}")
        gen = res.x[:T]
        cyc = float(unit.cycling_cost_pln_per_mw * (res.x[T:2 * T].sum() + res.x[2 * T:].sum()))
    rev = float((gen * price).sum())
    var = float(gen.sum() * mc)
    at_min = int(((gen <= lo + 1e-6) & (cap > 0)).sum())
    return DispatchResult(gen, cap, price, rev, var, cyc, at_min, float(gen.sum()),
                          rev / max(gen.sum(), 1e-9), float((cap - gen).sum()))


def cfd_settlement(gen_mwh: np.ndarray, price: np.ndarray, strike: float, reference: str = "daily_base",
                   exclude_negative: bool = False, two_way: bool = True) -> dict:
    """Difference payments for a two-way CfD.

    reference = 'hourly'     → hourly day-ahead price
              = 'daily_base' → daily arithmetic mean (TGeBase), PEJ-template spot leg
    Payment_t = gen_t × (strike − ref_t) (positive = top-up from Zarządca Rozliczeń, negative = pay-back).
    """
    if reference == "daily_base":
        ref = price.reshape(-1, 24).mean(axis=1).repeat(24)
    else:
        ref = price
    diff = strike - ref
    if not two_way:
        diff = np.maximum(diff, 0.0)
    pay = gen_mwh * diff
    if exclude_negative:
        pay = np.where(price < 0, 0.0, pay)
    return {"cfd_payment_pln": float(pay.sum()), "top_up_pln": float(pay[pay > 0].sum()),
            "pay_back_pln": float(-pay[pay < 0].sum()), "ref_mean": float(ref.mean())}
