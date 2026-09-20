"""Scenario definitions and the year-by-year simulation loop.

Scenarios (all price-taker on the Polish day-ahead market, hourly, perfect foresight):

    S1a  smr_cfd          BWRX-300, two-way CfD (strike 115/125/135 EUR/MWh, PEJ-template design:
                          daily TGeBase reference, 40-yr tenor, then merchant).  Dispatch on the
                          *effective* hourly price = market price + (strike − daily reference).
    S1b  smr_fixed        BWRX-300, fixed real price for life = last-12-month average spot
                          (a PPA / regulated-tariff proxy); must-run.
    S1c  smr_merchant     BWRX-300, merchant baseload (must-run at availability) — comparator.
    S2   smr_dynamic      BWRX-300, merchant, load-following 50–100 % with ramp limits, LP dispatch.
    S3a  gas_ccgt         ~300 MW CCGT 1+1, merchant, unit-commitment MILP (0–100 %, min load 40 %).
    S3b  gas_ocgt         2 × 150 MW frame OCGT peakers, merchant.
    S3c  gas_engines      4 × 76.5 MW blocks of reciprocating engines, merchant.
    S3d  gas_ccgt_cm      as S3a plus a 15-yr capacity-market contract (successor mechanism) —
                          sensitivity, not base case.

Each operating year gets its own 8,760-h price vector (reference-year shape re-anchored on the
annual mean path, with growing solar cannibalisation), its own monthly gas price and EUA price.
"""
from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

import numpy as np
import pandas as pd

from . import config, finance, gas, prices, smr

RESULTS = Path(__file__).resolve().parents[1] / "results"
MONTH_HOURS = [744, 672, 744, 720, 744, 720, 744, 744, 720, 744, 720, 744]
MONTH_OF_HOUR = np.repeat(np.arange(12), MONTH_HOURS)


# ------------------------------------------------------------------------------------------
# Market inputs per model year
# ------------------------------------------------------------------------------------------
class MarketTwin:
    def __init__(self, a: dict):
        self.a = a
        m = a["market"]
        self.ref = prices.reference_year(m["reference_window"])
        self.sm = prices.shape_model(self.ref)
        self.ref_end_year = int(self.ref.attrs["end"][:4])
        self.eur_pln = a["meta"]["eur_pln"]
        self.gas_month = np.asarray(m["gas_month_factor"])[MONTH_OF_HOUR]
        self._cache: dict[int, np.ndarray] = {}

    def annual_mean(self, year: int) -> float:
        m = self.a["market"]
        link = m.get("srmc_link", {})
        if link.get("enabled"):
            gas_p = config.path_value(m["gas_price_path"], year)
            eua = config.path_value(m["eua_path"], year) * self.eur_pln
            srmc = (gas_p + eua * m["gas_emission_factor_t_per_mwh_fuel"]) / link["eta"] + link["vom_pln_per_mwh"]
            return float(link["multiplier"] * srmc)
        return config.path_value(m["price_path"], year)

    def depression(self, year: int) -> float:
        c = self.a["market"]["cannibalisation"]
        if not c["enabled"]:
            return 0.0
        return float(min(c["growth_per_year"] * max(year - self.ref_end_year, 0), c["max_extra_depression"]))

    def price(self, year: int) -> np.ndarray:
        if year not in self._cache:
            self._cache[year] = prices.price_year(self.sm, self.annual_mean(year), self.depression(year))
        return self._cache[year]

    def gas_price(self, year: int) -> np.ndarray:
        return config.path_value(self.a["market"]["gas_price_path"], year) * self.gas_month

    def eua_pln(self, year: int) -> np.ndarray:
        return np.full(8760, config.path_value(self.a["market"]["eua_path"], year) * self.eur_pln)

    @property
    def reference_mean(self) -> float:
        return float(self.ref.mean())


