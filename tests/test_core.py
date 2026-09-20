"""Smoke tests: price twin integrity, dispatch sanity, finance identities."""
import numpy as np
from smrtwin import config, finance, gas, prices, smr


def test_reference_year_is_8760():
    r = prices.reference_year("last12m")
    assert len(r) == 8760 and abs(r.mean() - 483.4) < 5


def test_price_year_preserves_mean():
    sm = prices.shape_model(prices.reference_year("last12m"))
    p = prices.price_year(sm, 400.0, 0.2)
    assert abs(p.mean() - 400.0) < 1e-6 and (p < 0).sum() > 100


def test_smr_flexible_beats_baseload():
    sm = prices.shape_model(prices.reference_year("last12m"))
    p = prices.price_year(sm, 400.0, 0.1)
    u = smr.SMRUnit(); av = smr.availability_profile(0)
    d0 = smr.dispatch_baseload(u, p, av); d1 = smr.dispatch_flexible(u, p, av)
    assert d1.gross_margin_pln >= d0.gross_margin_pln - 1
    assert d1.gen_mwh.min() >= 0 and (d1.gen_mwh <= d1.cap_mw + 1e-6).all()


def test_gas_heuristic_matches_milp():
    sm = prices.shape_model(prices.reference_year("last12m"))
    p = prices.price_year(sm, 420.0, 0.05)
    g = gas.GasUnit("ccgt", 300, 0.57, 0.45, 0.4, 4, 4, {"hot": 150, "warm": 240, "cold": 350}, 8, 48, 1.2, 16, 0.925, 3)
    gp = np.full(8760, 165.0); e = np.full(8760, 500.0)
    m = gas.dispatch_portfolio([g], p, gp, e); h = gas.dispatch_heuristic([g], p, gp, e)
    assert abs(m.gross_margin_pln - h.gross_margin_pln) / m.gross_margin_pln < 0.03


def test_finance_identities():
    spec = finance.PlantSpec("x", 300, 6000, 3, [0.3, 0.45, 0.25], 2031, 30, 100, depreciation_split={"turbine_bop_7pct": 1.0}, budowle_share_of_capex=0.1)
    ops = [finance.OperatingYear(2031 + k, 1e6, 500e6, fuel_cost_pln=200e6) for k in range(30)]
    df = finance.build_cashflow(spec, ops, finance.TaxSpec())
    assert abs(df["capex"].sum() - 1800) < 1e-6
    assert (df["fcf_posttax"] <= df["fcf_pretax"] + 1e-9).all()
    k = finance.kpis(df, spec)
    assert k["lcoe_pln_per_mwh"] > 0 and k["irr_project_posttax"] is not None
