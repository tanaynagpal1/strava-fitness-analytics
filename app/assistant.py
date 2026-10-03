"""Ask AI brain: project knowledge, live data tools, a calorie calculator and the Gemini chat (free API).

The key is read from .streamlit/secrets.toml (GEMINI_API_KEY) and is never written anywhere else.
"""
import os

import pandas as pd
import streamlit as st

import filters
import report
import ui
from data import load

MODELS = ["gemini-flash-latest", "gemini-2.5-flash", "gemini-flash-lite-latest"]   # tried in this order
MAX_TURNS = 12          # only the last 12 messages are sent back, to stay inside the free limits

# ================================================================ calories: MET values (Compendium of Physical Activities, rounded)
MET = {
    "Walking, slow (3 km/h)": 2.8, "Walking, moderate (5 km/h)": 3.5, "Walking, brisk (6 km/h)": 4.3,
    "Walking, very brisk (6.5 km/h)": 5.0, "Hiking (cross-country)": 6.0, "Walking upstairs": 8.0,
    "Running, 8 km/h (7:30 min/km)": 8.3, "Running, 10 km/h (6:00 min/km)": 9.8,
    "Running, 11 km/h (5:30 min/km)": 11.0, "Running, 13 km/h (4:35 min/km)": 11.8,
    "Cycling, leisure (< 16 km/h)": 4.0, "Cycling, moderate (19–22 km/h)": 8.0, "Cycling, fast (22–26 km/h)": 10.0,
    "Stationary bike, moderate": 6.8, "Swimming, easy laps": 5.8, "Swimming, fast laps": 9.8,
    "Yoga (hatha)": 2.5, "Pilates": 3.0, "Stretching": 2.3, "Weight training, moderate": 3.5,
    "Weight training, vigorous": 6.0, "Circuit training / HIIT": 8.0, "Jump rope, moderate": 11.8,
    "Elliptical, moderate": 5.0, "Rowing machine, moderate": 7.0, "Aerobic dance / Zumba": 7.3,
    "Football (soccer), casual": 7.0, "Basketball, game": 8.0, "Badminton, social": 5.5,
    "Tennis, singles": 8.0, "Cricket": 4.8, "Gardening": 3.8, "Housework, general": 3.3,
    "Standing (light work)": 1.8, "Sitting quietly": 1.3, "Sleeping": 0.95,
}


def kcal(met, minutes, weight_kg):
    """Standard formula: kcal = MET × 3.5 × body weight (kg) ÷ 200 × minutes."""
    return met * 3.5 * weight_kg / 200 * minutes


