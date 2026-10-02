"""Insights & recommendations: computed once from the full cleaned data, shown on the Conclusion page and in the PDF."""
import datetime as dt

import pandas as pd
import streamlit as st
from fpdf import FPDF

import ui
from data import load

DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

LIMITATIONS = [
    "33 users, one month (2016): findings are directional, not representative of all Strava users.",
    "No age, gender or location - segments are based on behaviour only.",
    "No activity types: running, cycling or swimming are inferred from effort, never recorded.",
    "Correlation, not causation - 'linked with' is used throughout.",
]
NEXT_STEPS = [
    "A/B-test a 4:30 PM nudge against a nudge at each user's preferred workout time.",
    "Pilot the churn-risk trigger (10%+ two-week drop) on a larger user base.",
    "Validate the 5 personas on a bigger, recent dataset that includes activity types.",
    "Track the KPI named on each recommendation for 4-6 weeks after launch.",
]


@st.cache_data(show_spinner=False)
def build_insights():
    """Six insights with their evidence, recommendation and action chain - all numbers computed from the data."""
    daily, hourly, prof = load("daily_master"), load("hourly_clean"), load("user_profile")
    nights, wear = load("sleep_nights"), load("wear_log")
    judged = prof[~prof["low_data_user"]]
    out = []

    # 1 · timing
    by_hour = hourly.groupby("hour")["steps"].mean().reindex(range(24), fill_value=0)
    peak, end = int(by_hour.idxmax()), int(by_hour.rolling(3).sum().idxmax())
    prefs = prof["preferred_workout_time"].value_counts()
    pref_txt = " · ".join(f"{k} {v}" for k, v in prefs.items() if k != "No workouts")
    out.append(dict(
        title=f"Activity Peaks at {ui.hour_label(end - 2).split()[0]}–{ui.hour_label(end)}; Mornings Are the Favourite Workout Time",
        confidence="High", evidence=f"{hourly['user_id'].nunique()} users · {len(hourly):,} hours",
        facts=[("Peak hour", f"{ui.hour_label(peak)} · {by_hour[peak]:,.0f} steps/hour"),
               ("Busiest 3 hours", f"{ui.hour_label(end - 2)} – {ui.hour_label(end)}"),
               ("Preferred workout time", pref_txt)],
        page=("views/timing.py", "Timing"), spark=list(by_hour.values),
        rec=f"Schedule activity nudges at {ui.clock(peak - 1.5)}–{ui.clock(peak - 1)}, plus personal reminders at each user's preferred workout time.",
        chain=dict(Target="All segments", Timing=f"Daily, {ui.clock(peak - 1.5)} / preferred time", Feature="Reminders",
                   KPI="Notification → activity rate")))

    # 2 · churn risk
    fall = judged[judged["activity_trend"] == "Falling"]
    drop = (fall["steps_2nd_half"] / fall["steps_1st_half"] - 1).median()
    trend = judged["activity_trend"].value_counts()
    out.append(dict(
        title=f"{len(fall)} of {len(judged)} Users Walk 10%+ Less in the Second Half of the Month",
        confidence="Medium", evidence=f"{len(judged)} users · 1st vs 2nd half of the month",
        facts=[("Falling users", f"{len(fall)} of {len(judged)}"), ("Typical drop among them", f"{drop:.0%}"),
               ("Rising / stable", f"{trend.get('Rising', 0)} / {trend.get('Stable', 0)}")],
        page=("views/engagement.py", "Engagement"), spark=None,
        rec="Flag a 10%+ two-week drop as churn risk and trigger a re-engagement nudge.",
        chain=dict(Target="Falling users", Timing="Within 2 days of the drop", Feature="Streaks & challenges",
                   KPI="30-day retention")))

    # 3 · wear gaps
    ins = wear[~wear["wear_status"].isin(["stopped", "last_day"])]
    rate = (ins["wear_status"] == "worn").mean()
    gaps = ins[ins["wear_status"] != "worn"].groupby("user_id").size().sort_values(ascending=False)
    top = round(len(prof) / 4)
    wd = ins.groupby("day_of_week")["wear_status"].apply(lambda s: (s != "worn").mean())
    worst = wd.idxmax()
    out.append(dict(
        title=f"Wear Holds Steady at {rate:.0%} — but Gaps Cluster in a Few Users and on {worst}s",
        confidence="Medium", evidence=f"{wear['user_id'].nunique()} users · {len(wear):,} user-days",
        facts=[("Wear rate", f"{rate:.1%} of days in study"),
               (f"Top {top} users", f"hold {gaps.head(top).sum() / gaps.sum():.0%} of all gaps"),
               ("Worst weekday", f"{worst} · {wd.max():.0%} not fully worn")],
        page=("views/engagement.py", "Engagement"), spark=None,
        rec=f"Send band-off / charging reminders to gap-prone users, timed for {worst} evening.",
        chain=dict(Target=f"{top} gap-prone users", Timing=f"{worst} evening, after a missed day",
                   Feature="Charging reminder", KPI="Wear rate")))

    # 4 · sleep
    rel = nights[nights["reliable_night"]]
    in_range = (rel["sleep_category"] == "7–9 h").mean()
    short = (rel["sleep_category"] == "< 6 h").mean()
    out.append(dict(
        title=f"Half of Nights Hit 7–9 Hours — but More Than 1 in 5 Fall Short of 6",
        confidence="Medium", evidence=f"{rel['user_id'].nunique()} users · {len(rel)} reliable nights",
        facts=[("Typical night", ui.fmt_hours(rel["night_hours_asleep"].median())),
               ("Nights in 7–9 h", f"{in_range:.0%} ({int(round(in_range * len(rel)))} of {len(rel)})"),
               ("Nights under 6 h", f"{short:.0%} ({int(round(short * len(rel)))} of {len(rel)})")],
        page=("views/sleep.py", "Sleep"), spark=None,
        rec="Send a wind-down reminder 30 minutes before each user's typical bedtime.",
        chain=dict(Target="Short & irregular sleepers", Timing="Evening, personalised", Feature="Sleep tracking",
                   KPI="Share of 7–9 h nights")))

    # 5 · features
    none_ = judged.loc[judged["features_used"] == 0, "typical_steps"].median()
    multi = judged.loc[judged["features_used"] >= 2, "typical_steps"].median()
    one = int((prof["features_used"] == 1).sum())
    out.append(dict(
        title="Features Lose Most Users After the First Try; 2+ Features Go With More Steps",
        confidence="Low", evidence=f"{len(prof)} users · groups of 1–17",
        facts=[("Sleep tracking", f"{int(prof['tracks_sleep'].sum())} tried → {int((prof['reliable_nights'] >= 7).sum())} habit"),
               ("Weight logging", f"{int(prof['logs_weight'].sum())} tried → {int((prof['n_weight_logs'].fillna(0) >= 10).sum())} habit"),
               ("2+ features vs none", f"{multi - none_:+,.0f} typical daily steps")],
        page=("views/engagement.py", "Engagement"), spark=None,
        rec='Run a "try a second feature" onboarding push (sleep or weight) for one-feature users.',
        chain=dict(Target=f"One-feature users ({one})", Timing="First 2 weeks", Feature="Sleep / weight logging",
                   KPI="Features per user")))

    # 6 · step-free workouts
    free = hourly[hourly["stepless_effort"]]
    ranked = prof.assign(r_steps=prof["typical_steps"].rank(ascending=False, method="min"),
                         r_mvpa=prof["typical_mvpa_min"].rank(ascending=False, method="min")).set_index("user_id")
    star = free.groupby("user_id").size().idxmax() if len(free) else None
    facts = [("Step-free hard hours", f"{len(free)} hours · {free['user_id'].nunique()} users")]
    if star:
        facts.append((f"User …{star[-5:]}", f"#{int(ranked.loc[star, 'r_mvpa'])} by exercise, "
                                            f"#{int(ranked.loc[star, 'r_steps'])} by steps"))
    out.append(dict(
        title="Step Counts Miss Non-Walking Workouts",
        confidence="Medium", evidence=f"{free['user_id'].nunique()} users · {len(free)} step-free workout hours",
        facts=facts, page=("views/activity.py", "Activity"), spark=None,
        rec="Show active minutes next to steps in goals; promote workout logging for swim / gym sessions.",
        chain=dict(Target="Somewhat active & Active", Timing="At goal setting", Feature="Workout logging",
                   KPI="Logged workouts")))
    for i, ins_ in enumerate(out, start=1):
        ins_["n"] = i
    return out


