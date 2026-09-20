# BWRX-300 (Stalowa Wola / OSGE) – Techno-economic input research

Prepared 2026-09-20 for the digital-twin cost model. Every number below is tied to a URL and a year. Where a figure was not found, this is stated explicitly and a proxy is proposed with reasoning. Confidence: **H** = primary source, current; **M** = secondary or dated source, or requires interpretation; **L** = proxy / derived / weak sourcing.

## 0. Conventions and exchange rates

| Item | Value | Source |
|---|---|---|
| NBP Table A mid rate, 18 Sep 2026 (tab. 182/A/NBP/2026) | USD 3.7998 PLN; EUR 4.3633 PLN; CAD 2.7143 PLN | https://api.nbp.pl/api/exchangerates/rates/a/usd/last/1/ (and /eur/, /cad/) (2026) |
| Implied cross rates | CAD/USD 0.7143; EUR/USD 1.1483; CAD/EUR 0.6221 | derived |
| Price basis | Sources quoted in their own dollar-year (2018$, 2019$, 2022$, 2024$, "2024 CAD"). Converted at the Sep-2026 FX rates without inflation adjustment unless stated. For a "2026 real PLN" model, add ~2–8% cumulative US inflation for 2024$→2026$ figures (not done here; flagged). | – |
| BWRX-300 net efficiency used | 300 MWe / 870 MWt = 34.5% (net); gross ~316 MWe → 36.3% | GE Vernova General Description (Table 2-1) https://www.gevernova.com/content/dam/gevernova-nuclear/global/en_us/documents/carbon-free-power/005N9751-BWRX-300-General-Description.pdf (2023/24); IAEA ARIS status report (2020) https://clara.nz/docs/hardware-unsorted/iaea/BWRX-300_2020.pdf |

---

## 1. CAPEX

### 1.1 Darlington New Nuclear Project (OPG) – the only real BWRX-300 cost data

| Parameter | Value | Unit | Source URL | Year | Notes / confidence |
|---|---|---|---|---|---|
| 4-unit programme (1,200 MW) total | 20.9 | bn CAD (2024 CAD, incl. interest, escalation, contingency) | https://www.world-nuclear-news.org/articles/what-is-the-budget-for-canadas-first-smr-project ; https://www.worldnuclearreport.org/Ontario-s-Darlington-SMR-project-to-cost-nearly-21-billion-significantly-higher | 2025 (May) | **H**. Explicitly *not* an overnight cost. |
| Unit 1 "Release Quality Estimate" (RQE), incl. common scope | 7.7 | bn CAD | OPG OEB filing EB-2025-0297 Exh. D2-4-1 (updated 21 May 2026) https://files.opg.com/wp-content/uploads/2026/05/D2-04-01-Darlington-New-Nuclear-Project-Overview_Updated_20260521_260522_191835.pdf | 2026 | **H**. Unchanged vs May-2025 estimate → no 2026 cost overrun reported to date. |
| Unit 1 RQE breakdown | Core cost 5.1 bn (66%) + contingency 1.4 bn (18%) + capitalised interest 1.2 bn (16%) = 7.7 bn | bn CAD | same OEB filing (Chart 1, p. 8) | 2026 | **H**. This is the only public decomposition of contingency and IDC. |
| Common Scope Facilities embedded in Unit 1 | ~1.1 bn (OEB filing) / 1.6 bn (OPG press, incl. wider shared infrastructure) | bn CAD | OEB filing; WNN 2025 | 2025–26 | **M** – the two figures differ in scope definition (1.6 bn = "roads, sewers, bridges, buildings, fibre, cooling tunnels"). |
| Unit 1 reactor-only (7.7 − 1.6) | 6.1 | bn CAD | WNN; OPG Q1-2025 financial statements https://www.oeb.ca/sites/default/files/2025%20Q1%20Financial%20Statements.pdf | 2025 | **H** |
| Unit 4 estimate | 4.1 (≈33% cheaper than Unit 1) | bn CAD | WNN 2025 | 2025 | **M** (Class-4 estimate) |
| Units 2 & 3 (implied) | 20.9 − 7.7 − 4.1 = 9.1 → ~4.55 each | bn CAD | derived from WNN | 2025 | **L** derived; OPG has not published unit 2/3 figures ("being refined in definition phase"). |
| Owner's costs | Included in RQE ("licensing, engineering, procurement, construction, operations readiness, contingency, interest and escalation"); not separately disclosed | – | WNN 2025 | 2025 | Not found separately. |
| Equity financing secured | up to 3 bn CAD (Canada Growth Fund 2 bn + Building Ontario Fund 1 bn) | bn CAD | https://www.opg.com/news-resources/newsroom/our-stories/story/opg-marks-new-milestones-in-construction-of-g7s-first-small-modular-reactor/ | Oct 2025 | **H** |
| Q1-2025 DNNP capex spend | 605 m CAD in one quarter | m CAD | OPG Q1-2025 FS | 2025 | Useful for spend-profile calibration. |
| Rate-base in-service addition sought for 2030 | 6,585 m CAD (7.7 bn less ~1.1 bn CCR interest recovered concurrently) | m CAD | OEB filing | 2026 | **H** |

**Per-kW conversions (Sep-2026 FX; 300 MW net per unit, 1,200 MW programme):**

| Basis | CAD/kW | USD/kW | EUR/kW | PLN/kW |
|---|---|---|---|---|
| Unit 1 all-in RQE (7.7 bn) | 25,667 | 18,334 | 15,967 | 69,667 |
| Unit 1 excl. 1.6 bn common (6.1 bn) | 20,333 | 14,525 | 12,649 | 55,191 |
| Unit 1 "core" excl. contingency & IDC (5.1 bn) | 17,000 | 12,144 | 10,575 | 46,143 |
| Unit 1 core excl. common scope (5.1 − 1.1 = 4.0 bn) – closest to a FOAK *overnight EPC+owner* | 13,333 | 9,524 | 8,294 | 36,191 |
| 4-unit programme average (20.9 bn / 1,200 MW) | 17,417 | 12,441 | 10,834 | 47,274 |
| Unit 4 (4.1 bn) | 13,667 | 9,762 | 8,502 | 37,095 |
| Units 2/3 implied (4.55 bn) | 15,167 | 10,834 | 9,435 | 41,167 |

Caveat: the Unit-1 "core 5.1 bn" still includes escalation to nominal dollars during construction; a true 2024-real overnight cost for unit 1 excluding common scope is probably ~CAD 12,000–13,500/kW (≈ USD 8,600–9,600/kW). Confidence **M**.

### 1.2 TVA Clinch River (BWRX-300 Unit 1)

| Parameter | Value | Source | Year | Notes |
|---|---|---|---|---|
| Official TVA cost estimate | **Not published.** TVA: "the design … is not yet complete so it is premature to discuss the cost of building the first unit"; TVA is "developing the potential Clinch River project cost estimate and schedule" | https://neutronbytes.com/2025/12/05/doe-opens-its-checkbook-for-smrs-plans-to-spend-800m/ ; https://wpln.org/post/nuclear-hype-is-building-tva-plans-to-buy-in/ | Dec 2025 / Oct 2025 | **H** that no estimate exists publicly |
| Overnight cost figure cited in expert testimony from TVA filings | 17,949 USD/kW (2024$), excl. financing & inflation | https://cleanenergy.org/news/rush-to-build-new-nuclear-power-tva-and-administration-ignore-cost-and-safety/ (SACE, citing TVA filings) | 2025/26 | **M/L** – advocacy source quoting a filing; = 15,631 EUR/kW = 68,203 PLN/kW. Treat as an upper-bound FOAK marker. |
| DOE cost-share award | 400 m USD (TVA, from the 800 m USD "first mover" programme) | Neutron Bytes Dec 2025; https://www.powermag.com/doe-selects-tva-holtec-to-receive-800-million-to-advance-smr-deployment/ | 2025 | **H** |
| NRC schedule | Construction-permit application May 2025; final SEIS 1 Apr 2026; NRC staff recommended CP issuance (SER June 2026); NRC review cost ~1.4 m USD / 16,500 staff-h | https://www.ans.org/news/2026-07-01/article-8174/clinch-river-construction-permit-recommendation-follows-safety-evaluation/ ; https://public-inspection.federalregister.gov/2026-06571.pdf | 2026 | **H** |
| Target COD | 2032 | WPLN Oct 2025 | 2025 | **M** |

### 1.3 OSGE / Poland cost statements (chronological)

