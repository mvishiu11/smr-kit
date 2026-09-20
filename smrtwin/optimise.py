"""Optimisation and uncertainty layer.

1. **Break-even analysis** (root finding, Brent): the CfD strike, capex, or capacity payment at
   which post-tax project NPV = 0 for each technology — the "alternative cost" of firm capacity.
2. **Portfolio optimum**: minimise the net cost of adding ≥ 300 MW of firm (de-rated) capacity to the
   Polish system, choosing integer counts of SMR / CCGT / OCGT / engine blocks.  Because every asset
   is a price-taker its NPV is additive, so the problem is a small integer programme solved by
   enumeration; results are reported both merchant-only and with a capacity payment.
3. **Monte Carlo** over the joint uncertainty (capex, construction delay, price level, gas, EUA,
   capacity factor, WACC) with Latin-hypercube sampling; uses the fast dispatch rules.
4. **Tornado** one-at-a-time sensitivities.
"""
from __future__ import annotations

import copy
import itertools
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import brentq
from scipy.stats import qmc

from . import config, finance, gas, scenarios as sc, smr


# ------------------------------------------------------------------------------------------
# 1. Break-even
# ------------------------------------------------------------------------------------------
def breakeven_strike(a: dict, mt: sc.MarketTwin, res: dict | None = None) -> dict:
    """CfD strike (EUR/MWh) at which the SMR's post-tax NPV = 0, plus break-even capex at the
    assumed strike."""
    res = res or sc.run_scenario("S1a_smr_cfd", a, mt)
    tax = sc.tax_spec(a)
    uplift = finance.breakeven_price_uplift(res["spec"], res["ops"], tax)
    # the uplift applies to all MWh incl. post-tenor years; convert to an equivalent strike over the tenor
    tenor = int(a["smr"]["cfd"]["tenor_years"])
    r = res["spec"].wacc_real
    e = np.array([o.energy_mwh for o in res["ops"]])
    t = np.arange(len(e)) + res["spec"].construction_years
    disc = 1 / (1 + r) ** t
    ratio = (e * disc).sum() / (e[:tenor] * disc[:tenor]).sum()
    strike_assumed = res["kpis"].get("strike_pln", a["smr"]["cfd"]["strike_eur_per_mwh"] * a["meta"]["eur_pln"])
    strike_pln = strike_assumed + uplift * ratio
    be_capex = finance.breakeven_capex(res["spec"], res["ops"], tax)
    return {"breakeven_strike_pln": strike_pln, "breakeven_strike_eur": strike_pln / a["meta"]["eur_pln"],
            "uplift_pln_per_mwh": uplift, "breakeven_capex_pln_per_kw": be_capex,
            "assumed_strike_eur": strike_assumed / a["meta"]["eur_pln"], "assumed_capex_pln_per_kw": res["spec"].capex_pln_per_kw}


def required_support(res: dict, a: dict) -> dict:
    """For any scenario: constant PLN/MWh premium and PLN/kW-yr capacity payment needed for NPV = 0."""
    tax = sc.tax_spec(a)
    spec, ops = res["spec"], res["ops"]
    uplift = finance.breakeven_price_uplift(spec, ops, tax)
    # capacity payment: PLN/kW-yr over the whole life (levelised)
    def f(cp):
        ops2 = []
        for o in ops:
            o2 = finance.OperatingYear(**{**o.__dict__})
            o2.capacity_rev_pln = o.capacity_rev_pln + cp * spec.net_mw * 1000
            ops2.append(o2)
        df = finance.build_cashflow(spec, ops2, tax)
        return finance.npv(spec.wacc_real, df["fcf_posttax"].values)
    try:
        cp = float(brentq(f, -2000, 20000, xtol=0.5))
    except Exception:  # noqa: BLE001
        cp = np.nan
    return {"required_premium_pln_per_mwh": uplift, "required_capacity_payment_pln_per_kw_yr": cp,
            "required_capacity_payment_15yr_pln_per_kw_yr": cp * _lev_ratio(spec, len(ops), 15)}


