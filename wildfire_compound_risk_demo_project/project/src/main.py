"""
main.py

Loads CSV, computes metrics, computes risk states, generates all plots, saves to /project/output,
and prints a summary table (date, CFL, NRD, compound flag, risk_state, risk_multiplier).
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from data_loader import load_hourly_csv
from metrics import compute_all_daily_metrics
from risk_states import assign_risk_states
from visualization import plot_all_panels, plot_risk_multiplier_gauge


def run(csv_path: str, output_dir: str) -> None:
    loaded = load_hourly_csv(csv_path)
    hourly = loaded.hourly

    (daily_metrics, efw) = compute_all_daily_metrics(hourly)
    daily = daily_metrics.daily.copy()

    # Risk states
    daily["risk_state"] = assign_risk_states(daily)

    # Ensure required columns exist
    required = ["daily_CFL", "daily_NRD", "compound", "risk_state", "risk_multiplier"]
    missing = [c for c in required if c not in daily.columns]
    if missing:
        raise RuntimeError(f"Missing computed columns: {missing}")

    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Plots
    panels_png = plot_all_panels(hourly=hourly, efw=efw, daily=daily, output_dir=out_dir)
    gauge_html = plot_risk_multiplier_gauge(daily=daily, output_dir=out_dir)

    # Save daily table
    daily_out = out_dir / "daily_metrics_and_risk.csv"
    daily.reset_index(names="date").to_csv(daily_out, index=False)

    # Print summary
    summary = daily.reset_index(names="date")[["date", "daily_CFL", "daily_NRD", "compound", "risk_state", "risk_multiplier"]]
    summary["date"] = pd.to_datetime(summary["date"]).dt.date
    print("\nSummary (daily):")
    print(summary.to_string(index=False, justify="left", float_format=lambda x: f"{x:0.2f}"))

    print(f"\nSaved outputs:\n- {panels_png}\n- {gauge_html}\n- {daily_out}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Wildfire Compound Risk Demo App")
    parser.add_argument(
        "--csv",
        type=str,
        default=str(Path(__file__).resolve().parents[1] / "data" / "sample_california_2020.csv"),
        help="Path to input hourly CSV",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=str(Path(__file__).resolve().parents[1] / "output"),
        help="Output directory",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    run(csv_path=args.csv, output_dir=args.output)
