Wildfire Compound Risk Demo
Understanding Fire Weather Beyond Single Red‑Flag Days

This demo app computes daily wildfire‑risk metrics from hourly fire‑weather data and visualizes how heat, wind, humidity, and nighttime recovery interact to create escalating fire danger. It follows the same compound‑risk framework used across your hazard suite: daytime load, nighttime recovery, streaks, and nonlinear escalation.

Core idea:

Beyond single red‑flag days: recovery windows and fuel‑system margins matter more.

Wildfire danger doesn’t spike only when conditions are extreme — it builds through multi‑day drying, poor nighttime humidity recovery, and persistent wind, especially under drought or heat‑wave conditions. This demo captures those compounding dynamics.

📁 Project Structure
Code
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
1. 🔥 Conceptual Overview
Wildfire risk emerges from three interacting forces:

Fuel drying (heat, low humidity, drought)

Wind‑driven spread potential

Nighttime recovery windows (humidity rise + wind calming)

When nights fail to provide recovery — warm, dry, windy nights — fire danger accelerates even if daytime conditions remain constant.

This app quantifies:

Effective Fire Weather (EFW)

Cumulative Fire Load (CFL)

Nighttime Recovery Deficit (NRD)

Compound day–night strain

Streaks of high‑risk days

Nonlinear escalation

The result is a daily risk state that reflects system strain, not just peak conditions.

2. 📐 Key Metrics
The app computes four core metrics from hourly data.

2.1 Effective Fire Weather (EFW)
A simple proxy for combined heat, wind, and humidity stress:

Code
EFW = temp_c + 0.5 * wind_speed_ms - 0.2 * rh
Higher temperatures and winds increase EFW; higher humidity reduces it.

2.2 Cumulative Fire Load (CFL)
Daytime fire‑weather stress.

Code
baseline_fire = 20.0
CFL_hour = max(EFW - baseline_fire, 0)
daily_CFL = sum(CFL_hour)
cumulative_CFL = running sum
This captures how much of the day exceeds ignition/spread thresholds.

Note: Significant precipitation can reduce or reset CFL, but the implementation uses the simple definition above.

2.3 Nighttime Recovery Deficit (NRD)
Night window: 20:00–08:00

Code
baseline_night_rh = 60.0
baseline_night_wind = 5.0

NRD_hour = 0
if rh < baseline_night_rh or wind_speed_ms > baseline_night_wind:
    NRD_hour = 1
daily_NRD = sum(NRD_hour)
cumulative_NRD = running sum
NRD measures how many hours fail to provide recovery.

Warm, dry, windy nights → high NRD → rapid escalation.

2.4 Compound Day–Night Strain
Code
high_fire_day = (daily_CFL > 40.0)
poor_recovery_night = (daily_NRD > 4)
compound = high_fire_day and poor_recovery_night
Track streaks:

consecutive_high_fire_days

consecutive_poor_recovery_nights

consecutive_compound_cycles

Compound cycles indicate multi‑day fire‑weather overload.

3. 🚦 Daily Risk States
Risk states are assigned using daily metrics:

Code
Stable:
  CFL < 60.0 and NRD < 4 and compound_streak < 2

Straining:
  CFL >= 60.0 or NRD >= 4 or compound_streak >= 2

Failure:
  CFL >= 120.0 or NRD >= 8 or compound_streak >= 4
Stable → fuels retain moisture; nights provide recovery

Straining → fuels drying; nights failing; wind persistent

Failure → multi‑day overload; extreme spread potential

4. 📊 Visualization Suite
The app generates five panels:

Panel 1 — Timeline
temp_c

rh

wind_speed_ms

EFW overlay

Panel 2 — CFL Curve
cumulative_CFL

Panel 3 — NRD Bars
daily_NRD

Panel 4 — Risk State Band
green = Stable

amber = Straining

red = Failure

Panel 5 — Nonlinear Escalation Gauge
Code
risk_multiplier = 1 + (CFL / 60.0) + (NRD / 4.0) + (compound_streak * 0.5)
This reflects how fuel drying + wind + failed recovery create nonlinear increases in fire danger.

5. ▶️ Running the App
1. Install dependencies
Code
pip install -r requirements.txt
2. Run the main script
Code
python src/main.py
3. View outputs
/project/output/metrics_daily.csv

/project/output/risk_states.csv

/project/output/figures/*.png

6. 📥 Using Your Own CSV
Your CSV must include:

Code
timestamp
temp_c
rh
wind_speed_ms
precip_mm
Optional:

Code
fuel_dryness_index
vegetation_type_index
Place your file in /project/data/ and update the filename in main.py.

7. 📄 License
MIT License — free to use, modify, and distribute.

If you want, I can also generate:

a matching README for Inland Flooding

a matching README for Drought

or a top‑level README for your entire Compound Hazard Suite

Just say the word.