# ------------------------------------------------------------------------------------------
# Plant construction from assumptions
# ------------------------------------------------------------------------------------------
def smr_spec(a: dict, wacc_key: str = "smr_cfd", name: str = "SMR") -> finance.PlantSpec:
    s = a["smr"]
    return finance.PlantSpec(
        name=name, net_mw=s["net_mw_cases"], capex_pln_per_kw=s["capex_pln_per_kw"],
        construction_years=int(s["construction_years"]), spend_profile=_rescale_profile(s["spend_profile_5yr"], int(s["construction_years"])),
        cod_year=int(s["cod_year"]), life_years=int(s["life_years"]), fom_pln_per_kw_yr=s["fom_pln_per_kw_yr"],
        other_capex_mpln={"pre_development": s["pre_development_mpln"], "first_core": s["first_core_mpln"],
                          "grid_connection": s["grid_connection_mpln"]},
        other_capex_timing={"pre_development": "pre", "first_core": "last", "grid_connection": "spread"},
        sustaining_capex_pln_per_mwh=s["sustaining_capex_pln_per_mwh"], rated_cf_for_sustaining=0.90,
        depreciation_split=s["depreciation_split"], budowle_share_of_capex=s["property_tax"]["budowle_share_of_capex"],
        property_tax_rate=s["property_tax"]["rate"], property_tax_host_share=s["property_tax"]["host_gmina_share"],
        staff_fte=s["staff_fte_per_unit"], staff_cost_kpln_per_fte=s["staff_cost_kpln_per_fte"],
        licence_fee_share_of_revenue=a["gas"]["licence_fee_share_of_revenue"], wacc_real=a["macro"]["wacc_real"][wacc_key],
        construction_workers_peak=a["tax"]["construction_local_pit"]["peak_construction_workers_per_unit"] if a["tax"]["construction_local_pit"]["enabled"] else 0,
        construction_worker_gross_pln_month=a["tax"]["construction_local_pit"]["avg_worker_gross_pln_per_month"],
        construction_resident_share=a["tax"]["construction_local_pit"]["resident_share_in_gmina"], is_nuclear=True)


def gas_spec(a: dict, kind: str, n_units: int = 1, name: str | None = None) -> tuple[finance.PlantSpec, list[gas.GasUnit]]:
    g = a["gas"]["units"][kind]
    net = g["net_mw"] * n_units
    spec = finance.PlantSpec(
        name=name or g["label"], net_mw=net, capex_pln_per_kw=g["capex_pln_per_kw"],
        construction_years=int(g["construction_years"]), spend_profile=g["spend_profile"], cod_year=int(a["gas"]["cod_year"]),
        life_years=int(g["life_years"]), fom_pln_per_kw_yr=g["fom_pln_per_kw_yr"],
        other_capex_mpln={"grid_connection": 0.35 * net}, other_capex_timing={"grid_connection": "spread"},   # ~350 PLN/kW proxy
        depreciation_split=g["depreciation_split"], budowle_share_of_capex=g["budowle_share_of_capex"],
        property_tax_rate=a["gas"]["property_tax_rate"], property_tax_host_share=1.0,
        staff_fte=g["staff_fte"] * (1 if kind == "ccgt" else n_units), staff_cost_kpln_per_fte=g["staff_cost_kpln_per_fte"],
        licence_fee_share_of_revenue=a["gas"]["licence_fee_share_of_revenue"], fixed_other_pln_per_kw_yr=g["gas_exit_tariff_pln_per_kw_yr"],
        wacc_real=a["macro"]["wacc_real"]["gas"], decommissioning_provision_mpln=0.05 * g["capex_pln_per_kw"] * net * 1e-3,
        construction_workers_peak=300 * (net / 300), construction_worker_gross_pln_month=a["tax"]["construction_local_pit"]["avg_worker_gross_pln_per_month"],
        construction_resident_share=a["tax"]["construction_local_pit"]["resident_share_in_gmina"])
    units = [gas.GasUnit(f"{kind}{i+1}", g["net_mw"], g["eta_full_lhv"], g["eta_min_load_lhv"], g["min_load"],
                         int(g["min_up_hours"]), int(g["min_down_hours"]), dict(g["start_cost_pln_per_mw"]),
                         int(g["start_hot_max_off_hours"]), int(g["start_warm_max_off_hours"]), g["start_fuel_mwh_per_mw"],
                         g["vom_pln_per_mwh"], g["availability"], int(g["planned_outage_weeks"]),
                         a["market"]["gas_emission_factor_t_per_mwh_fuel"]) for i in range(n_units)]
    return spec, units


