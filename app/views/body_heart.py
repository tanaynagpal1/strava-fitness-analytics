"""Body & Heart — what body and heart-rate tracking patterns are visible?"""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import filters
import ui
from data import load

# ================================================================ data
profile = load("user_profile")
people = profile[profile["user_id"].isin(filters.selected_users())]
body = load("user_body_profile")
body = body[body["user_id"].isin(people["user_id"])]
logs = filters.filter_days(load("weight_logs_clean"))
heart = filters.filter_days(load("daily_heart_rate"))
dm = filters.filter_days(load("daily_master")).dropna(subset=["minutes_hr_above_100", "mvpa_min"])
RED = "#D9534F"

r = dm["mvpa_min"].corr(dm["minutes_hr_above_100"]) if len(dm) > 2 else float("nan")
share_logged = len(body) / max(len(people), 1)
if pd.notna(r) and r >= .3:
    title = f"Supporting Evidence: {'Few' if share_logged < .5 else 'Many'} Users Log Weight, and Heart Rate Backs Up the Effort Data"
else:
    title = "Supporting Evidence: Weight and Heart-Rate Tracking Patterns"

# ================================================================ header + data note
ui.page_header("Body & Heart", title, "What body and heart-rate tracking patterns are visible?")
st.html(f'<div class="note-warn">⚠️ <b>Small samples:</b> weight {len(body)} users, heart rate '
        f'{heart["user_id"].nunique()} users — descriptive only, no health interpretation.</div>')

# ================================================================ hero: heartbeat line
METRICS = {"Average": ("hr_avg", "bpm"), "Resting": ("hr_resting_est", "bpm"), "Peak": ("hr_peak", "bpm"),
           "Minutes > 100": ("minutes_hr_above_100", "min")}


def beat(x):
    """One heartbeat drawn from x: flat, small bump, sharp spike, recovery, flat."""
    return (f"L{x + 60},60 L{x + 70},52 L{x + 80},60 L{x + 92},60 L{x + 98},70 L{x + 108},14 L{x + 120},104 "
            f"L{x + 128},60 L{x + 150},60 L{x + 165},48 L{x + 180},60 L{x + 300},60 ")


with ui.card("ecg"):
    left, right = st.columns([1.3, 2], vertical_alignment="center")
    with left:
        st.html(f'<p class="pick-eyebrow" style="color:{RED}">Supporting evidence</p>'
                '<div class="rh-title">Heart Rate Agrees With the Band\'s Effort Data</div>'
                f'<p class="rh-sub">Pulse speed follows the selected metric · n = {heart["user_id"].nunique()} users · '
                f'{len(heart)} days</p>')
        metric = st.segmented_control("Heart-rate metric", list(METRICS), default="Average", key="bh_metric",
                                      label_visibility="collapsed") or "Average"
        col, unit = METRICS[metric]
        value = heart[col].median() if len(heart) else float("nan")
        bpm = value if unit == "bpm" and pd.notna(value) else 100            # pulse speed follows the metric
        st.html(f'<p class="ecg-value">Typical day: {value:.1f} {unit}</p>' if pd.notna(value)
                else '<p class="rh-sub">No heart-rate days in the current filter.</p>')
    with right, st.container(key="anim_ecg_body"):
        path = "M0,60 " + "".join(beat(x) for x in (0, 300, 600))
        st.markdown(f'<svg class="ecg" viewBox="0 0 900 120" preserveAspectRatio="none" style="--beat:{60 / bpm * 3:.2f}s">'
                    f'<path class="ecg-base" d="{path}"/><path class="ecg-line" d="{path}" pathLength="1000"/></svg>',
                    unsafe_allow_html=True)

# ================================================================ KPI row (5 cards)
st.write("")
c = st.columns(5)
ui.kpi_card(c[0], "Weight loggers", f"{len(body)} of {len(people)}", f"{share_logged:.0%} ever logged weight",
            count=(len(body), 0, f" of {len(people)}"))
ui.kpi_card(c[1], "Median BMI", f"{body['bmi'].median():.1f}" if len(body) else "–", f"WHO categories · n = {len(body)}")
ui.kpi_card(c[2], "Weight habit", f"{int(body['weight_habit'].sum())} users", "10+ logs in the month")
ui.kpi_card(c[3], "Heart-rate users", f"{heart['user_id'].nunique()}", f"{len(heart)} valid days", accent=RED,
            count=(heart["user_id"].nunique(), 0, ""))
ui.kpi_card(c[4], "Effort ↔ heart rate", f"r = {r:.2f}" if pd.notna(r) else "–", "MVPA vs minutes > 100 bpm",
            accent=RED, help="Pearson correlation across days with both measures. Linked with, not proof of cause.")

# ================================================================ row: BMI · weight entries · logging method
WORDS = {0: "No", 1: "Only One", 2: "Only Two", 3: "Only Three"}
TYPED, SCALE = ui.ORANGE, "#2F6BC2"
st.write("")
col1, col2, col3 = st.columns([1, 1.2, .9])

with col1, ui.card("bh_bmi"):
    cats = ["Underweight", "Normal", "Overweight", "Obese"]
    bmi = (body["bmi_category"].value_counts().reindex(cats, fill_value=0)
           .rename("people").rename_axis("category").reset_index())
    bmi["share"] = bmi["people"] / max(len(body), 1)
    bmi["label"] = bmi["people"].astype(str) + " (" + bmi["share"].map("{:.0%}".format) + ")"
    bmi["legend"], bmi["show_legend"], bmi["rank"] = bmi["category"], False, range(4)
    top = bmi.loc[bmi["people"].idxmax()]
    lead = "Most" if top["share"] > .5 else "Half of" if top["share"] == .5 else "The Largest Group of"
    ui.card_title(f"{lead} Weight Loggers {'Are' if lead != 'The Largest Group of' else 'Is'} in the "
                  f"{top['category']} Range" if len(body) else "No Weight Loggers in This Selection",
                  f"Users per WHO BMI category · n = {len(body)} · median BMI {body['bmi'].median():.1f}"
                  if len(body) else "Users per WHO BMI category")
    ui.chart(ui.track_bars(bmi, "category", "people",
                           {"Underweight": "#FAD3C0", "Normal": "#F8B597", "Overweight": ui.ORANGE, "Obese": "#9A3412"},
                           room=1.5), bmi[["category", "people", "share"]], key="bh_bmi", height=300, anim="grow")