# ================================================================ glossary: every keyword used on the dashboard
GLOSSARY = {
    "Valid day": "A day that is not the person's last (cut-short) day, has ≥ 100 steps and ≥ 10 hours with movement. 757 valid days remain from 940 raw rows.",
    "Wear rate": "Worn days ÷ days in the study (stopped days and the last day excluded). Overall 83.5%.",
    "Wear status": "Each person-day is worn, partial (< 10 movement hours), not worn (< 100 steps), stopped (after the person quit) or last day.",
    "Clean day": "Same as a valid day — a fully worn day the dashboard uses for activity numbers.",
    "Activity segment": "Grouping by typical (median) daily steps: Sedentary < 5,000 · Low active 5,000–7,499 · Somewhat active 7,500–9,999 · Active 10,000+.",
    "Engagement tier": "Grouping by how often the band was worn: Consistent ≥ 80% of study days · Irregular 25–79% · Barely using < 25% (or too little data).",
    "Persona": "Segment + tier combined into 5 audience groups: Committed Movers, On-and-Off Movers, Daily Strollers, Slipping Starters, Fading Users.",
    "Committed Movers": "Active or Somewhat active + Consistent wear (17 users). Best served by challenges and milestones.",
    "On-and-Off Movers": "Active or Somewhat active + Irregular wear (2 users). Need streak nudges on quiet days.",
    "Daily Strollers": "Low active or Sedentary + Consistent wear (3 users). Step them up with one brisk 10-minute walk.",
    "Slipping Starters": "Low active or Sedentary + Irregular wear (5 users). Need small daily goals and charging reminders.",
    "Fading Users": "Barely using the tracker, any segment, incl. the 2 low-data users (6 users). Need a win-back check-in.",
    "MVPA": "Moderate-to-Vigorous Physical Activity = very active + fairly active minutes. The WHO guideline is 150 MVPA minutes per week.",
    "Activity guideline": "Meets the guideline = typical weekly MVPA ≥ 150 minutes (WHO). Judged only for users with ≥ 7 valid days.",
    "Active minutes": "Very + fairly + lightly active minutes in a day.",
    "10K goal rate": "Share of a person's valid days with 10,000+ steps.",
    "Typical value": "Always the median of a person's days/nights (robust to odd days); a profile needs ≥ 7 days or nights.",
    "Low-data user": "Fewer than 7 valid days — kept in counts but not profiled (2 users).",
    "Activity trend": "Rising / Stable / Falling = 2nd-half vs 1st-half median steps changed by more than ±10% (split on 27 Apr). 12 of 31 are Falling.",
    "Week pattern": "Weekday-active / Weekend-active / Steady = weekend vs weekday steps differ by more than ±10%.",
    "Preferred workout time": "The time of day (Morning 5–11, Afternoon 12–4 PM, Evening 5–9 PM, Late, Night) with the most workout hours (hourly intensity ≥ 60).",
    "Step-free workout": "An hour with high effort (intensity ≥ 30) but zero steps — e.g. cycling, swimming or weights the step counter misses.",
    "Reliable night": "A night with ≥ 3 h asleep and no recording glitch. 384 of 410 nights.",
    "Sleep date": "A night belongs to the date you wake up.",
    "Night vs nap": "Main sleep + pieces within 2 h of it = the night; anything else (or a main sleep starting 9 AM–8 PM) is a nap.",
    "Sleep efficiency": "Minutes asleep ÷ minutes in bed. Median 94.3%; below 85% = restless sleeper.",
    "Sleep categories": "< 6 h, 6–7 h, 7–9 h (recommended), > 9 h. 49% of nights are 7–9 h; 22% are under 6 h.",
    "Bedtime group": "Early (before 10:30 PM), Typical, Late (after 12:30 AM) based on typical bedtime.",
    "Sleep adoption": "How often a person tracked sleep: Consistent, Regular, Tried, Never.",
    "Resting heart rate": "Estimated per day, only on days with ≥ 10 h of heart-rate readings. 13 users have valid HR days.",
    "Minutes above 100 bpm": "Daily minutes with heart rate over 100 — a proxy for effort.",
    "BMI": "Weight (kg) ÷ height (m)². WHO bands: < 18.5 under, 18.5–24.9 normal, 25–29.9 overweight, 30+ obese. Only 8 users log weight.",
    "Manual share": "Share of a person's weight entries typed in by hand (vs a smart scale).",
    "Features used": "How many of 3 extra features a person uses: sleep tracking, weight logging, workout logging. Users of 2+ walk ~1,100 more steps/day than users of none (linked, not caused).",
    "Wear gap": "Any study day that is not fully worn. 8 users hold 77% of all wear gaps; Sunday is the worst day.",
    "Churn risk": "A 10%+ drop in steps between month halves — the early-warning trigger in the recommendations.",
    "Effort": "Hourly/daily intensity from the tracker; effort and heart rate move together (r = 0.54).",
}