# ---------------------------------------------------------------- PDF
def _latin(text):
    """The built-in PDF fonts only know Latin-1, so swap the few fancy characters we use."""
    for a, b in {"–": "-", "—": "-", "→": "->", "…": "...", "≥": ">=", "·": "|", "’": "'", "“": '"', "”": '"',
                 "×": "x", "−": "-"}.items():
        text = text.replace(a, b)
    return text.encode("latin-1", "replace").decode("latin-1")


class _Report(FPDF):
    def header(self):
        if self.page_no() == 1:
            return
        self.set_font("Helvetica", "B", 8)
        self.set_text_color(252, 82, 0)
        self.cell(0, 6, "STRAVA FITNESS ANALYTICS  |  INSIGHTS & RECOMMENDATIONS", new_x="LMARGIN", new_y="NEXT")
        self.ln(2)

    def footer(self):
        self.set_y(-12)
        self.set_font("Helvetica", "", 7)
        self.set_text_color(140, 143, 152)
        self.cell(0, 5, _latin("Student case study (Labmentrix internship) on the public Fitbit tracker dataset · "
                               "Not affiliated with or endorsed by Strava"), align="L")
        self.cell(0, 5, f"Page {self.page_no()}", align="R")


@st.cache_data(show_spinner="Preparing the PDF …")
def make_pdf(insights):
    """A clean, printable A4 report of the insights, evidence and recommendations. Returns the PDF as bytes."""
    pdf = _Report(format="A4")
    pdf.set_auto_page_break(auto=True, margin=16)
    pdf.set_margins(16, 14, 16)
    w = pdf.w - 32
    colors = {"High": (31, 157, 116), "Medium": (224, 165, 38), "Low": (217, 83, 79)}

    # cover block
    pdf.add_page()
    pdf.set_fill_color(252, 82, 0)
    pdf.rect(0, 0, pdf.w, 6, "F")
    pdf.ln(10)
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(252, 82, 0)
    pdf.cell(0, 6, "STRAVA FITNESS ANALYTICS", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "B", 22)
    pdf.set_text_color(23, 25, 29)
    pdf.multi_cell(w, 10, "Insights & Recommendations", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(75, 85, 99)
    pdf.multi_cell(w, 5.5, _latin(f"33 tracker users · 12 Apr – 12 May 2016 · generated {dt.date.today():%d %b %Y}. "
                                  "Every number is computed from the cleaned data (63/63 pipeline checks passed)."),
                   new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    # key takeaways
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(23, 25, 29)
    pdf.cell(0, 8, "Key takeaways", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    for ins in insights:
        pdf.set_text_color(252, 82, 0)
        pdf.cell(7, 6, f"{ins['n']}.")
        pdf.set_text_color(23, 25, 29)
        pdf.multi_cell(w - 7, 6, _latin(ins["title"]), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    # one section per insight
    for ins in insights:
        if pdf.get_y() > pdf.h - 80:
            pdf.add_page()
        pdf.set_draw_color(230, 230, 233)
        pdf.line(16, pdf.get_y(), pdf.w - 16, pdf.get_y())
        pdf.ln(3)
        pdf.set_font("Helvetica", "B", 13)
        pdf.set_text_color(23, 25, 29)
        pdf.multi_cell(w, 6.5, _latin(f"{ins['n']}. {ins['title']}"), new_x="LMARGIN", new_y="NEXT")
        r, g, b = colors[ins["confidence"]]
        pdf.set_font("Helvetica", "B", 8)
        pdf.set_text_color(r, g, b)
        pdf.cell(0, 5, _latin(f"{ins['confidence'].upper()} CONFIDENCE  |  Evidence: {ins['evidence']}"),
                 new_x="LMARGIN", new_y="NEXT")
        pdf.ln(1)
        pdf.set_font("Helvetica", "", 9.5)
        for label, value in ins["facts"]:
            pdf.set_text_color(107, 114, 128)
            pdf.cell(55, 5.5, _latin(label))
            pdf.set_text_color(23, 25, 29)
            pdf.multi_cell(w - 55, 5.5, _latin(value), new_x="LMARGIN", new_y="NEXT")
        pdf.ln(1.5)
        pdf.set_font("Helvetica", "B", 8)
        pdf.set_text_color(194, 65, 12)
        pdf.cell(0, 5, "RECOMMENDATION", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(23, 25, 29)
        pdf.multi_cell(w, 5.5, _latin(ins["rec"]), new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 8.5)
        pdf.set_text_color(75, 85, 99)
        pdf.multi_cell(w, 5, _latin("   ->   ".join(f"{k}: {v}" for k, v in ins["chain"].items())),
                       new_x="LMARGIN", new_y="NEXT")
        pdf.ln(4)

    # limitations + next steps
    for head, items in [("Limitations", LIMITATIONS), ("Next steps", NEXT_STEPS)]:
        if pdf.get_y() > pdf.h - 50:
            pdf.add_page()
        pdf.set_font("Helvetica", "B", 12)
        pdf.set_text_color(23, 25, 29)
        pdf.cell(0, 8, head, new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 9.5)
        pdf.set_text_color(55, 65, 81)
        for item in items:
            pdf.multi_cell(w, 5.5, _latin(f"-  {item}"), new_x="LMARGIN", new_y="NEXT")
        pdf.ln(3)
    return bytes(pdf.output())