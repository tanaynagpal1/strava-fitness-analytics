"""About the Data — where does the data come from, how was it prepared, and how far can we trust it?"""
import re

import pandas as pd
import streamlit as st

import report
import ui
from data import DATA, load

REPORT = DATA.parents[1] / "reports" / "cleaning_check_report.md"     # written by run_pipeline.py

TABLES = [   # file, one row = …, what is in it
    ("daily_master", "person-day", "Steps, active minutes, distance, calories + last night's sleep & heart rate"),
    ("daily_clean", "person-day", "The valid days only, before sleep and heart rate are joined"),
    ("hourly_clean", "person-hour", "Steps, calories and effort for every hour of a valid day"),
    ("wear_log", "person × calendar day", "Worn / partial / not worn / stopped / last day — for engagement"),
    ("sleep_nights", "person-night", "Night sleep, efficiency, bedtime, naps and reliability flags"),
    ("sleep_sessions", "sleep session", "Each main sleep, night piece or nap"),
    ("daily_heart_rate", "person-day", "Average, resting and peak heart rate (days with ≥ 10 h of readings)"),
    ("weight_logs_clean", "weight entry", "Weight, BMI, manual entry vs smart scale"),
    ("user_body_profile", "person", "Median BMI and weight-logging habit"),
    ("user_profile", "person", "Segment, tier, persona, trend, sleep & body profile"),
]
SKIPPED = [
    ("dailyCalories · dailySteps · dailyIntensities", "100% identical to dailyActivity (checked on all 940 rows)"),
    ("minuteSteps · minuteCalories · minuteIntensities (Narrow + Wide)",
     "Add up exactly to the hourly files; Wide = the same data re-arranged"),
    ("minuteMETsNarrow", "Low priority — effort is already covered by intensity"),
]
CHIPS = ["Explicit American date formats", "Non-wear days removed & logged", "Naps split from night sleep",
         "Duplicates removed", "Medians for typical values", "7-day rule for every profile", "n shown on every chart"]

# ================================================================ data (always the full dataset)
counts = {name: len(load(name)) for name, _, _ in TABLES}
status = load("wear_log")["wear_status"].value_counts()
raw = int(status.sum() - status.get("stopped", 0))                          # rows in the raw daily file
nights, hr, body = load("sleep_nights"), load("daily_heart_rate"), load("user_body_profile")
users = load("user_profile")["user_id"].nunique()


def read_checks():
    """Pass/fail table from reports/cleaning_check_report.md -> (passed, total, DataFrame), or None if missing."""
    if not REPORT.exists():
        return None
    text = REPORT.read_text(encoding="utf-8")
    rows = [[c.strip() for c in line.strip().strip("|").split("|")]
            for line in text.split("## Checks", 1)[-1].splitlines() if line.startswith("|")]
    df = pd.DataFrame([r for r in rows[2:] if len(r) == 5], columns=["Ref", "Check", "Expected", "Actual", "Result"])
    m = re.search(r"\*\*(\d+) of (\d+) checks passed", text)
    return (int(m[1]), int(m[2]), df) if m else (int((df["Result"] == "✅").sum()), len(df), df)


checks = read_checks()

# ================================================================ header + pipeline
ui.page_header("About the Data", f"From 18 Raw Files to {len(TABLES)} Clean Tables",
               "Where does the data come from, how was it prepared — and how far can we trust it?")
st.html('<div class="note-warn">ℹ️ <b>This page describes the full dataset</b> — the filters above don\'t change it.</div>')

passed = f"{checks[0]}/{checks[1]}" if checks else "All"
steps = [("18", "Raw CSV files", f"Fitbit tracker export · {users} users · 31 days", ""),
         ("8", "Files used · 6 sources", "daily, 3 hourly, sleepDay, minuteSleep, weight, heart rate", ""),
         ("51", "Problems fixed", "dates, non-wear days, naps, duplicates, glitches — each with a check", "warm"),
         (str(len(TABLES)), "Clean tables", f"{passed} automated checks pass · ready for EDA and this dashboard", "cool")]
