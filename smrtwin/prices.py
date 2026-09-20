"""Hourly price twin of the Polish day-ahead market (TGE RDN / SDAC bidding zone PL).

Pipeline
--------
1. :func:`load_hourly_history` — merges PSE ``csdac-pln`` (PLN, 15-min → hourly mean, from
   14 Jun 2024) with energy-charts day-ahead EUR prices × NBP daily EUR/PLN (2019 → Jun 2024)
   into one hourly PLN/MWh series.
2. :func:`reference_year` — cuts an 8,760-h reference window (``last12m`` = the 12 full months
   before the data end, or a calendar year).
3. :func:`shape_model` — decomposes the reference year into a *seasonal-diurnal shape* (mean by
   month × weekday/weekend × hour, normalised to mean 1) and a *residual volatility* series, so
   the year can be re-synthesised or re-anchored on any annual mean.
4. :func:`price_year` — produces the 8,760-h PLN/MWh vector for a future model year: the
   reference year's hourly pattern re-anchored on the scenario's annual mean and (optionally)
   deepened around midday to represent solar cannibalisation.

The "digital twin" here is deliberately empirical: real Polish hourly prices carry the
weekday/weekend pattern, solar-dip, winter-evening peaks, negative hours and the 2025/26 gas
shock, none of which a synthetic sinusoid reproduces.  Price-taker assumption: 300–600 MW of new
capacity does not change prices (see ASSUMPTIONS.md for the caveat).
"""
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd

RAW = Path(__file__).resolve().parents[1] / "data" / "raw"
PROCESSED = Path(__file__).resolve().parents[1] / "data" / "processed"


# --------------------------------------------------------------------------------------
# 1. History
# --------------------------------------------------------------------------------------
@lru_cache(maxsize=1)
def load_hourly_history() -> pd.Series:
    """Hourly day-ahead price for PL in PLN/MWh, local time (Europe/Warsaw), DST-naive hours."""
    # --- PSE SDAC price (PLN) --------------------------------------------------------
    pse = pd.read_csv(RAW / "pse_csdac-pln.csv", usecols=["dtime_utc", "csdac_pln"])
    pse["t"] = pd.to_datetime(pse["dtime_utc"], utc=True)
    # dtime is period *end*; shift back 1 minute so 00:15 → belongs to hour 00
    pse["h"] = (pse["t"] - pd.Timedelta(minutes=1)).dt.floor("h")
    pse_h = pse.groupby("h")["csdac_pln"].mean()

    # --- energy-charts (EUR) × NBP EUR/PLN for the pre-PSE period ---------------------
    ec = pd.read_csv(RAW / "energy_charts_da_price_PL_eur.csv")
    ec["t"] = pd.to_datetime(ec["time_utc"], utc=True)
    ec["h"] = ec["t"].dt.floor("h")
    ec_h = ec.groupby("h")["price_eur_mwh"].mean()
    fx = pd.read_csv(RAW / "nbp_eur_pln.csv")
    fx["date"] = pd.to_datetime(fx["date"])
    fx = fx.set_index("date")["eur_pln"].asfreq("D").ffill()
    fx_h = fx.reindex(ec_h.index.tz_convert("Europe/Warsaw").normalize().tz_localize(None), method="ffill").values
    ec_pln = pd.Series(ec_h.values * fx_h, index=ec_h.index)

    start_pse = pse_h.index.min()
    hist = pd.concat([ec_pln[ec_pln.index < start_pse], pse_h]).sort_index()
    hist = hist[~hist.index.duplicated()]
    hist.index = hist.index.tz_convert("Europe/Warsaw")
    hist.name = "price_pln_mwh"
    return hist


def monthly_summary(hist: pd.Series | None = None) -> pd.DataFrame:
    hist = load_hourly_history() if hist is None else hist
    df = hist.to_frame()
    df["ym"] = df.index.to_period("M")
    g = df.groupby("ym")["price_pln_mwh"]
    out = pd.DataFrame({"mean": g.mean(), "std": g.std(), "min": g.min(), "max": g.max(),
                        "neg_hours": g.apply(lambda s: int((s < 0).sum())), "hours": g.size()})
    return out


# --------------------------------------------------------------------------------------
# 2. Reference year
# --------------------------------------------------------------------------------------
def _to_8760(s: pd.Series) -> pd.Series:
    """Drop 29 Feb and fix DST so the series has exactly 8,760 hourly values in local clock order."""
    s = s[~((s.index.month == 2) & (s.index.day == 29))]
    local_naive = s.index.tz_localize(None)
    s = pd.Series(s.values, index=local_naive)
    s = s[~s.index.duplicated(keep="first")]           # autumn DST duplicate hour
    full = pd.date_range(s.index.min().normalize(), periods=8760, freq="h")
    s = s.reindex(full).interpolate(limit_direction="both")   # spring DST gap
    return s


