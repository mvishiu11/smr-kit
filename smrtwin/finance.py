"""Project-finance layer: annual cash flows, Polish CIT, LCOE, NPV/IRR, debt overlay and
local-government revenue for one generating asset.

All money is **real PLN at the 2026 price level** (inflation only matters for the nominal
statutory items, which are handled in the assumptions as CPI-indexed equivalents).  Cash flows
are annual, end-of-year, with the financial-investment-decision year as t = 0.

Layout of the annual table (one row per calendar year, FID → end of life):

    capex, other_capex, revenue_market, cfd_payment, capacity_rev, balancing_rev, revenue,
    fuel, co2, vom, start, cycling, fund, fom, sustaining, property_tax, licence_fee,
    gas_exit_tariff, opex, ebitda, depreciation_tax, taxable_income, cit, ebit_acc, fcf_pretax,
    fcf_posttax, debt_draw, debt_service, interest, principal, equity_cf, dscr,
    local_property_tax_host, local_property_tax_neighbours, local_cit_gmina, local_cit_powiat,
    local_cit_wojewodztwo, local_pit_gmina, local_pit_powiat, local_pit_wojewodztwo,
    state_cit, state_eua_revenue, state_fund_contribution
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Sequence

import numpy as np
import pandas as pd
from scipy.optimize import brentq


# ------------------------------------------------------------------------------------------
# Data classes
# ------------------------------------------------------------------------------------------
@dataclass
class OperatingYear:
    """Physical/market result of one operating year (from the dispatch twins)."""
    year: int
    energy_mwh: float
    revenue_market_pln: float = 0.0      # Σ gen × hourly price (or fixed-price × gen)
    cfd_payment_pln: float = 0.0         # two-way difference payments (+ top-up, − pay-back)
    capacity_rev_pln: float = 0.0
    balancing_rev_pln: float = 0.0
    fuel_cost_pln: float = 0.0
    co2_cost_pln: float = 0.0
    co2_t: float = 0.0
    vom_cost_pln: float = 0.0
    start_cost_pln: float = 0.0
    cycling_cost_pln: float = 0.0
    fund_cost_pln: float = 0.0           # nuclear decommissioning/waste fund (statutory PLN/MWh)
    fom_multiplier: float = 1.0          # e.g. single-unit phase ×1.5
    capture_price: float = 0.0
    extra: dict = field(default_factory=dict)


@dataclass
class PlantSpec:
    name: str
    net_mw: float
    capex_pln_per_kw: float
    construction_years: int
    spend_profile: Sequence[float]        # fractions per construction year (sum 1)
    cod_year: int
    life_years: int
    fom_pln_per_kw_yr: float
    other_capex_mpln: dict = field(default_factory=dict)   # {"pre_development": 500, "first_core": 550, "grid": 125}
    other_capex_timing: dict = field(default_factory=dict) # {"pre_development": "pre", "first_core": "last", "grid": "spread"}
    sustaining_capex_pln_per_mwh: float = 0.0              # treated as annual fixed at rated CF
    rated_cf_for_sustaining: float = 0.90
    depreciation_split: dict = field(default_factory=dict) # {kst_group: share}
    budowle_share_of_capex: float = 0.15
    property_tax_rate: float = 0.02
    property_tax_host_share: float = 1.0                    # nuclear: 0.5 (art. 50)
    staff_fte: float = 60
    staff_cost_kpln_per_fte: float = 200                     # loaded (employer ZUS incl.)
    licence_fee_share_of_revenue: float = 0.005
    fixed_other_pln_per_kw_yr: float = 0.0                   # e.g. Gaz-System exit capacity booking
    wacc_real: float = 0.07
    decommissioning_provision_mpln: float = 0.0              # gas: end-of-life demolition (nuclear via fund)
    construction_workers_peak: float = 0.0
    construction_worker_gross_pln_month: float = 9000.0
    construction_resident_share: float = 0.25
    is_nuclear: bool = False

    @property
    def fid_year(self) -> int:
        return self.cod_year - self.construction_years

    @property
    def overnight_mpln(self) -> float:
        return self.capex_pln_per_kw * self.net_mw * 1000 / 1e6


@dataclass
class TaxSpec:
    cit_rate: float = 0.19
    loss_carry_forward_years: int = 5
    loss_utilisation_cap: float = 0.5
    depreciation_rates: dict = field(default_factory=lambda: {
        "buildings_2_5pct": 0.025, "structures_4_5pct": 0.045, "reactor_14pct": 0.14,
        "turbine_bop_7pct": 0.07, "devices_10pct": 0.10})
    local_shares: dict = field(default_factory=lambda: {
        "pit_gmina": 0.070, "pit_powiat": 0.020, "pit_wojewodztwo": 0.0035,
        "cit_gmina": 0.016, "cit_powiat": 0.017, "cit_wojewodztwo": 0.023})
    zus_employee_share: float = 0.1371
    zus_employer_share: float = 0.2048
    pit_threshold: float = 120000.0
    pit_low: float = 0.12
    pit_high: float = 0.32
    pit_free_amount_tax: float = 3600.0
    resident_share_in_gmina: float = 0.60
    minimum_tax_enabled: bool = False
    minimum_tax_rate: float = 0.10
    minimum_tax_base_share_of_revenue: float = 0.015


@dataclass
class DebtSpec:
    gearing: float = 0.0          # share of capex funded by debt (0 = unlevered)
    tenor_years: int = 20
    rate_real: float = 0.035      # real interest (nominal − CPI)
    grace_years: int = 0


# ------------------------------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------------------------------
def pit_on_gross(gross_pln_year: float, tax: TaxSpec) -> tuple[float, float]:
    """Return (PIT tax, PIT income base) for one employee at a given gross annual salary."""
    income = gross_pln_year * (1 - tax.zus_employee_share)
    t = tax.pit_low * min(income, tax.pit_threshold) + tax.pit_high * max(income - tax.pit_threshold, 0)
    t = max(t - tax.pit_free_amount_tax, 0.0)
    return t, income


def npv(rate: float, cf: np.ndarray, t0: int = 0) -> float:
    t = np.arange(len(cf)) - t0
    return float((cf / (1 + rate) ** t).sum())


def irr(cf: np.ndarray, lo: float = -0.5, hi: float = 1.0) -> float | None:
    f = lambda r: npv(r, cf)
    try:
        if f(lo) * f(hi) > 0:
            return None
        return float(brentq(f, lo, hi, maxiter=200))
    except Exception:  # noqa: BLE001
        return None


# ------------------------------------------------------------------------------------------
# Cash-flow engine
# ------------------------------------------------------------------------------------------
def build_cashflow(spec: PlantSpec, op_years: Sequence[OperatingYear], tax: TaxSpec | None = None,
                   debt: DebtSpec | None = None, eua_pln_per_t_by_year: dict[int, float] | None = None) -> pd.DataFrame:
    tax = tax or TaxSpec()
    debt = debt or DebtSpec()
    ops = {o.year: o for o in op_years}
    y0 = spec.fid_year
    y_end = spec.cod_year + spec.life_years - 1
    years = np.arange(y0, y_end + 1)
    n = len(years)
    df = pd.DataFrame(index=years)
    df.index.name = "year"
    z = np.zeros(n)

    # ---- CAPEX -------------------------------------------------------------------------
    capex = z.copy()
    prof = np.asarray(spec.spend_profile, dtype=float)
    prof = prof / prof.sum()
    for i, f in enumerate(prof):
        capex[i] += spec.overnight_mpln * f
    other = z.copy()
    for k, v in spec.other_capex_mpln.items():
        timing = spec.other_capex_timing.get(k, "spread")
        if timing == "pre":                        # spread over 2 years before FID … keep at FID (t=0)
            other[0] += v
        elif timing == "last":                     # last construction year (e.g. first core)
            other[spec.construction_years - 1] += v
        else:
            for i, f in enumerate(prof):
                other[i] += v * f
    df["capex"] = capex
    df["other_capex"] = other
    df["capex_total"] = capex + other

    # ---- Operations --------------------------------------------------------------------
    cols = ["energy_mwh", "revenue_market", "cfd_payment", "capacity_rev", "balancing_rev", "fuel", "co2",
            "co2_t", "vom", "start", "cycling", "fund", "fom", "sustaining", "property_tax", "licence_fee",
            "fixed_other", "staff_cost"]
    for c in cols:
        df[c] = 0.0
    op_flag = np.zeros(n, dtype=bool)
    for i, y in enumerate(years):
        if y in ops:
            o = ops[y]
            op_flag[i] = True
            m = 1e-6
            df.loc[y, "energy_mwh"] = o.energy_mwh
            df.loc[y, "revenue_market"] = o.revenue_market_pln * m
            df.loc[y, "cfd_payment"] = o.cfd_payment_pln * m
            df.loc[y, "capacity_rev"] = o.capacity_rev_pln * m
            df.loc[y, "balancing_rev"] = o.balancing_rev_pln * m
            df.loc[y, "fuel"] = o.fuel_cost_pln * m
            df.loc[y, "co2"] = o.co2_cost_pln * m
            df.loc[y, "co2_t"] = o.co2_t
            df.loc[y, "vom"] = o.vom_cost_pln * m
            df.loc[y, "start"] = o.start_cost_pln * m
            df.loc[y, "cycling"] = o.cycling_cost_pln * m
            df.loc[y, "fund"] = o.fund_cost_pln * m
            fom = spec.fom_pln_per_kw_yr * spec.net_mw * 1000 * m * o.fom_multiplier
            df.loc[y, "fom"] = fom
            df.loc[y, "staff_cost"] = spec.staff_fte * spec.staff_cost_kpln_per_fte * 1e-3   # memo: inside FOM
            df.loc[y, "sustaining"] = spec.sustaining_capex_pln_per_mwh * spec.net_mw * 8760 * spec.rated_cf_for_sustaining * m
            df.loc[y, "fixed_other"] = spec.fixed_other_pln_per_kw_yr * spec.net_mw * 1000 * m
    df["revenue"] = df["revenue_market"] + df["cfd_payment"] + df["capacity_rev"] + df["balancing_rev"]
    # property tax on budowle: 2 % of initial value, not depreciated (tax base = initial value)
    budowle_value = spec.overnight_mpln * spec.budowle_share_of_capex
    df.loc[op_flag, "property_tax"] = spec.property_tax_rate * budowle_value
    df.loc[op_flag, "licence_fee"] = spec.licence_fee_share_of_revenue * df.loc[op_flag, "revenue"].clip(lower=0)
    df["opex"] = (df["fuel"] + df["co2"] + df["vom"] + df["start"] + df["cycling"] + df["fund"] + df["fom"]
                  + df["sustaining"] + df["property_tax"] + df["licence_fee"] + df["fixed_other"])
    df["ebitda"] = df["revenue"] - df["opex"]

    # ---- Tax depreciation (KŚT straight line from COD) ------------------------------------
    dep = z.copy()
    cap_base = df["capex_total"].sum()      # first core + development + grid capitalised
    i_cod = int(np.where(years == spec.cod_year)[0][0])
    for grp, share in spec.depreciation_split.items():
        rate = tax.depreciation_rates[grp]
        amount = cap_base * share
        yrs = int(np.ceil(1 / rate - 1e-9))
        per = amount * rate
        for k in range(yrs):
            if i_cod + k < n:
                dep[i_cod + k] += min(per, amount - per * k)
    # sustaining capex expensed as incurred (conservative simplification); demolition at end of life
    decom = z.copy()
    if spec.decommissioning_provision_mpln:
        decom[-1] = spec.decommissioning_provision_mpln
    df["depreciation_tax"] = dep
    df["decommissioning"] = decom
    df["ebit_tax"] = df["ebitda"] - df["depreciation_tax"] - df["decommissioning"]

    # ---- Debt overlay (before tax: interest is deductible) -----------------------------------
    draw = z.copy(); interest = z.copy(); principal = z.copy(); balance = 0.0
    if debt.gearing > 0:
        for i in range(n):
            if years[i] < spec.cod_year:
                d = debt.gearing * df["capex_total"].iloc[i]
                idc = balance * debt.rate_real
                draw[i] = d + idc                 # IDC capitalised (rolled up)
                balance += d + idc
            else:
                k = years[i] - spec.cod_year
                if k < debt.grace_years:
                    interest[i] = balance * debt.rate_real
                elif k < debt.grace_years + debt.tenor_years:
                    r = debt.rate_real
                    nrem = debt.tenor_years - (k - debt.grace_years)
                    ann = balance * r / (1 - (1 + r) ** (-nrem)) if r > 0 else balance / nrem
                    interest[i] = balance * r
                    principal[i] = ann - interest[i]
                    balance -= principal[i]
    df["debt_draw"] = draw
    df["interest"] = interest
    df["principal"] = principal
    df["debt_service"] = interest + principal

    # ---- CIT with loss carry-forward (5 yrs, ≤50 % of each loss per year) ----------------------
    cit = z.copy(); taxable = z.copy(); losses: list[list[float]] = []  # [year_idx, remaining]
    for i in range(n):
        base = df["ebit_tax"].iloc[i] - interest[i]
        if base <= 0:
            if base < 0:
                losses.append([i, -base, -base])   # idx, remaining, original
            taxable[i] = base
            continue
        use = 0.0
        for L in losses:
            if i - L[0] > tax.loss_carry_forward_years or L[1] <= 0:
                continue
            u = min(L[1], tax.loss_utilisation_cap * L[2], base - use)
            L[1] -= u
            use += u
            if use >= base:
                break
        taxable[i] = base - use
        cit[i] = tax.cit_rate * taxable[i]
        if tax.minimum_tax_enabled and op_flag[i] and taxable[i] / max(df["revenue"].iloc[i], 1e-9) <= 0.02 \
                and (years[i] - spec.cod_year) >= 3:
            cit[i] = max(cit[i], tax.minimum_tax_rate * tax.minimum_tax_base_share_of_revenue * df["revenue"].iloc[i])
    df["taxable_income"] = taxable
    df["cit"] = cit

    # ---- Cash flows --------------------------------------------------------------------------
    df["fcf_pretax"] = df["ebitda"] - df["capex_total"] - df["decommissioning"]
    df["fcf_posttax"] = df["fcf_pretax"] - df["cit"]
    df["equity_cf"] = df["fcf_posttax"] + df["debt_draw"] - df["debt_service"]
    with np.errstate(divide="ignore", invalid="ignore"):
        df["dscr"] = np.where(df["debt_service"] > 0, (df["ebitda"] - df["cit"]) / df["debt_service"], np.nan)

    # ---- Local & state fiscal flows ------------------------------------------------------------
    ls = tax.local_shares
    df["local_property_tax_host"] = df["property_tax"] * spec.property_tax_host_share
    df["local_property_tax_neighbours"] = df["property_tax"] * (1 - spec.property_tax_host_share)
    pos_inc = df["taxable_income"].clip(lower=0)
    df["local_cit_gmina"] = pos_inc * ls["cit_gmina"]
    df["local_cit_powiat"] = pos_inc * ls["cit_powiat"]
    df["local_cit_wojewodztwo"] = pos_inc * ls["cit_wojewodztwo"]
    # operations staff PIT
    gross_per_fte = spec.staff_cost_kpln_per_fte * 1000 / (1 + tax.zus_employer_share)
    pit_t, pit_base = pit_on_gross(gross_per_fte, tax)
    staff_income_m = spec.staff_fte * pit_base * 1e-6
    df["pit_paid_staff"] = 0.0
    df.loc[op_flag, "pit_paid_staff"] = spec.staff_fte * pit_t * 1e-6
    df["local_pit_gmina"] = 0.0; df["local_pit_powiat"] = 0.0; df["local_pit_wojewodztwo"] = 0.0
    df.loc[op_flag, "local_pit_gmina"] = staff_income_m * ls["pit_gmina"] * tax.resident_share_in_gmina
    df.loc[op_flag, "local_pit_powiat"] = staff_income_m * ls["pit_powiat"] * tax.resident_share_in_gmina
    df.loc[op_flag, "local_pit_wojewodztwo"] = staff_income_m * ls["pit_wojewodztwo"] * tax.resident_share_in_gmina
    # construction-phase PIT (workers × spend profile)
    if spec.construction_workers_peak > 0:
        cw_gross = spec.construction_worker_gross_pln_month * 12
        _, cw_base = pit_on_gross(cw_gross, tax)
        for i, f in enumerate(prof):
            workers = spec.construction_workers_peak * f / prof.max()
            inc_m = workers * cw_base * 1e-6
            df.iloc[i, df.columns.get_loc("local_pit_gmina")] += inc_m * ls["pit_gmina"] * spec.construction_resident_share
            df.iloc[i, df.columns.get_loc("local_pit_powiat")] += inc_m * ls["pit_powiat"] * spec.construction_resident_share
    df["local_total"] = (df["local_property_tax_host"] + df["local_property_tax_neighbours"] + df["local_cit_gmina"]
                         + df["local_cit_powiat"] + df["local_cit_wojewodztwo"] + df["local_pit_gmina"]
                         + df["local_pit_powiat"] + df["local_pit_wojewodztwo"])
    df["state_cit"] = df["cit"]
    df["state_fund_contribution"] = df["fund"]
    # EUA cost of a Polish plant is (largely) auction revenue of the Polish state → fiscal transfer, not a loss to PL
    df["state_eua_revenue"] = df["co2"]
    df["cfd_cost_to_state"] = df["cfd_payment"]
    df["operating"] = op_flag
    return df


# ------------------------------------------------------------------------------------------
# KPIs
# ------------------------------------------------------------------------------------------
def kpis(df: pd.DataFrame, spec: PlantSpec, common_rate: float = 0.07) -> dict:
    r = spec.wacc_real
    cf_post = df["fcf_posttax"].values
    cf_pre = df["fcf_pretax"].values
    pv_energy = npv(r, df["energy_mwh"].values)
    pv_cost = npv(r, (df["capex_total"] + df["opex"] + df["decommissioning"]).values)
    pv_cost_ex_co2 = npv(r, (df["capex_total"] + df["opex"] - df["co2"] + df["decommissioning"]).values)
    pv_cost_post_tax = pv_cost + npv(r, df["cit"].values)
    pv_rev = npv(r, df["revenue"].values)
    pv_capex = npv(r, df["capex_total"].values)
    out = {
        "name": spec.name,
        "net_mw": spec.net_mw,
        "overnight_mpln": spec.overnight_mpln,
        "capex_total_mpln": float(df["capex_total"].sum()),
        "wacc_real": r,
        "npv_project_posttax_mpln": npv(r, cf_post),
        "npv_project_pretax_mpln": npv(r, cf_pre),
        "npv_at_common_rate_mpln": npv(common_rate, cf_post),
        "irr_project_posttax": irr(cf_post),
        "irr_project_pretax": irr(cf_pre),
        "lcoe_pln_per_mwh": pv_cost * 1e6 / pv_energy if pv_energy > 0 else np.nan,
        "lcoe_ex_co2_pln_per_mwh": pv_cost_ex_co2 * 1e6 / pv_energy if pv_energy > 0 else np.nan,
        "lcoe_capex_component": pv_capex * 1e6 / pv_energy if pv_energy > 0 else np.nan,
        "lcoe_post_tax_pln_per_mwh": pv_cost_post_tax * 1e6 / pv_energy if pv_energy > 0 else np.nan,
        "levelised_revenue_pln_per_mwh": pv_rev * 1e6 / pv_energy if pv_energy > 0 else np.nan,
        "energy_twh_life": df["energy_mwh"].sum() / 1e6,
        "avg_capacity_factor": float(df.loc[df["operating"], "energy_mwh"].mean() / (spec.net_mw * 8760)) if df["operating"].any() else np.nan,
        "avg_capture_price": float(df.loc[df["operating"], "revenue_market"].sum() * 1e6 / max(df["energy_mwh"].sum(), 1)),
        "cfd_payments_total_mpln": float(df["cfd_payment"].sum()),
        "cfd_payments_pv_mpln": npv(r, df["cfd_payment"].values),
        "co2_mt_life": df["co2_t"].sum() / 1e6,
        "local_revenue_total_mpln": float(df["local_total"].sum()),
        "local_revenue_avg_op_year_mpln": float(df.loc[df["operating"], "local_total"].mean()) if df["operating"].any() else 0.0,
        "local_property_tax_host_avg_mpln": float(df.loc[df["operating"], "local_property_tax_host"].mean()) if df["operating"].any() else 0.0,
        "state_cit_total_mpln": float(df["cit"].sum()),
        "state_eua_total_mpln": float(df["co2"].sum()),
        "payback_year": _payback(df),
        "equity_irr": irr(df["equity_cf"].values) if (df["debt_draw"] > 0).any() else None,
        "min_dscr": float(np.nanmin(df["dscr"].values)) if np.isfinite(df["dscr"].values).any() else None,
    }
    return out


def _payback(df: pd.DataFrame) -> int | None:
    cum = df["fcf_posttax"].cumsum()
    hit = cum[cum > 0]
    return int(hit.index[0]) if len(hit) else None


def breakeven_price_uplift(spec: PlantSpec, op_years: Sequence[OperatingYear], tax: TaxSpec,
                           target_npv: float = 0.0, lo: float = -600, hi: float = 2000) -> float:
    """Constant real PLN/MWh added to every MWh's revenue so that post-tax project NPV = target.
    For a CfD case this is the strike-price adjustment; for a merchant case the required price premium."""
    def f(delta):
        ops2 = []
        for o in op_years:
            o2 = OperatingYear(**{**o.__dict__})
            o2.revenue_market_pln = o.revenue_market_pln + delta * o.energy_mwh
            ops2.append(o2)
        df = build_cashflow(spec, ops2, tax)
        return npv(spec.wacc_real, df["fcf_posttax"].values) - target_npv
    return float(brentq(f, lo, hi, xtol=0.05))


def breakeven_capex(spec: PlantSpec, op_years: Sequence[OperatingYear], tax: TaxSpec,
                    lo: float = 2000, hi: float = 120000) -> float | None:
    """Overnight PLN/kW at which post-tax NPV = 0 given the revenue stream."""
    def f(c):
        s2 = PlantSpec(**{**spec.__dict__, "capex_pln_per_kw": c})
        df = build_cashflow(s2, op_years, tax)
        return npv(spec.wacc_real, df["fcf_posttax"].values)
    try:
        if f(lo) * f(hi) > 0:
            return None
        return float(brentq(f, lo, hi, xtol=10))
    except Exception:  # noqa: BLE001
        return None
