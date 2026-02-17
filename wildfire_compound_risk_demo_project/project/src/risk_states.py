"""
risk_states.py

Risk state thresholds (exact):

Let CFL = daily_CFL, NRD = daily_NRD, compound_streak = consecutive_compound_cycles.

Stable:
  CFL < 60.0 and NRD < 4 and compound_streak < 2

Straining:
  CFL >= 60.0 or NRD >= 4 or compound_streak >= 2

Failure:
  CFL >= 120.0 or NRD >= 8 or compound_streak >= 4

Failure overrides Straining; otherwise Stable if Stable condition else Straining.
"""

from __future__ import annotations
import pandas as pd
import numpy as np


def assign_risk_states(daily: pd.DataFrame) -> pd.Series:
    cfl = daily["daily_CFL"]
    nrd = daily["daily_NRD"]
    cs = daily["consecutive_compound_cycles"]

    stable = (cfl < 60.0) & (nrd < 4) & (cs < 2)
    failure = (cfl >= 120.0) | (nrd >= 8) | (cs >= 4)

    risk = np.where(failure, "Failure", np.where(stable, "Stable", "Straining"))
    return pd.Series(risk, index=daily.index, name="risk_state")
