# Strava Fitness Data Analytics

Turning 31 days of wearable data from 33 people (Fitbit public dataset, 12 Apr – 12 May 2016) into insights on **activity, sleep, body metrics and engagement** — to help Strava make data-driven marketing and product decisions.

The project has three parts:

1. **Phase 1 — Cleaning plan** (`Cleaning Notes/`): every data problem → evidence → solution → how we check it (51 problems).
2. **Phase 2 — Pipeline + EDA** (`src/`, `run_pipeline.py`, `notebooks/`): turns 18 raw files into 10 clean tables, re-tested by 63 automated checks.
3. **Dashboard** (`app/`): an 11-page Streamlit dashboard with live filters, animated charts, a PDF report and an AI assistant.

## The dashboard

| Page | Business question it answers |
|---|---|
| **Overview** | What does the overall user base look like? |
| **Activity** | How do activity levels differ across users? |
| **Timing** | When are users most active? |
| **Sleep** | How does sleep tracking and sleep behaviour vary? |
| **Engagement** | Which users consistently engage with tracking? |
| **Body & Heart** | What body and heart-rate tracking patterns are visible? |
| **Personas** | How can activity and engagement combine into actionable audience groups? |
| **User Explorer** | What does an individual user's behaviour look like? |
| **Conclusion** | What should the business take away? — 6 insights with evidence, recommendations and a **PDF download** |
| **Ask AI** | A Gemini chatbot that answers questions about the data, health & fitness, calories and any dashboard keyword |
| **About** | Where does the data come from, how was it prepared — and how far can we trust it? |

- **Filters** (activity segment, engagement tier, weekdays/weekends, dates) update every page except Conclusion and About.
- Every chart shows its **n**, has a **Show data** button with the table behind it, and uses honest titles ("linked with", never "causes").
- Charts animate when scrolled into view and replay every 15 s; the **Animations** switch turns all motion off.

## Folder layout

```
Strava/
├── Data Source/              raw CSVs (18 files, 8 used) — not in GitHub, see "Get the raw data"
├── Cleaning Notes/           Phase 1: every problem → evidence → solution → check, plus decision logs
├── src/                      Phase 2 cleaning + feature code (one module per data source)
│   ├── config.py             paths and every agreed threshold in one place
│   ├── load.py               reads the raw files with explicit date formats
│   ├── clean_daily.py        dailyActivity  (P1–P11) + wear_log
│   ├── clean_hourly.py       hourly files   (H1–H9)
│   ├── clean_sleep.py        sleepDay + minuteSleep (S1–S9, M1–M8)
│   ├── clean_weight.py       weightLogInfo  (W1–W7)
│   ├── clean_heart.py        heartrate_seconds (R1–R7)
│   ├── features.py           daily_master + user_profile (F1–F8, G, H1–H6)
│   └── checks.py             every "How we'll check" test from the Cleaning Notes
├── run_pipeline.py           runs everything in the agreed build order
├── data/processed/           the 10 clean tables the notebook and dashboard read
├── reports/                  cleaning_check_report.md (pass/fail of every check)
├── notebooks/                EDA (Q1–Q30)
├── app/                      Streamlit dashboard
│   ├── app.py                entry point: page config, logo, navigation, filters, footer
│   ├── views/                the 11 pages (one file each)
│   ├── filters.py            the shared filter bar
│   ├── ui.py                 colours, cards, KPI tiles, chart helpers, animations
│   ├── data.py               loads the clean tables once (cached)
│   ├── report.py             the 6 insights + the PDF report (Conclusion page)
│   ├── assistant.py          Ask AI: project knowledge, live data look-ups, Gemini chat
│   └── assets/               style.css + logo images
├── .streamlit/config.toml    dashboard theme (secrets.toml is local only — never in GitHub)
├── make_logo.py              one-off: builds the header logo from the two official logo images
├── requirements.txt          libraries for the dashboard (exact tested versions)
└── requirements-notebook.txt extra libraries for the EDA notebook
```

## Get the raw data

The raw files are not stored in this repository. Download the public **FitBit Fitness Tracker Data** (Möbius, CC0) from Kaggle: https://www.kaggle.com/datasets/arashnic/fitbit — and put the 18 CSV files in a folder called `Data Source/` inside the project. The processed tables in `data/processed/` are already included, so **the dashboard runs without this step**.

## How to run

Python 3.13 is recommended (tested with 3.13).

**Dashboard only**

```bash
pip install -r requirements.txt
streamlit run app/app.py        # opens the dashboard at http://localhost:8501
```

**Re-build the clean tables** (needs `Data Source/`)

```bash
python run_pipeline.py          # ~20 s → data/processed/*.csv + reports/cleaning_check_report.md
```

The run should end with **63/63 checks passed**. If a number changes, the report shows which rule (P / H / S / M / W / R / F) it belongs to.

**EDA notebook**

```bash
pip install -r requirements-notebook.txt
jupyter notebook notebooks/01_eda.ipynb
```

## Ask AI setup (free Gemini key)

The Ask AI page uses Google's free Gemini API. Without a key the page still opens — the calorie calculator and keyword glossary work, the chat is switched off.

1. Get a free key at https://aistudio.google.com/apikey
2. Create `.streamlit/secrets.toml` with one line:
```toml
   GEMINI_API_KEY = "your-key-here"
```
3. Restart the app.

`secrets.toml` is listed in `.gitignore` and must never be committed. On Streamlit Community Cloud, paste the same line into the app's **Settings → Secrets** instead.

The assistant answers project questions from live data look-ups (they follow the current filters), health & fitness questions from general knowledge (education, not medical advice) and calorie questions with the MET formula. On the free tier, avoid typing personal information into the chat.

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
| `user_profile.csv` | person — segments, tiers, personas, typical values | 33 |

## Key rules (details in Cleaning Notes)

- A **valid day** is not the person's last day and has ≥ 100 steps and ≥ 10 hours with movement.
- Use **medians** for typical values; build per-person profiles only with ≥ 7 days / nights.
- Remove only **impossible** values; never invent data (flag instead).
- The **sleep date** is the wake-up date. Night = main sleep + pieces within 2 h; everything else is a nap.
- **Activity segments** by typical daily steps: Sedentary < 5,000 · Low active 5,000–7,499 · Somewhat active 7,500–9,999 · Active 10,000+.
- **Engagement tiers** by share of days worn: Consistent ≥ 80% · Irregular 25–79% · Barely using < 25%.
- **5 personas** = segment × tier: Committed Movers, On-and-Off Movers, Daily Strollers, Slipping Starters, Fading Users.

## Limitations

- 33 users, one month (2016): findings are directional, not representative of all Strava users.
- No age, gender, location or activity types; small samples for sleep (24 users), heart rate (13) and weight (8).
- Correlation, not causation — "linked with" is used throughout.

## Built with

Python · pandas · NumPy · Plotly · Streamlit · fpdf2 (PDF report) · Google Gemini (Ask AI) · SciPy + Jupyter (EDA)

## Credits

- Data: *FitBit Fitness Tracker Data* — Furberg, Brinton, Keating & Ortiz (2016), Zenodo; shared on Kaggle by Möbius (CC0).
- Student case study by **Tanay Nagpal** for the Labmentrix data analytics internship.
- The Strava name and logo belong to Strava, Inc. and are used with permission for this case study. This project is **not affiliated with or endorsed by Strava**.