# ================================================================ the project, in words (static facts the model can quote)
PROJECT = """
DATASET: Public Fitbit Fitness Tracker dataset (Kaggle, Möbius / Amazon Mechanical Turk survey) used as a Strava case study.
33 users, 31 days, 12 Apr – 12 May 2016. 18 raw CSV files; 8 used (daily activity, hourly steps/calories/intensities,
sleepDay + minuteSleep, weight log, heart rate seconds). dailyCalories/Steps/Intensities are 100% identical to dailyActivity;
minute-level files add up exactly to the hourly files; the "Wide" files are the same data re-arranged; minuteMETs is low priority.
No age, gender, location or activity type (running/cycling/swimming are never recorded).

CLEANING (Phase 1 plan, Phase 2 code, 63/63 automated checks pass): American m/d/Y dates parsed explicitly; user_id kept as text;
each person's last day removed (cut short, 33 rows); days < 100 steps = not worn (77); days < 10 movement hours = partial (73);
757 valid days remain from 940. Medians not means; impossible values removed, never invented (flagged instead).
Tables: daily_clean 757, wear_log 1,023 (33×31), hourly_clean 17,987, sleep_nights 410 (24 users), sleep_sessions 459,
weight_logs_clean 67 (8 users), daily_heart_rate 280 (13 users), daily_master 757, user_profile 33.

SEGMENTS (all 33): Active 11, Somewhat active 10, Low active 5, Sedentary 5. TIERS: Consistent 20, Irregular 7, Barely using 6.
PERSONAS: Committed Movers 17, Fading Users 6, Slipping Starters 5, Daily Strollers 3, On-and-Off Movers 2.
Meets WHO guideline: 18 of 31 judged users. Workout time: Morning 13, Afternoon 9, Evening 8.
Features used 0/1/2/3: 7/18/7/1. Activity trend: Falling 12, Stable 12, Rising 7. Week pattern: Weekend-active 16, Weekday-active 11, Steady 4.
Sleep: median 7 h 13 m asleep, efficiency 94.3%, 49% of nights 7–9 h, 22% under 6 h. BMI (8 users): Normal 3, Overweight 4, Obese 1.

DASHBOARD PAGES: Overview (8 KPIs, hero, weekly trend), Activity (segments, guideline, weekend dumbbell, step-free workouts),
Timing (hour-of-day clock & heatmap, peak 6 PM), Sleep (night timeline, sleep categories, naps), Engagement (wear calendar,
retention, features), Body & Heart (BMI, ECG, effort vs HR), Personas (matrix, radar, playbook), User Explorer (one user's month),
Conclusion (6 insights + PDF download), Ask AI (this page), About (data source and limits).
The filter bar (segment, tier, weekdays/weekends, dates) changes every page except Conclusion. "This group" = the current filter.
"""

PERSONA_RULES = "\n".join(f"- {k}: {v}" for k, v in GLOSSARY.items() if k in ui.PERSONA_ORDER)


def _insights_text():
    """The six Conclusion insights as plain text (computed from the data, so the bot quotes the same numbers)."""
    lines = []
    for i, ins in enumerate(report.build_insights(), 1):
        facts = "; ".join(f"{a}: {b}" for a, b in ins["facts"])
        lines.append(f"{i}. {ins['title']} (confidence {ins['confidence']}). Evidence: {facts}. "
                     f"Recommendation: {ins['rec']}")
    return "\n".join(lines)


def filter_text():
    """Current filter in one line, e.g. 'All segments · All tiers · All days · 12 Apr – 12 May'."""
    s = st.session_state
    seg = ", ".join(s.get("f_segments") or []) or "All segments"
    tier = ", ".join(s.get("f_tiers") or []) or "All tiers"
    start, end = s.get("f_dates", filters.DEFAULTS["f_dates"])
    return f"{seg} · {tier} · {s.get('f_daytype', 'All days')} · {start:%d %b} – {end:%d %b}"

# ================================================================ tools Gemini can call (live numbers, current filter)
_on_tool = None                 # set by ask(): shows "Looking up …" in the chat while a tool runs


def _note(name):
    if _on_tool:
        _on_tool(name)


def _people():
    p = load("user_profile")
    return p[p["user_id"].isin(filters.selected_users())]


