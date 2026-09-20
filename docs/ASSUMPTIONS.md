# Assumptions register

The machine-readable register is `smrtwin/assumptions/default.yaml` — every parameter is a
`[low, central, high]` triplet with an inline source note. The three research notes under
`docs/research/` hold the full evidence with URLs, year and a confidence grade for each number:

| File | Covers |
|---|---|
| `research/01_smr_bwrx300_costs.md` | BWRX-300 capex (Darlington/OEB decomposition, TVA, OSGE statements, MIT, INL, ATB, EIA, Lazard), schedule and spend profile, O&M and staffing, fuel-cycle build-up, Polish decommissioning fund and liability law, flexibility physics and cycling costs, LCOE benchmarks, recommended PLN values (§9) and explicit gaps (§10). 70 sources. |
| `research/02_gas_plants_poland.md` | Polish CCGT/OCGT/engine EPC contracts 2020–2025 (Dolna Odra, Rybnik, Grudziądz, Ostrołęka, Adamów, Kozienice, Gdańsk, EC Stalowa Wola), international capex benchmarks, turbine inflation, technical parameters (efficiency, part load, starts), O&M and LTSA, TTF/TGE gas prices and forward proxy, Gaz-System tariffs, KOBiZE factors, EUA prices and forecasts, capacity-market auctions and rules, balancing services. ≈70 sources. |
| `research/03_polish_market_cfd_tax.md` | OSGE CfD application and PEJ CfD template (EC decision), CIT/depreciation/minimum tax/PSI, property tax 2025 definitions and art. 50 sharing, 2025 JST income-share system, PIT/ZUS parameters, TGE monthly day-ahead statistics 2025–Aug 2026, negative prices, forward curve, capacity market, macro and cost of capital, Stalowa Wola site status. ≈55 sources. |

Conventions: real PLN at 2026 prices; FX NBP 18 Sep 2026 (EUR 4.3633, USD 3.7998, CAD 2.7143);
foreign-currency benchmarks converted at those rates without inflation adjustment unless stated
(2022–2024 dollar figures understate 2026 costs by ≈ 5–8 %).

Items that are judgement rather than sourced (flagged L in the notes): the 2030+ electricity price path,
the CfD terms beyond the PEJ precedent, BWRX-300 O&M/EFOR/cycling costs, the property-tax *budowle*
share for nuclear, gas forward prices beyond 2027, the post-2030 capacity mechanism, grid-connection
cost shares, and the local-resident shares used for PIT allocation.