def _lev_ratio(spec: finance.PlantSpec, n_years: int, horizon: int) -> float:
    r = spec.wacc_real
    t = np.arange(n_years) + spec.construction_years
    d = 1 / (1 + r) ** t
    return d.sum() / d[:horizon].sum()


# ------------------------------------------------------------------------------------------
# 2. Portfolio optimum
# ------------------------------------------------------------------------------------------
def portfolio_optimum(a: dict, mt: sc.MarketTwin, unit_results: dict[str, dict], firm_target_mw: float = 300.0,
                      capacity_payment_pln_per_kw_yr: float = 0.0, max_units: dict | None = None) -> pd.DataFrame:
    """Enumerate integer portfolios of {smr, ccgt, ocgt_pair, engine_block4} meeting the firm-capacity
    target and rank by NPV (= − net system cost vs buying from the market)."""
    cm = a["market"]["capacity_market"]
    kwd = {"smr": cm["kwd_nuclear"], "ccgt": cm["kwd_ccgt"], "ocgt": cm["kwd_ocgt"], "engine": cm["kwd_ocgt"]}
    max_units = max_units or {"smr": 1, "ccgt": 2, "ocgt": 4, "engine": 4}
    rows = []
    keys = list(unit_results)
    for counts in itertools.product(*[range(max_units[k] + 1) for k in keys]):
        firm = sum(c * unit_results[k]["spec"].net_mw * kwd[k] for c, k in zip(counts, keys))
        if firm < firm_target_mw * kwd["smr"] - 1e-6 or firm > 1.6 * firm_target_mw or sum(counts) == 0:
            continue
        npv_m = sum(c * unit_results[k]["kpis"]["npv_project_posttax_mpln"] for c, k in zip(counts, keys))
        mw = sum(c * unit_results[k]["spec"].net_mw for c, k in zip(counts, keys))
        cap_pay = 0.0
        if capacity_payment_pln_per_kw_yr:
            for c, k in zip(counts, keys):
                spec = unit_results[k]["spec"]
                pv_ann = sum(1 / (1 + spec.wacc_real) ** (spec.construction_years + t) for t in range(min(15, spec.life_years)))
                cap_pay += c * capacity_payment_pln_per_kw_yr * spec.net_mw * 1000 * kwd[k] * pv_ann * (1 - a["tax"]["cit_rate"]) / 1e6
        energy = sum(c * unit_results[k]["kpis"]["energy_twh_life"] for c, k in zip(counts, keys))
        co2 = sum(c * unit_results[k]["kpis"]["co2_mt_life"] for c, k in zip(counts, keys))
        capex = sum(c * unit_results[k]["kpis"]["capex_total_mpln"] for c, k in zip(counts, keys))
        rows.append({**{f"n_{k}": c for c, k in zip(counts, keys)}, "mw": mw, "firm_mw": firm, "capex_mpln": capex,
                     "npv_merchant_mpln": npv_m, "npv_with_cap_payment_mpln": npv_m + cap_pay,
                     "net_cost_per_firm_mw_mpln": -(npv_m + cap_pay) / firm,
                     "energy_twh_life": energy, "co2_mt_life": co2})
    df = pd.DataFrame(rows).sort_values("net_cost_per_firm_mw_mpln").reset_index(drop=True)
    return df


# ------------------------------------------------------------------------------------------
# 3. Monte Carlo
# ------------------------------------------------------------------------------------------
MC_FACTORS = {
    # name: (low, central, high) multiplier or additive; sampled as triangular in LHS space
    "capex_mult": (0.75, 1.0, 1.45),
    "delay_years": (0, 1, 3),
    "price_mult": (0.80, 1.0, 1.25),
    "gas_mult": (0.75, 1.0, 1.40),
    "eua_mult": (0.70, 1.0, 1.30),
    "cf_adj": (-0.05, 0.0, 0.03),
    "wacc_adj": (-0.01, 0.0, 0.015),
    "fom_mult": (0.8, 1.0, 1.5),
}