def dashboard_kpis() -> str:
    """Headline numbers for the users and days in the CURRENT dashboard filter: users, valid days, median daily steps,
    median active minutes, 10K-goal day rate, wear rate, WHO guideline count and median sleep. Use for any question
    about 'this group', overall averages or how the current selection compares."""
    _note("dashboard_kpis()")
    days, nights = filters.filter_days(load("daily_master")), filters.filter_days(load("sleep_nights"))
    wear = filters.filter_days(load("wear_log"))
    if days.empty:
        return "No days match the current filter."
    in_study = wear[~wear["wear_status"].isin(["stopped", "last_day"])]
    rel = nights[nights["reliable_night"]]
    judged = _people()["meets_activity_guideline"].dropna()
    return (f"Filter: {filter_text()}\nUsers: {days['user_id'].nunique()} · valid days: {len(days)}\n"
            f"Median daily steps: {days['steps'].median():,.0f} · median active minutes: {days['active_min'].median():.0f}"
            f" · median MVPA minutes/day: {days['mvpa_min'].median():.0f}\n"
            f"Days with 10K+ steps: {days['goal_10k_met'].mean():.0%} · median calories/day: {days['calories'].median():,.0f}\n"
            f"Wear rate: {(in_study['wear_status'] == 'worn').mean():.1%}\n"
            f"Meet WHO 150-min guideline: {int((judged == True).sum())} of {len(judged)} judged users\n"
            f"Median sleep (reliable nights): {ui.fmt_hours(rel['night_hours_asleep'].median()) if len(rel) else 'n/a'}"
            f" over {len(rel)} nights")


def segment_by_tier() -> str:
    """Count of users in each activity segment × engagement tier (and persona sizes) for the current filter.
    Use for 'which people should we target', audience size or persona questions."""
    _note("segment_by_tier()")
    p = _people()
    if p.empty:
        return "No users match the current filter."
    tab = pd.crosstab(p["activity_segment"], p["engagement_tier"]).reindex(index=ui.SEGMENT_ORDER, columns=filters.TIERS,
                                                                           fill_value=0)
    per = p["persona"].value_counts()
    return (f"Filter: {filter_text()}\nSegment × tier (users):\n{tab.fillna(0).astype(int).to_string()}\n\n"
            f"Personas: " + ", ".join(f"{k} {v}" for k, v in per.items()))


def persona_profile(persona: str) -> str:
    """Median profile of one persona (Committed Movers, On-and-Off Movers, Daily Strollers, Slipping Starters,
    Fading Users) within the current filter: size, steps, exercise minutes, 10K rate, wear share, sleep, features,
    most common workout time and trend."""
    _note(f"persona_profile('{persona}')")
    p = _people()
    match = [x for x in ui.PERSONA_ORDER if x.lower() == persona.strip().lower()]
    if not match:
        return f"Unknown persona. Choose one of: {', '.join(ui.PERSONA_ORDER)}."
    g = p[p["persona"] == match[0]]
    if g.empty:
        return f"No {match[0]} in the current filter ({filter_text()})."
    w = g["preferred_workout_time"].value_counts().drop("No workouts", errors="ignore")
    return (f"{match[0]} — {len(g)} users ({GLOSSARY[match[0]]})\n"
            f"Median steps {g['typical_steps'].median():,.0f} · MVPA {g['typical_mvpa_min'].median():.0f} min/day · "
            f"10K-goal rate {g['goal_10k_rate'].median():.0%} · wear (clean-day share) {g['clean_day_share'].median():.0%}\n"
            f"Sleep {g['typical_sleep_hours'].median():.1f} h (users tracking sleep: {int(g['tracks_sleep'].sum())}) · "
            f"features used (median) {g['features_used'].median():.0f}\n"
            f"Most common workout time: {w.idxmax() if len(w) else 'none'} · trend: "
            + ", ".join(f"{k} {v}" for k, v in g["activity_trend"].value_counts().items()))


