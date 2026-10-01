# Strava Fitness Data Analytics

Turning 31 days of wearable data from 33 people (Fitbit public dataset, 12 Apr – 12 May 2016) into insights on **activity, sleep, body metrics and engagement** — to help Strava make data-driven marketing and product decisions.

## Folder layout

```
Strava/
├── Data Source/            raw CSVs (18 files, 8 used — see Cleaning Notes/00_Summary.md)
├── Cleaning Notes/         Phase 1: every problem → evidence → solution → check, plus decision logs
├── src/                    Phase 2 cleaning + feature code (one module per data source)
│   ├── config.py           paths and every agreed threshold in one place
│   ├── load.py             reads the raw files with explicit date formats
│   ├── clean_daily.py      dailyActivity  (P1–P11) + wear_log
│   ├── clean_hourly.py     hourly files   (H1–H9)
│   ├── clean_sleep.py      sleepDay + minuteSleep (S1–S9, M1–M8)
│   ├── clean_weight.py     weightLogInfo  (W1–W7)
│   ├── clean_heart.py      heartrate_seconds (R1–R7)
│   ├── features.py         daily_master + user_profile (F1–F7, G, H1–H6)
│   └── checks.py           every "How we'll check" test from the Cleaning Notes
├── run_pipeline.py         runs everything in the agreed build order
├── data/processed/         the 10 clean tables the notebook and dashboard read
├── reports/                cleaning_check_report.md (pass/fail of every check)
├── notebooks/              EDA (Q1–Q30)
└── app/                    Streamlit dashboard (11 pages)
```

## How to run

```bash
pip install -r requirements.txt
python run_pipeline.py          # ~15 s → data/processed/*.csv + reports/cleaning_check_report.md
```

The run should end with **61/61 checks passed**. If a number changes, the report shows which rule (P / H / S / M / W / R / F) it belongs to.

## Output tables

| File | One row per | Rows |
|---|---|---|
| `daily_clean.csv` | person × valid day | 757 |
| `wear_log.csv` | person × study day (incl. not-worn / partial / stopped) | 1,023 |
| `hourly_clean.csv` | person × hour on valid days | 17,987 |
| `sleep_nights.csv` | person × wake-up date | 410 |
| `sleep_sessions.csv` | sleep session (main / night piece / nap) | 459 |
| `weight_logs_clean.csv` | weight entry | 67 |
| `user_body_profile.csv` | person who logs weight | 8 |
| `daily_heart_rate.csv` | person × valid day with ≥ 10 h of readings | 280 |
| `daily_master.csv` | person × valid day, with sleep + heart rate joined | 757 |
| `user_profile.csv` | person — segments, tiers, typical values | 33 |

## Key rules (details in Cleaning Notes)

- A **valid day** is not the person's last day and has ≥ 100 steps and ≥ 10 hours with movement.
- Use **medians** for typical values; build per-person profiles only with ≥ 7 days / nights.
- Remove only **impossible** values; never invent data (flag instead).
- The **sleep date** is the wake-up date. Night = main sleep + pieces within 2 h; everything else is a nap.
