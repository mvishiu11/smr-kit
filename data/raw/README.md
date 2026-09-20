# Raw market data (not committed — ~55 MB)

Re-download with `python -m smrtwin.data.download` (PSE open API, energy-charts.info, NBP):

| file | source | content |
|---|---|---|
| pse_csdac-pln.csv | https://api.raporty.pse.pl/api/csdac-pln | SDAC day-ahead price PL, PLN/MWh, 15-min from 1 Oct 2025, hourly before (from 14 Jun 2024) |
| pse_rce-pln.csv | …/rce-pln | RCE settlement price |
| pse_his-wlk-cal.csv | …/his-wlk-cal | KSE hourly fundamentals (demand, wind, PV) |
| pse_cmbp-tp.csv | …/cmbp-tp | balancing-capacity prices (FCR/aFRR/mFRR) |
| pse_crb-rozl.csv | …/crb-rozl | balancing energy settlement prices |
| energy_charts_da_price_PL_eur.csv | https://api.energy-charts.info/price?bzn=PL | day-ahead PL EUR/MWh 2019→ (ENTSO-E via Fraunhofer ISE, CC BY 4.0) |
| nbp_eur_pln.csv | https://api.nbp.pl | NBP table-A EUR/PLN daily mid |

`data/processed/` (committed) holds the derived 8,760-h reference years and monthly summary.