def user_lookup(user_id: str) -> str:
    """Full profile of one user by ID (the full 10-digit ID or its last few digits): segment, tier, persona, steps,
    exercise, wear, trend, workout time, sleep, BMI and heart rate. Ignores the filter."""
    _note(f"user_lookup('{user_id}')")
    p = load("user_profile")
    digits = "".join(ch for ch in str(user_id) if ch.isdigit())
    hit = p[p["user_id"].str.endswith(digits)] if digits else p.iloc[0:0]
    if hit.empty:
        return f"No user ID ends with '{user_id}'. IDs are 10 digits, e.g. {p['user_id'].iloc[0]}."
    if len(hit) > 1:
        return "Several users match: " + ", ".join(hit["user_id"]) + ". Ask with more digits."
    u = hit.iloc[0]

    def val(col, fmt="{}"):
        return fmt.format(u[col]) if pd.notna(u[col]) else "no data"
    return (f"User {u['user_id']}: {u['persona']} · {u['activity_segment']} · {u['engagement_tier']}\n"
            f"Valid days {u['clean_days']} of 31 · stopped early: {bool(u['stopped_early'])}\n"
            f"Typical steps {val('typical_steps', '{:,.0f}')} · MVPA {val('typical_mvpa_min', '{:.0f}')} min/day · "
            f"10K-goal rate {val('goal_10k_rate', '{:.0%}')} · calories {val('typical_calories', '{:,.0f}')}\n"
            f"Trend {u['activity_trend']} (1st half {val('steps_1st_half', '{:,.0f}')} → 2nd half "
            f"{val('steps_2nd_half', '{:,.0f}')}) · week pattern {u['week_pattern']} · workout time "
            f"{u['preferred_workout_time']} · peak hour {val('peak_activity_hour', '{:.0f}')}:00\n"
            f"Sleep {val('typical_sleep_hours', '{:.1f}')} h · efficiency {val('typical_sleep_efficiency', '{:.0%}')} · "
            f"bedtime {val('typical_bedtime')} ({u['sleep_adoption_level']})\n"
            f"BMI {val('bmi', '{:.1f}')} ({val('bmi_category')}) · resting HR {val('typical_resting_hr', '{:.0f} bpm')}\n"
            f"Features used {u['features_used']} of 3")


def hourly_pattern() -> str:
    """Average steps by hour of day (0–23) for the current filter, with the peak hour and busiest 3-hour window.
    Use for 'when are people active' or notification timing questions."""
    _note("hourly_pattern()")
    h = filters.filter_days(load("hourly_clean"))
    if h.empty:
        return "No hours match the current filter."
    by = h.groupby("hour")["steps"].mean().reindex(range(24), fill_value=0)
    end = int(by.rolling(3).sum().idxmax())
    return (f"Filter: {filter_text()}\nPeak hour {ui.hour_label(int(by.idxmax()))} ({by.max():,.0f} steps/hour); "
            f"busiest 3 h: {ui.hour_label(end - 2)}–{ui.hour_label(end)}\n"
            + " · ".join(f"{ui.hour_label(i)} {v:,.0f}" for i, v in by.items()))


def weekday_pattern() -> str:
    """Median steps and wear rate for each day of the week in the current filter."""
    _note("weekday_pattern()")
    d, w = filters.filter_days(load("daily_master")), filters.filter_days(load("wear_log"))
    if d.empty:
        return "No days match the current filter."
    w = w[~w["wear_status"].isin(["stopped", "last_day"])]
    steps = d.groupby(d["date"].dt.day_name())["steps"].median()
    wear = w.groupby(w["date"].dt.day_name())["wear_status"].apply(lambda s: (s == "worn").mean())
    return "\n".join(f"{day}: median steps {steps.get(day, float('nan')):,.0f} · wear rate {wear.get(day, float('nan')):.0%}"
                     for day in report.DAYS)


