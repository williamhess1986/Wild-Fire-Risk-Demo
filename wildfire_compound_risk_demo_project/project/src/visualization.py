"""
visualization.py

Generates required visualizations:

Panel 1 — Timeline
  temp_c, rh, wind_speed_ms, EFW overlay

Panel 2 — CFL curve
  cumulative_CFL

Panel 3 — NRD bars
  daily_NRD

Panel 4 — Risk state band
  green / amber / red

Panel 5 — Nonlinear escalation gauge
  risk_multiplier = 1 + (CFL / 60.0) + (NRD / 4.0) + (compound_streak * 0.5)

Outputs:
- Matplotlib multi-panel PNG
- Plotly gauge HTML (last day)
"""

from __future__ import annotations

from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

import plotly.graph_objects as go


RISK_COLORS = {
    "Stable": "green",
    "Straining": "orange",
    "Failure": "red",
}


def plot_all_panels(
    hourly: pd.DataFrame,
    efw: pd.Series,
    daily: pd.DataFrame,
    output_dir: str | Path,
    title: str = "Wildfire Compound Risk Demo",
) -> Path:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    fig, axes = plt.subplots(4, 1, figsize=(14, 14), constrained_layout=True)

    # Panel 1: timeline overlay
    ax = axes[0]
    ax.plot(hourly.index, hourly["temp_c"], label="temp_c")
    ax.plot(hourly.index, hourly["rh"], label="rh")
    ax.plot(hourly.index, hourly["wind_speed_ms"], label="wind_speed_ms")
    ax.plot(efw.index, efw.values, label="EFW")
    ax.set_title(f"{title} — Panel 1: Timeline (hourly)")
    ax.set_ylabel("Value (mixed units)")
    ax.legend(ncol=4, fontsize=9)
    ax.xaxis.set_major_locator(mdates.AutoDateLocator())
    ax.xaxis.set_major_formatter(mdates.ConciseDateFormatter(ax.xaxis.get_major_locator()))

    # Panel 2: cumulative CFL
    ax = axes[1]
    ax.plot(daily.index, daily["cumulative_CFL"], label="cumulative_CFL")
    ax.set_title("Panel 2: Cumulative Fire Load (CFL)")
    ax.set_ylabel("Cumulative CFL")
    ax.legend()

    # Panel 3: daily NRD bars
    ax = axes[2]
    ax.bar(daily.index, daily["daily_NRD"])
    ax.set_title("Panel 3: Nighttime Recovery Deficit (NRD) — daily")
    ax.set_ylabel("Hours of poor recovery")

    # Panel 4: risk state band (background spans)
    ax = axes[3]
    ax.set_title("Panel 4: Risk State Band")
    ax.set_ylim(0, 1)
    ax.set_yticks([])
    ax.set_xlabel("Date")

    # Create colored spans for each day
    for date, row in daily.iterrows():
        state = row["risk_state"]
        color = RISK_COLORS.get(state, "gray")
        start = pd.to_datetime(date)
        end = start + pd.Timedelta(days=1)
        ax.axvspan(start, end, ymin=0, ymax=1, alpha=0.35, color=color)

    # Add a thin line to show day boundaries
    ax.plot(daily.index, np.zeros(len(daily)), alpha=0)  # just to get xlim
    ax.xaxis.set_major_locator(mdates.AutoDateLocator())
    ax.xaxis.set_major_formatter(mdates.ConciseDateFormatter(ax.xaxis.get_major_locator()))

    out_png = output_dir / "wildfire_compound_risk_panels.png"
    fig.savefig(out_png, dpi=160)
    plt.close(fig)
    return out_png


def plot_risk_multiplier_gauge(
    daily: pd.DataFrame,
    output_dir: str | Path,
    title: str = "Nonlinear Escalation Gauge",
) -> Path:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    last_date = daily.index.max()
    last = daily.loc[last_date]
    value = float(last["risk_multiplier"])

    fig = go.Figure(
        go.Indicator(
            mode="gauge+number+delta",
            value=value,
            title={"text": f"{title}<br><span style='font-size:0.8em'>{last_date.date()}</span>"},
            delta={"reference": 1.0},
            gauge={
                "axis": {"range": [0, max(6, value * 1.25)]},
                "steps": [
                    {"range": [0, 2], "color": "lightgreen"},
                    {"range": [2, 4], "color": "gold"},
                    {"range": [4, max(6, value * 1.25)], "color": "salmon"},
                ],
                "threshold": {"line": {"width": 4}, "value": value},
            },
        )
    )

    out_html = output_dir / "risk_multiplier_gauge.html"
    fig.write_html(out_html, include_plotlyjs="cdn")
    return out_html