def _rescale_profile(p5: list[float], years: int) -> list[float]:
    x5 = np.linspace(0, 1, len(p5) + 1)
    cum = np.concatenate([[0], np.cumsum(p5)])
    xn = np.linspace(0, 1, years + 1)
    c = np.interp(xn, x5, cum)
    return list(np.diff(c))


def smr_unit(a: dict) -> smr.SMRUnit:
    s = a["smr"]
    f = s["flexibility"]
    return smr.SMRUnit(net_mw=s["net_mw_cases"], thermal_mwt=s["thermal_mwt"], min_load=f["min_load"],
                       ramp_up_mw_per_h=0.35 * s["net_mw_cases"], ramp_down_mw_per_h=0.35 * s["net_mw_cases"],
                       fuel_pln_per_mwh=s["fuel_pln_per_mwh"], vom_pln_per_mwh=s["vom_pln_per_mwh"],
                       fund_pln_per_mwh=s["decommissioning_fund_pln_per_mwh"],
                       eff_penalty_pts_at_50=f["efficiency_penalty_pts_at_50pct"],
                       cycling_cost_pln_per_mw=f["cycling_cost_pln_per_mw_change"])


# ------------------------------------------------------------------------------------------
# SMR scenarios
# ------------------------------------------------------------------------------------------
def run_smr(a: dict, mt: MarketTwin, mode: str, strike_pln: float | None = None, fixed_price: float | None = None,
            verbose: bool = False) -> tuple[finance.PlantSpec, list[finance.OperatingYear], dict]:
    """mode ∈ {cfd, fixed, merchant, dynamic}."""
    s = a["smr"]
    unit = smr_unit(a)
    wacc_key = "smr_cfd" if mode in ("cfd", "fixed") else "smr_merchant"
    spec = smr_spec(a, wacc_key, name={"cfd": "SMR CfD", "fixed": "SMR fixed price", "merchant": "SMR merchant baseload",
                                       "dynamic": "SMR dynamic (50–100 %)"}[mode])
    av = s["availability"]
    fl = s["flexibility"]
    cfd = s["cfd"]
    ops, hourly_log = [], {}
    for k in range(spec.life_years):
        year = spec.cod_year + k
        p = mt.price(year)
        avail = smr.availability_profile(k, refuel_cycle_months=int(av["refuel_cycle_months"]),
                                         refuel_outage_days=av["refuel_outage_days"], major_days_per_10yr=av["major_inspection_days_per_10yr"],
                                         efor=av["forced_outage_rate"], outage_month=int(av["outage_month"]),
                                         foak_extra_efor=av["foak_first_years_extra_efor"])
        cfd_pay = 0.0
        if mode == "fixed":
            d = smr.dispatch_baseload(unit, np.full(8760, fixed_price), avail)
            rev_market = d.revenue_pln
        elif mode == "merchant":
            d = smr.dispatch_baseload(unit, p, avail)
            rev_market = d.revenue_pln
        elif mode == "dynamic":
            d = smr.dispatch_flexible(unit, p, avail)
            rev_market = d.revenue_pln
        elif mode == "cfd":
            in_tenor = k < int(cfd["tenor_years"])
            if in_tenor:
                ref = p.reshape(-1, 24).mean(axis=1).repeat(24) if cfd["reference"] == "daily_base" else p
                p_eff = p + (strike_pln - ref)
                # the plant follows the CfD-effective price (never below variable cost), else must-run
                d = smr.dispatch_flexible(unit, p_eff, avail)
                rev_market = float((d.gen_mwh * p).sum())
                cfd_pay = smr.cfd_settlement(d.gen_mwh, p, strike_pln, cfd["reference"], cfd["exclude_negative_hours"], cfd["two_way"])["cfd_payment_pln"]
            else:
                d = smr.dispatch_flexible(unit, p, avail)
                rev_market = d.revenue_pln
        else:
            raise ValueError(mode)
        gen = d.gen_mwh
        load = np.divide(gen, d.cap_mw, out=np.ones_like(gen), where=d.cap_mw > 0)
        eta_rel = unit.eta_rel(np.clip(load, unit.min_load, 1.0))
        fuel = float((gen * unit.fuel_pln_per_mwh / eta_rel).sum())
        ucf_loss = fl["load_following_ucf_loss"] if mode in ("dynamic", "cfd") else 0.0
        fom_mult = (s["single_unit_fom_multiplier"] if k < int(s["single_unit_years"]) else 1.0) * (1 + (fl["load_following_fom_uplift"] if mode in ("dynamic", "cfd") else 0.0))
        energy = float(gen.sum()) * (1 - ucf_loss)
        o = finance.OperatingYear(
            year=year, energy_mwh=energy, revenue_market_pln=rev_market * (1 - ucf_loss), cfd_payment_pln=cfd_pay * (1 - ucf_loss),
            capacity_rev_pln=a["market"]["capacity_market"]["price_pln_per_kw_yr"] * a["market"]["capacity_market"]["kwd_nuclear"] * spec.net_mw * 1000
            if k < a["market"]["capacity_market"]["contract_years"] else 0.0,
            fuel_cost_pln=fuel * (1 - ucf_loss), vom_cost_pln=energy * unit.vom_pln_per_mwh, cycling_cost_pln=d.cycling_cost_pln,
            fund_cost_pln=energy * unit.fund_pln_per_mwh, fom_multiplier=fom_mult, capture_price=d.capture_price,
            extra={"hours_at_min": d.hours_at_min, "curtailed_mwh": d.curtailed_mwh, "price_mean": float(p.mean()),
                   "neg_hours": int((p < 0).sum()), "avail_mean": float(avail.mean())})
        ops.append(o)
        if k in (0, 5, 10, 20, 40):
            hourly_log[year] = {"price": p, "gen": gen, "cap": d.cap_mw}
        if verbose:
            print(f"  {spec.name} {year}: E={energy/1e6:.3f} TWh capture={d.capture_price:.0f} mean={p.mean():.0f} cfd={cfd_pay/1e6:.0f} m")
    return spec, ops, hourly_log