def sleep_summary() -> str:
    """Sleep facts for the current filter: nights, median sleep, efficiency, category shares, bedtime and naps."""
    _note("sleep_summary()")
    n = filters.filter_days(load("sleep_nights"))
    n = n[n["reliable_night"]]
    if n.empty:
        return "No reliable sleep nights in the current filter."
    cats = pd.cut(n["night_hours_asleep"], [0, 6, 7, 9, 99], labels=["< 6 h", "6–7 h", "7–9 h", "> 9 h"], right=False)
    share = cats.value_counts(normalize=True).reindex(["< 6 h", "6–7 h", "7–9 h", "> 9 h"])
    return (f"Filter: {filter_text()}\n{len(n)} reliable nights from {n['user_id'].nunique()} users\n"
            f"Median asleep {ui.fmt_hours(n['night_hours_asleep'].median())} · efficiency {n['sleep_efficiency'].median():.1%}"
            f" · median bedtime {ui.clock(18 + n['bedtime_hrs_after_6pm'].median())}\n"
            "Categories: " + " · ".join(f"{k} {v:.0%}" for k, v in share.items()))


def calories_burned(activity: str, minutes: float, weight_kg: float) -> str:
    """Estimate calories burned for an activity using MET values (Compendium of Physical Activities).
    activity: plain words like 'running 10 km/h', 'brisk walk', 'cycling', 'yoga', 'swimming'.
    minutes: duration. weight_kg: body weight in kg (use 70 if the user did not say, and say so)."""
    _note(f"calories_burned('{activity}', {minutes:g} min, {weight_kg:g} kg)")
    words = [w for w in activity.lower().replace(",", " ").split() if len(w) > 2]
    scored = sorted(MET, key=lambda k: -sum(w in k.lower() for w in words))
    best = [k for k in scored[:3] if any(w in k.lower() for w in words)]
    if not best:
        return ("Activity not in the MET table — estimate with your own MET knowledge using "
                "kcal = MET × 3.5 × kg ÷ 200 × minutes. Table: " + ", ".join(MET))
    return "\n".join(f"{k}: MET {MET[k]} → ≈ {kcal(MET[k], minutes, weight_kg):,.0f} kcal "
                     f"({minutes:g} min, {weight_kg:g} kg)" for k in best) + \
        "\nFormula: kcal = MET × 3.5 × kg ÷ 200 × minutes. Real burn varies ±20% with fitness, terrain and intensity."


TOOLS = [dashboard_kpis, segment_by_tier, persona_profile, user_lookup, hourly_pattern, weekday_pattern,
         sleep_summary, calories_burned]


# ================================================================ system prompt
def system_prompt():
    glossary = "\n".join(f"- {k}: {v}" for k, v in GLOSSARY.items())
    return f"""You are the Ask AI assistant inside the "Strava Fitness Analytics" Streamlit dashboard, a student case study
(Labmentrix internship) on the public Fitbit dataset. You are friendly, precise and detailed, like a senior analyst who is
also a certified fitness coach. You answer THREE kinds of questions:

1) PROJECT & DATA questions (the data, cleaning, EDA, charts, personas, insights, recommendations, any user).
   - Use the facts below and CALL THE TOOLS for live numbers. The tools follow the dashboard filter currently set
     ({filter_text()}); "this group" / "these users" means that filter. Never invent a number; if something is not in
     our data (age, gender, location, activity types, 2024 data …) say "That's not in our data" and explain what is.
   - Say "linked with", not "caused by". Mention small samples (e.g. only 8 users log weight, 13 have heart rate).
2) HEALTH, FITNESS, EXERCISE, NUTRITION, SLEEP, HEART RATE, CALORIES questions — answer from solid general knowledge
   (WHO, ACSM, CDC, NHS, sleep-foundation guidance), in detail: explain the why, give practical numbers, plans or steps.
   - For "how many calories does X burn" ALWAYS call calories_burned (assume 70 kg if no weight is given and say so),
     show the formula, and add tips. You may also connect the answer to our data (e.g. typical calories/day here).
   - Safety: you give general education, not medical advice. For symptoms, injuries, pregnancy, medicines, heart
     problems or extreme diets, give general info and recommend a doctor/physio; for chest pain, fainting or similar,
     tell them to seek urgent care. Never diagnose, never give medication doses, never encourage very low-calorie
     diets, over-training or weight-loss faster than ~0.5–1 kg/week.
3) KEYWORD questions — if the message is just a word or term (e.g. "MVPA", "wear rate", "BMI", "VO2 max", "persona"),
   define it: first what it means ON THIS DASHBOARD (glossary below) if it is there, with our numbers, then the general
   meaning, then where to see it in the dashboard.
Anything clearly unrelated (coding help, politics, celebrities …): reply in one or two friendly sentences that you only
cover this project and health/fitness, and suggest a related question.

STYLE: Markdown. Start with a direct one-sentence answer in bold-free plain text, then detail with short headings or
bullets, **bold the key numbers**. Use tables for comparisons. Keep it readable (usually 120–350 words; longer only for
plans). End with ONE source line in italics, exactly one of:
*Source: dashboard data · <tool names used>* / *Source: project docs* / *Source: general fitness knowledge — not from our data*
(combine with " + " when both). Then on the very last line write follow-ups in this exact format:
<<FOLLOWUPS: question 1 | question 2 | question 3>>  (three short, useful next questions, max 8 words each).

PROJECT FACTS:{PROJECT}
PERSONA RULES:
{PERSONA_RULES}

SIX INSIGHTS (Conclusion page, full data):
{_insights_text()}

GLOSSARY (dashboard keywords):
{glossary}

MET TABLE (calories): {", ".join(f"{k} {v}" for k, v in MET.items())}
"""


