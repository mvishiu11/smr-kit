# Methodology

## 1. Scope and framing

The model values one generating asset at a time against the Polish wholesale market, as a
**price-taker**. Three families of scenarios are run on identical market inputs:

| Family | Asset | Revenue mechanism | Dispatch rule |
|---|---|---|---|
| S1a | BWRX-300, 300 MWe | Two-way CfD, strike 115/125/135 €/MWh, 40-year tenor, then merchant | Profit-max on the CfD-effective price (market + strike − daily reference); never below variable cost |
| S1b | BWRX-300 | Fixed real price for life = last-12-month spot average (483.4 PLN/MWh) | Must-run at availability |
| S1c | BWRX-300 | Merchant (comparator) | Must-run |
| S2 | BWRX-300 | Merchant | LP load-following 50–100 % with ramp limits |
| S3a–c | CCGT 300 MW / 2×150 MW OCGT / 4×76.5 MW engines | Merchant (+ balancing) | Unit-commitment MILP 0–100 % |
| S3d | CCGT | + 15-year capacity contract (successor mechanism sensitivity) | as S3a |

"Alternative cost" is read directly from NPV: for a price-taker, NPV = PV(value of output at market
prices) − PV(all costs), i.e. minus the net cost to the system of building the asset rather than
buying the same MWh from the market. Break-even support (strike, PLN/MWh premium, PLN/kW-yr capacity
payment) is the explicit price of that alternative.

## 2. Market digital twin (`smrtwin/prices.py`)

1. **History.** PSE `csdac-pln` (SDAC clearing price for bidding zone PL; 15-min from 1 Oct 2025,
   averaged to hourly) from 14 Jun 2024, chained with energy-charts.info day-ahead EUR prices × NBP
   daily EUR/PLN for 2019–Jun 2024.
2. **Reference year.** The last 12 full months (1 Sep 2025 – 31 Aug 2026): 8,760 hours, DST and
   leap-day normalised. Mean 483.4 PLN/MWh, σ 259, p5 = 7, p95 = 860, 311 negative hours, 605 hours
   below 60 PLN/MWh. (Calendar 2025: 442 vs TGE's volume-weighted 446.30.)
3. **Shape model.** The reference year is decomposed into a normalised expected shape
   `E[p | month, weekday/weekend, hour]` and a residual (spikes, negative hours, the winter-2026 gas shock).
4. **Future years.** `price_year(mean_y, depression_y)` re-anchors the full shape + residual on the
   scenario's annual mean and deepens midday hours by `depression_y` (solar cannibalisation:
   1 pp/yr central, capped at 35 %, redistributed to evening/night so the annual mean is preserved).
   Annual means: 2027–29 from TGE BASE_Y forwards (Aug-2026 VWAP), 2030+ judgement
   (410 → 380 PLN/MWh real by 2050 central; 320 → 280 low; 470 → 520 high).
   An optional `srmc_link` ties the mean to CCGT SRMC(gas, EUA) × multiplier (calibrated 0.97–1.04
   on 2025 and Aug-2026) for a gas-indexed sensitivity.
5. **Gas and CO2.** Monthly gas price = annual path (TGE GAS_BASE_Y-27 214 PLN/MWh_th; TTF proxy
   38/33/31 €/MWh + 4 € PL premium thereafter) × monthly seasonality from TTF 2024–25. EUA path
   87 → 115 (2030) → 150 €/t (2040) central.

## 3. SMR twin (`smrtwin/smr.py`)

* 870 MWt → 300 MWe net (η = 34.5 %). Refuelling every 18 months (15 d), 25-day inspection every
  10 years, planned outages placed in April (historically lowest prices); EFOR 3 % (+3 pp first 3 years).
* Load following by reactor power reduction between 50 and 100 %: fuel burn tracks thermal power
  (fuel cost per MWh ≈ constant; unburnt reactivity extends the cycle), turbine off-design penalty
  1.5 efficiency points at 50 %; ramp 0.5 %/min in 50–90 % (→ 105 MW/h in the hourly LP), 2 %/min above.
  No on/off cycling (licence basis; xenon; days to restart).
* Marginal cost = fuel (31 PLN/MWh) + VOM (11) + statutory decommissioning/waste fund (17.16 PLN/MWh,
  Dz.U. 2012 poz. 1213; 26 CPI-indexed central) ≈ 59–68 PLN/MWh.
* Dispatch: LP `max Σ(p_t − mc)·g_t − c_cyc·Σ|Δg|` s.t. ramp bounds and `0.5·cap_t ≤ g_t ≤ cap_t`
  (HiGHS, 8,760 × 3 variables, 0.1 s). Load-following scenarios carry a 1.2 % capability loss and
  1 % O&M uplift (NEA 2011 French-fleet evidence).