flow = '<i class="ab-arrow">→</i>'.join(
    f'<div class="ab-step {cls}" style="animation-delay:{i * 140}ms"><b>{n}</b><span>{t}</span><small>{s}</small></div>'
    for i, (n, t, s, cls) in enumerate(steps))
st.html(f'<div class="ab-flow">{flow}</div><div class="ab-chips">'
        + "".join(f"<span>✓ {c}</span>" for c in CHIPS) + "</div>")

# ================================================================ clean tables
with ui.card("ab_tables"):
    ui.card_title(f"The {len(TABLES)} Clean Tables", "Every page of this dashboard reads only these files (data/processed)")
    tiles = "".join(f'<div class="ab-tile" style="animation-delay:{i * 60}ms"><code>{name}</code>'
                    f'<p><b>{counts[name]:,}</b> rows · 1 row = {grain}</p><small>{what}</small></div>'
                    for i, (name, grain, what) in enumerate(TABLES))
    st.html(f'<div class="ab-grid">{tiles}</div>')

# ================================================================ row: raw day -> valid day · coverage by source
c1, c2 = st.columns(2)
with c1, ui.card("ab_funnel"):
    last, off, part = status.get("last_day", 0), status.get("not_worn", 0), status.get("partial", 0)
    fun = pd.DataFrame({"stage": ["Raw daily rows", "After removing last days", "After removing not-worn days",
                                  "After removing partial days"],
                        "rows": [raw, raw - last, raw - last - off, raw - last - off - part],
                        "removed": [0, last, off, part]})
    ui.card_title(f"{fun['rows'].iloc[-1] / raw:.0%} of Raw Days Survive Cleaning — {fun['rows'].iloc[-1]:,} Valid Days",
                  f"Daily rows left after each cleaning rule · n = {raw:,} raw person-days")
    fun["label"] = [f"{r:,}" + (f"  (−{d})" if d else "") for r, d in zip(fun["rows"], fun["removed"])]
    fun["legend"] = ["Before cleaning", "Being cleaned", "Being cleaned", "Valid days"]
    fun["show_legend"], fun["rank"] = ~fun["legend"].duplicated(), [1, 2, 2, 3]
    fig = ui.track_bars(fun, "stage", "rows", {"Before cleaning": "#9CA3AF", "Being cleaned": "#F6AE84",
                                               "Valid days": ui.ORANGE}, room=1.3)
    ui.chart(fig, fun[["stage", "rows", "removed"]], key="ab_funnel", height=300, anim="grow",
             note="Removed days are not lost — wear_log keeps them as not worn / partial for the Engagement page.")

with c2, ui.card("ab_cover"):
    src = pd.DataFrame({"source": ["Daily activity", "Hourly activity", "Sleep", "Heart rate", "Weight"],
                        "users": [load("daily_master")["user_id"].nunique(), load("hourly_clean")["user_id"].nunique(),
                                  nights["user_id"].nunique(), hr["user_id"].nunique(),
                                  load("weight_logs_clean")["user_id"].nunique()]})
    ui.card_title(f"Activity Covers All {users} Users — Weight Only {src['users'].iloc[-1]}",
                  f"Users with at least one clean record per source · n = {users} users")
    src["label"] = [f"{u} of {users} ({u / users:.0%})" for u in src["users"]]
    src["legend"] = ["All users" if u == users else "Most users" if u >= users / 2 else "Few users" for u in src["users"]]
    src["show_legend"] = ~src["legend"].duplicated()
    src["rank"] = src["legend"].map({"All users": 1, "Most users": 2, "Few users": 3})
    fig = ui.track_bars(src, "source", "users", {"All users": ui.TEAL, "Most users": "#E0A526", "Few users": "#E76F51"},
                        room=1.45)
    ui.chart(fig, src[["source", "users"]], key="ab_cover", height=300, anim="grow",
             note="The fewer users behind a source, the more carefully its findings should be read.")