# ================================================================ Gemini
def api_key():
    """Key from .streamlit/secrets.toml (local + Streamlit Cloud) or an environment variable."""
    try:
        key = st.secrets.get("GEMINI_API_KEY")
    except Exception:          # no secrets.toml at all
        key = None
    return key or os.environ.get("GEMINI_API_KEY")


@st.cache_resource(show_spinner=False)
def _client(key):
    from google import genai
    return genai.Client(api_key=key)


def _history(messages):
    from google.genai import types
    out = []
    for m in messages[-MAX_TURNS:]:
        out.append(types.Content(role="user" if m["role"] == "user" else "model",
                                 parts=[types.Part.from_text(text=m["content"])]))
    return out


def ask(messages, question, on_tool=None):
    """Stream the answer to `question` (generator of text pieces). `messages` = earlier chat turns.
    Tries the next model if one is unavailable or over its free limit."""
    global _on_tool
    from google.genai import errors, types

    _on_tool = on_tool
    config = types.GenerateContentConfig(
        system_instruction=system_prompt(), tools=TOOLS, temperature=0.4,
        automatic_function_calling=types.AutomaticFunctionCallingConfig(maximum_remote_calls=5))
    client = _client(api_key())
    last = None
    for model in MODELS:
        started = False
        try:
            chat = client.chats.create(model=model, config=config, history=_history(messages))
            for chunk in chat.send_message_stream(question):
                for cand in chunk.candidates or []:
                    for part in (cand.content.parts if cand.content else None) or []:
                        if part.text and not part.thought:
                            started = True
                            yield part.text
            if started:
                return
        except errors.APIError as e:
            last = e
            if started or e.code not in (404, 429, 500, 503):
                raise
    if last:
        raise last


def explain_error(e):
    """Friendly text for the common API problems."""
    code = getattr(e, "code", None)
    if code == 429:
        return "The free Gemini limit was reached for now. Wait about a minute and ask again (the free tier allows a few requests per minute)."
    if code in (400, 401, 403):
        return "Gemini rejected the API key. Check `GEMINI_API_KEY` in `.streamlit/secrets.toml`, then restart the app."
    if code in (500, 503):
        return "Gemini is busy right now. Please try again in a moment."
    return f"Something went wrong talking to Gemini ({type(e).__name__}). Please try again."


def split_followups(text):
    """Remove the <<FOLLOWUPS: …>> line from the answer and return (clean text, [questions])."""
    if "<<FOLLOWUPS" not in text:
        return text.strip(), []
    body, _, tail = text.partition("<<FOLLOWUPS")
    qs = [q.strip(" :>\n") for q in tail.split(">>")[0].lstrip(":").split("|")]
    return body.strip(), [q for q in qs if q][:3]