| Date | Statement | Value | USD/kW | EUR/kW | PLN/kW | Source | Conf. |
|---|---|---|---|---|---|---|---|
| Apr–Oct 2023 | OSGE per-unit capex estimates fluctuating | 1.3 → 1.5 → 1.6 bn EUR | 4,976–6,124 | 4,333–5,333 | 18,900–23,300 | Polityka Insight "Mały atom – nadzieje kontra rzeczywistość" (Jul 2024) https://www.politykainsight.pl/_resource/multimedium/20362816 | M |
| 2024 (interview) | OSGE: programme of ~10 units by 2035 ≈ 15 bn EUR; first unit up to 1.6 bn EUR, subsequent ~1.2 bn EUR average | 1.6 / 1.2 bn EUR | 6,124 / 4,593 | 5,333 / 4,000 | 23,269 / 17,453 | https://www.bankier.pl/wiadomosc/Orlen-Synthos-Green-Energy-szacuje-koszt-programu-budowy-blokow-SMR-do-35-na-ok-15-mld-euro-wywiad-8622777.html | M |
| 2025 | OSGE preliminary: ~2 bn USD per 300 MW unit | 2.0 bn USD | 6,667 | 5,806 | 25,333 | https://www.wnp.pl/energia/ile-bedzie-kosztowac-smr-y-w-polsce-estymacje-sa-obarczone-ryzykiem,1081680.html | M |
| 2025 | OSGE (R. Kasprów): capex "around 2 bn EUR" per unit, depends on number of units; CfD reference price expectation 115–135 EUR/MWh (headline says 125–145) for the first 14 units | 2.0 bn EUR | 7,656 | 6,667 | 29,090 | https://zielonagospodarka.pl/osge-oczekuje-cen-125-145-euromwh-w-kontraktach-roznicowych-dla-14-pierwszych-reaktorow-bwrx-300-21182 | M |
| 29 Jun 2026 | OSGE formally asked Ministry of Energy to notify a CfD for 14 BWRX-300 (Włocławek, Stawy Monowskie, Stalowa Wola); first unit COD 2032 at Włocławek; no capex/strike price disclosed; advisors KPMG, ETARA | – | – | – | – | https://osge.com/osge-wnioskuje-o-pierwszy-w-ue-kontrakt-roznicowy-dla-malych-reaktorow-modulowych/ | H |
| 6 Jul 2026 | Ministry of Energy: no procedure yet; will run "in-depth analyses"; only the State can notify the EC | – | – | – | – | https://www.wnp.pl/energia/osge-chce-wsparcia-panstwa-dla-malych-reaktorow-ministerstwo-energii-reaguje,1078724.html | H |
| 19 Jul 2026 | ME (P. Gajda): SMR roadmap due end-July 2026; CfD + state debt guarantees are the intended instruments; ~125 EUR/MWh is "relatively high"; "we will learn everything only after the reference unit is completed" | ~125 EUR/MWh reference | – | – | 545 PLN/MWh | https://www.bankier.pl/wiadomosc/SMR-y-z-pomoca-panstwa-Polska-przygotowuje-model-wsparcia-9169024.html ; wnp.pl 1081680 | H |
| 2026 | No PLN-denominated per-unit figure, no EC notification published, no Polish government capex assumption for SMR found | – | – | – | – | searched: EC state-aid register, ME, wnp, Bankier | H (absence) |
| Comparator: Fermi Energia (Estonia, 2×BWRX-300) | ~3.3 bn EUR for two units (1.65 bn/unit); LCOE "below 100 EUR/MWh" | 1.65 bn EUR | 6,316 | 5,500 | 23,998 | https://fermi.ee/en/bwrx-300/ | M |

### 1.4 MIT (Shirvan, ANP-TR-201, July 2024) – BWRX-300 specific

| Parameter | Value (2024 USD) | USD/kW | EUR/kW | PLN/kW | Source | Conf. |
|---|---|---|---|---|---|---|
| FOAK overnight, bottom-up, excl. owner's cost | 14,000 | 14,000 | 12,192 | 53,197 | https://web.mit.edu/kshirvan/www/research/ANP201%20TR%20CANES.pdf (p. 22) | H |
| FOAK top-down range excl. owner's | 11,000–17,600 | – | – | 41,798–66,876 | same (p. 21) | H |
| FOAK incl. owner's cost (Scenario 1 baseline) | 16,700–17,000 | 17,000 | 14,805 | 64,597 | same (p. 22) | H |
| 9th unit (1 unit then 8 sequential; 1.8× cumulative learning) | 9,500 | 9,500 | 8,273 | 36,098 | same (p. 22) | H |
| Learning | 1.3× cumulative for 8 parallel units; 1.8× FOAK→NOAK by analogy with AP1000 | – | – | – | same | H |
| FOAK schedule | >5 years first nuclear concrete → start of commissioning | – | – | – | same (p. 21) | H |
| Financing multiplier | 1.48 (50% debt @6.5%, 12.5% equity) | – | – | – | same | H |
| O&M / fuel | O&M 28.2 $/MWh (8-unit fleet, 90% CF) ≈ 222 $/kW-yr; 38.7 $/MWh single unit ≈ 305 $/kW-yr; fuel 9 $/MWh; CF 85% rising to 93% after 20 yrs | – | – | – | same (p. 23) | H |
| LCOE | Scenario 1: 237 $/MWh unsubsidised / 167 with ITC+LPO; Scenario 2: FOAK 194 $/MWh (with ITC/LPO), 135→123 $/MWh for 4–12-pack follow-on | – | – | – | same (p. 24) | H |

### 1.5 Generic SMR / nuclear cost benchmarks and learning rates

| Source | Parameter | Low | Central | High | Unit | URL | Year | Conf. |
|---|---|---|---|---|---|---|---|---|
| INL meta-analysis (Abou-Jaoude et al., INL/RPT-24-77048) | SMR 300 MWe "BOAK" overnight (Advanced/Moderate/Conservative) | 5,500 | 8,000 | 10,000 | 2022 USD/kW | https://gain.inl.gov/content/uploads/4/2024/11/INL-RPT-24-77048-Meta-Analysis-of-Adv-Nuclear-Reactor-Cost-Estimations.pdf | Apr 2024 | H |
| INL 2024 | Learning rate SMR / large | – | 9.5% / 8% per doubling | – | – | same | 2024 | H |
| INL 2024 | 2050 SMR overnight after learning | 2,000 | – | 6,250 | 2022 USD/kW | same | 2024 | H |
| INL lit. review (INL/RPT-23-72972 Rev.3) | Learning-rate range recommended | 5% | 10% | 15% | per doubling | https://gain.inl.gov/content/uploads/4/2024/11/INL-RPT-23-72972-Literature-Review-of-Adv-Reactor-Cost-Estimates.pdf | Oct 2023 | H |
| INL 2023 | Multi-unit scaling exponent / O&M multiplier | 0.80–0.85 OCC exponent; 0.5–0.7 O&M multiplier vs single unit | – | – | – | same | 2023 | H |
| NREL/NLR ATB 2025 | SMR 300 MWe: LR 9.5%; construction 43/55/71 months (Adv/Mod/Cons); CF 93%; 60-yr life; ramp 10%/min | – | – | – | – | https://atb.nlr.gov/electricity/2025/nuclear | 2025 | H |
| Nøland et al. (NTNU, IAEA paper, based on INL 2024) | 300 MW SMR overnight 2030 (Q1/median/Q3) | 5,891 | 8,568 | 10,710 | 2024 USD/kW | https://conferences.iaea.org/event/374/papers/31012/files/12710-IAEA_Paper-57_SMR_final_V3.pdf | 2024 | M |
| Nøland et al. | LCOE 2030 @5% WACC | 66 | 88 | 116 | USD/MWh | same | 2024 | M |
| EIA AEO2025 | Nuclear SMR (480 MW): base overnight 8,467; total overnight 9,314 (×1.10 optimism); lead time 6 yr | – | 9,314 | – | 2024 USD/kW | https://docs.catalyst.coop/pudl/en/nightly/_downloads/fcef77222b0e504440dfa03fa3984d08/eiaaeo_2025_electricity_market_assumptions.pdf | 2025 | H |
| EIA AEO2025 | Large LWR (2,156 MW): total overnight 7,821 | – | 7,821 | – | 2024 USD/kW | same | 2025 | H |
| Lazard LCOE+ v18 | US new nuclear capital cost (Vogtle-based) | 9,020 | – | 14,820 | USD/kW | https://www.lazard.com/media/uounhon4/lazards-lcoeplus-june-2025.pdf | Jun 2025 | H |
| Lazard LCOE+ v19 | US new nuclear capital cost | 12,300 | – | 17,570 | USD/kW | https://www.lazard.com/media/kcfconhf/lazards-lcoeplus_vf.pdf | Jul 2026 | H |
| IEA/NEA Projected Costs 2020 | Nuclear overnight, 8 plants (min/median/mean/max) | 2,157 | 3,370 (median), 3,606 (mean) | 6,920 | 2018 USD/kW | https://iea.blob.core.windows.net/assets/ae17da3d-e8a5-4163-a3ec-2e6fb0b5677d/Projected-Costs-of-Generating-Electricity-2020.pdf (Table 3.1) | 2020 | H (dated) |
| IEA/NEA 2020 | Contingency convention 15% of overnight (nuclear) | – | 15% | – | – | same | 2020 | H |
| GEH original target (IAEA ARIS 2020) | 1 bn USD FOAK; ~2,250 USD/kW NOAK; LCOE 35–50 USD/MWh | – | 2,250 | – | USD/kW | https://clara.nz/docs/hardware-unsorted/iaea/BWRX-300_2020.pdf | 2020 | H (source) / L (credibility – superseded by Darlington) |
| Carbon Commentary (Darlington vs. forecasts) | 2020 NOAK forecast 2,900 USD/kW (2023$); 2023 estimates 7,400–12,350 USD/kW; Darlington unit 1 ≈ 14,600 USD/kW excl. shared | – | – | – | USD/kW | https://www.carboncommentary.com/blog/2025/5/11/the-first-test-for-new-small-modular-reactors-smr | May 2025 | M |

**Learning-rate note:** INL 15% is the *optimistic* end of INL's recommended 5/10/15% range (INL 2023 lit. review); INL 2024 / NREL ATB 2025 adopt 9.5% for SMRs. MIT applies 1.3× (8 parallel) to 1.8× (sequential) cumulative FOAK→NOAK factors. Darlington's own trajectory (Unit 1 excl. common 6.1 → Unit 4 4.1 bn CAD) is a 33% reduction over 2 doublings ≈ 18% per doubling *including* the shared-infrastructure effect – i.e. consistent with the optimistic end, but Class-4 estimates.

---

## 2. Construction schedule and spend profile