# ================================================================ row: data checks · trust per source
c1, c2 = st.columns([1.25, 1])
with c1, ui.card("ab_checks"):
    if checks:
        ok, total, df = checks
        ui.card_title(f"{ok} of {total} Automated Data Checks Pass",
                      "Every rule from the Cleaning Notes is re-tested each time the pipeline runs "
                      "(reports/cleaning_check_report.md)")
        FAMILY = {"All": "", "Daily (P)": "P", "Hourly (H)": "H", "Sleep (S/M)": "SM", "Weight (W)": "W",
                  "Heart (R)": "R", "Features (F/G)": "FG"}
        fam = st.pills("Rule family", list(FAMILY), default="All", key="ab_fam", label_visibility="collapsed")
        show = df if not FAMILY.get(fam) else df[df["Ref"].str[0].isin(list(FAMILY[fam]))]
        st.dataframe(show, hide_index=True, height=360,
                     column_config={"Ref": st.column_config.TextColumn(width="small"),
                                    "Result": st.column_config.TextColumn(width="small")})
    else:
        ui.card_title("Automated Data Checks")
        st.info("Run `python run_pipeline.py` to create `reports/cleaning_check_report.md` — its pass/fail table "
                "appears here.")

with c2, ui.card("ab_trust"):
    manual = load("weight_logs_clean")["is_manual"].mean()
    trust = [("Steps & activity", "High", "#1F9D74",
              f"{users} users · {counts['daily_master']:,} valid days · {counts['hourly_clean']:,} hours"),
             ("Sleep", "Medium", "#B7791F",
              f"{nights['user_id'].nunique()} users · {int(nights['reliable_night'].sum())} of {len(nights)} nights "
              "reliable · naps split out from night sleep"),
             ("Heart rate", "Medium–Low", "#B7791F",
              f"{hr['user_id'].nunique()} users · {len(hr)} days with ≥ 10 h of readings · resting HR is an estimate, "
              "so heart rate is used as supporting evidence, never on its own"),
             ("Weight & BMI", "Low", "#D9534F",
              f"{body['user_id'].nunique()} users · {counts['weight_logs_clean']} entries · {manual:.0%} typed by hand "
              "· shown for completeness only")]
    ui.card_title("How Much to Trust Each Source", "Confidence depends on how many people and days stand behind it")
    st.html('<div class="ab-trust">' + "".join(
        f'<div style="animation-delay:{i * 100}ms"><span class="ab-lvl" style="color:{c}; border-color:{c}">● {lvl}</span>'
        f'<b>{name}</b><small>{note}</small></div>' for i, (name, lvl, c, note) in enumerate(trust)) + "</div>")

# ================================================================ row: skipped files · limitations · source & credits
c1, c2, c3 = st.columns([1.2, 1, 1])
with c1, ui.card("ab_skip"):
    ui.card_title("10 Files Skipped — and Why", "Nothing was dropped without a check")
    st.html('<div class="ab-rows">' + "".join(f"<div><b>{f}</b><span>{why}</span></div>" for f, why in SKIPPED) + "</div>")

with c2, ui.card("ab_limits"):
    ui.card_title("Limitations", "Read every chart with these in mind")
    extra = [f"Coverage: sleep {nights['user_id'].nunique()} users · heart rate {hr['user_id'].nunique()} · "
             f"weight {body['user_id'].nunique()}.",
             "Student case study — not affiliated with or endorsed by Strava."]
    st.html('<ul class="ins-list">' + "".join(f"<li>{x}</li>" for x in report.LIMITATIONS + extra) + "</ul>")

with c3, ui.card("ab_credits"):
    ui.card_title("Source & Credits")
    st.html('<div class="ab-rows">'
            "<div><b>Dataset</b><span>FitBit Fitness Tracker Data — consenting Fitbit users from an Amazon "
            "Mechanical Turk survey (Furberg et al., 2016, Zenodo), shared on Kaggle by Möbius</span></div>"
            "<div><b>Period</b><span>12 Apr – 12 May 2016 · 18 CSV files</span></div>"
            "<div><b>Built with</b><span>Python · pandas · Plotly · Streamlit · Google Gemini (Ask AI)</span></div>"
            "<div><b>Project</b><span>Labmentrix data analytics internship — Strava case study by Tanay Nagpal</span></div>"
            "</div>")