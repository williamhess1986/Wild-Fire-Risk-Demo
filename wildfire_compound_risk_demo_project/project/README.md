# Wildfire Compound Risk Demo App — Tight Edition

**Beyond single red‑flag days: recovery windows and fuel‑system margins matter more.**

This repo is a runnable demo that computes **daily wildfire compound-risk metrics** from **hourly fire‑weather data** and visualizes how *fuel‑system strain* can build when **hot/windy afternoons** combine with **failed nighttime recovery**.

---

## What this measures

### 1) Effective Fire Weather (EFW)

Hourly “effective” fire‑weather pressure:

```python
EFW = temp_c + 0.5 * wind_speed_ms - 0.2 * rh
```

### 2) Cumulative Fire Load (CFL)

A simple **fuel-system strain proxy**: hourly pressure above a baseline, summed daily and accumulated.

```python
baseline_fire = 20.0
CFL_hour = max(EFW - baseline_fire, 0)
daily_CFL = sum(CFL_hour)
cumulative_CFL = running sum
```

> **Reset logic note:** significant `precip_mm` can be used to reset or reduce CFL, but this demo keeps the simple definition above (per spec).

### 3) Nighttime Recovery Deficit (NRD) — 20:00–08:00

Counts hours where **nighttime recovery** is poor (too dry and/or too windy).

```python
baseline_night_rh = 60.0
baseline_night_wind = 5.0

NRD_hour = 0
if rh < baseline_night_rh or wind_speed_ms > baseline_night_wind:
    NRD_hour = 1  # hour of poor recovery
daily_NRD = sum(NRD_hour)
cumulative_NRD = running sum
```

Night window handling:
- hours **20:00–23:00** count for the same calendar date
- hours **00:00–07:00** count for the **previous** date (continuation of the same night)

### 4) Compound strain (cycles)

```python
high_fire_day = (daily_CFL > 40.0)
poor_recovery_night = (daily_NRD > 4)  # more than 4 hours of poor recovery
compound = high_fire_day and poor_recovery_night

consecutive_high_fire_days = running streak of high_fire_day
consecutive_poor_recovery_nights = running streak of poor_recovery_night
consecutive_compound_cycles = running streak of compound
```

### 5) Risk states (daily)

Let `CFL = daily_CFL`, `NRD = daily_NRD`, `compound_streak = consecutive_compound_cycles`.

**Stable**
- `CFL < 60.0 and NRD < 4 and compound_streak < 2`

**Straining**
- `CFL >= 60.0 or NRD >= 4 or compound_streak >= 2`

**Failure**
- `CFL >= 120.0 or NRD >= 8 or compound_streak >= 4`

Failure overrides Straining.

### 6) Nonlinear escalation (risk multiplier)

A simple “how quickly the system can tip” multiplier:

```python
risk_multiplier = 1 + (CFL / 60.0) + (NRD / 4.0) + (compound_streak * 0.5)
```

Interpretation: **fuel drying + wind exposure + failed recovery** increases the odds that the next ignition becomes hard to control.

---

## Repo structure

```
/project
  /src
    data_loader.py
    metrics.py
    risk_states.py
    visualization.py
    main.py
  /data
    sample_california_2020.csv
    sample_australia_2019_2020.csv
    sample_future_drier_hotter.csv
  /notebooks
    demo.ipynb
  README.md
  requirements.txt
  LICENSE
```

---

## Install + run

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

python src/main.py --csv data/sample_california_2020.csv --output output
```

Outputs are written to `output/`:
- `wildfire_compound_risk_panels.png` (Panels 1–4)
- `risk_multiplier_gauge.html` (Panel 5)
- `daily_metrics_and_risk.csv`

---

## Input CSV schema (strict)

Required columns:

- `timestamp` (ISO8601)
- `temp_c` (float)
- `rh` (float)
- `wind_speed_ms` (float)
- `precip_mm` (float)

Optional:

- `fuel_dryness_index` (0–1)
- `vegetation_type_index` (0–1)

---

## Use your own CSV

1) Export/prepare an hourly CSV using the schema above.
2) Run:

```bash
python src/main.py --csv path/to/your.csv --output output
```

If your timestamps include a timezone offset, that’s fine — they’ll be parsed as UTC and stored timezone‑naive in the app.

---

## License

MIT — see `LICENSE`.
