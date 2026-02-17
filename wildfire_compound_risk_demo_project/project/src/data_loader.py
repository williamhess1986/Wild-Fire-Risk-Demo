"""
data_loader.py

Loads and validates hourly fire-weather CSV files.

Required columns:
- timestamp (ISO8601)
- temp_c (float)
- rh (float)
- wind_speed_ms (float)
- precip_mm (float)

Optional columns:
- fuel_dryness_index (0-1)
- vegetation_type_index (0-1)
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

import pandas as pd


REQUIRED_COLS = ["timestamp", "temp_c", "rh", "wind_speed_ms", "precip_mm"]
OPTIONAL_COLS = ["fuel_dryness_index", "vegetation_type_index"]


@dataclass(frozen=True)
class LoadedData:
    hourly: pd.DataFrame


def _validate_columns(df: pd.DataFrame) -> None:
    missing = [c for c in REQUIRED_COLS if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}. Found: {list(df.columns)}")

    # Reject unknown columns only if they could indicate schema issues:
    # allow extra columns, but warn via exception message? Keep permissive for real-world usage.
    # This project uses strict required columns and will ignore extras.
    return


def load_hourly_csv(csv_path: str | Path) -> LoadedData:
    """
    Load hourly CSV and return a DataFrame indexed by UTC-naive timestamps (timezone stripped).
    """
    csv_path = Path(csv_path)
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV not found: {csv_path}")

    df = pd.read_csv(csv_path)
    _validate_columns(df)

    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="raise", utc=True).dt.tz_convert(None)
    df = df.sort_values("timestamp").reset_index(drop=True)

    # Type coercion
    for c in ["temp_c", "rh", "wind_speed_ms", "precip_mm"]:
        df[c] = pd.to_numeric(df[c], errors="raise")

    # Optional columns: if missing, fill with NaN (kept for extensibility)
    for c in OPTIONAL_COLS:
        if c not in df.columns:
            df[c] = pd.NA
        else:
            df[c] = pd.to_numeric(df[c], errors="coerce")

    # Basic sanity bounds
    if (df["rh"] < 0).any() or (df["rh"] > 100).any():
        raise ValueError("Relative humidity (rh) must be within [0, 100].")
    if (df["wind_speed_ms"] < 0).any():
        raise ValueError("wind_speed_ms must be >= 0.")
    if (df["precip_mm"] < 0).any():
        raise ValueError("precip_mm must be >= 0.")

    df = df.set_index("timestamp")
    # Ensure strictly hourly spacing isn't required, but helpful for demo; forward-fill missing hours if gaps exist.
    df = df.asfreq("H")

    return LoadedData(hourly=df)