| Parameter | Low | Central | High | Unit | Source | Notes / conf. |
|---|---|---|---|---|---|---|
| Darlington Unit 1 key dates | Site prep autumn 2022; Licence to Construct 4 Apr 2025; province approval 8 May 2025; shaft excavation done 23 Mar 2026; RHP-1 lifted 1 Apr 2026; reactor basemat placed 1 May 2026; Licence-to-Operate application 2/17 Apr 2026; next hold point RPV installation | | | | OEB filing 2026; https://www.nucnet.org/news/canada-s-opg-completes-installation-of-reactor-basemat-for-first-darlington-smr-5-5-2026 ; https://www.world-nuclear-news.org/articles/opg-applies-for-operating-licence-for-bwrx-300-smr | **H** |
| Darlington Unit 1 COD target | Oct 2030 (OEB filing) / "end of 2030" (OPG) | | | | OEB filing; OPG Oct 2025 | **H**; unchanged in 2026 |
| Darlington Units 2–4 | Definition phase; no in-service dates approved for 2027–31; "mid-2030s" | | | | OEB filing; WNN | **H** |
| Implied Unit-1 duration, licence → COD | | ~66 months (Apr 2025 → Oct 2030) | | months | derived | **M** |
| Implied Unit-1 duration, basemat/first structural concrete → COD | | ~53 months (May 2026 → Oct 2030) | | months | derived | **M** |
| GEH/OSGE vendor claim (NOAK) | 24 | 30–36 | 36 | months first nuclear concrete → fuel load / criticality | https://www.gevernova.com/nuclear/carbon-free-power/bwrx-300-small-modular-reactor ; IAEA ARIS 2020 (26 months to criticality, 30 with commissioning); Polityka Insight 2024 (30–36) | **H** for the claim; **L** as a forecast |
| MIT FOAK | | >60 | | months first concrete → commissioning start | MIT ANP-201 (2024) | H |
| INL/NREL ATB 2025 SMR | 43 | 55 | 71 | months | ATB 2025; INL 2024 | H |
| EIA AEO2025 lead time | | 72 | | months (incl. licensing) | EIA AEO2025 | H |
| IEA/NEA 2020 convention | | 84 | | months, nuclear | IEA/NEA 2020 | H |
| **Recommended for Polish FOAK unit (Stalowa Wola, unit 1)** | 48 | 60 | 72 | months first structural concrete → COD | judgement anchored on Darlington (~53–66) and ATB moderate/conservative | M |
| **Recommended for follow-on units** | 36 | 48 | 60 | months | judgement | L |

**Spend profile (S-curve) conventions in the literature:**

| Source | Assumption | URL |
|---|---|---|
| IEA/NEA Projected Costs 2020 | **Linear (uniform) expense schedule** over 7-year nuclear construction; IDC computed on that basis | https://iea.blob.core.windows.net/assets/ae17da3d-e8a5-4163-a3ec-2e6fb0b5677d/Projected-Costs-of-Generating-Electricity-2020.pdf ("Construction cost profiles") |
| INL (Bolisetti et al., INL/RPT-24-7767, Jun 2024) | Normalised spend curves from TIMCAT scheduler; IDC = Σ[OCC·β_t·((1+r)^(t/T)) − OCC]; 100% spent before startup testing; extra 16-month startup period accrues interest | https://inldigitallibrary.inl.gov/sites/sti/sti/Sort_109810.pdf |
| MIT OCW 22.812 (Ganda/Deutch lineage) | Linearly rising expenditure rate (e.g., 80→160 $M/yr) with continuous compounding | https://ocw.mit.edu/courses/22-812j-managing-nuclear-technology-spring-2004/c496144f2e576a709ec0cba58ff10e15_ps3soln.pdf |
| MIT ANP-201 | Financing multiplier 1.48 on overnight for FOAK BWRX-300 (implies front-loaded + long schedule) | MIT 2024 |
| Darlington actuals | 605 m CAD spent in Q1-2025 alone (pre-first-concrete), ~521 m CAD released for Units 2–4 planning – i.e., substantial early spend on long-lead items (RPV procured before basemat) | OPG Q1-2025 FS; OEB filing 2026 |

**Proxy recommendation:** no BWRX-300-specific S-curve is published. Use a beta/sine S-curve with ~10–15% of overnight spent before first structural concrete (long-lead RPV, site prep, licensing), peak spend in years 2–3 of a 5-year build, e.g. annual shares 12 / 24 / 30 / 22 / 12% (FOAK, 60 months). Test sensitivity against the IEA/NEA uniform profile. Confidence **L** (proxy).

---

## 3. O&M and staffing

### 3.1 Fixed and variable O&M benchmarks

| Source | Fixed O&M (USD/kW-yr) | ⇒ PLN/kW-yr @3.7998 | ⇒ USD/MWh @93% CF | Variable O&M (USD/MWh) | Dollar-yr | URL | Conf. |
|---|---|---|---|---|---|---|---|
| INL 2024 meta-analysis, SMR 300 MWe (Adv / Mod / Cons) | 118 / 136 / 216 | 448 / 517 / 821 | 14.5 / 16.7 / 26.5 | 2.2 / 2.6 / 2.8 | 2022 | INL/RPT-24-77048 | H |
| EIA AEO2025, SMR 480 MW | 123.88 | 471 | 15.2 | 3.23 | 2024 | AEO2025 EMM assumptions | H |
| EIA AEO2025, large LWR | 158.61 | 603 | 19.5 | 2.54 | 2024 | same | H |
| Lazard v18 (Jun 2025) & v19 (Jul 2026), US new nuclear | 136–158 | 517–600 | 16.7–19.4 | 4.40–5.15 | 2025/26 | Lazard v18, v19 | H |
| Rao, Kaffine & Hodge (2026), "manufacturer-advertised" BWRX-300 | 140.16 | 533 | 17.2 | 3.55 (fuel 8.44) | – | https://arxiv.org/abs/2609.08929 | M (secondary compilation) |
| MIT ANP-201, BWRX-300 non-fuel O&M | 222 (8-unit fleet) / 305 (single unit) equiv. | 843 / 1,159 | 28.2 / 38.7 @90% | incl. | 2024 | MIT 2024 | H |
| NEI "Nuclear Costs in Context" – US operating fleet 2025 actuals | Operating 20.82 $/MWh (+ capital 9.69 + fuel 5.95 = 36.46 total); multi-unit 19.72; single-unit 25.66 $/MWh | – | – | – | 2025 | https://www.nei.org/getContentAsset/47fa8caa-9b0d-4029-932c-07f902e82f4f/8d8ff8d6-b2ae-401b-a63c-f6b108e809d2/2024-Costs-in-Context-final.pdf | H |
| IEA/NEA 2020 | O&M 9.7–25.8 USD/MWh across 8 plants (US 11.6; France 14.3; Korea 18.4) | – | – | – | 2018 | IEA/NEA 2020 Table 3 | H (dated) |
| IEA/NEA 2020 (LTO case) | Fixed O&M 85 USD/kW-yr; variable 1.5 USD/MWh | 323 | 10.4 | 1.5 | 2018 | same, LTO note | H |
| PNNL-30225 (Apr 2021) | BWRX-300 inputs confidential (GEH design-to-cost); only LCOE 43.98 $/MWh @4% real WACC (40.6–56.1 for 3–7%) 2019$; 95% CF; 60 yr | – | – | – | 2019 | https://www.pnnl.gov/sites/default/files/media/file/PNNL%20report_Techno-economic%20assessment%20for%20Gen%20III+%20SMR%20Deployments%20in%20the%20PNW_April%202021.pdf | H (that inputs are not public) |
| OPG DNNP O&M | **Not disclosed** in 2026 OEB filing excerpt or press | – | – | – | – | OEB filing | – |
| "Asuega et al. 2023" | **Not located** under that name. The closest match is Egieya, Amidu & Hachaichi, "Small modular reactors: An assessment of workforce requirements and operating costs", Progress in Nuclear Energy 159 (May 2023): NPC of operating-staff salaries for a 300 MWe iPWR ≈ 431 m USD @10% (±8%); maintenance/construction 18%, operations 9%, management 8% of headcount | – | – | – | – | https://www.sciencedirect.com/science/article/abs/pii/S0149197023000677 | M |

### 3.2 Staffing

| Parameter | Low | Central | High | Unit | Source | Notes |
|---|---|---|---|---|---|---|
| GEH design claim, single BWRX-300 | | ~75 | | people, normal operations | IAEA ARIS status report 2020 | Vendor claim; excludes security/outage contractors; treat as floor. **M** |
| NuScale 12-module (924 MWe) plant – NRC-driven staffing | | ~300 incl. security | | people | PNNL-30225 (2021) | Proxy: ~0.32 FTE/MW |
| OPG DNNP 4 units | 3,700 "jobs per year over 65 years" (direct+indirect+induced, economic-impact figure, **not** plant headcount) | | | | OPG Oct 2025; OEB 2026 | Not a staffing number |
| Carbon Commentary comparison | Darlington 4 SMR "2,500 workers projected" vs Sizewell B ~900 | | | | Carbon Commentary May 2025 | Unclear basis; **L** |
| Polish PEJ (3×AP1000, 3.75 GW) | ~860 permanent operational staff (~0.23 FTE/MW) | | | | https://www.money.pl/gospodarka/elektrownia-jadrowa-w-choczewie-przepis-na-najbogatsza-gmine-w-kraju-6946809054423904a.html (2023) | Polish reference for large plant |
| **Recommended FTE per BWRX-300 unit (4-unit site, per-unit share incl. shared services & security)** | 120 | 180 | 250 | FTE/unit | judgement: between vendor 75 and NRC-scale ~0.3 FTE/MW | **L** |
| Polish salary – energy sector average (GUS, enterprise sector, section D electricity/gas/steam) | | 14,346 | | PLN gross/month, Jul 2026 | https://ssgk.stat.gov.pl/Wynagrodzenia_i_swiadczenia_spoleczne.html | H; national average 9,509 PLN |
| Polish energy-sector specialist salaries 2026 | 12,000 (schedulers) – 15,000 (designers) | 20,000–25,000 (managers/specialists) | 30,000–40,000 (senior/PM) | PLN gross/month | https://www.gazetaprawna.pl/praca/rynek-pracy/artykuly/11290684,pracownikow-brakuje-wiec-placa-coraz-wiecej-nawet-40-tys-zl-miesiec.html (Aug 2026) | H |
| Polish nuclear (PEJ / Bechtel-Westinghouse) offers | 80,000 | – | 300,000–387,000 | PLN gross/year | https://forsal.pl/gospodarka/aktualnosci/artykuly/11214116,placa-nawet-380-tys-zl-elektrownia-jadrowa-zatrudni-nawet-10-tys-osob.html (2026) | H (construction-phase roles) |
| **Recommended average loaded cost per nuclear FTE (Poland, 2026)** | 200k | 290k (≈20k PLN/month ×12 ×1.2 employer overheads) | 380k | PLN/yr | derived from above | M |
| ⇒ Staff cost per unit | 180 FTE × 290k = 52 m PLN/yr ≈ 174 PLN/kW-yr ≈ 46 USD/kW-yr (i.e. ~30–40% of a ~130 USD/kW-yr fixed O&M; the rest is materials, contractors, outage services, fees, insurance) | | | | derived | Consistent with US where labour ≈ 40–50% of O&M; Polish wage advantage partly offsets FOAK inefficiency. |