def _tri(u: np.ndarray, lo: float, c: float, hi: float) -> np.ndarray:
    fc = (c - lo) / (hi - lo)
    return np.where(u < fc, lo + np.sqrt(u * (hi - lo) * (c - lo)), hi - np.sqrt((1 - u) * (hi - lo) * (hi - c)))


def monte_carlo(a_raw: dict, n: int = 300, seed: int = 7, scenarios: tuple[str, ...] = ("S1a_smr_cfd", "S2_smr_dynamic", "S3a_gas_ccgt", "S3b_gas_ocgt"),
                verbose: bool = False) -> pd.DataFrame:
    sampler = qmc.LatinHypercube(d=len(MC_FACTORS), seed=seed)
    U = sampler.random(n)
    draws = {k: _tri(U[:, i], *v) for i, (k, v) in enumerate(MC_FACTORS.items())}
    base = config.resolve(a_raw, "central")
    mt0 = sc.MarketTwin(base)
    rows = []
    for j in range(n):
        a = copy.deepcopy(base)
        d = {k: float(v[j]) for k, v in draws.items()}
        a["smr"]["capex_pln_per_kw"] *= d["capex_mult"]
        for u in a["gas"]["units"].values():
            u["capex_pln_per_kw"] *= 0.5 + 0.5 * d["capex_mult"]         # gas capex less uncertain than nuclear
            u["fom_pln_per_kw_yr"] *= d["fom_mult"]
        a["smr"]["fom_pln_per_kw_yr"] *= d["fom_mult"]
        a["smr"]["cod_year"] = int(base["smr"]["cod_year"] + round(d["delay_years"]))
        a["smr"]["construction_years"] = int(base["smr"]["construction_years"] + round(d["delay_years"]))
        a["market"]["price_path"]["values"] = [v * d["price_mult"] for v in base["market"]["price_path"]["values"]]
        a["market"]["gas_price_path"]["values"] = [v * d["gas_mult"] for v in base["market"]["gas_price_path"]["values"]]
        a["market"]["eua_path"]["values"] = [v * d["eua_mult"] for v in base["market"]["eua_path"]["values"]]
        a["smr"]["availability"]["forced_outage_rate"] = float(np.clip(base["smr"]["availability"]["forced_outage_rate"] - d["cf_adj"], 0.005, 0.3))
        for k in a["macro"]["wacc_real"]:
            a["macro"]["wacc_real"][k] += d["wacc_adj"]
        mt = sc.MarketTwin(a)
        mt.sm = mt0.sm; mt.ref = mt0.ref   # reuse the shape (saves re-reading history)
        rec = {"draw": j, **d}
        for name in scenarios:
            try:
                r = _fast_scenario(name, a, mt)
                rec[f"npv_{name}"] = r["kpis"]["npv_project_posttax_mpln"]
                rec[f"lcoe_{name}"] = r["kpis"]["lcoe_pln_per_mwh"]
                rec[f"irr_{name}"] = r["kpis"]["irr_project_posttax"]
            except Exception as e:  # noqa: BLE001
                rec[f"npv_{name}"] = np.nan
                if verbose:
                    print("draw", j, name, "failed:", e)
        rows.append(rec)
        if verbose and j % 25 == 0:
            print("MC draw", j, {k: round(v, 3) for k, v in d.items()}, {k: round(v) for k, v in rec.items() if k.startswith("npv_")})
    return pd.DataFrame(rows)


def _fast_scenario(name: str, a: dict, mt: sc.MarketTwin) -> dict:
    """Same as scenarios.run_scenario but with the closed-form / heuristic dispatch rules."""
    cfg = sc.SCENARIOS[name]
    tax = sc.tax_spec(a)
    if cfg["kind"] == "smr":
        # monkey-patch: bang-bang dispatch instead of the LP (ramp/cycling ignored, <0.2 % NPV effect)
        orig = smr.dispatch_flexible
        smr.dispatch_flexible = lambda unit, price, avail, ramp=True: orig(unit, price, avail, ramp=False)
        try:
            strike = a["smr"]["cfd"]["strike_eur_per_mwh"] * a["meta"]["eur_pln"]
            fixed = mt.reference_mean
            spec, ops, _ = sc.run_smr(a, mt, cfg["mode"], strike_pln=strike, fixed_price=fixed)
        finally:
            smr.dispatch_flexible = orig
    else:
        orig = gas.dispatch_portfolio
        gas.dispatch_portfolio = lambda units, p, g, e, block_hours=168, outage_start_hour=None: gas.dispatch_heuristic(units, p, g, e, outage_start_hour)
        try:
            spec, ops, _ = sc.run_gas(a, mt, cfg["tech"], cfg["n"], cfg.get("capacity_market", False))
        finally:
            gas.dispatch_portfolio = orig
    df = finance.build_cashflow(spec, ops, tax)
    return {"spec": spec, "ops": ops, "cashflow": df, "kpis": finance.kpis(df, spec)}