with col2, ui.card("bh_logs"):
    per = (logs.groupby("user_id").agg(entries=("date", "size"), manual=("is_manual", "mean"))
           .sort_values("entries", ascending=False).reset_index())
    per["who"] = "…" + per["user_id"].str[-5:]
    per["legend"] = per["manual"].map(lambda m: "Typed by hand" if m >= .5 else "Smart scale")
    per["label"], per["show_legend"], per["rank"] = per["entries"].astype(str), False, range(len(per))
    habit = int((per["entries"] >= 10).sum())
    ui.card_title(f"{WORDS.get(habit, str(habit))} User{'' if habit == 1 else 's'} Turned Weight Logging Into a Habit",
                  "Weight entries per user in the selected dates · colour = how they logged · habit = 10+ entries")
    st.html(f'<div class="chips"><span><i style="background:{TYPED}"></i>Typed by hand</span>'
            f'<span><i style="background:{SCALE}"></i>Smart scale</span></div>')
    if per.empty:
        st.caption("No weight entries in the current filter.")
    else:
        ui.chart(ui.track_bars(per, "who", "entries", {"Typed by hand": TYPED, "Smart scale": SCALE}, room=1.25),
                 per[["who", "entries", "legend"]], key="bh_logs", height=300, anim="grow")

with col3, ui.card("bh_method"):
    typed = int((body["manual_share"] >= .5).sum())
    scale = len(body) - typed
    ui.card_title("Most Loggers Type Their Weight by Hand" if typed > scale
                  else "Most Loggers Use a Smart Scale" if scale > typed else "Loggers Split Between Hand and Scale",
                  f"Users by logging method · n = {len(body)}")
    fig = go.Figure(go.Pie(labels=["Typed by hand", "Smart scale"], values=[typed, scale], hole=.62, sort=False,
                           marker=dict(colors=[TYPED, SCALE], line=dict(color="#FFFFFF", width=3)), textinfo="none",
                           hovertemplate="%{label}: %{value} users<extra></extra>", direction="clockwise"))
    fig.add_annotation(text=f"<b>{typed} of {len(body)}</b><br><span style='font-size:11px'>type by hand</span>",
                       showarrow=False, font=dict(size=22, color="#17191D"))
    ui.chart(fig, pd.DataFrame({"method": ["Typed by hand", "Smart scale"], "users": [typed, scale]}),
             key="bh_method", height=300, anim="fade")

# ================================================================ row: exercise vs raised heart rate · can / cannot say
col1, col2 = st.columns([1.7, 1])

with col1, ui.card("bh_scatter"):
    ui.card_title("More Exercise Minutes, More Minutes of Raised Heart Rate" if pd.notna(r) and r >= .3
                  else "Exercise Minutes and Raised Heart Rate",
                  f"Each dot = one day · {len(dm)} days · {dm['user_id'].nunique()} users · "
                  f"correlation {r:.2f} (linked with, not proof)" if pd.notna(r) else "Not enough heart-rate days")
    fig = go.Figure(go.Scatter(x=dm["mvpa_min"], y=dm["minutes_hr_above_100"], mode="markers",
                               marker=dict(size=8, color=RED, opacity=.75, line=dict(color="#FFFFFF", width=1)),
                               customdata="…" + dm["user_id"].str[-5:],
                               hovertemplate="%{customdata} · %{x:.0f} MVPA min · %{y:.0f} min above 100 bpm<extra></extra>"))
    fig.update_xaxes(title="Moderate-to-vigorous minutes (band)", rangemode="tozero")
    fig.update_yaxes(title="Minutes above 100 bpm", rangemode="tozero")
    ui.chart(fig, dm[["user_id", "date", "mvpa_min", "minutes_hr_above_100"]], key="bh_scatter", height=380,
             anim="dots")

with col2, ui.card("bh_limits"):
    ui.card_title("What This Page Can — and Cannot — Say",
                  f"Small samples: weight {len(body)} users, heart rate {heart['user_id'].nunique()} users")
    st.html(f"""<ul class="limits">
<li class="ok">The band's effort minutes line up with heart rate (r = {r:.2f}) → activity data is trustworthy.</li>
<li class="ok">Weight logging is rare ({share_logged:.0%}) and mostly manual → easier logging is an opportunity.</li>
<li class="no">No claims that BMI changes activity or sleep — {len(body)} users is too few.</li>
<li class="no">No resting-heart-rate fitness claims — our {heart['user_id'].nunique()} users don't show that pattern.</li>
</ul>""")

# ================================================================ so what?
stopped = int((per["entries"] <= 5).sum()) if len(per) else 0
st.html(f"""<div class="sowhat"><div class="icon">💡</div><div><h4>So what?</h4><ul>
<li>Promote <b>smart-scale / one-tap weight logging</b> — {stopped} of {len(per)} loggers stopped after 1–5 entries.</li>
<li>Use heart-rate agreement as a <b>trust message</b>: "your effort minutes are real effort".</li>
</ul><small>Numbers follow your filters.</small></div></div>""")