---

## 4. Fuel cycle, back-end and decommissioning fund

### 4.1 BWRX-300 fuel design parameters

| Parameter | Low | Central | High | Unit | Source | Conf. |
|---|---|---|---|---|---|---|
| Fuel | GNF2 10×10, 92 rods + 2 water rods, 14 part-length rods; ~185 kgU/assembly | | | | CNSC/GEH NEDO-33977 non-proprietary https://api.cnsc-ccsn.gc.ca/dms/digital-medias/CMD24-H3-Ref-BWRX-300-DNNP-GNF2-Fuel-Design-Qualification-and-BWR-Fuel-Licensing-Non-Proprietary-Information.PDF/object (2024); GE General Description | H |
| Core | 240 assemblies (⇒ ~44 tU core) | | | | GE General Description Table 2-1; IAEA ARIS 2020 | H |
| Enrichment | 3.4% average (ARIS 2020) | 3.4–4.2% | 4.95% max pellet | wt% U-235 | IAEA ARIS 2020; Fermi Energia; PNNL "<5%" | H for range; 24-month cycle likely needs higher average (INIS-MX-3701 study: 24-month at full power https://inis.iaea.org/records/dap7j-rys74) |
| Discharge burnup | 45 | 49.5 | 55 | GWd/tU (core average); pin 63 vs 70 limit | IAEA ARIS 2020 | H |
| Refuelling cycle | 12 | 18–24 | 24 | months | GE; PNNL; ARIS | H |
| Planned outage | 10 | 15 | 20 | days per refuelling; +25 days every 120 months (major inspection) | IAEA ARIS 2020 | M (vendor) |

### 4.2 Market prices (2026)

| Component | Spot (Aug/Sep 2026) | Long-term (2026) | Low / High for model | Source | Conf. |
|---|---|---|---|---|---|
| U3O8 | 89.68 USD/lb (31 Aug 2026, Cameco avg of UxC/TradeTech); intraday peak 100.25 (28 Jan 2026) | 96.50 USD/lb (Cameco, 31 Aug 2026); TradeTech LT 97.00 (30 Jun 2026, 18-yr high) | 70 / 130 (BofA target 130) | https://www.cameco.com/invest/markets/uranium-price ; https://www.uranium.info/press_releases.php ; https://discoveryalert.com/analysis/uranium-price-analysis-scarcity-enrichment/ | H |
| Conversion (NA) | 64–66 USD/kgU (late 2025, "near record") | ~52 USD/kgU term (late 2025); ~55.5 LT (Aug 2026, TradeTech via secondary post – unverified) | 40 / 70 | https://nunoamadomendes.substack.com/p/the-part-you-could-buy ; https://x.com/quakes99/status/2094695542769012832 (secondary) | M |
| Enrichment (SWU) | ~200 USD/SWU (end-2025 and mid-2026) | 166–173 USD/SWU (end-2025); ~183 LT (Aug 2026, secondary) | 150 / 220 | discoveryalert (Sep 2026); nunoamadomendes (2026) | M |
| Fabrication (BWR) | – | 300 USD/kgU (WNA 2021 example) | 300 / 450 | https://world-nuclear.org/information-library/economic-aspects/economics-of-nuclear-power | M (dated; BWR 10×10 with part-length rods typically pricier than PWR) |
| WNA reference calc (Sep 2021 prices) | 8.9 kg U3O8 @94.6 $/kg + 7.5 kgU conv @16 + 7.3 SWU @55 + 300 fab = 1,663 $/kg; 45 GWd/t → 0.46 c/kWh (4.6 $/MWh) | | | WNA | H (method) |

### 4.3 BWRX-300 fuel cost build-up (own calculation, tails 0.25%, 1% process loss, η = 34.5% net)

| Case | Enrich. / burnup | U3O8 (17.9 lb/kgU) | Conversion (6.83 kgU) | SWU (4.61) | Fab. | Total USD/kgU | MWh_e/kgU | **USD/MWh** | **PLN/MWh** |
|---|---|---|---|---|---|---|---|---|---|
| Low | 3.4% / 49.5 GWd/t; U 70 $/lb, conv 40, SWU 150, fab 300 | 1,256 | 276 | 691 | 300 | 2,523 | 410 | **6.2** | 23 |
| Central (LT prices) | 3.4% / 49.5; U 96.5, conv 55.5, SWU 183, fab 350 | 1,731 | 383 | 843 | 350 | 3,308 | 410 | **8.1** | 31 |
| Central (spot) | U 89.68, conv 65, SWU 200, fab 350 | 1,609 | 449 | 922 | 350 | 3,329 | 410 | 8.1 | 31 |
| 24-month variant | 4.2% / 55 GWd/t, LT prices | 2,171 | 480 | 1,143 | 350 | 4,144 | 455 | 9.1 | 35 |
| High | 3.4% / 49.5; U 130, conv 70, SWU 220, fab 450 | 2,332 | 483 | 1,014 | 450 | 4,279 | 410 | **10.4** | 40 |

Cross-checks: INL 2024 SMR fuel 10.0/11.0/12.1 USD/MWh (2022$, incl. disposal); MIT 9 USD/MWh; Rao et al. BWRX-300 advertised 8.44 USD/MWh; IEA/NEA 2020 front-end 7 + back-end 2.33 = 9.33 USD/MWh (2018$); NEI US fleet 2025 actual 5.95 USD/MWh (legacy contracts). Confidence in central 8 USD/MWh front-end: **M-H**. Note: first core (240 assemblies ≈ 44 tU ≈ 145 m USD at central prices) is normally capitalised.

### 4.4 Back-end / decommissioning – Polish law (verified)

| Item | Value | Source | Conf. |
|---|---|---|---|
| Legal basis | Art. 38d Prawo atomowe: operator of an NPP must create a decommissioning fund (fundusz likwidacyjny) and pay in per MWh produced, quarterly by the 15th of the following month; Council of Ministers sets the rate by regulation considering plant life, waste volume, decommissioning and waste costs | https://arslege.pl/fundusz-likwidacyjny/k264/a49139/ | H |
| **Rate** | **17.16 PLN per MWh of electricity produced**, covering (i) final management of spent fuel and radioactive waste and (ii) decommissioning of the NPP – Rozporządzenie Rady Ministrów z 10 października 2012 r. (Dz.U. 2012 poz. 1213), §1 | https://dziennikustaw.gov.pl/D2012000121301.pdf (full text retrieved: "na kwotę wynoszącą 17,16 zł od każdej wyprodukowanej w elektrowni jądrowej megawatogodziny (MWh) energii elektrycznej") | **H** |
| Status | In force ("obowiązujący", IN_FORCE), entry into force 21 Nov 2012, **never amended or indexed** (ELI record change date 14 Mar 2024 is metadata only) | https://api.sejm.gov.pl/eli/acts/DU/2012/1213 ; http://isap.sejm.gov.pl/isap.nsf/DocDetails.xsp?id=WDU20120001213 | H |
| In other currencies | 17.16 PLN = 4.52 USD = 3.93 EUR per MWh (Sep 2026 FX); in 2012 PLN it was worth ≈ 5.3 USD | derived | H |
| Reporting form | Quarterly statement template – Dz.U. 2021 poz. 393 (t.j.) | https://sip.lex.pl/akty-prawne/dzu-dziennik-ustaw/wzor-kwartalnego-sprawozdania-o-wysokosci-uiszczonej-wplaty-na-fundusz-17763869 | H |
| Adequacy check vs. international convention | IEA/NEA 2020: decommissioning = 15% of overnight cost; back-end 2.33 USD/MWh. For a 300 MW unit at ~9,000 USD/kW overnight, 15% = 405 m USD; 17.16 PLN/MWh × 2.46 TWh/yr × 60 yr ≈ 2.5 bn PLN ≈ 670 m USD nominal (undiscounted, no fund return) – so the statutory rate roughly covers decommissioning + waste only if invested and if unit costs stay near 9,000 USD/kW; it is **not indexed** and was set for a 2012 large-reactor programme. Expect revision (the 2024 industry commentary notes 2011-era financial parameters are "likely to increase") | https://piu.org.pl/wp-content/uploads/2024/03/WU%202023-04_02_Sroka_Wajda.pdf ; IEA/NEA 2020 | M |
| US benchmark | Decommissioning 0.1–0.2 c/kWh (1–2 USD/MWh); back-end up to 10% of per-kWh cost | WNA Economics page | M |
| Recommended model treatment | Statutory 17.16 PLN/MWh as the cash outflow (low = 17.16 nominal frozen; central = 17.16 indexed to CPI from 2012 ≈ 26 PLN/MWh in 2026 terms; high = 35 PLN/MWh if re-based to a BWRX-300 cost of 15% × capex). Separately, do not double-count a decommissioning provision. | judgement | M |

---

## 5. Operating parameters and flexibility

| Parameter | Low | Central | High | Unit | Source | Conf. |
|---|---|---|---|---|---|---|
| Thermal power | | 870 | | MWt | GE General Description Table 2-1; ARIS | H |
| Gross electrical | | ~316 (GE Gen. Desc.) / 300 (PNNL "gross") | | MWe | GE 2023/24; PNNL 2021 | H (inconsistent labelling across sources) |
| Net electrical | 270 | 290–300 | 300 | MWe | ARIS 2020 ("270–290 MWe net to grid, 300 gross"); GE/OSGE "up to 300 MW" | M – **use 300 MWe net central, sensitivity 285** |
| Design life | | 60 | 80 (Lazard v19 range for US nuclear) | years | GE; ARIS; Polityka Insight (">60 with potential 20-yr extension") | H |
| Capacity factor (vendor target) | | 95% | | % lifetime (MWe-yrs delivered / capacity × life) | ARIS 2020; GE Apr 2026 article ("~95% incl. planned refuelling outages") https://www.gevernova.com/nuclear/resources/article/bwrx-300-dispatchable-power-grid-decarbonization ; PNNL ">95%" | H (claim) |
| Capacity factor (modelling convention) | 85% (MIT FOAK, IEA/NEA) | 90–93% (INL/ATB 93%; MIT 93% after 20 yr; Lazard 89–94%) | 95% | % | MIT 2024; ATB 2025; IEA/NEA 2020; Lazard v19 | H |
| World fleet actuals | 81.5% (2023) → 83% (2024); BWRs achieve the highest CFs on average; >60% of reactors >80% | | | % | https://world-nuclear.org/news-and-media/press-statements/world-nuclear-performance-report-2025-nuclear-delivers-record-breaking-year-in-electricity-generation ; https://world-nuclear.org/images/articles/World-Nuclear-Performance-Report-2024.pdf | H |
| Forced outage rate / UCLF | 1% | 2–3% | 5% (FOAK first years) | % of period | Not retrieved from PRIS (site redirected to analytics app); proxy from world CF distribution and US fleet ~90%+ CF | L (proxy) |
| Planned outage | 10 d / 12 mo | 15 d / 18–24 mo + 25 d / 10 yr | 20 d + FOAK extended outages | days | ARIS 2020 | M |
| Load-following range | | 50–100% | | % power, daily | GE Gen. Desc. §3.2; ARIS; Fermi | H |
| Ramp rates | 0.5%/min (50–90%) | 2%/min (90–100%) | SCCRI 0.8%/s for fast frequency response | % Pr/min | GE General Description §3.2 | H |
| EUR requirement (for comparison) | 50–100% at ≥3% Pr/min; 2 cycles/day, 5/week, 200/yr over 90% of the cycle | | modern designs ≥5%/min | | NEA 2011 "Technical and Economic Aspects of Load Following" https://www.oecd-nea.org/upload/docs/application/pdf/2021-12/technical_and_economic_aspects_of_load_following_with_nuclear_power_plants.pdf | H |
| ⇒ BWRX-300 vs EUR | Meets power range; **0.5%/min in the 50–90% band is below the EUR 3%/min** – a 50→100% ramp takes ~85 min | | | | derived | M |
| NREL ATB flexibility assumption for SMRs | | 10%/min | | | ATB 2025 | H (generic, optimistic vs GE spec) |
| Capability loss from load following (French fleet) | | 1.2% | 2% | % UCF | NEA 2011 | H |

### 5.1 Two physical mechanisms of part-load and their fuel/cost implications

1. **Reactor thermal power reduction (control rods; BWRX-300 is natural-circulation, so no recirculation-flow control – rods and feedwater-temperature only).** Thermal power tracks electrical output roughly proportionally; fuel *burn* (fissions) per MWh is essentially unchanged, so **fuel cost per MWh generated is ~constant** and the fuel *saved* during the cycle extends the cycle length (energy is banked, not lost). However, the plant's fixed costs (capital, staff, fund contributions in PLN/MWh are variable so they fall) are spread over fewer MWh, so **LCOE rises ~1:1 with lost load factor** – NEA 2011: 85%→75% load factor raises nuclear LCOE ~10–12% at 5% discount, because fuel is only ~16% of generation cost and "one cannot make savings on the fuel cost while not producing electricity" (i.e., the reactivity saved has little market value if the plant is capacity-limited later). Minor negatives: xenon transients limit manoeuvring late in cycle (Blanchard & Massol 2025 https://www.sciencedirect.com/science/article/pii/S0377221725002577), slight valve/component wear ("slight increase of the maintenance costs", NEA 2011), and a small **thermal-efficiency penalty at part load** (turbine off-design): PNNL-30225 notes efficiency "will also decline if load following is to be undertaken" and shows a 28%→32% efficiency change moving LCOE 48→44 USD/MWh, i.e., ~1 USD/MWh per efficiency point. Sources: IAEA NP-T-3.23 (2018) https://www-pub.iaea.org/MTCD/Publications/PDF/P1756_web.pdf ; NEA 2011; PNNL 2021.

2. **Turbine (steam) bypass to the condenser at constant reactor power.** Used for fast, short-duration output reductions and frequency response: "a quick and short duration of reduction in electrical output without changing the thermal power … by dumping (bypassing the turbine and directing some steam to the main condenser)" (IAEA NP-T-3.23, 2018). Here **fuel is consumed at full rate while MWh are not sold → fuel cost per delivered MWh rises inversely with output** (at 50% bypass, fuel cost/MWh doubles to ~16 USD/MWh) and condenser/heat-sink loading is unchanged. It is only economic for minutes-to-hours balancing when the ancillary-service price exceeds the wasted-fuel value. Bypass capacity for BWRX-300 is not quantified publicly (GE General Description mentions a turbine bypass system without %; typical BWR designs 25–100%). Confidence **M**.

### 5.2 Cost of cycling – what exists

| Source | Finding | URL | Conf. |
|---|---|---|---|
| NEA 2011 | No EUR/MW-per-cycle number; qualitative "slight increase" in maintenance; 1.2–2% UCF loss in France | NEA 2011 | H |
| IAEA NP-T-3.23 (2018) | Qualitative: increased wear/erosion-corrosion, more frequent maintenance, fuel-utilisation and cycle-length effects; no $ figures | IAEA 2018 | H |
| Blanchard & Massol (EJOR 2025) | Literature: "increasing nuclear flexibility comes at little to no additional cost"; models no explicit cycling cost | EJOR 2025 | M |
| Jenkins et al. (Applied Energy 2018) | MILP with xenon and cycle-reactivity constraints; system benefits quantified; no explicit $/MW cycling cost in abstract | https://www.sciencedirect.com/science/article/abs/pii/S0306261918303180 | M |
| JRC (Lokhov) 2010 | "Load-following operating mode … incidence on O&M costs" – report exists but not retrieved | https://publications.jrc.ec.europa.eu/repository/handle/JRC60700 | – |
| **Not found** | A published EUR/MW-per-cycle wear cost for nuclear (unlike the well-known NREL/Intertek fossil cycling costs) | – | – |
| **Proxy recommendation** | Model cycling as (a) lost MWh (dominant), (b) +1–2% UCF loss if daily load-following is routine, (c) +0–2% on fixed O&M, (d) thermal efficiency −1 to −2 points at 50–70% load (≈ +0.5–1 USD/MWh fuel), (e) turbine-bypass hours charged full fuel at zero output. No per-cycle EUR/MW term. | judgement | L |

---

## 6. Lifetime, degradation, refurbishment

| Parameter | Low | Central | High | Unit | Source | Conf. |
|---|---|---|---|---|---|---|
| Design/licence life | 60 | 60 | 80 (US practice via renewals; Lazard v19 60–80) | years | GE; Lazard v19 | H |
| Major mid-life refurbishment / LTO capex | 450 | 700 | 950 | USD/kW (≈1,710–3,610 PLN/kW), typically at 30–40 years, 2-year refurbishment, incl. 5% contingency | NEA EGLTO 2021 https://www.oecd-nea.org/upload/docs/application/pdf/2021-07/nea_7524_eglto.pdf ; IEA/NEA 2020 LTO case (1,000 USD/kW mean) | H (large-reactor data; SMR proxy) |
| MIT refurbishment allowance | | 6.25 USD/MWh (AP1000, 80-yr life) | | USD/MWh | MIT ANP-201 | H |
| US fleet ongoing capital | | 9.69 USD/MWh (2025; +24% y/y due to life-extension upgrades); ~8.80 multi-unit / 13.64 single-unit | | USD/MWh | NEI Aug 2026 | H |
| Major-inspection outage | | 25 days every 120 months | | days | IAEA ARIS 2020 | M |
| Output degradation | Not published for BWRX-300; existing BWR fleet shows no systematic derating (BWRs have the highest CFs) – model 0%/yr central, sensitivity −0.1%/yr | | | | WNPR 2024 | L |
| Recommended model | Sustaining capex 2–3% of overnight per decade (≈ 8–10 USD/MWh) + one LTO package of 700 USD/kW at year 35–40 if life >60 is modelled | | | | judgement (NEI, NEA) | M |

---

## 7. Insurance, liability, regulatory fees, grid connection, taxes (Poland)

| Item | Value | Source | Conf. |
|---|---|---|---|
| Liability regime | Vienna Convention 1963 + Joint Protocol 1988 apply in Poland; Prawo atomowe Ch. 12 (art. 100–108) – operator's liability capped at **300 million SDR** (art. 102), mandatory insurance up to that sum (art. 103) | https://piu.org.pl/wp-content/uploads/2024/03/WU%202023-04_02_Sroka_Wajda.pdf (Wiadomości Ubezpieczeniowe 4/2023); https://sip.lex.pl/akty-prawne/dzu-dziennik-ustaw/prawo-atomowe-16890219/roz-12 | H |
| 300 m SDR in PLN | ≈1.55–1.65 bn PLN (2024 articles) | wnp.pl Sep 2024 https://www.wnp.pl/energia/ubezpieczenie-elektrowni-jadrowej-w-polsce-mamy-powazny-problem,873053.html | H |
| Insurance-market gap | Polish insurers' combined nuclear capacity ~200 m PLN – "several times lower" than required; a Polish nuclear pool and alignment with international conventions needed before 2030; benchmarks: Germany 2.5 bn EUR (unlimited), France 700 m EUR, Belgium 1.2 bn EUR, US ~500 m USD/reactor | wnp.pl 2024 | H |
| Annual premium | **Not published for Poland.** Proxy: international practice 0.2–0.5% of insured limit → 3–8 m PLN/yr per site for 300 m SDR third-party cover; plus property/BI insurance ~0.1–0.3% of replacement value (≈ 8–25 m PLN/yr per unit at 8 bn PLN). Treat as part of fixed O&M (~1–3 USD/kW-yr). | judgement | L |
| Expected change | Liability limit and minimum insurance set in 2011 "likely to increase" (possible move to Paris/Brussels-type 700 m EUR levels) | PIU 2024 | M |
| PAA licence fees (per application) | Construction permit 5.0 m PLN; commissioning (rozruch) 1.9 m PLN; operation 1.9 m PLN; decommissioning 2.0 m PLN; statutory decision times 24 / 9 / 6 / 9 months | DISE / W. Wrochna presentation https://dise.org.pl/prezentacja_Wojciech_Wrochna.pdf | M (secondary; check current Prawo atomowe art. 39–39a fee table) |
| PAA ongoing supervision fee | No annual supervision fee found in Polish law (PAA is budget-funded; unlike NRC hourly fee recovery). Model 0, or 0.5–1 m PLN/yr for inspections/expert reviews borne by operator. | searches on gov.pl/paa | M (absence) |
| Grid connection – PSE conditions | Warunki przyłączenia issued 20/21 Nov 2024 to "BWRX-300 Stawy Monowskie Sp. z o.o." for **1,329.6 MW** at SE Byczyna (4 units); nuclear gets 10 years (vs 2) to sign the connection agreement. **Stalowa Wola: no EJ entry in the PSE applicants list as of 30 Jun 2026** (only a 240 MW storage entry at SE Stalowa Wola dated 1 Apr 2026 and the legacy CHP). PSE planning: 1,250 MW net SMR by 2036, 1,874 MW by 2040. | PSE list https://www.pse.pl/documents/20182/51490/Wykaz_podmiotow_ubiegajacych_sie_o_przylaczenie.pdf (state 30 Jun 2026); https://energetyka24.com/atom/wiadomosci/projekt-smr-z-reaktorami-bwrx-300-z-warunkami-przylaczenia-teraz-osge-ma-dwa-lata-na-umowe ; https://globenergia.pl/polska-szykuje-sie-na-atom-w-planach-duza-elektrownia-i-prawie-2-gw-malych-reaktorow-smr/ | H |
| Grid connection – fees (>1 kV, after 13 Mar 2026 Energy Law amendment) | Application fee 1 PLN/kW (cap 100k PLN); advance 60 PLN/kW; performance bond 30 PLN/kW (≤100 MW) / 60 PLN/kW (>100 MW), cap 12 m PLN. Actual connection charge for sources at 110 kV+ = negotiated share of real cost (not found quantified). | https://www.energiadlalodzi.pl/wp-content/uploads/2026/04/Oplaty-przylaczeniowe-zgodnie-z-nowelizacja.pdf | M |
| Grid connection – cost proxy | Stalowa Wola has an existing 220/110 kV node (EC Stalowa Wola, 422 MW connection) – so a 1,200 MW site likely needs a new 400 kV bay/line. Proxy 150–400 m PLN for 4 units (PNNL US benchmarks ~4–8 USD/kW for terminals + line costs). Confidence L. | PSE list; PNNL-30225 | L |
| Property tax (podatek od nieruchomości) | Structures (budowle) taxed at 2% of value annually; PEJ host municipalities expected to become "among the richest" (50% to host, 50% to neighbours); no PLN figure published. Proxy: 2% × taxable structure share (~30–50% of capex) ≈ 50–80 m PLN/yr per 300 MW unit – material (≈2–3 USD/MWh). Verify exemption negotiations. | https://www.money.pl/gospodarka/elektrownia-jadrowa-w-choczewie-przepis-na-najbogatsza-gmine-w-kraju-6946809054423904a.html ; EY 2024 | L |
| Environmental fees | Closed-loop cooling at Stalowa Wola (0.8–1.2 thousand m³/h vs 50–90 thousand for once-through; San River insufficient) → water fees minor; cooling-tower capex and ~1–2% net-output penalty vs once-through | https://www.gazetaprawna.pl/biznes/energetyka/artykuly/11245284,mala-elektrownia-atomowa-w-stalowej-woli-powstanie-w-latach-30.html | M |
| Site status (Sep 2026) | Environmental decision application to GDOŚ filed Apr 2026, scope set 10 Jun 2026 (transboundary); Sejm committee approved land transfer 16 Jul 2026; ARP letter of intent; target "two blocks by 2035"; Stalowa Wola is 3rd/4th in OSGE sequence after Włocławek (2032) and Stawy Monowskie | https://www.wnp.pl/energia/projekt-osge-przyspiesza-jest-decyzja-sejmowej-komisji-ws-stalowej-woli,1081775.html ; https://arp.pl/pl/aktualnosci/arp-sa-i-osge-sp-z-oo-podpisaly-list-intencyjny-dotyczacy-wspolpracy-przy-projekcie-budowy-malych-reaktorow-modulowych-w-stalowej-woli/ | H |

---

## 8. Published LCOE for BWRX-300 and nuclear ranges

| Source | LCOE | Key assumptions | URL | Year | Conf. |
|---|---|---|---|---|---|
| OPG / IESO (Darlington 4 units) | 14.9 CAD c/kWh ≈ 106 USD/MWh ≈ 404 PLN/MWh, 60-yr life, "contingent on federal ITC"; alternative wind+solar+storage 13.5–18.4 c/kWh | regulated cost recovery; CAD 20.9 bn | WNN 2025; https://www.cbc.ca/lite/story/1.7529338 | May 2025 | H |
| MIT ANP-201 | FOAK 194 USD/MWh (with ITC/LPO); 8-parallel 237 unsubsidised / 167 subsidised; sequential follow-on 135→123 | 2024$, 50/50 D/E, 6.5% debt / 12.5% equity, 85→93% CF, 80-yr | MIT 2024 | 2024 | H |
| PNNL-30225 (GEH target pricing) | 44 USD/MWh @4% real WACC; 40.6–56.1 for 3–7%; ±3–5 USD/MWh per 5-pt CF change | 2019$, 95% CF, 60 yr, public-power financing | PNNL 2021 | 2021 | H (as GEH target; superseded) |
| INL 2023 lit. review citing GEH | 44–51 USD/MWh (2019$) | same lineage | INL 2023 | 2023 | M |
| GEH (ARIS 2020) | 35–50 USD/MWh target | vendor | ARIS 2020 | 2020 | L |
| Nøland et al. (INL-based) | 2030 median 88 (66–116) USD/MWh @5% WACC | 300 MW SMR, 2024$ | IAEA paper 2024 | 2024 | M |
| Lazard v18 | US new nuclear 141–220 USD/MWh unsubsidised | Vogtle-based, 84 mo, 92–89% CF | Lazard Jun 2025 | 2025 | H |
| Lazard v19 | 175–255 USD/MWh unsubsidised | 12,300–17,570 USD/kW; 60–84 mo; 89–94% CF; 60–80 yr | Lazard Jul 2026 | 2026 | H |
| IEA/NEA 2020 | New nuclear 39–62 (3%), 53–102 (7%), 67–146 (10%) USD/MWh (2018$), 85% CF, 60 yr, 7-yr build; LTO 25–50 | median overnight 3,370 | IEA/NEA 2020 | 2020 | H (dated) |
| Rao, Kaffine & Hodge (2026) | SMRs at "manufacturer-advertised" operating costs unviable without subsidies above historic levels; avg SMR opex ≈ 45.5 USD/MWh (fuel 23.7 avg across designs) | | https://arxiv.org/abs/2609.08929 | 2026 | M |
| OSGE expectation (CfD) | 115–135 EUR/MWh (≈ 502–589 PLN/MWh) for first 14 units; declining with volume; ME calls ~125 EUR/MWh "relatively high" | | zielonagospodarka 2025; Bankier Jul 2026 | 2025–26 | H |
| Fermi Energia | "below 100 EUR/MWh" | 2 units, Estonia | fermi.ee | 2025/26 | L |
| Polish large-nuclear CfD (PEJ, EC notification) | 470–550 PLN/MWh real strike (base), 600–680 with +40% capex, 60-yr contract, 92.7% CF, capex 192 bn PLN nominal | | https://www.bankier.pl/wiadomosc/Do-550-zl-za-MWh-To-cena-w-kontrakcie-roznicowym-dla-polskiej-elektrowni-jadrowej-8896336.html | 2025 | H |

---

## 9. Recommended central assumptions for the Polish model (PLN, 2026 real, per 300 MWe-net unit at a 4-unit Stalowa Wola site)

| Parameter | Low | **Central** | High | Unit | Basis |
|---|---|---|---|---|---|
| Overnight EPC + owner's cost, **unit 1 (Polish FOAK)** | 30,000 | **42,000** | 56,000 | PLN/kW | Darlington unit-1 core excl. common+contingency+IDC ≈ 36,200 PLN/kW (2024 CAD) escalated ~5% and ×1.05–1.15 for Polish first-of-fleet/site; MIT FOAK ex-owner 53,200; INL conservative 38,000 |
| Contingency, unit 1 | 15% | **20%** | 30% | % of overnight | OPG 18% of RQE (≈27% of core); IEA/NEA 15% |
| Common/shared site infrastructure (4-unit site, allocated to unit 1 or spread) | 3,500 | **5,000** | 7,000 | PLN/kW of unit 1 (i.e., 1.05–2.1 bn PLN for the site) | OPG 1.1–1.6 bn CAD (= 3.0–4.3 bn PLN) for a greenfield lakeside site with cooling tunnels; Stalowa Wola brownfield with existing grid node and closed-loop cooling → lower |
| Overnight cost, **units 2–4** (learning) | 24,000 | **32,000** | 42,000 | PLN/kW | Darlington unit 4 ≈ 37,100 PLN/kW all-in incl. IDC → ~28,000–30,000 overnight; OSGE 1.2–2.0 bn EUR = 17,500–29,100 PLN/kW; INL moderate 30,400; 9.5–15% LR |
| Learning rate for fleet beyond unit 4 | 5% | **9.5%** | 15% | per doubling | INL 2024 / ATB 2025 central; INL range |
| Construction duration unit 1 (first structural concrete → COD) | 48 | **60** | 72 | months | Darlington ~53–66; ATB moderate 55 |
| Construction duration units 2–4 | 36 | **48** | 60 | months | ATB adv/mod; vendor 24–36 not credible for first fleet |
| Spend profile | uniform | **S-curve 12/24/30/22/12% over 5 yrs, ~10–15% pre-first-concrete** | front-loaded (long-lead RPV) | % per year | IEA/NEA uniform; INL normalised curve; OPG early spend |
| Pre-construction/development cost (licensing, EIA, FEED, PAA fees 6.9 m PLN) | 300 | **500** | 900 | m PLN per site | OPG 105 m CAD 2020–22 preliminary + 521 m CAD released for units 2–4 definition; OSGE "hundreds of millions PLN" for confirmatory studies |
| Net output | 285 | **300** | 300 | MWe | ARIS 270–290 vs GE 300; closed-loop cooling penalty |
| Capacity factor, years 1–3 / steady state | 80% / 88% | **85% / 92%** | 90% / 95% | % | MIT 85→93; ATB 93; vendor 95; BWR fleet best-in-class |
| Planned outage | 15 d / 18 mo + 25 d / 10 yr | **15 d / 18–24 mo + 25 d / 10 yr** | 25 d / 12 mo | days | ARIS |
| Fixed O&M (excl. fuel, incl. staff, insurance, materials, contractors), 4-unit site | 400 | **520** | 820 | PLN/kW-yr (≈ 105 / 137 / 216 USD/kW-yr) | INL Adv/Mod/Cons 448/517/821 PLN; EIA 471; Lazard 517–600; Polish labour ~35% of total at 180 FTE × 290k PLN |
| Fixed O&M single-unit phase (before units 2–4) | ×1.3 | **×1.5** | ×1.8 | multiplier on 4-unit value | INL O&M multiplier 0.5–0.7 for multi-unit; MIT 38.7 vs 28.2 $/MWh |
| Variable O&M (non-fuel) | 8 | **11** | 15 | PLN/MWh (≈ 2.2–3.9 USD/MWh) | INL 2.2–2.8; EIA 3.23; Lazard 4.4–5.15 |
| Staff | 120 | **180** | 250 | FTE per unit (site share) | §3.2 |
| Loaded staff cost | 200 | **290** | 380 | k PLN/FTE-yr | GUS energy-sector 14.3k/month; market 20–25k for nuclear-grade specialists ×1.2 |
| Fuel (front-end) | 23 | **31** | 40 | PLN/MWh (6.2 / 8.1 / 10.4 USD/MWh) | §4.3 own build-up; LT prices Aug 2026 |
| First core (capitalised) | 450 | **550** | 700 | m PLN per unit | 44 tU × 3,300 USD/kgU × 3.80 |
| Spent fuel + decommissioning fund (statutory) | 17.16 (frozen nominal) | **26** (CPI-indexed equivalent; expect regulation update) | 35 | PLN/MWh | Dz.U. 2012 poz. 1213; IEA/NEA 15% of overnight |
| Nuclear liability insurance + property insurance | 10 | **20** | 40 | m PLN/yr per unit (≈ 3–13 PLN/kW-yr) | proxy §7 – included in fixed O&M range above; show separately if desired |
| Property tax | 30 | **60** | 80 | m PLN/yr per unit | 2% × taxable structures; **not** in the O&M benchmarks above (US benchmarks include US property taxes of different structure) |
| Grid connection (4-unit site) | 150 | **250** | 400 | m PLN | proxy §7 |
| Sustaining capex | 15 | **25** | 40 | PLN/MWh (≈ 4–10 USD/MWh) | NEI 8.8–13.6 USD/MWh (US fleet incl. LTO); MIT 6.25 |
| LTO / mid-life refurbishment (if life >60 modelled) | 1,700 | **2,700** | 3,600 | PLN/kW at year 35–40 | NEA EGLTO 450–950 USD/kW |
| Design life | 60 | **60** | 80 | years | GE |
| Load-following: range / ramp | 50–100% / 0.5%/min (50–90%), 2%/min (90–100%) | | | | GE Gen. Desc. |
| Load-following cost model | lost MWh only | **lost MWh + 1.2% UCF loss + 1% fixed O&M + η −1.5 pt at 50–70% load; turbine-bypass hours at full fuel burn** | + 2% UCF, + 2% O&M | | NEA 2011; IAEA 2018; PNNL 2021 |
| Reference CfD strike (for revenue-side calibration) | 500 | **545** | 590 | PLN/MWh (115–135 EUR) | OSGE 2025; ME Jul 2026 |

---

## 10. Explicit uncertainties and gaps

1. **No BWRX-300 overnight cost has ever been published.** Darlington's CAD 7.7 bn/20.9 bn are all-in nominal figures (incl. IDC, escalation, contingency); only the OEB 2026 filing decomposes unit 1 (5.1 core / 1.4 contingency / 1.2 interest). Units 2–4 are Class-4 estimates. TVA has no public estimate; the 17,949 USD/kW figure is second-hand.
2. **OSGE's figures (1.2–2.0 bn EUR/unit) have moved by ±50% in three years and are not backed by a published estimate;** the Ministry of Energy itself says costs will be known only after the Canadian reference unit (2030). The Polish SMR roadmap promised for end-July 2026 was not found published as of 20 Sep 2026; no EC state-aid notification for OSGE exists yet.
3. **Escalation basis:** benchmarks are in 2018–2024 dollars; no uniform inflation adjustment to 2026 real PLN was applied (add ~5–8% for 2024$→2026$; ~25% for 2018$→2026$). FX at one date (18 Sep 2026).
4. **O&M:** no operating BWRX-300 exists; benchmark spread is 118–216 USD/kW-yr (INL) up to 222–305 USD/kW-yr (MIT). Vendor 75-FTE claim vs NRC-style ~300 per plant. Polish wage levels are a genuine advantage, but FOAK operations, security and regulatory expectations are not yet defined by PAA for SMRs.
5. **Fuel:** enrichment for the licensed Darlington core is redacted (NEDO-33977); 3.4% average is a 2020 vendor figure and a 24-month cycle probably implies ~4–4.5%. SWU and conversion 2026 LT prices come partly from secondary posts (UxC/TradeTech are paywalled). Fabrication price for GNF2 not public.
6. **Decommissioning fund:** 17.16 PLN/MWh (2012, verified full text, still in force) is un-indexed and pre-dates SMRs; a revision is likely once the first CfD is negotiated – the model should carry a scenario at 25–35 PLN/MWh.
7. **Liability/insurance:** 300 m SDR cap verified; premiums not public; Polish insurance pool capacity gap (~200 m PLN vs ~1.6 bn PLN) unresolved – a cost or a state-backstop item for 2030+.
8. **Grid:** PSE conditions exist only for Stawy Monowskie (1,329.6 MW, Nov 2024); Stalowa Wola has no listed nuclear connection application as of 30 Jun 2026; connection cost share not quantified.
9. **Flexibility economics:** no peer-reviewed EUR/MW-per-cycle wear cost for nuclear; GE's 0.5%/min in the 50–90% band is below EUR's 3%/min; turbine-bypass capacity not disclosed.
10. **Forced-outage rate for BWRX-300** is unknowable pre-operation; PRIS UCLF pages could not be retrieved (site redirect). 2–3% central is a fleet-average proxy; FOAK first 3 years likely 5–10%.
11. **Property tax** (2% of structures) could be one of the largest "other" opex items in Poland (~2–3 USD/MWh) and is absent from all US-derived O&M benchmarks; exemptions or valuation rules for nuclear structures are unsettled.
12. **"Asuega et al. 2023" could not be located**; the nearest peer-reviewed workforce study is Egieya et al. (2023). If the caller has the exact citation, staffing numbers should be re-checked against it.

## Source list (distinct, ≥25)

1. WNN – How is CAD 20.9 bn calculated (2025) https://www.world-nuclear-news.org/articles/what-is-the-budget-for-canadas-first-smr-project
2. OPG OEB filing EB-2025-0297 D2-4-1 (updated May 2026) https://files.opg.com/wp-content/uploads/2026/05/D2-04-01-Darlington-New-Nuclear-Project-Overview_Updated_20260521_260522_191835.pdf
3. OPG Q1-2025 financial statements https://www.oeb.ca/sites/default/files/2025%20Q1%20Financial%20Statements.pdf
4. World Nuclear Industry Status Report / Globe and Mail (2025) https://www.worldnuclearreport.org/Ontario-s-Darlington-SMR-project-to-cost-nearly-21-billion-significantly-higher
5. CBC (May 2025) https://www.cbc.ca/lite/story/1.7529338
6. OPG milestones (Oct 2025) https://www.opg.com/news-resources/newsroom/our-stories/story/opg-marks-new-milestones-in-construction-of-g7s-first-small-modular-reactor/
7. NucNet basemat (May 2026) https://www.nucnet.org/news/canada-s-opg-completes-installation-of-reactor-basemat-for-first-darlington-smr-5-5-2026
8. WNN – OPG operating-licence application (Apr 2026) https://www.world-nuclear-news.org/articles/opg-applies-for-operating-licence-for-bwrx-300-smr
9. SACE on TVA (2025/26) https://cleanenergy.org/news/rush-to-build-new-nuclear-power-tva-and-administration-ignore-cost-and-safety/
10. Neutron Bytes – DOE $800 m (Dec 2025) https://neutronbytes.com/2025/12/05/doe-opens-its-checkbook-for-smrs-plans-to-spend-800m/
11. ANS – Clinch River SER (Jul 2026) https://www.ans.org/news/2026-07-01/article-8174/clinch-river-construction-permit-recommendation-follows-safety-evaluation/
12. WPLN – TVA (Oct 2025) https://wpln.org/post/nuclear-hype-is-building-tva-plans-to-buy-in/
13. MIT ANP-TR-201 (Jul 2024) https://web.mit.edu/kshirvan/www/research/ANP201%20TR%20CANES.pdf
14. INL/RPT-24-77048 meta-analysis (Apr 2024) https://gain.inl.gov/content/uploads/4/2024/11/INL-RPT-24-77048-Meta-Analysis-of-Adv-Nuclear-Reactor-Cost-Estimations.pdf
15. INL/RPT-23-72972 literature review (Oct 2023) https://gain.inl.gov/content/uploads/4/2024/11/INL-RPT-23-72972-Literature-Review-of-Adv-Reactor-Cost-Estimates.pdf
16. INL/RPT-24-7767 cost-reduction pathways (Jun 2024) https://inldigitallibrary.inl.gov/sites/sti/sti/Sort_109810.pdf
17. NREL/NLR ATB 2025 nuclear https://atb.nlr.gov/electricity/2025/nuclear
18. EIA AEO2025 EMM assumptions https://docs.catalyst.coop/pudl/en/nightly/_downloads/fcef77222b0e504440dfa03fa3984d08/eiaaeo_2025_electricity_market_assumptions.pdf
19. Lazard LCOE+ v18 (Jun 2025) https://www.lazard.com/media/uounhon4/lazards-lcoeplus-june-2025.pdf
20. Lazard LCOE+ v19 (Jul 2026) https://www.lazard.com/media/kcfconhf/lazards-lcoeplus_vf.pdf
21. IEA/NEA Projected Costs of Generating Electricity 2020 https://iea.blob.core.windows.net/assets/ae17da3d-e8a5-4163-a3ec-2e6fb0b5677d/Projected-Costs-of-Generating-Electricity-2020.pdf
22. NEA EGLTO (2021) https://www.oecd-nea.org/upload/docs/application/pdf/2021-07/nea_7524_eglto.pdf
23. NEA Load Following (2011) https://www.oecd-nea.org/upload/docs/application/pdf/2021-12/technical_and_economic_aspects_of_load_following_with_nuclear_power_plants.pdf
24. IAEA NP-T-3.23 Non-baseload Operation (2018) https://www-pub.iaea.org/MTCD/Publications/PDF/P1756_web.pdf
25. IAEA ARIS BWRX-300 status report (2020) https://clara.nz/docs/hardware-unsorted/iaea/BWRX-300_2020.pdf
26. GE Vernova BWRX-300 General Description https://www.gevernova.com/content/dam/gevernova-nuclear/global/en_us/documents/carbon-free-power/005N9751-BWRX-300-General-Description.pdf
27. GE Vernova BWRX-300 product page https://www.gevernova.com/nuclear/carbon-free-power/bwrx-300-small-modular-reactor ; dispatchable-power article (Apr 2026) https://www.gevernova.com/nuclear/resources/article/bwrx-300-dispatchable-power-grid-decarbonization
28. CNSC/GEH NEDO-33977 GNF2 fuel (2024) https://api.cnsc-ccsn.gc.ca/dms/digital-medias/CMD24-H3-Ref-BWRX-300-DNNP-GNF2-Fuel-Design-Qualification-and-BWR-Fuel-Licensing-Non-Proprietary-Information.PDF/object
29. INIS-MX-3701 BWRX-300 fuel management https://inis.iaea.org/records/dap7j-rys74
30. PNNL-30225 (Apr 2021) https://www.pnnl.gov/sites/default/files/media/file/PNNL%20report_Techno-economic%20assessment%20for%20Gen%20III+%20SMR%20Deployments%20in%20the%20PNW_April%202021.pdf
31. Nøland et al., IAEA SMR cost projections (2024) https://conferences.iaea.org/event/374/papers/31012/files/12710-IAEA_Paper-57_SMR_final_V3.pdf
32. Rao, Kaffine & Hodge (2026) https://arxiv.org/abs/2609.08929
33. Egieya et al., Prog. Nucl. Energy 159 (2023) https://www.sciencedirect.com/science/article/abs/pii/S0149197023000677
34. Blanchard & Massol, EJOR (2025) https://www.sciencedirect.com/science/article/pii/S0377221725002577
35. Jenkins et al., Applied Energy (2018) https://www.sciencedirect.com/science/article/abs/pii/S0306261918303180
36. NEI Nuclear Costs in Context (Aug 2026) https://www.nei.org/getContentAsset/47fa8caa-9b0d-4029-932c-07f902e82f4f/8d8ff8d6-b2ae-401b-a63c-f6b108e809d2/2024-Costs-in-Context-final.pdf
37. WNA Economics of Nuclear Power https://world-nuclear.org/information-library/economic-aspects/economics-of-nuclear-power
38. WNA World Nuclear Performance Report 2025 (press) https://world-nuclear.org/news-and-media/press-statements/world-nuclear-performance-report-2025-nuclear-delivers-record-breaking-year-in-electricity-generation ; WNPR 2024 PDF https://world-nuclear.org/images/articles/World-Nuclear-Performance-Report-2024.pdf
39. Cameco uranium price page (Aug 2026) https://www.cameco.com/invest/markets/uranium-price
40. TradeTech press releases (2026) https://www.uranium.info/press_releases.php
41. Discovery Alert uranium/SWU analysis (Sep 2026) https://discoveryalert.com/analysis/uranium-price-analysis-scarcity-enrichment/
42. Nuno Amado Mendes, fuel-cycle price notes (2026) https://nunoamadomendes.substack.com/p/the-part-you-could-buy
43. Rozporządzenie RM 10.10.2012 (Dz.U. 2012 poz. 1213) full text https://dziennikustaw.gov.pl/D2012000121301.pdf ; ELI status https://api.sejm.gov.pl/eli/acts/DU/2012/1213
44. Prawo atomowe art. 38d https://arslege.pl/fundusz-likwidacyjny/k264/a49139/ ; Ch. 12 liability https://sip.lex.pl/akty-prawne/dzu-dziennik-ustaw/prawo-atomowe-16890219/roz-12
45. Sroka & Wajda, Wiadomości Ubezpieczeniowe 4/2023 https://piu.org.pl/wp-content/uploads/2024/03/WU%202023-04_02_Sroka_Wajda.pdf
46. wnp.pl – nuclear insurance gap (Sep 2024) https://www.wnp.pl/energia/ubezpieczenie-elektrowni-jadrowej-w-polsce-mamy-powazny-problem,873053.html
47. DISE / Wrochna – SMR licensability & PAA fees https://dise.org.pl/prezentacja_Wojciech_Wrochna.pdf
48. PSE list of connection applicants (30 Jun 2026) https://www.pse.pl/documents/20182/51490/Wykaz_podmiotow_ubiegajacych_sie_o_przylaczenie.pdf
49. Energetyka24 – PSE conditions for Stawy Monowskie (Nov 2024) https://energetyka24.com/atom/wiadomosci/projekt-smr-z-reaktorami-bwrx-300-z-warunkami-przylaczenia-teraz-osge-ma-dwa-lata-na-umowe
50. Globenergia – PSE SMR planning (May 2026) https://globenergia.pl/polska-szykuje-sie-na-atom-w-planach-duza-elektrownia-i-prawie-2-gw-malych-reaktorow-smr/
51. Connection fees after Mar-2026 amendment https://www.energiadlalodzi.pl/wp-content/uploads/2026/04/Oplaty-przylaczeniowe-zgodnie-z-nowelizacja.pdf
52. OSGE CfD application (29 Jun 2026) https://osge.com/osge-wnioskuje-o-pierwszy-w-ue-kontrakt-roznicowy-dla-malych-reaktorow-modulowych/
53. wnp.pl – ME reaction (Jul 2026) https://www.wnp.pl/energia/osge-chce-wsparcia-panstwa-dla-malych-reaktorow-ministerstwo-energii-reaguje,1078724.html
54. Bankier – SMR support model (19 Jul 2026) https://www.bankier.pl/wiadomosc/SMR-y-z-pomoca-panstwa-Polska-przygotowuje-model-wsparcia-9169024.html
55. wnp.pl – SMR cost uncertainty (2025/26) https://www.wnp.pl/energia/ile-bedzie-kosztowac-smr-y-w-polsce-estymacje-sa-obarczone-ryzykiem,1081680.html
56. ZielonaGospodarka – OSGE 115–135 EUR/MWh (2025) https://zielonagospodarka.pl/osge-oczekuje-cen-125-145-euromwh-w-kontraktach-roznicowych-dla-14-pierwszych-reaktorow-bwrx-300-21182
57. Bankier – OSGE 15 bn EUR programme interview (2024) https://www.bankier.pl/wiadomosc/Orlen-Synthos-Green-Energy-szacuje-koszt-programu-budowy-blokow-SMR-do-35-na-ok-15-mld-euro-wywiad-8622777.html
58. Polityka Insight – Mały atom (Jul 2024) https://www.politykainsight.pl/_resource/multimedium/20362816
59. Fermi Energia BWRX-300 page https://fermi.ee/en/bwrx-300/
60. wnp.pl – Sejm committee, Stalowa Wola (Jul 2026) https://www.wnp.pl/energia/projekt-osge-przyspiesza-jest-decyzja-sejmowej-komisji-ws-stalowej-woli,1081775.html
61. Gazeta Prawna – Stalowa Wola SMR cooling (2026) https://www.gazetaprawna.pl/biznes/energetyka/artykuly/11245284,mala-elektrownia-atomowa-w-stalowej-woli-powstanie-w-latach-30.html
62. ARP–OSGE letter of intent https://arp.pl/pl/aktualnosci/arp-sa-i-osge-sp-z-oo-podpisaly-list-intencyjny-dotyczacy-wspolpracy-przy-projekcie-budowy-malych-reaktorow-modulowych-w-stalowej-woli/
63. Bankier – PEJ CfD 470–550 PLN/MWh (2025) https://www.bankier.pl/wiadomosc/Do-550-zl-za-MWh-To-cena-w-kontrakcie-roznicowym-dla-polskiej-elektrowni-jadrowej-8896336.html
64. GUS – wages Jul 2026 https://ssgk.stat.gov.pl/Wynagrodzenia_i_swiadczenia_spoleczne.html
65. Gazeta Prawna – energy-sector salaries (Aug 2026) https://www.gazetaprawna.pl/praca/rynek-pracy/artykuly/11290684,pracownikow-brakuje-wiec-placa-coraz-wiecej-nawet-40-tys-zl-miesiec.html
66. Forsal – PEJ salaries (2026) https://forsal.pl/gospodarka/aktualnosci/artykuly/11214116,placa-nawet-380-tys-zl-elektrownia-jadrowa-zatrudni-nawet-10-tys-osob.html
67. Money.pl – Choczewo tax/staff (2023) https://www.money.pl/gospodarka/elektrownia-jadrowa-w-choczewie-przepis-na-najbogatsza-gmine-w-kraju-6946809054423904a.html
68. Carbon Commentary – Darlington vs forecasts (May 2025) https://www.carboncommentary.com/blog/2025/5/11/the-first-test-for-new-small-modular-reactors-smr
69. NBP FX API (18 Sep 2026) https://api.nbp.pl/api/exchangerates/rates/a/usd/last/1/
70. MIT OCW 22.812 IDC problem set https://ocw.mit.edu/courses/22-812j-managing-nuclear-technology-spring-2004/c496144f2e576a709ec0cba58ff10e15_ps3soln.pdf
