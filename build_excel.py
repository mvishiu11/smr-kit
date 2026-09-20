"""Build the Excel financial model (live formulas) from the assumptions YAML and the digital-twin
dispatch outputs in results/.  Structure follows the EnergyScope template: Dashboard → Input
(LOW/CENTRAL/HIGH with a case switch) → Model sheets on an annual timeline → Tables, plus a Twin
sheet holding the hourly-dispatch outputs (capacity factor, capture ratio, heat rate per operating
year) and a Sources sheet.

Usage: python build_excel.py [out.xlsx]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from openpyxl import Workbook
from openpyxl.comments import Comment
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter as L
from openpyxl.worksheet.datavalidation import DataValidation

from smrtwin import config

ROOT = Path(__file__).resolve().parent
RES = ROOT / "results"
Y0, Y1 = 2027, 2096                     # timeline
NY = Y1 - Y0 + 1
C0 = 7                                   # first year column (G)
K_MAX = 60
CASES = ["LOW", "CENTRAL", "HIGH"]

FONT = "Arial"
F_IN = Font(name=FONT, color="0000FF", size=9)
F_LINK = Font(name=FONT, color="008000", size=9)
F_FX = Font(name=FONT, size=9)
F_B = Font(name=FONT, bold=True, size=9)
F_H = Font(name=FONT, bold=True, size=12)
F_SEC = Font(name=FONT, bold=True, size=10, color="FFFFFF")
FILL_SEC = PatternFill("solid", fgColor="1F3864")
FILL_KEY = PatternFill("solid", fgColor="FFFF00")
FILL_SEL = PatternFill("solid", fgColor="E2EFDA")
FILL_HDR = PatternFill("solid", fgColor="D9E1F2")
NUM = '#,##0;(#,##0);-'
NUM1 = '#,##0.0;(#,##0.0);-'
PCT = '0.0%;(0.0%);-'
YEAR_FMT = '0'

SCEN = [  # (sheet, scenario id, kind, label, twin key)
    ("Model_SMR_CfD", "S1a_smr_cfd", "smr_cfd", "SMR · CfD (two-way, PEJ template)"),
    ("Model_SMR_Fixed", "S1b_smr_fixed_spotavg", "smr_fixed", "SMR · fixed price = last-12-month average spot"),
    ("Model_SMR_Dynamic", "S2_smr_dynamic", "smr_dyn", "SMR · merchant, dynamic 50–100 % dispatch"),
    ("Model_CCGT", "S3a_gas_ccgt", "ccgt", "CCGT 1+1 ~300 MW · merchant dynamic"),
    ("Model_OCGT", "S3b_gas_ocgt", "ocgt", "OCGT 2×150 MW · merchant dynamic"),
    ("Model_Engines", "S3c_gas_engines", "engine", "Gas engines 4×76.5 MW · merchant dynamic"),
]


def ycol(y: int) -> str:
    return L(C0 + y - Y0)


class InputSheet:
    """Writes Input rows and keeps a registry name → absolute cell address of the *selected* value."""

    def __init__(self, ws, case_cell: str):
        self.ws = ws
        self.r = 7
        self.reg: dict[str, str] = {}
        self.case_cell = case_cell
        self.sec = 0
        ws.column_dimensions["A"].width = 4; ws.column_dimensions["B"].width = 5; ws.column_dimensions["C"].width = 52
        ws.column_dimensions["D"].width = 14
        for c in "EFGH":
            ws.column_dimensions[c].width = 13
        ws.column_dimensions["I"].width = 90
        ws["B2"] = "Input"; ws["B2"].font = F_H
        ws["B3"] = "Blue = hard-coded assumption (edit LOW / CENTRAL / HIGH); green-shaded column H = value selected by the case switch on Dashboard!C4. Money in real PLN, 2026 price level."
        ws["B3"].font = Font(name=FONT, italic=True, size=9)
        for j, h in enumerate(["#", "Parameter", "Unit", "LOW", "CENTRAL", "HIGH", "Selected", "Source / note"], start=2):
            c = ws.cell(row=5, column=j, value=h); c.font = F_B; c.fill = FILL_HDR
        ws.freeze_panes = "E6"

    def section(self, title: str):
        self.sec += 1
        self.r += 1
        c = self.ws.cell(row=self.r, column=2, value=f"{self.sec}. {title}")
        c.font = F_SEC
        for j in range(2, 10):
            self.ws.cell(row=self.r, column=j).fill = FILL_SEC
        self.r += 1

    def param(self, key: str, label: str, unit: str, vals, source: str = "", fmt: str = NUM, key_flag: bool = False):
        ws = self.ws; r = self.r
        if not isinstance(vals, (list, tuple)):
            vals = [vals, vals, vals]
        ws.cell(row=r, column=3, value=label).font = F_FX
        ws.cell(row=r, column=4, value=unit).font = F_FX
        for j, v in enumerate(vals):
            c = ws.cell(row=r, column=5 + j, value=v); c.font = F_IN; c.number_format = fmt
            if key_flag:
                c.fill = FILL_KEY
        c = ws.cell(row=r, column=8, value=f"=INDEX(E{r}:G{r},1,{self.case_cell})"); c.font = F_FX; c.number_format = fmt; c.fill = FILL_SEL
        ws.cell(row=r, column=9, value=source).font = Font(name=FONT, size=8, color="52514E")
        self.reg[key] = f"Input!$H${r}"
        self.r += 1
        return r

    def series(self, key: str, label: str, unit: str, rows3: list[list[float]], source: str = "", fmt: str = NUM):
        """Per-year path: three case rows + a selected row, values in the timeline columns."""
        ws = self.ws
        ws.cell(row=self.r, column=3, value=label).font = F_B
        ws.cell(row=self.r, column=4, value=unit).font = F_FX
        ws.cell(row=self.r, column=9, value=source).font = Font(name=FONT, size=8, color="52514E")
        for j, y in enumerate(range(Y0, Y1 + 1)):
            c = ws.cell(row=self.r, column=C0 + 3 + j, value=y); c.font = F_B; c.number_format = YEAR_FMT
        self.r += 1
        rows = []
        for ci, cs in enumerate(CASES):
            ws.cell(row=self.r, column=3, value=f"   {cs}").font = F_FX
            for j, v in enumerate(rows3[ci]):
                c = ws.cell(row=self.r, column=C0 + 3 + j, value=float(v)); c.font = F_IN; c.number_format = fmt
            rows.append(self.r); self.r += 1
        ws.cell(row=self.r, column=3, value="   Selected").font = F_B
        for j in range(NY):
            col = L(C0 + 3 + j)
            c = ws.cell(row=self.r, column=C0 + 3 + j, value=f"=CHOOSE({self.case_cell},{col}{rows[0]},{col}{rows[1]},{col}{rows[2]})")
            c.font = F_FX; c.number_format = fmt; c.fill = FILL_SEL
        self.reg[key] = self.r      # row number; column offset = C0+3 (J..)
        self.r += 2
        return self.r - 2


def path_rows(path_node: dict, mult: float = 1.0) -> list[list[float]]:
    out = []
    for cs in ("low", "central", "high"):
        out.append([float(np.interp(y, path_node["anchor_years"], path_node[cs]) * mult) for y in range(Y0, Y1 + 1)])
    return out


def load_twin(scenario: str) -> dict[str, pd.DataFrame]:
    out = {}
    for cs in ("low", "central", "high"):
        f = RES / cs / scenario / "operating_years.csv"
        out[cs] = pd.read_csv(f) if f.exists() else None
    return out


def build(out: Path):
    raw = config.load_raw()
    A = {cs: config.resolve(raw, cs) for cs in ("low", "central", "high")}
    ac = A["central"]
    wb = Workbook()
    dash = wb.active; dash.title = "Dashboard"
    inp = wb.create_sheet("Input")
    twin = wb.create_sheet("Twin")
    models = {s[0]: wb.create_sheet(s[0]) for s in SCEN}
    tables = wb.create_sheet("Tables")
    src = wb.create_sheet("Sources")

    # ---------------------------------------------------------------- Dashboard header / switch
    dash.column_dimensions["A"].width = 3; dash.column_dimensions["B"].width = 46
    for c in "CDEFGHIJ":
        dash.column_dimensions[c].width = 17
    dash["B1"] = "SMR vs alternatives — digital-twin financial model (Stalowa Wola, BWRX-300)"; dash["B1"].font = F_H
    dash["B2"] = "AM R&D / EnergyScope · real PLN 2026 · hourly dispatch from the Python twin (smrtwin) · all formulas live"; dash["B2"].font = Font(name=FONT, italic=True, size=9)
    dash["B3"] = "Assumption case"; dash["B3"].font = F_B
    dash["C3"] = "CENTRAL"; dash["C3"].font = F_IN; dash["C3"].fill = FILL_KEY
    dv = DataValidation(type="list", formula1='"LOW,CENTRAL,HIGH"', allow_blank=False); dash.add_data_validation(dv); dv.add("C3")
    dash["B4"] = "Case index (1 = LOW, 2 = CENTRAL, 3 = HIGH)"; dash["C4"] = '=MATCH(C3,{"LOW","CENTRAL","HIGH"},0)'
    dash["D3"] = "LOW = every parameter at its low value (cheap SMR AND low prices); use Input to mix cases."; dash["D3"].font = Font(name=FONT, italic=True, size=8)
    CASE = "Dashboard!$C$4"
    I = InputSheet(inp, CASE)

    # ---------------------------------------------------------------- Input: model set-up
    I.section("Model set-up")
    I.param("base_year", "Price base year (real terms)", "year", 2026, "All money real PLN at 2026 level", fmt="0")
    I.param("eur_pln", "EUR/PLN", "PLN", ac["meta"]["eur_pln"], "NBP table A mid, 18 Sep 2026 (4.3633)", fmt="0.0000")
    I.param("usd_pln", "USD/PLN", "PLN", ac["meta"]["usd_pln"], "NBP table A mid, 18 Sep 2026", fmt="0.0000")
    I.param("hours", "Hours per year", "h", 8760, fmt="0")

    I.section("Macro and cost of capital")
    w = raw["macro"]["wacc_real"]
    I.param("wacc_smr_cfd", "Real post-tax WACC — SMR with CfD", "%", w["smr_cfd"], "PEJ EC decision (OJ C 2025/1389) Table 1: nominal 6–8 % with aid; deflated at 2.5 % CPI", PCT, True)
    I.param("wacc_smr_merch", "Real post-tax WACC — SMR merchant", "%", w["smr_merchant"], "PEJ Table 1 without aid: 8.5–10.5 % nominal", PCT, True)
    I.param("wacc_gas", "Real post-tax WACC — gas", "%", w["gas"], "Ministry of Climate LCOE note 7 % real (70 % debt @6 %, 30 % equity @9.5 %)", PCT, True)
    I.param("cpi", "CPI long run (memo, for nominal conversions)", "%", raw["macro"]["cpi_long_run"], "NBP target 2.5 %", PCT)

    # ---------------------------------------------------------------- Input: market
    I.section("Market — Polish day-ahead market (TGE RDN / SDAC), gas, CO2, capacity")
    m = raw["market"]
    I.param("ref_mean", "Reference year mean day-ahead price (Sep 2025–Aug 2026, hourly PSE/TGE data)", "PLN/MWh", 483.39, "PSE csdac-pln API, 8,760 hourly values; TGE 2025 vol.-weighted 446.30", NUM1)
    I.param("fixed_price", "Fixed price for SMR-fixed scenario (= reference mean unless overridden)", "PLN/MWh", 483.39, "Scenario S1b: 'average spot over the last year'", NUM1, True)
    I.param("cm_price", "Capacity-market price (successor mechanism, if any)", "PLN/kW-yr", m["capacity_market"]["price_pln_per_kw_yr"], "2030 main auction cleared 465.02 PLN/kW-yr (URE, 11 Dec 2025); no auction exists for delivery ≥2031 → 0 in base", NUM, True)
    I.param("cm_years", "Capacity contract length", "years", m["capacity_market"]["contract_years"], "17 y new low-emission; 15 y new gas", "0")
    I.param("kwd_nuc", "De-rating factor nuclear (KWD)", "#", m["capacity_market"]["kwd_nuclear"], "Dz.U. 2025 poz. 1066 (2030 auction parameters)", "0.0000")
    I.param("kwd_ccgt", "De-rating factor CCGT", "#", m["capacity_market"]["kwd_ccgt"], "same", "0.0000")
    I.param("kwd_ocgt", "De-rating factor OCGT / engines", "#", m["capacity_market"]["kwd_ocgt"], "same", "0.0000")
    I.param("bal_ccgt", "Balancing-capacity revenue CCGT", "PLN/kW-yr", m["balancing_pln_per_kw_yr"]["ccgt"], "aFRR/mFRR 2025 ~180 PLN/MW/h falling to 50–90 by 2027; low contracted share", NUM)
    I.param("bal_ocgt", "Balancing-capacity revenue OCGT / engines", "PLN/kW-yr", m["balancing_pln_per_kw_yr"]["ocgt"], "mFRR/RR from standstill", NUM)
    I.param("ef_gas", "CO2 emission factor natural gas", "t/MWh_th", m["gas_emission_factor_t_per_mwh_fuel"], "KOBiZE 2025 ETS factor 55.73 kg/GJ", "0.0000")
    I.param("licence_fee", "URE licence fee (share of revenue)", "%", raw["gas"]["licence_fee_share_of_revenue"], "Proposal from 2027: 0.5 % uncapped (current 0.05 %, cap 2.5 m PLN)", "0.00%")
    r_price = I.series("price_path", "Annual mean day-ahead price path (real 2026)", "PLN/MWh", path_rows(m["price_path"]), "2027–29 TGE BASE_Y forwards (Aug-2026 VWAP 495.5/444.5/420.1); 2030+ judgement bridging TGE 2029 and PEJ counterfactual; hourly shape from the twin")
    r_gas = I.series("gas_path", "Gas price at PL virtual point (real 2026)", "PLN/MWh_th", path_rows(m["gas_price_path"]), "TGE GAS_BASE_Y-27 Aug-2026 214.20; TTF forward proxy 38/33/31 EUR + 4 EUR PL premium")
    r_eua = I.series("eua_path", "EUA price (real 2026)", "EUR/t", path_rows(m["eua_path"]), "Spot 86.9 EUR/t (18 Sep 2026); Reuters poll 2027 93; consensus 2030 126 (80–147)")

    # ---------------------------------------------------------------- Input: SMR
    I.section("SMR — GE Vernova Hitachi BWRX-300 (one 300 MWe unit at a 4-unit site)")
    s = raw["smr"]
    I.param("smr_mw", "Net capacity", "MW", s["net_mw_cases"], "GE 'up to 300 MWe'; IAEA ARIS 270–290 net; closed-loop cooling penalty in low", NUM)
    I.param("smr_capex", "Overnight cost, all-in (EPC + owner's + contingency + site share), excl. IDC", "PLN/kW", s["capex_pln_per_kw"], "Darlington unit-1 core excl. common/IDC ≈36,200 PLN/kW (OEB EB-2025-0297); MIT ANP-201 FOAK 14,000 $/kW; INL 2024 SMR 5,500–10,000 $/kW; OSGE ~2 bn EUR/unit; central = mid-fleet unit with 9.5 % learning", NUM, True)
    I.param("smr_constr", "Construction duration (first structural concrete → COD)", "years", s["construction_years"], "Darlington ~53–66 months; NREL ATB 2025 43/55/71 months", "0", True)
    I.param("smr_cod", "Commercial operation date", "year", s["cod_year"], "Stalowa Wola = OSGE site 3/4; fleet first unit Włocławek 2032; transboundary EIA started Jun 2026", "0", True)
    I.param("smr_life", "Operating life", "years", s["life_years"], "GE design life 60 y", "0")
    I.param("smr_predev", "Pre-development (licensing, EIA, FEED, PAA fees)", "m PLN", s["pre_development_mpln"], "OPG 105 m CAD preliminary + 521 m CAD definition phase; PAA fees 6.9 m PLN", NUM)
    I.param("smr_core", "First core (capitalised)", "m PLN", s["first_core_mpln"], "44 tU × ~3,300 USD/kgU (U3O8 96.5 $/lb LT, SWU 183 $, conv 55.5 $, fab 350 $)", NUM)
    I.param("smr_grid", "Grid connection (unit share)", "m PLN", s["grid_connection_mpln"], "Proxy 150–400 m PLN for 4-unit site; PSE conditions exist for Stawy Monowskie only", NUM)
    I.param("smr_fom", "Fixed O&M (staff, insurance, materials, contractors, regulatory)", "PLN/kW-yr", s["fom_pln_per_kw_yr"], "INL 2024 Adv/Mod/Cons 118/136/216 $/kW-yr; EIA AEO2025 124; Lazard 136–158", NUM, True)
    I.param("smr_fom_mult", "Single-unit-phase FOM multiplier (first years before units 2–4)", "×", s["single_unit_fom_multiplier"], "INL multi-unit O&M multiplier 0.5–0.7; MIT 38.7 vs 28.2 $/MWh", "0.00")
    I.param("smr_single_yrs", "Years operated as single unit", "years", s["single_unit_years"], "assumption", "0")
    I.param("smr_fte", "Staff", "FTE", s["staff_fte_per_unit"], "GEH claim ~75; NRC-style ~0.3 FTE/MW; PEJ 860 for 3.75 GW", NUM)
    I.param("smr_fte_cost", "Loaded cost per FTE", "k PLN/yr", s["staff_cost_kpln_per_fte"], "GUS energy sector 14.3k PLN/month; nuclear specialists 20–25k ×1.2 employer overhead", NUM)
    I.param("smr_fuel", "Nuclear fuel (front end)", "PLN/MWh", s["fuel_pln_per_mwh"], "Own build-up: 3.4 %/49.5 GWd/t; U3O8 70/96.5/130 $/lb; SWU 150/183/220; INL 10–12 $/MWh incl. disposal", NUM1, True)
    I.param("smr_vom", "Variable O&M (non-fuel)", "PLN/MWh", s["vom_pln_per_mwh"], "INL 2.2–2.8 $/MWh; EIA 3.23; Lazard 4.4–5.15", NUM1)
    I.param("smr_fund", "Decommissioning & spent-fuel fund (statutory)", "PLN/MWh", s["decommissioning_fund_pln_per_mwh"], "Dz.U. 2012 poz. 1213: 17.16 PLN/MWh, unindexed since 2012; central = CPI-indexed equivalent", NUM1)
    I.param("smr_sust", "Sustaining capex (treated as annual fixed at 90 % CF)", "PLN/MWh", s["sustaining_capex_pln_per_mwh"], "NEI US fleet 8.8–13.6 $/MWh; MIT 6.25", NUM1)
    I.param("smr_budowle", "Share of capex taxable as 'budowle' (2 % property tax)", "%", s["property_tax"]["budowle_share_of_capex"], "Post-2025 definitions (Dz.U. 2024 poz. 1757): only construction parts; untested for nuclear", PCT, True)
    I.param("smr_host", "Host-gmina share of property tax", "%", s["property_tax"]["host_gmina_share"], "Art. 50 nuclear investment act: 50 % passed to bordering gminas", PCT)
    I.param("smr_lf_ucf", "Load-following capability loss (dynamic / CfD dispatch)", "%", s["flexibility"]["load_following_ucf_loss"], "NEA 2011: French fleet 1.2–2 % UCF", PCT)
    I.param("smr_lf_fom", "Load-following FOM uplift", "%", s["flexibility"]["load_following_fom_uplift"], "NEA 2011 'slight increase'; IAEA NP-T-3.23", PCT)
    I.param("strike", "CfD strike price", "EUR/MWh", s["cfd"]["strike_eur_per_mwh"], "Brief 115–135; OSGE public statements 125–145 (Oct 2025); fleet avg ~120; ME calls ~125 'relatively high'", NUM1, True)
    I.param("tenor", "CfD tenor", "years", s["cfd"]["tenor_years"], "PEJ precedent: 60 requested → 40 approved", "0", True)
    I.param("smr_workers", "Peak construction workforce (unit)", "FTE", raw["tax"]["construction_local_pit"]["peak_construction_workers_per_unit"], "Darlington ~2,500 for 4 units", NUM)
    I.param("smr_dep_b", "Tax depreciation split — buildings 2.5 %", "%", s["depreciation_split"]["buildings_2_5pct"], "KŚT group 1", PCT)
    I.param("smr_dep_s", "Tax depreciation split — structures 4.5 %", "%", s["depreciation_split"]["structures_4_5pct"], "KŚT group 2", PCT)
    I.param("smr_dep_r", "Tax depreciation split — reactor 14 %", "%", s["depreciation_split"]["reactor_14pct"], "KŚT 349 nuclear reactors", PCT)
    I.param("smr_dep_t", "Tax depreciation split — turbine/BOP 7 %", "%", s["depreciation_split"]["turbine_bop_7pct"], "KŚT group 3", PCT)
    I.param("smr_dep_d", "Tax depreciation split — devices 10 %", "%", s["depreciation_split"]["devices_10pct"], "KŚT group 4/6", PCT)

    # ---------------------------------------------------------------- Input: gas units
    g = raw["gas"]
    I.section("Gas — common")
    I.param("gas_cod", "Gas plant COD", "year", g["cod_year"], "Turbine lead times 3–5 y; order 2027 → COD 2031", "0", True)
    I.param("gas_ptax", "Property tax rate on budowle", "%", g["property_tax_rate"], "2 % of initial value", PCT)
    I.param("gas_grid", "Grid connection proxy", "PLN/kW", 350, "400 kV bay/line share 50–150 m PLN per 300 MW", NUM)
    I.param("gas_decom", "End-of-life demolition provision (share of overnight)", "%", 0.05, "assumption", PCT)
    I.param("gas_workers", "Peak construction workforce per 300 MW", "FTE", 300, "assumption", NUM)
    gkeys = {}
    for kind, n, label in (("ccgt", 1, "CCGT 1+1 F-class, ~300 MW"), ("ocgt", 2, "OCGT frame peakers, 2 × 150 MW"), ("engine", 4, "Gas engines, 4 blocks × 76.5 MW (≈17 × 18 MW)")):
        u = g["units"][kind]
        I.section(f"Gas — {label}")
        mw = u["net_mw"] * n
        p = kind
        I.param(f"{p}_mw", "Net capacity (portfolio)", "MW", mw, "", NUM)
        I.param(f"{p}_capex", "All-in capex (EPC + owner's costs)", "PLN/kW", u["capex_pln_per_kw"], {"ccgt": "Polish 2025 EPC 4,800–5,500 PLN/kW for 560–1,340 MW (Kozienice, Gdańsk, Grudziądz II) +15–20 % scale penalty; Lazard-high/GridLab $2,000–2,600/kW", "ocgt": "DESNZ 2025 £361/kW; EIA $791/kW; PGE HL-class OCGT ~5,900 PLN/kW incl. 12-y LTSA", "engine": "DESNZ £529/kW; PGE Kraków/Gdynia CHP engines 7,600–8,900 PLN/kWe (upper bound)"}[kind], NUM, True)
        I.param(f"{p}_constr", "Construction duration", "years", u["construction_years"], "DESNZ 2.2/3.0/3.2; Polish reality 4–5 y", "0")
        I.param(f"{p}_life", "Operating life", "years", u["life_years"], "DESNZ 20/25/30; Lazard 30", "0")
        I.param(f"{p}_eta", "Net efficiency at full load (LHV)", "%", u["eta_full_lhv"], {"ccgt": "300 MW-class scale penalty vs 63–64 % H-class; Grudziądz >61 %; EC Stalowa Wola 57.4–60 %", "ocgt": "DESNZ 38.9 %; EIA 41.3 %; GE 9HA SC 44 %", "engine": "Wärtsilä 50DF 49.4 %, 31SG >50 %; DESNZ 44.6 %"}[kind], PCT)
        I.param(f"{p}_fom", "Fixed O&M incl. LTSA fixed fee", "PLN/kW-yr", u["fom_pln_per_kw_yr"], "EIA/Lazard/DESNZ; Dolna Odra LTSA ≈61 PLN/kW-yr", NUM)
        I.param(f"{p}_vom", "Variable O&M incl. hours-based LTSA", "PLN/MWh", u["vom_pln_per_mwh"], "Lazard 2.75–5 $/MWh; DESNZ £4.44", NUM1)
        I.param(f"{p}_exit", "Gas transmission exit-capacity booking (Gaz-System)", "PLN/kW-yr", u["gas_exit_tariff_pln_per_kw_yr"], "Tariff 19 exit ≈0.381 gr/(kWh/h)/h annual firm; peakers book monthly/daily products", NUM)
        I.param(f"{p}_fte", "Staff", "FTE", u["staff_fte"] * (1 if kind == "ccgt" else n), "EC Stalowa Wola ~60 FTE for 450 MW CHP", NUM)
        I.param(f"{p}_fte_cost", "Loaded cost per FTE", "k PLN/yr", u["staff_cost_kpln_per_fte"], "GUS energy sector", NUM)
        I.param(f"{p}_budowle", "Share of capex taxable as budowle", "%", u["budowle_share_of_capex"], "structures, foundations, stacks, pipelines", PCT)
        I.param(f"{p}_dep_b", "Tax depreciation split — buildings 2.5 %", "%", u["depreciation_split"]["buildings_2_5pct"], "", PCT)
        I.param(f"{p}_dep_s", "Tax depreciation split — structures 4.5 %", "%", u["depreciation_split"]["structures_4_5pct"], "", PCT)
        I.param(f"{p}_dep_t", "Tax depreciation split — turbines/boilers 7 %", "%", u["depreciation_split"]["turbine_bop_7pct"], "KŚT group 3 (engines 14 % — conservatively 7 %)", PCT)
        I.param(f"{p}_dep_d", "Tax depreciation split — devices 10 %", "%", u["depreciation_split"]["devices_10pct"], "", PCT)
        gkeys[kind] = p

    # ---------------------------------------------------------------- Input: tax
    t = raw["tax"]
    I.section("Taxes and local-government revenue (2025 JST revenue system)")
    I.param("cit", "CIT rate", "%", t["cit_rate"], "19 %", PCT)
    I.param("dep_b", "Tax depreciation rate — buildings", "%/yr", t["depreciation_rates"]["buildings_2_5pct"], "KŚT annex 1 CIT", PCT)
    I.param("dep_s", "Tax depreciation rate — structures", "%/yr", t["depreciation_rates"]["structures_4_5pct"], "", PCT)
    I.param("dep_r", "Tax depreciation rate — nuclear reactor (KŚT 349)", "%/yr", t["depreciation_rates"]["reactor_14pct"], "", PCT)
    I.param("dep_t", "Tax depreciation rate — turbines / boilers / power machinery", "%/yr", t["depreciation_rates"]["turbine_bop_7pct"], "", PCT)
    I.param("dep_d", "Tax depreciation rate — technical devices", "%/yr", t["depreciation_rates"]["devices_10pct"], "", PCT)
    ls = t["local_shares_2025_system"]
    I.param("cit_gmina", "Gmina share of taxpayers' CIT income", "%", ls["cit_gmina"], "Ustawa o dochodach JST (Dz.U. 2024 poz. 1572): shares of INCOME, not tax", "0.00%")
    I.param("cit_powiat", "Powiat share of CIT income", "%", ls["cit_powiat"], "", "0.00%")
    I.param("cit_woj", "Województwo share of CIT income", "%", ls["cit_wojewodztwo"], "", "0.00%")
    I.param("pit_gmina", "Gmina share of residents' PIT income", "%", ls["pit_gmina"], "gmina 7.0 % (city with powiat rights 8.6 %)", "0.00%")
    I.param("pit_powiat", "Powiat share of PIT income", "%", ls["pit_powiat"], "", "0.00%")
    I.param("pit_woj", "Województwo share of PIT income", "%", ls["pit_wojewodztwo"], "", "0.00%")
    e = t["employee"]
    I.param("zus_ee", "Employee ZUS share", "%", e["zus_employee_share"], "9.76+1.5+2.45 %", "0.00%")
    I.param("zus_er", "Employer ZUS share", "%", e["zus_employer_share"], "≈20.48 %", "0.00%")
    I.param("pit_thr", "PIT bracket threshold", "PLN", e["pit_bracket_threshold_pln"], "12 % / 32 %", NUM)
    I.param("pit_lo", "PIT lower rate", "%", e["pit_rate_low"], "", PCT)
    I.param("pit_hi", "PIT upper rate", "%", e["pit_rate_high"], "", PCT)
    I.param("pit_free", "PIT tax-reducing amount", "PLN", e["pit_free_amount_tax_pln"], "30,000 PLN tax-free", NUM)
    I.param("res_share", "Share of plant staff resident in host gmina", "%", e["resident_share_in_gmina"], "assumption", PCT)
    I.param("cw_gross", "Construction worker gross salary", "PLN/month", t["construction_local_pit"]["avg_worker_gross_pln_per_month"], "assumption", NUM)
    I.param("cw_res", "Construction workers resident in gmina", "%", t["construction_local_pit"]["resident_share_in_gmina"], "assumption", PCT)

    # ---------------------------------------------------------------- Twin sheet
    twin.column_dimensions["A"].width = 3; twin.column_dimensions["B"].width = 26; twin.column_dimensions["C"].width = 34; twin.column_dimensions["D"].width = 10
    twin["B1"] = "Twin — outputs of the hourly digital-twin dispatch (Python: smrtwin), per operating year k"; twin["B1"].font = F_H
    twin["B2"] = "cf = capacity factor; capture = generation-weighted price ÷ annual mean price; cfd_ref = generation-weighted CfD reference (daily TGeBase) ÷ annual mean; heat = MWh_th per MWh_e incl. no-load & start fuel; start = start costs (wear) PLN/MWh_e; fuel_ratio = SMR fuel cost ÷ (energy × fuel price). Re-generate with `python build_excel.py` after `python run_all.py`."
    twin["B2"].font = Font(name=FONT, italic=True, size=8)
    for k in range(1, K_MAX + 1):
        c = twin.cell(row=4, column=C0 + k - 1, value=k); c.font = F_B
    twin["C4"] = "operating year k →"; twin["C4"].font = F_B
    TW: dict[tuple[str, str], int] = {}   # (scenario, metric) → selected row
    tr = 5
    metrics_by_kind = {"smr_cfd": ["cf", "capture", "cfd_ref", "fuel_ratio"], "smr_fixed": ["cf", "fuel_ratio"], "smr_dyn": ["cf", "capture", "fuel_ratio"],
                       "ccgt": ["cf", "capture", "heat", "start"], "ocgt": ["cf", "capture", "heat", "start"], "engine": ["cf", "capture", "heat", "start"]}
    for sheet, scen, kind, label in SCEN:
        tw = load_twin(scen)
        twin.cell(row=tr, column=2, value=label).font = F_SEC
        for j in range(2, C0 + K_MAX):
            twin.cell(row=tr, column=j).fill = FILL_SEC
        tr += 1
        for met in metrics_by_kind[kind]:
            rows = []
            for cs in ("low", "central", "high"):
                df = tw[cs]
                twin.cell(row=tr, column=2, value=f"{met} · {cs}").font = F_FX
                if df is not None:
                    a_cs = A[cs]
                    mw = a_cs["smr"]["net_mw_cases"] if kind.startswith("smr") else a_cs["gas"]["units"][kind]["net_mw"] * {"ccgt": 1, "ocgt": 2, "engine": 4}[kind]
                    for i, row in df.iterrows():
                        k = i + 1
                        if k > K_MAX:
                            break
                        en = row["energy_mwh"]; pm = row["x_price_mean"]
                        if met == "cf":
                            v = en / (mw * 8760)
                        elif met == "capture":
                            v = (row["revenue_market_pln"] / en) / pm if en > 0 else 1
                        elif met == "cfd_ref":
                            strike = a_cs["smr"]["cfd"]["strike_eur_per_mwh"] * a_cs["meta"]["eur_pln"]
                            v = ((strike - row["cfd_payment_pln"] / en) / pm) if (en > 0 and row["cfd_payment_pln"] != 0) else 1
                        elif met == "fuel_ratio":
                            v = row["fuel_cost_pln"] / (en * a_cs["smr"]["fuel_pln_per_mwh"]) if en > 0 else 1
                        elif met == "heat":
                            gasm = row["x_gas_mean"]
                            v = row["fuel_cost_pln"] / (en * gasm) if en > 0 else 0
                        elif met == "start":
                            v = row["start_cost_pln"] / en if en > 0 else 0
                        c = twin.cell(row=tr, column=C0 + k - 1, value=float(v)); c.font = F_IN; c.number_format = "0.000"
                rows.append(tr); tr += 1
            twin.cell(row=tr, column=2, value=f"{met} · selected").font = F_B
            for k in range(1, K_MAX + 1):
                col = L(C0 + k - 1)
                c = twin.cell(row=tr, column=C0 + k - 1, value=f"=CHOOSE({CASE},{col}{rows[0]},{col}{rows[1]},{col}{rows[2]})")
                c.font = F_FX; c.number_format = "0.000"; c.fill = FILL_SEL
            TW[(scen, met)] = tr; tr += 1
        tr += 1

    # ---------------------------------------------------------------- Model sheets
    R = I.reg
    KP: dict[str, dict] = {}
    for sheet, scen, kind, label in SCEN:
        ws = models[sheet]
        KP[sheet] = build_model(ws, sheet, scen, kind, label, R, TW, r_price, r_gas, r_eua, CASE, gkeys)

    # ---------------------------------------------------------------- Dashboard KPIs
    dash["B6"] = "Key results by scenario (selected case)"; dash["B6"].font = F_B
    heads = ["Scenario", "NPV post-tax (m PLN)", "IRR post-tax", "LCOE (PLN/MWh)", "Levelised revenue (PLN/MWh)", "Avg capacity factor", "Local gov. revenue (m PLN/op-yr)", "CfD/support PV (m PLN)", "Break-even strike / premium (PLN/MWh)"]
    for j, h in enumerate(heads):
        c = dash.cell(row=7, column=2 + j, value=h); c.font = F_B; c.fill = FILL_HDR; c.alignment = Alignment(wrap_text=True, vertical="top")
    r = 8
    for sheet, scen, kind, label in SCEN:
        k = KP[sheet]
        dash.cell(row=r, column=2, value=label).font = F_FX
        for j, key in enumerate(["npv", "irr", "lcoe", "levrev", "cf", "local", "cfd_pv", "be"]):
            c = dash.cell(row=r, column=3 + j, value=f"='{sheet}'!{k[key]}"); c.font = F_LINK
            c.number_format = PCT if key in ("irr", "cf") else NUM
        r += 1
    dash.cell(row=r + 1, column=2, value="Break-even column: for the CfD sheet = strike (EUR/MWh) at which NPV = 0 (pre-tax exact / post-tax approximated as linear in strike); for other sheets = constant PLN/MWh premium on all output needed for NPV = 0.").font = Font(name=FONT, italic=True, size=8)
    dash.cell(row=r + 2, column=2, value="'Alternative cost' reading: NPV of a merchant asset = value of its output at market prices − its full cost, i.e. minus the net cost to the system of building it instead of buying from the market.").font = Font(name=FONT, italic=True, size=8)
    r += 4
    dash.cell(row=r, column=2, value="Key figures by year — selected case (m PLN)").font = F_B
    r += 1
    yrs = list(range(2030, 2071, 5))
    dash.cell(row=r, column=2, value="Year").font = F_B
    for j, y in enumerate(yrs):
        c = dash.cell(row=r, column=3 + j, value=y); c.font = F_B; c.number_format = YEAR_FMT
    r += 1
    for sheet, scen, kind, label in SCEN:
        k = KP[sheet]
        for key, nm in (("fcf_row", "post-tax FCF"), ("rev_row", "revenue"), ("local_row", "local gov. revenue")):
            dash.cell(row=r, column=2, value=f"{label} — {nm}").font = F_FX
            for j, y in enumerate(yrs):
                c = dash.cell(row=r, column=3 + j, value=f"='{sheet}'!{ycol(y)}{k[key]}"); c.font = F_LINK; c.number_format = NUM
            r += 1
        r += 1
    dash.freeze_panes = "C8"

    # ---------------------------------------------------------------- Tables: cost per MWh breakdown
    tables.column_dimensions["B"].width = 44
    for c in "CDEFGH":
        tables.column_dimensions[c].width = 22
    tables["B2"] = "1. Levelised cost breakdown, PLN/MWh (selected case; discounted at each asset's WACC)"; tables["B2"].font = F_B
    comps = [("Capital (overnight + other capex)", "pv_capex"), ("Fixed O&M", "pv_fom"), ("Fuel", "pv_fuel"), ("CO2 (EUA)", "pv_co2"), ("Variable O&M + starts", "pv_vom"),
             ("Decommissioning fund / provision", "pv_fund"), ("Sustaining capex", "pv_sust"), ("Property tax, licence fee, gas capacity booking", "pv_other"), ("LCOE total", "pv_cost"), ("Levelised revenue", "pv_rev")]
    tables.cell(row=4, column=2, value="Component").font = F_B
    for j, (sheet, scen, kind, label) in enumerate(SCEN):
        c = tables.cell(row=4, column=3 + j, value=label); c.font = F_B; c.fill = FILL_HDR; c.alignment = Alignment(wrap_text=True)
    for i, (nm, key) in enumerate(comps):
        tables.cell(row=5 + i, column=2, value=nm).font = F_B if key in ("pv_cost", "pv_rev") else F_FX
        for j, (sheet, scen, kind, label) in enumerate(SCEN):
            k = KP[sheet]
            c = tables.cell(row=5 + i, column=3 + j, value=f"=IFERROR('{sheet}'!{k[key]}*1000000/'{sheet}'!{k['pv_energy']},0)"); c.font = F_LINK; c.number_format = NUM1
    tables["B17"] = "2. Fiscal flows over life, m PLN undiscounted (selected case)"; tables["B17"].font = F_B
    fl = [("CIT paid to State", "sum_cit"), ("EUA purchases (≈ Polish state auction revenue)", "sum_co2"), ("Decommissioning fund contributions", "sum_fund"), ("CfD payments received (+) / paid back (−)", "sum_cfd"),
          ("Property tax — host gmina", "sum_pt_host"), ("Property tax — neighbouring gminas", "sum_pt_nb"), ("CIT-income shares — gmina/powiat/województwo", "sum_lcit"), ("PIT-income shares — gmina/powiat/województwo", "sum_lpit")]
    for i, (nm, key) in enumerate(fl):
        tables.cell(row=18 + i, column=2, value=nm).font = F_FX
        for j, (sheet, scen, kind, label) in enumerate(SCEN):
            c = tables.cell(row=18 + i, column=3 + j, value=f"='{sheet}'!{KP[sheet][key]}"); c.font = F_LINK; c.number_format = NUM

    # ---------------------------------------------------------------- Sources
    src.column_dimensions["B"].width = 130
    src["B1"] = "Sources (full citations with URLs in docs/ASSUMPTIONS.md of the repository)"; src["B1"].font = F_H
    lines = [
        "OPG, OEB filing EB-2025-0297 Exh. D2-4-1 (May 2026) — Darlington BWRX-300 unit-1 cost decomposition (5.1 core / 1.4 contingency / 1.2 IDC bn CAD).",
        "World Nuclear News (2025) — Darlington 4-unit programme CAD 20.9 bn; unit 1 CAD 6.1 bn + 1.6 bn common.",
        "MIT CANES ANP-TR-201 (Shirvan, Jul 2024) — BWRX-300 FOAK overnight 14,000 $/kW; O&M 28–39 $/MWh; LCOE.",
        "INL/RPT-24-77048 (2024) meta-analysis; INL/RPT-23-72972 (2023) — SMR overnight 5,500–10,000 $/kW (2022$), learning 5–15 %/doubling.",
        "NREL/NLR ATB 2025 nuclear; EIA AEO2025 electricity-market assumptions; Lazard LCOE+ v18 (Jun 2025) and v19 (Jul 2026).",
        "IAEA ARIS BWRX-300 status report (2020); GE Vernova BWRX-300 General Description (2023/24) — 870 MWt, 50–100 % load following, ramp 0.5/2 %/min.",
        "NEA (2011) Technical and Economic Aspects of Load Following; IAEA NP-T-3.23 (2018) Non-baseload operation; PNNL-30225 (2021).",
        "Rozporządzenie RM 10.10.2012 (Dz.U. 2012 poz. 1213) — decommissioning fund 17.16 PLN/MWh; Prawo atomowe art. 38d, ch. 12 (300 m SDR liability).",
        "EUR-Lex OJ C 2025/1389 — EC opening decision on PEJ state aid: CfD design (daily blended TGE reference, 40-y tenor), WACC table, strike 470–550 PLN/MWh.",
        "OSGE press release 29 Jun 2026 (CfD application, 14 units); Bankier/PAP 7 Oct 2025 (125–145 EUR/MWh, ~2 bn EUR/unit); Bankier 19 Jul 2026 (Ministry of Energy).",
        "TGE monthly reports RAPORT_2025_01…RAPORT_2026_08 (TGeBase, BASE_Y forwards); PSE open API csdac-pln (hourly SDAC prices, Jun 2024–Sep 2026); energy-charts.info (2019–2024); NBP FX.",
        "URE capacity-market auction results (delivery 2027–2030: 406.35 / 244.90 / 264.90 / 465.02 PLN/kW-yr); Dz.U. 2025 poz. 1066 (KWD factors).",
        "Polimex/Energa/Enea/ZE PAK/PGE investor releases 2020–2026 — Polish CCGT/OCGT EPC contract values; NIK 2018 (EC Stalowa Wola).",
        "EIA AEO2025; Lazard 2025; GridLab (Sep 2025); UK DESNZ Electricity Generation Costs 2025; Gas Turbine World 2024; Wood Mackenzie (Apr 2026) — gas capex benchmarks and turbine inflation.",
        "KOBiZE 2025 ETS emission factors (55.73 kg CO2/GJ); Gaz-System tariffs 18/19; TTF monthly (Protergia); Trading Economics EUA; Reuters/GMK EUA polls.",
        "Ustawa o dochodach JST (Dz.U. 2024 poz. 1572); ustawa o inwestycjach w obiekty energetyki jądrowej art. 50; Dz.U. 2024 poz. 1757 (property-tax definitions); KŚT depreciation table; podatki.gov.pl PIT 2026.",
    ]
    for i, t_ in enumerate(lines):
        src.cell(row=3 + i, column=2, value=f"{i+1}. {t_}").font = F_FX

    for ws in wb.worksheets:
        for row in ws.iter_rows():
            for c in row:
                if c.font is None or c.font.name != FONT:
                    c.font = Font(name=FONT, size=c.font.size if c.font else 9, bold=c.font.bold if c.font else False,
                                  italic=c.font.italic if c.font else False, color=c.font.color if c.font else None)
    wb.save(out)
    print("saved", out)


def build_model(ws, sheet: str, scen: str, kind: str, label: str, R: dict, TW: dict, r_price: int, r_gas: int, r_eua: int, CASE: str, gkeys: dict) -> dict:
    """Write one annual model sheet; returns addresses of KPI cells and key rows."""
    ws.column_dimensions["A"].width = 3; ws.column_dimensions["B"].width = 50; ws.column_dimensions["C"].width = 11; ws.column_dimensions["D"].width = 14
    ws.column_dimensions["E"].width = 3; ws.column_dimensions["F"].width = 3
    for j in range(NY):
        ws.column_dimensions[L(C0 + j)].width = 10.5
    ws["B1"] = label; ws["B1"].font = F_H
    ws["B2"] = "Annual model, real PLN m (2026). Column D = totals / KPIs. Timeline columns G→. Dispatch quantities come from the Twin sheet (hourly digital twin)."; ws["B2"].font = Font(name=FONT, italic=True, size=8)
    ws["B4"] = "Year"; ws["B4"].font = F_B
    for j, y in enumerate(range(Y0, Y1 + 1)):
        c = ws.cell(row=4, column=C0 + j, value=y); c.font = F_B; c.number_format = YEAR_FMT; c.fill = FILL_HDR
    ws.freeze_panes = "G5"
    smr = kind.startswith("smr")
    p = None if smr else gkeys[kind]
    rows: dict[str, int] = {}
    cur = [6]

    def sec(title):
        c = ws.cell(row=cur[0], column=2, value=title); c.font = F_SEC
        for j in range(2, C0 + NY):
            ws.cell(row=cur[0], column=j).fill = FILL_SEC
        cur[0] += 1

    def line(key, lab, unit, f, fmt=NUM, total=None, bold=False):
        """f(col, prev_col) → formula string for the year column."""
        r = cur[0]
        rows[key] = r
        ws.cell(row=r, column=2, value=lab).font = F_B if bold else F_FX
        ws.cell(row=r, column=3, value=unit).font = F_FX
        for j in range(NY):
            col = L(C0 + j); prev = L(C0 + j - 1) if j > 0 else None
            c = ws.cell(row=r, column=C0 + j, value=f(col, prev)); c.font = F_FX; c.number_format = fmt
            if bold:
                c.font = F_B
        if total == "sum":
            c = ws.cell(row=r, column=4, value=f"=SUM({L(C0)}{r}:{L(C0+NY-1)}{r})"); c.font = F_B; c.number_format = fmt
        rows[key] = r; cur[0] += 1
        return r

    def scalar(key, lab, formula, fmt=NUM, bold=True):
        r = cur[0]
        ws.cell(row=r, column=2, value=lab).font = F_B if bold else F_FX
        c = ws.cell(row=r, column=4, value=formula); c.font = F_B if bold else F_FX; c.number_format = fmt
        rows[key] = r; cur[0] += 1
        return f"$D${r}"

    # ---- scalar inputs pulled into column D (green links) --------------------------------------
    sec("1. Parameters (links to Input, selected case)")
    def link(key, lab, ref, fmt=NUM):
        r = cur[0]
        ws.cell(row=r, column=2, value=lab).font = F_FX
        c = ws.cell(row=r, column=4, value=f"={ref}"); c.font = F_LINK; c.number_format = fmt
        rows[key] = r; cur[0] += 1
        return f"$D${r}"
    MW = link("mw", "Net capacity, MW", R["smr_mw"] if smr else R[f"{p}_mw"])
    CAPEX = link("capex", "Overnight capex, PLN/kW", R["smr_capex"] if smr else R[f"{p}_capex"])
    CONSTR = link("constr", "Construction years", R["smr_constr"] if smr else R[f"{p}_constr"], "0")
    COD = link("cod", "COD year", R["smr_cod"] if smr else R["gas_cod"], "0")
    LIFE = link("life", "Life years", R["smr_life"] if smr else R[f"{p}_life"], "0")
    FID = scalar("fid", "FID year (COD − construction)", f"={COD}-{CONSTR}", "0", False)
    WACC = link("wacc", "Real post-tax WACC", R["wacc_smr_cfd"] if kind in ("smr_cfd", "smr_fixed") else R["wacc_smr_merch"] if smr else R["wacc_gas"], PCT)
    FOM = link("fom", "Fixed O&M, PLN/kW-yr", R["smr_fom"] if smr else R[f"{p}_fom"])
    VOM = link("vom", "Variable O&M, PLN/MWh", R["smr_vom"] if smr else R[f"{p}_vom"], NUM1)
    FX = link("fx", "EUR/PLN", R["eur_pln"], "0.0000")
    CIT = link("cit", "CIT rate", R["cit"], PCT)
    LIC = link("lic", "Licence fee share of revenue", R["licence_fee"], "0.00%")
    FTE = link("fte", "Staff FTE", R["smr_fte"] if smr else R[f"{p}_fte"])
    FTEC = link("ftec", "Loaded cost per FTE, k PLN", R["smr_fte_cost"] if smr else R[f"{p}_fte_cost"])
    BUD = link("bud", "Budowle share of capex", R["smr_budowle"] if smr else R[f"{p}_budowle"], PCT)
    PTR = scalar("ptr", "Property tax rate", f"=0.02" if smr else f"={R['gas_ptax']}", PCT, False)
    HOST = scalar("host", "Host-gmina share of property tax", f"={R['smr_host']}" if smr else "=1", PCT, False)
    OVN = scalar("ovn", "Overnight cost, m PLN", f"={CAPEX}*{MW}*1000/1000000")
    if smr:
        FUEL = link("fuelp", "Nuclear fuel, PLN/MWh", R["smr_fuel"], NUM1)
        FUND = link("fund", "Decommissioning fund, PLN/MWh", R["smr_fund"], NUM1)
        SUST = link("sust", "Sustaining capex, PLN/MWh @90 % CF", R["smr_sust"], NUM1)
        PREDEV = link("predev", "Pre-development, m PLN", R["smr_predev"])
        CORE = link("core", "First core, m PLN", R["smr_core"])
        GRID = link("grid", "Grid connection, m PLN", R["smr_grid"])
        FOMM = link("fomm", "Single-unit FOM multiplier", R["smr_fom_mult"], "0.00")
        SUY = link("suy", "Single-unit years", R["smr_single_yrs"], "0")
        LFU = link("lfu", "Load-following capability loss", R["smr_lf_ucf"], PCT)
        LFF = link("lff", "Load-following FOM uplift", R["smr_lf_fom"], PCT)
        KWD = link("kwd", "Capacity-market de-rating", R["kwd_nuc"], "0.0000")
        WORK = link("work", "Peak construction workforce", R["smr_workers"])
        if kind == "smr_cfd":
            STRIKE_EUR = link("strike_eur", "CfD strike, EUR/MWh", R["strike"], NUM1)
            STRIKE = scalar("strike", "CfD strike, PLN/MWh", f"={STRIKE_EUR}*{FX}", NUM1)
            TENOR = link("tenor", "CfD tenor, years", R["tenor"], "0")
        if kind == "smr_fixed":
            FIXP = link("fixp", "Fixed price, PLN/MWh", R["fixed_price"], NUM1)
        dep_shares = [("b", R["smr_dep_b"], R["dep_b"]), ("s", R["smr_dep_s"], R["dep_s"]), ("r", R["smr_dep_r"], R["dep_r"]), ("t", R["smr_dep_t"], R["dep_t"]), ("d", R["smr_dep_d"], R["dep_d"])]
    else:
        ETA = link("eta", "Net efficiency full load", R[f"{p}_eta"], PCT)
        EF = link("ef", "CO2 factor, t/MWh_th", R["ef_gas"], "0.0000")
        EXIT = link("exit", "Gas exit-capacity booking, PLN/kW-yr", R[f"{p}_exit"])
        GRIDK = link("gridk", "Grid connection, PLN/kW", R["gas_grid"])
        DECOM = link("decom", "Demolition provision share", R["gas_decom"], PCT)
        KWD = link("kwd", "Capacity-market de-rating", R["kwd_ccgt"] if kind == "ccgt" else R["kwd_ocgt"], "0.0000")
        BAL = link("bal", "Balancing revenue, PLN/kW-yr", R["bal_ccgt"] if kind == "ccgt" else R["bal_ocgt"])
        WORK = scalar("work", "Peak construction workforce", f"={R['gas_workers']}*{MW}/300", NUM, False)
        dep_shares = [("b", R[f"{p}_dep_b"], R["dep_b"]), ("s", R[f"{p}_dep_s"], R["dep_s"]), ("t", R[f"{p}_dep_t"], R["dep_t"]), ("d", R[f"{p}_dep_d"], R["dep_d"])]
    CMP = link("cmp", "Capacity-market price, PLN/kW-yr", R["cm_price"])
    CMY = link("cmy", "Capacity contract years", R["cm_years"], "0")
    cur[0] += 1

    # ---- timeline ---------------------------------------------------------------------------
    sec("2. Timing")
    Y = lambda col: f"{col}$4"
    line("constr", "Construction flag", "0/1", lambda c, pv: f"=IF(AND({Y(c)}>={FID},{Y(c)}<{COD}),1,0)", "0")
    line("op", "Operating flag", "0/1", lambda c, pv: f"=IF(AND({Y(c)}>={COD},{Y(c)}<{COD}+{LIFE}),1,0)", "0")
    line("k", "Operating year k", "#", lambda c, pv: f"=IF({c}{rows['op']}=1,{Y(c)}-{COD}+1,0)", "0")
    line("t", "Discount period (years from FID)", "#", lambda c, pv: f"={Y(c)}-{FID}", "0")
    line("df", "Discount factor", "#", lambda c, pv: f"=IF({Y(c)}>={FID},1/(1+{WACC})^{c}{rows['t']},0)", "0.0000")
    # spend profile: S-curve for nuclear, front-loaded for gas — Beta-like weights normalised over construction years
    line("sprof", "Capex spend share (S-curve, normalised)", "%", lambda c, pv: (
        f"=IF({c}{rows['constr']}=1,1+1.7*SIN(PI()*(({Y(c)}-{FID}+0.5)/{CONSTR}))^2,0)" if smr else f"=IF({c}{rows['constr']}=1,IF({Y(c)}-{FID}=0,0.3,IF({Y(c)}-{FID}=1,0.45,0.25/MAX({CONSTR}-2,1))),0)"), PCT)
    line("sprofn", "Capex spend share normalised", "%", lambda c, pv: f"=IF(SUM(${L(C0)}{rows['sprof']}:${L(C0+NY-1)}{rows['sprof']})>0,{c}{rows['sprof']}/SUM(${L(C0)}{rows['sprof']}:${L(C0+NY-1)}{rows['sprof']}),0)", PCT)
    cur[0] += 1

    sec("3. Investment (m PLN)")
    line("capex", "Overnight capex spend", "m PLN", lambda c, pv: f"={OVN}*{c}{rows['sprofn']}", total="sum")
    if smr:
        line("ocapex", "Other capex (pre-development at FID, first core at COD−1, grid spread)", "m PLN",
             lambda c, pv: f"=IF({Y(c)}={FID},{PREDEV},0)+IF({Y(c)}={COD}-1,{CORE},0)+{GRID}*{c}{rows['sprofn']}", total="sum")
    else:
        line("ocapex", "Other capex (grid connection, spread)", "m PLN", lambda c, pv: f"={GRIDK}*{MW}/1000*{c}{rows['sprofn']}", total="sum")
    line("capext", "Total capex", "m PLN", lambda c, pv: f"={c}{rows['capex']}+{c}{rows['ocapex']}", total="sum", bold=True)
    cur[0] += 1

    sec("4. Market inputs (selected case, from Input)")
    pc = lambda c: L(C0 + 3 + (int(L_to_i(c)) - C0))   # Input series column for same year
    line("pmean", "Annual mean day-ahead price", "PLN/MWh", lambda c, pv: f"=Input!{pc(c)}{r_price}", NUM1)
    if not smr:
        line("gasp", "Gas price (PL virtual point)", "PLN/MWh_th", lambda c, pv: f"=Input!{pc(c)}{r_gas}", NUM1)
        line("eua", "EUA price", "PLN/t", lambda c, pv: f"=Input!{pc(c)}{r_eua}*{FX}", NUM1)
    cur[0] += 1

    sec("5. Dispatch (from hourly twin) and revenue")
    twc = lambda met, c: f"IFERROR(INDEX(Twin!${L(C0)}${TW[(scen, met)]}:${L(C0+K_MAX-1)}${TW[(scen, met)]},1,{c}{rows['k']}),0)"
    line("cf", "Capacity factor (twin)", "%", lambda c, pv: f"=IF({c}{rows['op']}=1,{twc('cf', c)},0)", PCT)
    if kind in ("smr_cfd", "smr_dyn"):
        line("energy", "Net generation (twin CF already net of load-following capability loss)", "MWh", lambda c, pv: f"={c}{rows['cf']}*{MW}*8760", NUM, total="sum")
    else:
        line("energy", "Net generation", "MWh", lambda c, pv: f"={c}{rows['cf']}*{MW}*8760", NUM, total="sum")
    if kind == "smr_fixed":
        line("capture", "Realised price", "PLN/MWh", lambda c, pv: f"=IF({c}{rows['op']}=1,{FIXP},0)", NUM1)
    else:
        line("capture", "Capture price = mean × capture ratio (twin)", "PLN/MWh", lambda c, pv: f"=IF({c}{rows['op']}=1,{c}{rows['pmean']}*{twc('capture', c)},0)", NUM1)
    line("revm", "Market revenue", "m PLN", lambda c, pv: f"={c}{rows['energy']}*{c}{rows['capture']}/1000000", total="sum")
    if kind == "smr_cfd":
        line("cfdref", "CfD reference price (daily TGeBase, generation-weighted; twin)", "PLN/MWh", lambda c, pv: f"=IF(AND({c}{rows['op']}=1,{c}{rows['k']}<={TENOR}),{c}{rows['pmean']}*{twc('cfd_ref', c)},0)", NUM1)
        line("cfd", "CfD difference payment (+ top-up / − pay-back)", "m PLN", lambda c, pv: f"=IF(AND({c}{rows['op']}=1,{c}{rows['k']}<={TENOR}),{c}{rows['energy']}*({STRIKE}-{c}{rows['cfdref']})/1000000,0)", total="sum")
    else:
        line("cfd", "CfD difference payment", "m PLN", lambda c, pv: "=0", total="sum")
    line("caprev", "Capacity-market revenue", "m PLN", lambda c, pv: f"=IF(AND({c}{rows['op']}=1,{c}{rows['k']}<={CMY}),{CMP}*{KWD}*{MW}*1000/1000000,0)", total="sum")
    if smr:
        line("balrev", "Balancing-services revenue", "m PLN", lambda c, pv: "=0", total="sum")
    else:
        line("balrev", "Balancing-services revenue", "m PLN", lambda c, pv: f"=IF({c}{rows['op']}=1,{BAL}*{MW}*1000/1000000,0)", total="sum")
    line("rev", "Total revenue", "m PLN", lambda c, pv: f"={c}{rows['revm']}+{c}{rows['cfd']}+{c}{rows['caprev']}+{c}{rows['balrev']}", total="sum", bold=True)
    cur[0] += 1

    sec("6. Operating costs (m PLN)")
    if smr:
        line("fuel", "Nuclear fuel (incl. part-load efficiency effect, twin ratio)", "m PLN", lambda c, pv: f"={c}{rows['energy']}*{FUEL}*IF({c}{rows['op']}=1,{twc('fuel_ratio', c)},0)/1000000", total="sum")
        line("co2", "CO2 cost", "m PLN", lambda c, pv: "=0", total="sum")
        line("vomc", "Variable O&M", "m PLN", lambda c, pv: f"={c}{rows['energy']}*{VOM}/1000000", total="sum")
        line("start", "Start-up / cycling cost", "m PLN", lambda c, pv: "=0", total="sum")
        line("fundc", "Decommissioning & waste fund", "m PLN", lambda c, pv: f"={c}{rows['energy']}*{FUND}/1000000", total="sum")
        line("fomc", "Fixed O&M (× single-unit multiplier, × load-following uplift)", "m PLN",
             lambda c, pv: f"=IF({c}{rows['op']}=1,{FOM}*{MW}*1000/1000000*IF({c}{rows['k']}<={SUY},{FOMM},1)*(1+{LFF if kind in ('smr_cfd','smr_dyn') else 0}),0)", total="sum")
        line("staff", "  memo: staff cost inside fixed O&M", "m PLN", lambda c, pv: f"=IF({c}{rows['op']}=1,{FTE}*{FTEC}/1000,0)", total="sum")
        line("sustc", "Sustaining capex", "m PLN", lambda c, pv: f"=IF({c}{rows['op']}=1,{SUST}*{MW}*8760*0.9/1000000,0)", total="sum")
        line("exitc", "Gas capacity booking", "m PLN", lambda c, pv: "=0", total="sum")
    else:
        line("heat", "Heat input (twin heat rate incl. no-load & start fuel)", "MWh_th", lambda c, pv: f"=IF({c}{rows['op']}=1,{c}{rows['energy']}*{twc('heat', c)},0)", NUM, total="sum")
        line("fuel", "Gas cost", "m PLN", lambda c, pv: f"={c}{rows['heat']}*{c}{rows['gasp']}/1000000", total="sum")
        line("co2t", "CO2 emissions", "t", lambda c, pv: f"={c}{rows['heat']}*{EF}", NUM, total="sum")
        line("co2", "CO2 cost (EUA)", "m PLN", lambda c, pv: f"={c}{rows['co2t']}*{c}{rows['eua']}/1000000", total="sum")
        line("vomc", "Variable O&M", "m PLN", lambda c, pv: f"={c}{rows['energy']}*{VOM}/1000000", total="sum")
        line("start", "Start-up costs (wear; twin)", "m PLN", lambda c, pv: f"=IF({c}{rows['op']}=1,{c}{rows['energy']}*{twc('start', c)}/1000000,0)", total="sum")
        line("fundc", "Decommissioning fund", "m PLN", lambda c, pv: "=0", total="sum")
        line("fomc", "Fixed O&M incl. LTSA", "m PLN", lambda c, pv: f"=IF({c}{rows['op']}=1,{FOM}*{MW}*1000/1000000,0)", total="sum")
        line("staff", "  memo: staff cost inside fixed O&M", "m PLN", lambda c, pv: f"=IF({c}{rows['op']}=1,{FTE}*{FTEC}/1000,0)", total="sum")
        line("sustc", "Sustaining capex", "m PLN", lambda c, pv: "=0", total="sum")
        line("exitc", "Gas exit-capacity booking (Gaz-System)", "m PLN", lambda c, pv: f"=IF({c}{rows['op']}=1,{EXIT}*{MW}*1000/1000000,0)", total="sum")
    line("ptax", "Property tax (2 % of budowle value)", "m PLN", lambda c, pv: f"=IF({c}{rows['op']}=1,{PTR}*{BUD}*{OVN},0)", total="sum")
    line("lic", "URE licence fee", "m PLN", lambda c, pv: f"=IF({c}{rows['op']}=1,{LIC}*MAX({c}{rows['rev']},0),0)", total="sum")
    line("opex", "Total opex", "m PLN", lambda c, pv: f"={c}{rows['fuel']}+{c}{rows['co2']}+{c}{rows['vomc']}+{c}{rows['start']}+{c}{rows['fundc']}+{c}{rows['fomc']}+{c}{rows['sustc']}+{c}{rows['exitc']}+{c}{rows['ptax']}+{c}{rows['lic']}", total="sum", bold=True)
    line("ebitda", "EBITDA", "m PLN", lambda c, pv: f"={c}{rows['rev']}-{c}{rows['opex']}", total="sum", bold=True)
    if smr:
        line("decomp", "End-of-life provision (nuclear: covered by fund)", "m PLN", lambda c, pv: "=0", total="sum")
    else:
        line("decomp", "End-of-life demolition provision", "m PLN", lambda c, pv: f"=IF({Y(c)}={COD}+{LIFE}-1,{DECOM}*{OVN},0)", total="sum")
    cur[0] += 1

    sec("7. Tax (Polish CIT, straight-line KŚT depreciation, loss carry-forward)")
    CAPT = f"$D${rows['capext']}"
    for tag, share_ref, rate_ref in dep_shares:
        line(f"dep_{tag}", f"Depreciation — KŚT group ({tag})", "m PLN", lambda c, pv, sr=share_ref, rr=rate_ref: f"=IF(AND({c}{rows['op']}=1,{c}{rows['k']}<=ROUNDUP(1/{rr},0)),MIN({CAPT}*{sr}*{rr},MAX({CAPT}*{sr}-{CAPT}*{sr}*{rr}*({c}{rows['k']}-1),0)),0)", total="sum")
    dep_keys = [f"dep_{t}" for t, _, _ in dep_shares]
    line("dep", "Total tax depreciation", "m PLN", lambda c, pv: "=" + "+".join(f"{c}{rows[k]}" for k in dep_keys), total="sum", bold=True)
    line("ebit", "Taxable EBIT (EBITDA − depreciation − provisions)", "m PLN", lambda c, pv: f"={c}{rows['ebitda']}-{c}{rows['dep']}-{c}{rows['decomp']}", total="sum")
    rows["losspool"] = cur[0] + 1
    line("lossuse", "Loss utilisation (50 % cap per year, simplified pool)", "m PLN", lambda c, pv: (f"=IF({c}{rows['ebit']}>0,MIN({pv}{rows['losspool']},0.5*{c}{rows['ebit']}),0)" if pv else "=0"))
    line("losspool", "Loss pool carried forward (EoY)", "m PLN", lambda c, pv: (f"=MAX({pv}{rows['losspool']}-{c}{rows['lossuse']}+MAX(-{c}{rows['ebit']},0),0)" if pv else f"=MAX(-{c}{rows['ebit']},0)"))
    line("taxable", "Taxable income", "m PLN", lambda c, pv: f"=MAX({c}{rows['ebit']}-{c}{rows['lossuse']},0)", total="sum")
    line("citc", "CIT", "m PLN", lambda c, pv: f"={c}{rows['taxable']}*{CIT}", total="sum", bold=True)
    cur[0] += 1

    sec("8. Cash flow and valuation (m PLN)")
    line("fcfpre", "Pre-tax free cash flow", "m PLN", lambda c, pv: f"={c}{rows['ebitda']}-{c}{rows['capext']}-{c}{rows['decomp']}", total="sum")
    line("fcf", "Post-tax free cash flow (unlevered)", "m PLN", lambda c, pv: f"={c}{rows['fcfpre']}-{c}{rows['citc']}", total="sum", bold=True)
    line("cum", "Cumulative post-tax FCF", "m PLN", lambda c, pv: (f"={pv}{rows['cum']}+{c}{rows['fcf']}" if pv else f"={c}{rows['fcf']}"))
    line("dfcf", "Discounted post-tax FCF", "m PLN", lambda c, pv: f"={c}{rows['fcf']}*{c}{rows['df']}", total="sum")
    rng = lambda key: f"${L(C0)}${rows[key]}:${L(C0+NY-1)}${rows[key]}"
    SP = lambda key: f"SUMPRODUCT({rng(key)},{rng('df')})"
    NPV = scalar("npv", "NPV post-tax @ WACC (m PLN)", f"=SUMPRODUCT({rng('fcf')},{rng('df')})")
    NPVPRE = scalar("npvpre", "NPV pre-tax @ WACC (m PLN)", f"=SUMPRODUCT({rng('fcfpre')},{rng('df')})")
    IRR = scalar("irr", "IRR post-tax (real)", f"=IFERROR(IRR(OFFSET({L(C0)}{rows['fcf']},0,{FID}-{Y0},1,{LIFE}+{CONSTR}),0.05),\"n/a\")", PCT)
    PVE = scalar("pv_energy", "PV of generation (MWh)", f"={SP('energy')}", NUM)
    PVC = scalar("pv_cost", "PV of all costs (capex + opex + provisions)", f"={SP('capext')}+{SP('opex')}+{SP('decomp')}")
    scalar("pv_capex", "PV capex", f"={SP('capext')}", NUM, False)
    scalar("pv_fom", "PV fixed O&M", f"={SP('fomc')}", NUM, False)
    scalar("pv_fuel", "PV fuel", f"={SP('fuel')}", NUM, False)
    scalar("pv_co2", "PV CO2", f"={SP('co2')}", NUM, False)
    scalar("pv_vom", "PV variable O&M + starts", f"={SP('vomc')}+{SP('start')}", NUM, False)
    scalar("pv_fund", "PV decommissioning fund / provision", f"={SP('fundc')}+{SP('decomp')}", NUM, False)
    scalar("pv_sust", "PV sustaining capex", f"={SP('sustc')}", NUM, False)
    scalar("pv_other", "PV property tax + licence + gas booking", f"={SP('ptax')}+{SP('lic')}+{SP('exitc')}", NUM, False)
    PVR = scalar("pv_rev", "PV of revenue", f"={SP('rev')}")
    LCOE = scalar("lcoe", "LCOE (PLN/MWh)", f"=IFERROR({PVC}*1000000/{PVE},0)", NUM1)
    LEVREV = scalar("levrev", "Levelised revenue (PLN/MWh)", f"=IFERROR({PVR}*1000000/{PVE},0)", NUM1)
    CF = scalar("cf", "Average capacity factor", f"=IFERROR(AVERAGEIF({rng('op')},1,{rng('cf')}),0)", PCT)
    CFDPV = scalar("cfd_pv", "PV of CfD payments / capacity support (m PLN)", f"={SP('cfd')}+{SP('caprev')}")
    if kind == "smr_cfd":
        # exact pre-tax break-even strike; post-tax approximation with (1−CIT) factor on the increment
        BE = scalar("be", "Break-even strike EUR/MWh (post-tax ≈; NPV=0)", f"=({STRIKE}-{NPV}/((1-{CIT})*SUMPRODUCT({rng('energy')},{rng('df')},--({rng('k')}<={TENOR}),--({rng('k')}>0))/1000000))/{FX}", NUM1)
    else:
        BE = scalar("be", "Required premium PLN/MWh on all output (post-tax ≈; NPV=0)", f"=-{NPV}/((1-{CIT})*{PVE}/1000000)", NUM1)
    cur[0] += 1

    sec("9. Fiscal flows — local government and State (m PLN)")
    line("pt_host", "Property tax → host gmina (Stalowa Wola)", "m PLN", lambda c, pv: f"={c}{rows['ptax']}*{HOST}", total="sum")
    line("pt_nb", "Property tax → bordering gminas (art. 50)", "m PLN", lambda c, pv: f"={c}{rows['ptax']}*(1-{HOST})", total="sum")
    line("lcit_g", "CIT-income share → gmina", "m PLN", lambda c, pv: f"={c}{rows['taxable']}*{R['cit_gmina']}", total="sum")
    line("lcit_p", "CIT-income share → powiat", "m PLN", lambda c, pv: f"={c}{rows['taxable']}*{R['cit_powiat']}", total="sum")
    line("lcit_w", "CIT-income share → województwo", "m PLN", lambda c, pv: f"={c}{rows['taxable']}*{R['cit_woj']}", total="sum")
    # PIT: per-FTE income base = gross × (1 − employee ZUS); gross = loaded cost /(1+employer ZUS)
    GROSS = scalar("gross", "Gross salary per FTE (PLN/yr)", f"={FTEC}*1000/(1+{R['zus_er']})", NUM, False)
    INC = scalar("inc", "PIT income base per FTE (PLN/yr)", f"={GROSS}*(1-{R['zus_ee']})", NUM, False)
    PITT = scalar("pitt", "PIT per FTE (PLN/yr)", f"=MAX({R['pit_lo']}*MIN({INC},{R['pit_thr']})+{R['pit_hi']}*MAX({INC}-{R['pit_thr']},0)-{R['pit_free']},0)", NUM, False)
    CWINC = scalar("cwinc", "Construction worker PIT income base (PLN/yr)", f"={R['cw_gross']}*12*(1-{R['zus_ee']})", NUM, False)
    line("lpit_g", "PIT-income share → gmina (staff + construction workers)", "m PLN",
         lambda c, pv: f"=({c}{rows['op']}*{FTE}*{INC}*{R['res_share']}+{c}{rows['constr']}*{WORK}*{c}{rows['sprofn']}/MAX({rng('sprofn')})*{CWINC}*{R['cw_res']})*{R['pit_gmina']}/1000000", total="sum")
    line("lpit_p", "PIT-income share → powiat", "m PLN",
         lambda c, pv: f"=({c}{rows['op']}*{FTE}*{INC}*{R['res_share']}+{c}{rows['constr']}*{WORK}*{c}{rows['sprofn']}/MAX({rng('sprofn')})*{CWINC}*{R['cw_res']})*{R['pit_powiat']}/1000000", total="sum")
    line("lpit_w", "PIT-income share → województwo", "m PLN", lambda c, pv: f"={c}{rows['op']}*{FTE}*{INC}*{R['res_share']}*{R['pit_woj']}/1000000", total="sum")
    line("local", "Total local-government revenue", "m PLN", lambda c, pv: f"={c}{rows['pt_host']}+{c}{rows['pt_nb']}+{c}{rows['lcit_g']}+{c}{rows['lcit_p']}+{c}{rows['lcit_w']}+{c}{rows['lpit_g']}+{c}{rows['lpit_p']}+{c}{rows['lpit_w']}", total="sum", bold=True)
    line("pitpaid", "PIT paid by staff (State + JST, memo)", "m PLN", lambda c, pv: f"={c}{rows['op']}*{FTE}*{PITT}/1000000", total="sum")
    local_row = rows["local"]
    LOCAL = scalar("local_avg", "Local revenue per operating year, average (m PLN)", f"=IFERROR(SUMIF({rng('op')},1,{rng('local')})/COUNTIF({rng('op')},1),0)", NUM1)
    scalar("sum_cit", "CIT paid over life (m PLN)", f"=SUM({rng('citc')})", NUM, False)
    scalar("sum_co2", "EUA cost over life (m PLN)", f"=SUM({rng('co2')})", NUM, False)
    scalar("sum_fund", "Fund contributions over life (m PLN)", f"=SUM({rng('fundc')})", NUM, False)
    scalar("sum_cfd", "CfD payments over life (m PLN)", f"=SUM({rng('cfd')})", NUM, False)
    scalar("sum_pt_host", "Property tax host gmina over life (m PLN)", f"=SUM({rng('pt_host')})", NUM, False)
    scalar("sum_pt_nb", "Property tax neighbours over life (m PLN)", f"=SUM({rng('pt_nb')})", NUM, False)
    scalar("sum_lcit", "CIT-income shares over life (m PLN)", f"=SUM({rng('lcit_g')})+SUM({rng('lcit_p')})+SUM({rng('lcit_w')})", NUM, False)
    scalar("sum_lpit", "PIT-income shares over life (m PLN)", f"=SUM({rng('lpit_g')})+SUM({rng('lpit_p')})+SUM({rng('lpit_w')})", NUM, False)

    out = {k: f"$D${rows[k]}" for k in ("npv", "npvpre", "irr", "pv_energy", "pv_cost", "pv_capex", "pv_fom", "pv_fuel", "pv_co2", "pv_vom", "pv_fund", "pv_sust", "pv_other", "pv_rev", "lcoe", "levrev", "cf", "cfd_pv", "be", "local_avg", "sum_cit", "sum_co2", "sum_fund", "sum_cfd", "sum_pt_host", "sum_pt_nb", "sum_lcit", "sum_lpit")}
    out["local"] = out.pop("local_avg")
    out["fcf_row"] = rows["fcf"]; out["rev_row"] = rows["rev"]; out["local_row"] = local_row
    return out


def L_to_i(col: str) -> int:
    from openpyxl.utils import column_index_from_string
    return column_index_from_string(col)


if __name__ == "__main__":
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "excel" / "SMR_vs_Alternatives_Financial_Model.xlsx"
    out.parent.mkdir(exist_ok=True, parents=True)
    build(out)
