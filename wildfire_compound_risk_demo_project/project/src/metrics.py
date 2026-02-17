"""
metrics.py

Implements metric definitions EXACTLY as specified.

3.1 Effective Fire Weather (EFW)
    EFW = temp_c + 0.5 * wind_speed_ms - 0.2 * rh

3.2 Cumulative Fire Load (CFL)
    baseline_fire = 20.0
    CFL_hour = max(EFW - baseline_fire, 0)
    daily_CFL = sum(CFL_hour)
    cumulative_CFL = running sum

    Reset logic (in comments): significant precip_mm can be used to reset or reduce CFL,
    but implementation keeps the simple definition above.

3.3 Nighttime Recovery Deficit (NRD) — 20:00–08:00
    baseline_night_rh = 60.0
    baseline_night_wind = 5.0

    NRD_hour = 0
    if rh < baseline_night_rh or wind_speed_ms > baseline_night_wind:
        NRD_hour = 1  # hour of poor recovery
    daily_NRD = sum(NRD_hour)
    cumulative_NRD = running sum

Night window handling:
- Hours 20:00–23:00 are assigned to the same calendar date.
- Hours 00:00–07:00 are assigned to the previous calendar date (continuation of the same night).
This yields one "night" total per date.
"""

from __future__ import annotations

from dataclasses import dataclass
import pandas as pd
import numpy as np


@dataclass(frozen=True)
class DailyMetrics:
    daily: pd.DataFrame  # indexed by date (datetime64[ns])


def compute_hourly_efw(hourly: pd.DataFrame) -> pd.Series:
    efw = hourly["temp_c"] + 0.5 * hourly["wind_speed_ms"] - 0.2 * hourly["rh"]
    return efw.rename("EFW")


def compute_daily_cfl(hourly: pd.DataFrame, efw: pd.Series) -> pd.DataFrame:
    baseline_fire = 20.0
    cfl_hour = np.maximum(efw - baseline_fire, 0.0)
    cfl_hour = pd.Series(cfl_hour, index=hourly.index, name="CFL_hour")

    # daily sum (calendar day)
    daily_cfl = cfl_hour.resample("D").sum(min_count=1).rename("daily_CFL")

    # Note: precip reset logic could be implemented by reducing CFL based on precip_mm,
    # but the spec requires keeping the simple definition above.

    cumulative_cfl = daily_cfl.cumsum().rename("cumulative_CFL")

    out = pd.concat([daily_cfl, cumulative_cfl], axis=1)
    return out


def compute_daily_nrd(hourly: pd.DataFrame) -> pd.DataFrame:
    baseline_night_rh = 60.0
    baseline_night_wind = 5.0

    is_poor = (hourly["rh"] < baseline_night_rh) | (hourly["wind_speed_ms"] > baseline_night_wind)
    nrd_hour = is_poor.astype(int).rename("NRD_hour")

    # Night window 20:00–08:00 (00–07 belongs to previous day)
    hour = nrd_hour.index.hour
    in_night = (hour >= 20) | (hour < 8)
    nrd_hour = nrd_hour.where(in_night, 0)

    night_date = nrd_hour.index.normalize()
    # shift early-morning hours to previous day
    night_date = night_date - pd.to_timedelta((hour < 8).astype(int), unit="D")
    nrd_hour = nrd_hour.copy()
    nrd_hour.index = pd.MultiIndex.from_arrays([night_date, nrd_hour.index], names=["date", "timestamp"])

    daily_nrd = nrd_hour.groupby(level="date").sum().rename("daily_NRD")
    # Ensure daily index is datetime64[ns] normalized
    daily_nrd.index = pd.to_datetime(daily_nrd.index)

    cumulative_nrd = daily_nrd.cumsum().rename("cumulative_NRD")
    out = pd.concat([daily_nrd, cumulative_nrd], axis=1)
    return out


def _running_streak(flag: pd.Series) -> pd.Series:
    """Running streak length for consecutive True values."""
    streak = np.zeros(len(flag), dtype=int)
    run = 0
    for i, v in enumerate(flag.fillna(False).to_numpy(dtype=bool)):
        if v:
            run += 1
        else:
            run = 0
        streak[i] = run
    return pd.Series(streak, index=flag.index, name=f"consecutive_{flag.name}_streak")


def compute_compound_strain(daily: pd.DataFrame) -> pd.DataFrame:
    high_fire_day = (daily["daily_CFL"] > 40.0).rename("high_fire_day")
    poor_recovery_night = (daily["daily_NRD"] > 4).rename("poor_recovery_night")
    compound = (high_fire_day & poor_recovery_night).rename("compound")

    consecutive_high_fire_days = _running_streak(high_fire_day).rename("consecutive_high_fire_days")
    consecutive_poor_recovery_nights = _running_streak(poor_recovery_night).rename("consecutive_poor_recovery_nights")
    consecutive_compound_cycles = _running_streak(compound).rename("consecutive_compound_cycles")

    out = pd.concat(
        [high_fire_day, poor_recovery_night, compound,
         consecutive_high_fire_days, consecutive_poor_recovery_nights, consecutive_compound_cycles],
        axis=1
    )
    return out


def compute_all_daily_metrics(hourly: pd.DataFrame) -> DailyMetrics:
    efw = compute_hourly_efw(hourly)
    cfl = compute_daily_cfl(hourly, efw)
    nrd = compute_daily_nrd(hourly)

    # Align on daily dates
    daily = pd.concat([cfl, nrd], axis=1).sort_index()
    daily = daily.fillna(0.0)

    compound = compute_compound_strain(daily)
    daily = pd.concat([daily, compound], axis=1)

    # Risk multiplier
    daily["risk_multiplier"] = (
        1.0
        + (daily["daily_CFL"] / 60.0)
        + (daily["daily_NRD"] / 4.0)
        + (daily["consecutive_compound_cycles"] * 0.5)
    )

    return DailyMetrics(daily=daily), efw
