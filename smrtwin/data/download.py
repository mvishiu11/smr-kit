"""Download raw Polish power-market data used by the digital twin.

Sources
-------
* PSE (Polskie Sieci Elektroenergetyczne) open API  https://api.raporty.pse.pl/api/
    - ``csdac-pln``  : SDAC day-ahead clearing price for the Polish bidding zone, PLN/MWh
                       (hourly until 30 Sep 2025, 15-minute from 1 Oct 2025)
    - ``rce-pln``    : RCE market price (used for RES settlement), PLN/MWh
    - ``his-wlk-cal``: KSE hourly fundamentals (demand, wind, PV, ...)
    - ``cmbp-tp``    : balancing-capacity prices (FCR, aFRR, mFRR) PLN/MW/h
    - ``crb-rozl``   : balancing energy settlement prices
* energy-charts.info (Fraunhofer ISE, data from ENTSO-E / SMARD, CC BY 4.0)
    - day-ahead price for bidding zone PL, EUR/MWh, from 2015

All files are written to ``data/raw`` as CSV.  Re-running is idempotent (files are
overwritten).  The PSE API is paginated (``$first`` / ``nextLink``); we page by
business_date ranges to keep requests small.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

import pandas as pd

RAW = Path(__file__).resolve().parents[2] / "data" / "raw"
PSE_API = "https://api.raporty.pse.pl/api/"
EC_API = "https://api.energy-charts.info/price"


def _get_json(url: str, retries: int = 5, timeout: int = 60) -> dict:
    last = None
    for i in range(retries):
        try:
            with urllib.request.urlopen(url, timeout=timeout) as r:
                return json.loads(r.read().decode())
        except Exception as e:  # noqa: BLE001
            last = e
            time.sleep(2 * (i + 1))
    raise RuntimeError(f"failed after {retries} retries: {url}: {last}")


def pse_entity(entity: str, start: dt.date, end: dt.date, step_days: int = 14) -> pd.DataFrame:
    """Fetch a PSE entity for [start, end] inclusive, paging through nextLink."""
    frames = []
    d = start
    while d <= end:
        d2 = min(d + dt.timedelta(days=step_days - 1), end)
        flt = f"business_date ge '{d.isoformat()}' and business_date le '{d2.isoformat()}'"
        url = f"{PSE_API}{entity}?$filter={urllib.parse.quote(flt)}&$first=20000"
        while url:
            js = _get_json(url)
            frames.append(pd.DataFrame(js.get("value", [])))
            url = js.get("nextLink")
        print(f"  {entity}: {d} .. {d2}  rows so far {sum(len(f) for f in frames):,}", file=sys.stderr)
        d = d2 + dt.timedelta(days=1)
    df = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    return df


def energy_charts_prices(start: dt.date, end: dt.date) -> pd.DataFrame:
    """Day-ahead price PL in EUR/MWh from energy-charts (hourly; 15-min after Oct 2025)."""
    frames = []
    d = start
    while d <= end:
        d2 = min(d + dt.timedelta(days=90), end)
        url = f"{EC_API}?bzn=PL&start={d.isoformat()}&end={d2.isoformat()}"
        js = _get_json(url)
        f = pd.DataFrame({"unix_seconds": js["unix_seconds"], "price_eur_mwh": js["price"]})
        frames.append(f)
        print(f"  energy-charts: {d} .. {d2}  rows {len(f):,}", file=sys.stderr)
        d = d2 + dt.timedelta(days=1)
    df = pd.concat(frames, ignore_index=True).drop_duplicates("unix_seconds")
    df["time_utc"] = pd.to_datetime(df["unix_seconds"], unit="s", utc=True)
    return df[["time_utc", "price_eur_mwh"]]


def nbp_eur_pln(start: dt.date, end: dt.date) -> pd.DataFrame:
    """Daily NBP table-A EUR/PLN mid rates (API limit 93 days per call)."""
    frames = []
    d = start
    while d <= end:
        d2 = min(d + dt.timedelta(days=92), end)
        url = f"https://api.nbp.pl/api/exchangerates/rates/a/eur/{d.isoformat()}/{d2.isoformat()}/?format=json"
        try:
            js = _get_json(url, retries=3, timeout=30)
            frames.append(pd.DataFrame(js["rates"])[["effectiveDate", "mid"]])
        except Exception as e:  # noqa: BLE001
            print(f"  nbp {d}..{d2} failed: {e}", file=sys.stderr)
        d = d2 + dt.timedelta(days=1)
    df = pd.concat(frames, ignore_index=True).rename(columns={"effectiveDate": "date", "mid": "eur_pln"})
    return df


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--start", default="2024-06-14", help="PSE API history start (API launched Jun 2024)")
    ap.add_argument("--end", default=(dt.date.today() - dt.timedelta(days=1)).isoformat())
    ap.add_argument("--ec-start", default="2019-01-01", help="energy-charts history start")
    ap.add_argument("--skip", nargs="*", default=[], help="entities to skip")
    a = ap.parse_args(argv)
    RAW.mkdir(parents=True, exist_ok=True)
    start, end = dt.date.fromisoformat(a.start), dt.date.fromisoformat(a.end)

    if "energy-charts" not in a.skip:
        ec = energy_charts_prices(dt.date.fromisoformat(a.ec_start), end)
        ec.to_csv(RAW / "energy_charts_da_price_PL_eur.csv", index=False)
    if "nbp" not in a.skip:
        fx = nbp_eur_pln(dt.date.fromisoformat(a.ec_start), end)
        fx.to_csv(RAW / "nbp_eur_pln.csv", index=False)

    for ent in ["csdac-pln", "rce-pln", "his-wlk-cal", "cmbp-tp", "crb-rozl"]:
        if ent in a.skip:
            continue
        df = pse_entity(ent, start, end)
        df.to_csv(RAW / f"pse_{ent}.csv", index=False)
        print(f"wrote pse_{ent}.csv  {len(df):,} rows", file=sys.stderr)


if __name__ == "__main__":
    main()