* CfD settlement follows the PEJ EC decision: daily blended TGE reference (TGeBase leg), monthly
  two-way settlement, no explicit negative-hour exclusion but no offers below variable cost.

## 4. Gas twin (`smrtwin/gas.py`)

* Heat input `H = a·cap·u + b·g` fitted through full-load efficiency (57 % CCGT / 39 % OCGT / 48 %
  engines, LHV) and minimum-load efficiency (45 / 28 / 42 %), giving the strong part-load penalty of
  combined cycles. Minimum load 40 / 30 / 10 %, min up/down 4 / 1 / 1 h, hot/warm/cold starts by
  preceding off-time with wear cost (150/240/350 PLN/MW for CCGT, Kumar/NREL 2012 escalated) and start
  fuel. Availability 92.5 / 95 / 95 %, three-week planned outage.
* Weekly unit-commitment MILPs (168 h, HiGHS) chained through end-of-week state; a dynamic-programming
  heuristic (on/off state DP with per-start penalty) reproduces the MILP within 1 % and runs 100× faster
  — used for Monte Carlo and tornado runs, validated in `tests/`.
* Variable cost = gas/η + EUA × 0.2006 t/MWh_th (KOBiZE) + VOM. CCGT SRMC(central 2035) ≈ 470 PLN/MWh.

## 5. Finance (`smrtwin/finance.py`)

* Real PLN at 2026 prices, annual, end-of-year, FID = t0. Overnight capex spread on an S-curve
  (12/24/30/22/12 % over 5 years, INL/TIMCAT-style), pre-development at FID, first core in the last
  construction year, grid connection spread. Financing cost enters through the real post-tax WACC
  (SMR CfD 5 %, SMR merchant 7 %, gas 7 %; PEJ EC-decision Table 1 deflated), not as explicit IDC.
* Opex: fixed O&M (SMR 520 PLN/kW-yr, ×1.5 while operated as a single unit for 3 years), VOM, fuel,
  CO2, fund, sustaining capex (25 PLN/MWh at rated CF), property tax (2 % of the budowle share of
  capex, undepreciated), URE licence fee (0.5 % of revenue), Gaz-System exit-capacity booking.
* Tax: straight-line KŚT depreciation by asset group (buildings 2.5 %, structures 4.5 %, reactor 14 %,
  turbines/boilers 7 %, devices 10 %), CIT 19 %, loss carry-forward 5 years at ≤50 % per year
  (minimum income tax switchable, off by default). Optional debt overlay (gearing, tenor, real rate,
  IDC roll-up) yields equity IRR and DSCR; base results are unlevered project NPV/IRR.
* KPIs: NPV (own WACC and a common 7 %), IRR, LCOE = PV(costs)/PV(MWh), levelised revenue, capture
  price, CfD payments PV, CO2, payback.
* Local revenue (2025 JST system): property tax (nuclear: 50 % to bordering gminas, art. 50),
  1.6/1.7/2.3 % of the SPV's CIT income to gmina/powiat/województwo, 7.0/2.0/0.35 % of resident
  employees' PIT income (60 % resident share), construction-phase PIT (1,500 peak workers, 25 % resident).

## 6. Optimisation and uncertainty (`smrtwin/optimise.py`)

* **Break-even** by Brent root finding: CfD strike (converted from a life-long PLN/MWh uplift to a
  tenor-equivalent strike using discounted energy weights), overnight capex, constant PLN/MWh premium,
  levelised and 15-year capacity payment.
* **Portfolio optimum**: enumerate integer counts of {SMR, CCGT, 2×OCGT, 4×engine} delivering
  ≥ 300 MW × KWD firm capacity (≤ 1.6× target), rank by net cost per firm MW, merchant and with a
  465 PLN/kW-yr successor capacity mechanism.
* **Monte Carlo**: 300 Latin-hypercube draws, triangular marginals — SMR capex ×0.75–1.45, delay 0–3 y,
  price ×0.8–1.25, gas ×0.75–1.4, EUA ×0.7–1.3, EFOR ±, WACC −1/+1.5 pp, O&M ×0.8–1.5; fast dispatch.
* **Tornado**: one-at-a-time low/high case per parameter.

## 7. Excel model (`build_excel.py`)

Same logic, live formulas: `Input` (LOW/CENTRAL/HIGH columns + case switch via `INDEX`), six
`Model_*` sheets (annual timeline 2027–2096, flags → capex → market → dispatch (from `Twin`) → opex →
KŚT depreciation → CIT → FCF → NPV/IRR/LCOE → fiscal flows), `Twin` (capacity factor, capture ratio,
CfD reference ratio, heat rate, start cost per operating year from the Python dispatch, per case),
`Tables`, `Sources`. 27,600 formulas, zero errors after LibreOffice recalculation. Simplifications vs
Python: loss pool without 5-year expiry; analytic S-curve; twin ratios fixed per case (dispatch does
not re-optimise when a user edits a price).