# ------------------------------------------------------------------------------------------
# Gas scenarios
# ------------------------------------------------------------------------------------------
def run_gas(a: dict, mt: MarketTwin, kind: str, n_units: int = 1, capacity_market: bool = False,
            verbose: bool = False, name: str | None = None) -> tuple[finance.PlantSpec, list[finance.OperatingYear], dict]:
    spec, units = gas_spec(a, kind, n_units, name)
    cm = a["market"]["capacity_market"]
    kwd = {"ccgt": cm["kwd_ccgt"], "ocgt": cm["kwd_ocgt"], "engine": cm["kwd_ocgt"]}[kind]
    bal = a["market"]["balancing_pln_per_kw_yr"]["ccgt" if kind == "ccgt" else "ocgt"]
    ops, hourly_log = [], {}
    for k in range(spec.life_years):
        year = spec.cod_year + k
        p = mt.price(year)
        d = gas.dispatch_portfolio(units, p, mt.gas_price(year), mt.eua_pln(year))
        cap_rev = 0.0
        if capacity_market and k < 15:
            cap_rev = max(cm["price_pln_per_kw_yr"], 400.0) * kwd * spec.net_mw * 1000   # successor mechanism at ≥400 PLN/kW-yr
        o = finance.OperatingYear(
            year=year, energy_mwh=d.energy_mwh, revenue_market_pln=d.revenue_pln, capacity_rev_pln=cap_rev,
            balancing_rev_pln=bal * spec.net_mw * 1000, fuel_cost_pln=d.fuel_cost_pln, co2_cost_pln=d.co2_cost_pln, co2_t=d.co2_t,
            vom_cost_pln=d.vom_cost_pln, start_cost_pln=d.start_cost_pln, capture_price=d.capture_price,
            extra={"starts": d.starts, "running_hours": d.running_hours.tolist(), "price_mean": float(p.mean()),
                   "gas_mean": float(mt.gas_price(year).mean()), "eua": float(mt.eua_pln(year)[0]),
                   "srmc_full": gas.srmc(units[0], float(mt.gas_price(year).mean()), float(mt.eua_pln(year)[0]))})
        ops.append(o)
        if k in (0, 5, 10, 20):
            hourly_log[year] = {"price": p, "gen": d.gen_mwh, "on": d.on_by_unit.sum(axis=0)}
        if verbose:
            print(f"  {spec.name} {year}: E={d.energy_mwh/1e6:.3f} TWh CF={d.energy_mwh/(spec.net_mw*8760):.2f} capture={d.capture_price:.0f} "
                  f"srmc={o.extra['srmc_full']:.0f} margin={d.gross_margin_pln/1e6:.0f} m starts={d.starts}")
    return spec, ops, hourly_log