# ------------------------------------------------------------------------------------------
# 4. Tornado
# ------------------------------------------------------------------------------------------
TORNADO = {
    "SMR overnight capex": ("smr.capex_pln_per_kw", "smr"),
    "SMR WACC (real)": ("macro.wacc_real.smr_cfd", "macro"),
    "Electricity price path": ("market.price_path", "market"),
    "CfD strike": ("smr.cfd.strike_eur_per_mwh", "smr"),
    "SMR fixed O&M": ("smr.fom_pln_per_kw_yr", "smr"),
    "SMR forced-outage rate": ("smr.availability.forced_outage_rate", "smr"),
    "Construction duration": ("smr.construction_years", "smr"),
    "Nuclear fuel price": ("smr.fuel_pln_per_mwh", "smr"),
    "Decommissioning fund rate": ("smr.decommissioning_fund_pln_per_mwh", "smr"),
    "Property-tax base (budowle share)": ("smr.property_tax.budowle_share_of_capex", "smr"),
}
TORNADO_GAS = {
    "CCGT capex": ("gas.units.ccgt.capex_pln_per_kw", "gas"),
    "Gas price path": ("market.gas_price_path", "market"),
    "EUA price path": ("market.eua_path", "market"),
    "Electricity price path": ("market.price_path", "market"),
    "Gas WACC (real)": ("macro.wacc_real.gas", "macro"),
    "CCGT efficiency": ("gas.units.ccgt.eta_full_lhv", "gas"),
    "CCGT fixed O&M": ("gas.units.ccgt.fom_pln_per_kw_yr", "gas"),
}


def _get(raw: dict, path: str):
    d = raw
    for p in path.split("."):
        d = d[p]
    return d


def tornado(a_raw: dict, scenario: str, params: dict, fast: bool = True) -> pd.DataFrame:
    base = config.resolve(a_raw, "central")
    mt = sc.MarketTwin(base)
    run = _fast_scenario if fast else (lambda n, a, m: sc.run_scenario(n, a, m))
    b = run(scenario, base, mt)["kpis"]["npv_project_posttax_mpln"]
    rows = []
    for label, (path, _) in params.items():
        vals = {}
        for case in ("low", "high"):
            a = copy.deepcopy(base)
            node = _get(a_raw, path)
            # path node: dict with low/central/high lists; triplet: list of 3
            if isinstance(node, dict) and "anchor_years" in node:
                _set(a, path, {"anchor_years": node["anchor_years"], "values": node[case]})
            elif isinstance(node, list) and len(node) == 3:
                _set(a, path, node[0 if case == "low" else 2])
            else:
                continue
            m2 = sc.MarketTwin(a); m2.sm = mt.sm; m2.ref = mt.ref
            vals[case] = run(scenario, a, m2)["kpis"]["npv_project_posttax_mpln"]
        if vals:
            rows.append({"parameter": label, "npv_low_case": vals.get("low"), "npv_high_case": vals.get("high"), "npv_base": b,
                         "swing": abs(vals.get("high", b) - vals.get("low", b))})
    return pd.DataFrame(rows).sort_values("swing", ascending=False).reset_index(drop=True)


def _set(a: dict, path: str, val) -> None:
    d = a
    parts = path.split(".")
    for p in parts[:-1]:
        d = d[p]
    d[parts[-1]] = val