def reference_year(window: str = "last12m", hist: pd.Series | None = None) -> pd.Series:
    """Return an 8,760-h series (naive local time index) for the requested window."""
    hist = load_hourly_history() if hist is None else hist
    if window == "last12m":
        mx = hist.index.max()
        end = pd.Timestamp(year=mx.year, month=mx.month, day=1, tz="Europe/Warsaw")   # first day of the last (partial) month
        start = end - pd.DateOffset(years=1)
        s = hist[(hist.index >= start) & (hist.index < end)]
    elif window.startswith("cal"):
        y = int(window[3:])
        s = hist[hist.index.year == y]
    else:
        raise ValueError(window)
    s8760 = _to_8760(s)
    if len(s8760) != 8760:
        raise RuntimeError(f"reference window {window}: got {len(s8760)} hours")
    s8760.attrs["window"] = window
    s8760.attrs["start"] = str(s.index.min().date())
    s8760.attrs["end"] = str(s.index.max().date())
    return s8760


# --------------------------------------------------------------------------------------
# 3. Shape model
# --------------------------------------------------------------------------------------
@dataclass
class ShapeModel:
    ref: pd.Series                 # 8,760 reference prices
    seasonal_diurnal: np.ndarray   # 8,760 normalised expected shape (mean 1)
    residual: np.ndarray           # ref/mean − shape
    month: np.ndarray
    hour: np.ndarray
    weekend: np.ndarray
    solar_index: np.ndarray        # 0..1 weight of midday hours (for cannibalisation)

    @property
    def annual_mean(self) -> float:
        return float(self.ref.mean())


def shape_model(ref: pd.Series) -> ShapeModel:
    idx = ref.index
    month = idx.month.values
    hour = idx.hour.values
    weekend = (idx.dayofweek.values >= 5).astype(int)
    norm = ref.values / ref.values.mean()
    df = pd.DataFrame({"n": norm, "m": month, "h": hour, "w": weekend})
    key = df.groupby(["m", "w", "h"])["n"].transform("mean").values
    residual = norm - key
    # solar index: bell around 12:30 local, scaled by month (PV yield ~ Dec 0.15 → Jun 1.0)
    month_pv = np.array([0.15, 0.30, 0.55, 0.80, 0.95, 1.00, 1.00, 0.90, 0.70, 0.45, 0.20, 0.12])
    diurnal = np.exp(-0.5 * ((hour + 0.5 - 12.5) / 3.0) ** 2)
    solar = diurnal * month_pv[month - 1]
    return ShapeModel(ref, key, residual, month, hour, weekend, solar)


# --------------------------------------------------------------------------------------
# 4. Price year synthesis
# --------------------------------------------------------------------------------------
def price_year(sm: ShapeModel, annual_mean: float, extra_midday_depression: float = 0.0,
               keep_residual: bool = True, seasonal_multipliers: dict[int, float] | None = None) -> np.ndarray:
    """8,760 hourly prices (PLN/MWh) for one model year.

    Parameters
    ----------
    annual_mean : target arithmetic annual mean of the produced series.
    extra_midday_depression : fraction (0–0.35) by which midday prices are additionally pushed
        down relative to the reference year (solar cannibalisation).  The depression is
        redistributed to the other hours so that the annual mean is preserved.
    keep_residual : if False, the smooth seasonal-diurnal expectation is used (no volatility);
        if True the reference year's actual residual is kept (preferred: realistic spikes and
        negative hours).
    seasonal_multipliers : optional {month: multiplier} to re-weight seasons (mean re-normalised).
    """
    base = sm.seasonal_diurnal + (sm.residual if keep_residual else 0.0)
    if seasonal_multipliers:
        mult = np.array([seasonal_multipliers.get(int(m), 1.0) for m in sm.month])
        base = base * mult
    if extra_midday_depression > 0:
        # Depress midday hours proportionally to solar index; negative prices are pushed further negative.
        cut = extra_midday_depression * sm.solar_index * np.abs(base)
        base = base - cut
        # redistribute the removed value to evening/night hours (the "shoulder premium" observed 2024–26)
        shoulder = (1 - sm.solar_index) * ((sm.hour >= 16) | (sm.hour <= 8))
        base = base + cut.sum() * shoulder / shoulder.sum()
    base = base / base.mean()
    return base * annual_mean


def summarise_year(p: np.ndarray) -> dict:
    return {
        "mean": float(p.mean()), "std": float(p.std()), "p5": float(np.percentile(p, 5)),
        "p95": float(np.percentile(p, 95)), "min": float(p.min()), "max": float(p.max()),
        "neg_hours": int((p < 0).sum()), "hours_below_60": int((p < 60).sum()),
    }


def save_processed():
    PROCESSED.mkdir(parents=True, exist_ok=True)
    hist = load_hourly_history()
    hist.to_csv(PROCESSED / "da_price_PL_hourly_pln.csv", header=True)
    monthly_summary(hist).to_csv(PROCESSED / "da_price_PL_monthly.csv")
    for w in ("last12m", "cal2025", "cal2024", "cal2023"):
        try:
            r = reference_year(w, hist)
            r.to_csv(PROCESSED / f"reference_year_{w}.csv", header=["price_pln_mwh"])
        except Exception as e:  # noqa: BLE001
            print("skip", w, e)


if __name__ == "__main__":
    save_processed()
    h = load_hourly_history()
    print(h.index.min(), h.index.max(), len(h))
    print(monthly_summary(h).tail(15))
    r = reference_year("last12m")
    print(r.attrs, summarise_year(r.values))