# ------------------------------------------------------------------------------------------
# Orchestration
# ------------------------------------------------------------------------------------------
SCENARIOS = {
    "S1a_smr_cfd": dict(kind="smr", mode="cfd"),
    "S1b_smr_fixed_spotavg": dict(kind="smr", mode="fixed"),
    "S1c_smr_merchant_baseload": dict(kind="smr", mode="merchant"),
    "S2_smr_dynamic": dict(kind="smr", mode="dynamic"),
    "S3a_gas_ccgt": dict(kind="gas", tech="ccgt", n=1),
    "S3b_gas_ocgt": dict(kind="gas", tech="ocgt", n=2),
    "S3c_gas_engines": dict(kind="gas", tech="engine", n=4),
    "S3d_gas_ccgt_capmarket": dict(kind="gas", tech="ccgt", n=1, capacity_market=True),
}


def tax_spec(a: dict) -> finance.TaxSpec:
    t = a["tax"]
    e = t["employee"]
    return finance.TaxSpec(cit_rate=t["cit_rate"], loss_carry_forward_years=int(t["loss_carry_forward_years"]),
                           loss_utilisation_cap=t["loss_utilisation_cap"], depreciation_rates=t["depreciation_rates"],
                           local_shares=t["local_shares_2025_system"], zus_employee_share=e["zus_employee_share"],
                           zus_employer_share=e["zus_employer_share"], pit_threshold=e["pit_bracket_threshold_pln"],
                           pit_low=e["pit_rate_low"], pit_high=e["pit_rate_high"], pit_free_amount_tax=e["pit_free_amount_tax_pln"],
                           resident_share_in_gmina=e["resident_share_in_gmina"], minimum_tax_enabled=t["minimum_tax"]["enabled"],
                           minimum_tax_rate=t["minimum_tax"]["rate"], minimum_tax_base_share_of_revenue=t["minimum_tax"]["base_share_of_revenue"])


def run_scenario(name: str, a: dict, mt: MarketTwin, verbose: bool = False, strike_eur: float | None = None) -> dict:
    cfg = SCENARIOS[name]
    tax = tax_spec(a)
    if cfg["kind"] == "smr":
        strike = (strike_eur if strike_eur is not None else a["smr"]["cfd"]["strike_eur_per_mwh"]) * a["meta"]["eur_pln"]
        fixed = mt.reference_mean if a["market"]["fixed_price_source"] == "reference_mean" else a["market"]["fixed_price_value_pln_per_mwh"]
        spec, ops, hourly = run_smr(a, mt, cfg["mode"], strike_pln=strike, fixed_price=fixed, verbose=verbose)
        meta = {"strike_pln": strike, "fixed_price_pln": fixed}
    else:
        spec, ops, hourly = run_gas(a, mt, cfg["tech"], cfg["n"], cfg.get("capacity_market", False), verbose=verbose)
        meta = {}
    df = finance.build_cashflow(spec, ops, tax)
    k = finance.kpis(df, spec)
    k.update(meta)
    k["scenario"] = name
    k["case"] = a["_case"]
    return {"spec": spec, "ops": ops, "cashflow": df, "kpis": k, "hourly": hourly}


def save_results(res: dict, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    res["cashflow"].to_csv(out_dir / "cashflow.csv")
    pd.DataFrame([{**{kk: vv for kk, vv in o.__dict__.items() if kk != "extra"}, **{f"x_{kk}": vv for kk, vv in o.extra.items()}}
                  for o in res["ops"]]).to_csv(out_dir / "operating_years.csv", index=False)
    with open(out_dir / "kpis.json", "w") as f:
        json.dump(res["kpis"], f, indent=2, default=float)
    for y, h in res["hourly"].items():
        pd.DataFrame(h).to_csv(out_dir / f"hourly_{y}.csv", index=False)
