"""End-to-end pipeline: scenarios × cases → break-evens → portfolio optimum → Monte Carlo → tornado → figures.

Usage:  python run_all.py [--mc 300] [--no-mc] [--fast]
Outputs: results/<case>/<scenario>/…, results/summary.csv, results/*.csv|json, figures/*.png
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd

from smrtwin import config, finance, optimise as op, scenarios as sc

ROOT = Path(__file__).resolve().parent
RES = ROOT / "results"
FIG = ROOT / "figures"
PAL = {"smr": "#2a78d6", "smr2": "#4a3aa7", "ccgt": "#eb6834", "ocgt": "#eda100", "engine": "#1baf7a", "grey": "#52514e", "neg": "#e34948"}


def run_cases(raw: dict, fast: bool, mc_ok: bool) -> pd.DataFrame:
    rows = []
    store = {}
    for case in ("low", "central", "high"):
        a = config.resolve(raw, case)
        mt = sc.MarketTwin(a)
        for name in sc.SCENARIOS:
            t = time.time()
            r = op._fast_scenario(name, a, mt) if fast else sc.run_scenario(name, a, mt)
            r["kpis"]["scenario"] = name; r["kpis"]["case"] = case
            if "strike_pln" not in r["kpis"]:
                r["kpis"]["strike_pln"] = a["smr"]["cfd"]["strike_eur_per_mwh"] * a["meta"]["eur_pln"]
            r["hourly"] = r.get("hourly", {})
            sc.save_results(r, RES / case / name)
            sup = op.required_support(r, a)
            r["kpis"].update(sup)
            rows.append(r["kpis"])
            store[(case, name)] = r
            print(f"[{case}] {name}: NPV {r['kpis']['npv_project_posttax_mpln']:.0f} m PLN, LCOE {r['kpis']['lcoe_pln_per_mwh']:.0f}, "
                  f"CF {r['kpis']['avg_capacity_factor']:.2f}, premium {sup['required_premium_pln_per_mwh']:.0f} PLN/MWh ({time.time()-t:.0f}s)")
        # break-even strike / capex for the CfD case
        be = op.breakeven_strike(a, mt, store[(case, "S1a_smr_cfd")])
        with open(RES / case / "breakeven_smr.json", "w") as f:
            json.dump(be, f, indent=2, default=float)
        print(f"[{case}] break-even strike {be['breakeven_strike_eur']:.1f} EUR/MWh; break-even capex {be['breakeven_capex_pln_per_kw']}")
        # portfolio optimum (merchant and with a 465 PLN/kW-yr successor capacity mechanism)
        unit_res = {"smr": store[(case, "S1c_smr_merchant_baseload")], "ccgt": store[(case, "S3a_gas_ccgt")],
                    "ocgt": store[(case, "S3b_gas_ocgt")], "engine": store[(case, "S3c_gas_engines")]}
        for cp in (0.0, 465.02):
            pf = op.portfolio_optimum(a, mt, unit_res, capacity_payment_pln_per_kw_yr=cp)
            pf.to_csv(RES / case / f"portfolio_optimum_cp{int(cp)}.csv", index=False)
    # mixed cases: SMR cost case × market case
    for smr_case in ("low", "central", "high"):
        for mkt_case in ("low", "central", "high"):
            if smr_case == mkt_case:
                continue
            a = config.resolve(raw, "central", overrides={"smr": smr_case, "market": mkt_case})
            mt = sc.MarketTwin(a)
            for name in ("S1a_smr_cfd", "S2_smr_dynamic", "S1c_smr_merchant_baseload"):
                r = op._fast_scenario(name, a, mt)
                k = r["kpis"]; k["scenario"] = name; k["case"] = f"smr-{smr_case}/market-{mkt_case}"
                k.update(op.required_support(r, a))
                rows.append(k)
    df = pd.DataFrame(rows)
    df.to_csv(RES / "summary.csv", index=False)
    return df, store


def strike_sweep(raw: dict) -> pd.DataFrame:
    """NPV vs CfD strike (EUR/MWh) for the three SMR capex cases."""
    rows = []
    for case in ("low", "central", "high"):
        a = config.resolve(raw, "central", overrides={"smr": case})
        mt = sc.MarketTwin(a)
        for s in range(95, 156, 10):
            a2 = config.resolve(raw, "central", overrides={"smr": case}, edits={"smr.cfd.strike_eur_per_mwh": s})
            r = op._fast_scenario("S1a_smr_cfd", a2, mt)
            rows.append({"smr_case": case, "strike_eur": s, "npv_mpln": r["kpis"]["npv_project_posttax_mpln"],
                         "cfd_cost_pv_mpln": r["kpis"]["cfd_payments_pv_mpln"], "irr": r["kpis"]["irr_project_posttax"]})
    df = pd.DataFrame(rows); df.to_csv(RES / "strike_sweep.csv", index=False)
    return df


def figures(summary: pd.DataFrame, store: dict, sweep: pd.DataFrame, mc: pd.DataFrame | None, tor: pd.DataFrame, tor_gas: pd.DataFrame):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True,
                         "grid.color": "#e6e5e1", "grid.linewidth": 0.6, "figure.facecolor": "#fcfcfb", "axes.facecolor": "#fcfcfb"})
    FIG.mkdir(exist_ok=True)
    order = list(sc.SCENARIOS)
    labels = {"S1a_smr_cfd": "SMR · CfD 125 €", "S1b_smr_fixed_spotavg": "SMR · fixed = last-12m avg", "S1c_smr_merchant_baseload": "SMR · merchant baseload",
              "S2_smr_dynamic": "SMR · dynamic 50–100 %", "S3a_gas_ccgt": "CCGT 300 MW", "S3b_gas_ocgt": "OCGT 2×150 MW", "S3c_gas_engines": "Engines 4×76 MW",
              "S3d_gas_ccgt_capmarket": "CCGT + capacity contract"}
    col = {k: (PAL["smr"] if k.startswith("S1") else PAL["smr2"] if k.startswith("S2") else PAL["ccgt"] if "ccgt" in k else PAL["ocgt"] if "ocgt" in k else PAL["engine"]) for k in order}

    # 1. NPV by scenario, three cases
    fig, ax = plt.subplots(figsize=(9, 4.2))
    w = 0.26
    for i, case in enumerate(("low", "central", "high")):
        d = summary[summary.case == case].set_index("scenario").reindex(order)
        ax.bar(np.arange(len(order)) + (i - 1) * w, d["npv_project_posttax_mpln"] / 1000, w, color=[col[k] for k in order],
               alpha=[0.45, 1.0, 0.7][i], edgecolor="#fcfcfb", linewidth=1, label=f"{case} case")
    ax.axhline(0, color="#52514e", lw=0.8)
    ax.set_xticks(range(len(order))); ax.set_xticklabels([labels[k] for k in order], rotation=25, ha="right")
    ax.set_ylabel("Post-tax project NPV, bn PLN (real 2026)"); ax.set_title("NPV by scenario — low / central / high assumption cases (bar shade)")
    ax.legend(frameon=False); fig.tight_layout(); fig.savefig(FIG / "fig1_npv_by_scenario.png", dpi=160); plt.close(fig)

    # 2. LCOE stack (central) vs levelised revenue
    fig, ax = plt.subplots(figsize=(9, 4.2))
    d = summary[summary.case == "central"].set_index("scenario").reindex(order)
    ax.bar(range(len(order)), d["lcoe_capex_component"], color="#9ec5f4", label="capital", edgecolor="#fcfcfb")
    ax.bar(range(len(order)), d["lcoe_pln_per_mwh"] - d["lcoe_capex_component"], bottom=d["lcoe_capex_component"], color="#256abf", label="O&M + fuel + CO₂ + taxes/fees", edgecolor="#fcfcfb")
    ax.scatter(range(len(order)), d["levelised_revenue_pln_per_mwh"], color=PAL["ccgt"], zorder=5, s=36, label="levelised revenue (market + CfD + capacity)")
    for i, k in enumerate(order):
        ax.annotate(f"{d.loc[k,'lcoe_pln_per_mwh']:.0f}", (i, d.loc[k, "lcoe_pln_per_mwh"]), ha="center", va="bottom", fontsize=8, color="#0b0b0b")
    ax.set_xticks(range(len(order))); ax.set_xticklabels([labels[k] for k in order], rotation=25, ha="right")
    ax.set_ylabel("PLN/MWh (real 2026)"); ax.set_title("Levelised cost vs levelised revenue — central case"); ax.legend(frameon=False)
    fig.tight_layout(); fig.savefig(FIG / "fig2_lcoe_vs_revenue.png", dpi=160); plt.close(fig)

    # 3. NPV vs strike
    fig, ax = plt.subplots(figsize=(7, 4))
    for case, c in zip(("low", "central", "high"), ("#86b6ef", "#2a78d6", "#0d366b")):
        d = sweep[sweep.smr_case == case]
        ax.plot(d.strike_eur, d.npv_mpln / 1000, color=c, lw=2, marker="o", ms=4, label=f"SMR capex {case}")
    ax.axhline(0, color="#52514e", lw=0.8); ax.axvspan(115, 135, color="#eda100", alpha=0.12, label="OSGE / brief range 115–135")
    ax.set_xlabel("CfD strike, EUR/MWh (real)"); ax.set_ylabel("NPV, bn PLN"); ax.set_title("SMR NPV vs CfD strike"); ax.legend(frameon=False)
    fig.tight_layout(); fig.savefig(FIG / "fig3_npv_vs_strike.png", dpi=160); plt.close(fig)

    # 4. Hourly dispatch week (central, first full year): SMR dynamic vs CCGT vs price
    r_s = store[("central", "S2_smr_dynamic")]; r_g = store[("central", "S3a_gas_ccgt")]
    ys = min(r_s["hourly"]); yg = min(r_g["hourly"])
    h0 = 24 * 15; h1 = h0 + 24 * 7   # mid-January week
    fig, axs = plt.subplots(2, 1, figsize=(10, 5.5), sharex=True)
    p = r_s["hourly"][ys]["price"]
    axs[0].plot(range(h1 - h0), p[h0:h1], color=PAL["grey"], lw=1.5); axs[0].set_ylabel("Day-ahead price, PLN/MWh"); axs[0].set_title(f"One January week — hourly price ({ys}) and dispatch")
    axs[1].plot(range(h1 - h0), r_s["hourly"][ys]["gen"][h0:h1], color=PAL["smr2"], lw=2, label=f"SMR dynamic ({ys})")
    axs[1].plot(range(h1 - h0), r_g["hourly"][yg]["gen"][h0:h1], color=PAL["ccgt"], lw=2, label=f"CCGT ({yg})")
    axs[1].set_ylabel("MW"); axs[1].set_xlabel("hour of week"); axs[1].legend(frameon=False)
    fig.tight_layout(); fig.savefig(FIG / "fig4_dispatch_week.png", dpi=160); plt.close(fig)

    # 4b. the week with the most negative-price hours (solar dip)
    neg = (p < 0).astype(int)
    wk = np.array([neg[i:i + 168].sum() for i in range(0, 8760 - 168, 24)])
    h0 = int(wk.argmax()) * 24; h1 = h0 + 24 * 7
    fig, axs = plt.subplots(2, 1, figsize=(10, 5.5), sharex=True)
    axs[0].plot(range(h1 - h0), p[h0:h1], color=PAL["grey"], lw=1.5); axs[0].axhline(0, color="#e34948", lw=0.8); axs[0].set_ylabel("PLN/MWh"); axs[0].set_title(f"Week with most negative-price hours (from day {h0//24}) — hourly price ({ys}) and dispatch")
    axs[1].plot(range(h1 - h0), r_s["hourly"][ys]["gen"][h0:h1], color=PAL["smr2"], lw=2, label="SMR dynamic")
    axs[1].plot(range(h1 - h0), r_g["hourly"][yg]["gen"][h0:h1], color=PAL["ccgt"], lw=2, label="CCGT")
    axs[1].set_ylabel("MW"); axs[1].set_xlabel("hour of week"); axs[1].legend(frameon=False)
    fig.tight_layout(); fig.savefig(FIG / "fig4b_dispatch_week_summer.png", dpi=160); plt.close(fig)

    # 5. Cumulative cash flow
    fig, ax = plt.subplots(figsize=(8, 4.2))
    for k in ("S1a_smr_cfd", "S1c_smr_merchant_baseload", "S2_smr_dynamic", "S3a_gas_ccgt", "S3b_gas_ocgt"):
        cf = store[("central", k)]["cashflow"]["fcf_posttax"].cumsum() / 1000
        ax.plot(cf.index, cf.values, color=col[k], lw=2, label=labels[k])
    ax.axhline(0, color="#52514e", lw=0.8); ax.set_ylabel("Cumulative post-tax FCF, bn PLN (undiscounted)"); ax.set_title("Cumulative cash flow — central case"); ax.legend(frameon=False, fontsize=8)
    fig.tight_layout(); fig.savefig(FIG / "fig5_cumulative_cashflow.png", dpi=160); plt.close(fig)

    # 6. Tornado
    for tdf, fn, ttl in ((tor, "fig6_tornado_smr_cfd.png", "SMR CfD — NPV sensitivity (one-at-a-time, low→high case)"), (tor_gas, "fig6b_tornado_ccgt.png", "CCGT — NPV sensitivity")):
        fig, ax = plt.subplots(figsize=(8, 4))
        y = np.arange(len(tdf))[::-1]
        ax.barh(y, (tdf.npv_low_case - tdf.npv_base) / 1000, color="#86b6ef", label="low case")
        ax.barh(y, (tdf.npv_high_case - tdf.npv_base) / 1000, color="#0d366b", label="high case")
        ax.set_yticks(y); ax.set_yticklabels(tdf.parameter); ax.axvline(0, color="#52514e", lw=0.8)
        ax.set_xlabel(f"ΔNPV vs base ({tdf.npv_base.iloc[0]/1000:.2f} bn PLN), bn PLN"); ax.set_title(ttl); ax.legend(frameon=False)
        fig.tight_layout(); fig.savefig(FIG / fn, dpi=160); plt.close(fig)

    # 7. Monte Carlo
    if mc is not None and len(mc):
        fig, ax = plt.subplots(figsize=(8, 4.2))
        for k in ("S1a_smr_cfd", "S2_smr_dynamic", "S3a_gas_ccgt", "S3b_gas_ocgt"):
            c = f"npv_{k}"
            if c in mc:
                v = mc[c].dropna() / 1000
                ax.hist(v, bins=40, histtype="step", lw=2, color=col[k], label=f"{labels[k]}  (P(NPV>0)={100*(v>0).mean():.0f} %)")
        ax.axvline(0, color="#52514e", lw=0.8); ax.set_xlabel("Post-tax NPV, bn PLN"); ax.set_ylabel("draws"); ax.set_title(f"Monte Carlo ({len(mc)} LHS draws) — joint uncertainty"); ax.legend(frameon=False, fontsize=8)
        fig.tight_layout(); fig.savefig(FIG / "fig7_monte_carlo.png", dpi=160); plt.close(fig)

    # 8. Local government revenue
    fig, ax = plt.subplots(figsize=(8, 4))
    comps = ["local_property_tax_host", "local_property_tax_neighbours", "local_cit_gmina", "local_cit_powiat", "local_cit_wojewodztwo", "local_pit_gmina", "local_pit_powiat", "local_pit_wojewodztwo"]
    cl = ["#2a78d6", "#86b6ef", "#eb6834", "#f2a07f", "#f9d0bf", "#1baf7a", "#7fd5b3", "#c4ecd9"]
    keys = ["S1a_smr_cfd", "S3a_gas_ccgt", "S3b_gas_ocgt", "S3c_gas_engines"]
    bottom = np.zeros(len(keys))
    for c, cc in zip(comps, cl):
        vals = np.array([store[("central", k)]["cashflow"].loc[lambda d: d.operating, c].mean() for k in keys])
        ax.bar(range(len(keys)), vals, bottom=bottom, color=cc, label=c.replace("local_", "").replace("_", " "), edgecolor="#fcfcfb"); bottom += vals
    ax.set_xticks(range(len(keys))); ax.set_xticklabels([labels[k] for k in keys]); ax.set_ylabel("m PLN per operating year"); ax.set_title("Local-government revenue per operating year — central case")
    ax.legend(frameon=False, fontsize=7, ncol=2); fig.tight_layout(); fig.savefig(FIG / "fig8_local_revenue.png", dpi=160); plt.close(fig)

    # 9. Price twin: reference year monthly means + a synthetic future year
    mt = sc.MarketTwin(config.resolve(config.load_raw(), "central"))
    fig, axs = plt.subplots(1, 2, figsize=(11, 3.8))
    ref = mt.ref.values.reshape(365, 24)
    axs[0].plot(range(24), ref.mean(axis=0), color="#2a78d6", lw=2, label="Sep-2025→Aug-2026 actual")
    for y, c in ((2035, "#eb6834"), (2045, "#1baf7a")):
        axs[0].plot(range(24), mt.price(y).reshape(365, 24).mean(axis=0), color=c, lw=2, label=f"twin {y}")
    axs[0].set_xlabel("hour"); axs[0].set_ylabel("mean price, PLN/MWh"); axs[0].set_title("Average diurnal profile"); axs[0].legend(frameon=False)
    dur = np.sort(mt.ref.values)[::-1]
    axs[1].plot(dur, color="#2a78d6", lw=2, label="reference year")
    axs[1].plot(np.sort(mt.price(2035))[::-1], color="#eb6834", lw=2, label="twin 2035")
    axs[1].axhline(0, color="#52514e", lw=0.8); axs[1].set_ylim(-300, 1500); axs[1].set_xlabel("hours"); axs[1].set_title("Price-duration curve"); axs[1].legend(frameon=False)
    fig.tight_layout(); fig.savefig(FIG / "fig9_price_twin.png", dpi=160); plt.close(fig)


def load_store() -> dict:
    """Rebuild the minimal `store` needed for figures from results/ on disk."""
    store = {}
    for case in ("low", "central", "high"):
        for name in sc.SCENARIOS:
            d = RES / case / name
            if not (d / "cashflow.csv").exists():
                continue
            hourly = {int(f.stem.split("_")[1]): pd.read_csv(f).to_dict("series") for f in d.glob("hourly_*.csv")}
            hourly = {y: {k: v.values for k, v in h.items()} for y, h in hourly.items()}
            store[(case, name)] = {"cashflow": pd.read_csv(d / "cashflow.csv", index_col=0), "hourly": hourly,
                                   "kpis": json.load(open(d / "kpis.json"))}
    return store


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--figures-only", action="store_true")
    ap.add_argument("--mc", type=int, default=300)
    ap.add_argument("--no-mc", action="store_true")
    ap.add_argument("--fast", action="store_true", help="use heuristic dispatch everywhere (no MILP/LP)")
    args = ap.parse_args()
    RES.mkdir(exist_ok=True)
    raw = config.load_raw()
    t0 = time.time()
    if args.figures_only:
        mc = pd.read_csv(RES / "monte_carlo.csv") if (RES / "monte_carlo.csv").exists() else None
        figures(pd.read_csv(RES / "summary.csv"), load_store(), pd.read_csv(RES / "strike_sweep.csv"), mc,
                pd.read_csv(RES / "tornado_smr_cfd.csv"), pd.read_csv(RES / "tornado_ccgt.csv"))
        return
    summary, store = run_cases(raw, args.fast, not args.no_mc)
    sweep = strike_sweep(raw)
    tor = op.tornado(raw, "S1a_smr_cfd", op.TORNADO); tor.to_csv(RES / "tornado_smr_cfd.csv", index=False)
    tor_gas = op.tornado(raw, "S3a_gas_ccgt", op.TORNADO_GAS); tor_gas.to_csv(RES / "tornado_ccgt.csv", index=False)
    mc = None
    if not args.no_mc:
        mc = op.monte_carlo(raw, n=args.mc, verbose=True); mc.to_csv(RES / "monte_carlo.csv", index=False)
        q = mc.filter(like="npv_").describe(percentiles=[0.05, 0.25, 0.5, 0.75, 0.95]).T
        q["p_npv_positive"] = [(mc[c] > 0).mean() for c in q.index]
        q.to_csv(RES / "monte_carlo_summary.csv")
        print(q)
    figures(summary, store, sweep, mc, tor, tor_gas)
    print(f"done in {time.time()-t0:.0f}s")


if __name__ == "__main__":
    main()
