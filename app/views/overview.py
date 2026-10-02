"""Overview — a month of movement, sleep and tracking at a glance."""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import filters
import ui
from data import load

# ================================================================ data: filtered slice + everyone
profile = load("user_profile")
people = profile[profile["user_id"].isin(filters.selected_users())]
days = filters.filter_days(load("daily_master"))
nights = filters.filter_days(load("sleep_nights"))
wear = filters.filter_days(load("wear_log"))
filtered = len(days) < len(load("daily_master"))


def kpis(daily, sleep, wear_log, prof):
    """The 8 headline numbers for one slice of the data."""
    rel = sleep[sleep["reliable_night"]]
    in_study = wear_log[~wear_log["wear_status"].isin(["stopped", "last_day"])]
    judged = prof["meets_activity_guideline"].dropna()
    raw = wear_log[wear_log["wear_status"] != "stopped"]
    return {
        "users": daily["user_id"].nunique(), "profiled": int((~prof["low_data_user"]).sum()),
        "days": len(daily), "raw_days": len(raw),
        "steps": daily["steps"].median(), "active": daily["active_min"].median(),
        "goal": daily["goal_10k_met"].mean(),
        "meets": int((judged == True).sum()), "judged": len(judged),
        "wear": (in_study["wear_status"] == "worn").mean(),
        "sleep": rel["night_hours_asleep"].median(), "nights": len(rel),
    }


f = kpis(days, nights, wear, people)
a = kpis(load("daily_master"), load("sleep_nights"), load("wear_log"), profile)


def vs_all(value, everyone, text):
    """Small comparison line under a KPI — only when the filters narrow the data."""
    if not filtered or pd.isna(value):
        return None
    return text.format(value - everyone) + " vs everyone"


# ================================================================ header
ui.page_header("Overview", "A Month of Movement, Sleep and Tracking at a Glance",
               "What does the overall user base look like?")
if days.empty:
    st.info("No days match these filters. Try widening them, or press **Reset**.")
    st.stop()

weekly = days[days["week_no"] <= 4].groupby("week_no")["steps"].median()

# ================================================================ hero banner
with st.container(key="hero"):
    left, right = st.columns([1.05, 1], vertical_alignment="center")
    with left:
        ui.hero_text(f["steps"], f["users"], f["days"])
    with right:
        pace = st.session_state.get("hero_pace") or "Loop"
        if pace and pace != "Loop" and int(pace[-1]) in weekly.index:
            pace_steps, pace_text = weekly[int(pace[-1])], f"{pace} · typical {weekly[int(pace[-1])]:,.0f} steps"
        else:
            pace_steps, pace_text = f["steps"], f"Looping · speed follows typical steps ({f['steps']:,.0f})"
        ui.hero_route(pace_steps)
        with st.container(horizontal=True, horizontal_alignment="right"):
            st.segmented_control("Runner pace", ["Loop", "Week 1", "Week 2", "Week 3", "Week 4"],
                                 default="Loop", key="hero_pace", label_visibility="collapsed")
        st.html(f'<p class="hero-pace">{pace_text}</p>'
                '<p class="hero-note">Abstract route — not a real GPS route · runner speed = typical daily steps</p>')

# ================================================================ KPI row (8 cards)
st.write("")
c = st.columns(4) + st.columns(4) # two rows of 4 cards
ui.kpi_card(c[0], "Users", f"{f['users']}", f"{f['profiled']} with 7+ clean days",
            help="People with at least one clean day in the filtered data.", count=(f["users"], 0, ""))
ui.kpi_card(c[1], "Clean days", f"{f['days']:,}",
            f"of {f['raw_days']:,} raw · {f['days'] / max(f['raw_days'], 1):.0%} kept",
            help="Days left after cleaning (not the last day, 100+ steps, 10+ hours with movement).",
            count=(f["days"], 0, ""))
ui.kpi_card(c[2], "Typical daily steps", f"{f['steps']:,.0f}", "median · weeks 1–4",
            vs_all(f["steps"], a["steps"], "{:+,.0f}"), "Median steps across filtered days; the line shows weeks 1–4.",
            spark=list(weekly.values), count=(round(f["steps"]), 0, ""))
ui.kpi_card(c[3], "Typical active minutes", f"{f['active']:.0f}", "median per day",
            vs_all(f["active"], a["active"], "{:+.0f} min"), "Light + moderate + vigorous minutes (median).",
            count=(round(f["active"]), 0, ""))
ui.kpi_card(c[4], "10K goal days", f"{f['goal']:.0%}", "of clean days",
            vs_all(f["goal"] * 100, a["goal"] * 100, "{:+.0f} pts"), "Share of filtered days with 10,000+ steps.",
            count=(round(f["goal"] * 100), 0, "%"))
ui.kpi_card(c[5], "Meet exercise guideline", f"{f['meets']}/{f['judged']}", "≥150 active min / week",
            help="WHO guideline, per person over the whole month — follows the segment and tier filters only.")
ui.kpi_card(c[6], "Wear rate", "–" if pd.isna(f["wear"]) else f"{f['wear']:.1%}", "worn days ÷ days in study",
            vs_all(f["wear"] * 100, a["wear"] * 100, "{:+.1f} pts"),
            "Each person's export-cut last day and days after they stopped are excluded.", accent=ui.TEAL,
            count=(round(f["wear"] * 100, 1), 1, "%"))
ui.kpi_card(c[7], "Typical night", ui.fmt_hours(f["sleep"]).replace(" m", "m").replace(" h ", "h "),
            f"{f['nights']} reliable nights", vs_all(f["sleep"] * 60, a["sleep"] * 60, "{:+.0f} min"),
            "Median hours asleep on reliable nights (dated by wake-up day).", accent=ui.PURPLE)


# ================================================================ helper: horizontal bars on grey tracks
def track_bars(df, label_col, value_col, colors):
    """Horizontal bars drawn over a light grey full-length 'track', with 'n (share)' at the right end."""
    total = max(df[value_col].max(), 1) * 1.1
    fig = go.Figure()
    fig.add_bar(y=df[label_col], x=[total] * len(df), orientation="h", marker_color=ui.TRACK,
                hoverinfo="skip", showlegend=False, text=df["label"], textposition="outside",
                textfont=dict(size=13, color="#17191D"))
    for _, r in df.iterrows():
        fig.add_bar(y=[r[label_col]], x=[r[value_col]], orientation="h", name=r["legend"],
                    marker_color=colors[r["legend"]], legendgroup=r["legend"],
                    showlegend=r["show_legend"], legendrank=r["rank"], hovertemplate=f"{r[label_col]}: %{{x}}<extra></extra>")
    fig.update_layout(barmode="overlay", bargap=.38)
    fig.update_xaxes(visible=False, range=[0, total * 1.18])
    fig.update_yaxes(categoryorder="array", categoryarray=list(df[label_col])[::-1], title=None)
    return fig


# ================================================================ charts, row 1
st.write("")
left, right = st.columns(2)

with left, ui.card("trend"):
    d4 = days[days["week_no"] <= 4]
    per_week = d4.groupby(["user_id", "week_no"]).size().unstack(fill_value=0)
    fixed = per_week[(per_week >= 1).all(axis=1)].index
    wk = (d4[d4["user_id"].isin(fixed)].groupby("week_no")["steps"].median()
          .rename("median_steps").reset_index())
    wk["week"] = "Week " + wk["week_no"].astype(str)
    change = wk["median_steps"].iloc[-1] / wk["median_steps"].iloc[0] - 1 if len(wk) > 1 else 0
    verb = "Held Steady" if abs(change) < .10 else ("Rose" if change > 0 else "Fell")
    ui.card_title(f"Activity {verb} Across the Month",
                  f"Median daily steps · fixed group of {len(fixed)} users present in all weeks shown")
    lo, hi = wk["median_steps"].min(), wk["median_steps"].max()
    fig = go.Figure(go.Scatter(x=wk["week"], y=wk["median_steps"], mode="lines+markers", fill="tozeroy",
                               line=dict(color=ui.ORANGE, width=2.5), marker=dict(size=8),
                               fillcolor="rgba(252,76,2,.10)",
                               hovertemplate="%{x}: %{y:,.0f} steps<extra></extra>"))
    fig.update_yaxes(range=[max(0, (lo * .75) // 1000 * 1000), (hi * 1.1 // 1000 + 1) * 1000], tickformat=",")
    ui.chart(fig, wk[["week", "median_steps"]], key="ov_trend", anim="draw")

with right, ui.card("segments"):
    seg = (people["activity_segment"].value_counts().reindex(ui.SEGMENT_ORDER).fillna(0).astype(int)
           .rename("people").rename_axis("segment").reset_index())
    n = int(seg["people"].sum())
    seg["share"] = seg["people"] / max(n, 1)
    seg["label"] = seg["people"].astype(str) + " (" + seg["share"].map("{:.0%}".format) + ")"
    seg["legend"], seg["show_legend"], seg["rank"] = seg["segment"], False, range(1, 5)
    hi_n = int(seg.loc[seg["segment"].isin(["Somewhat active", "Active"]), "people"].sum())
    ui.card_title(f"{hi_n} of {n} Users Walk 7,500+ Steps on a Typical Day",
                  f"Users per activity segment · n = {n} (low-data users excluded)")
    ui.chart(track_bars(seg, "segment", "people", ui.SEGMENT_COLORS),
             seg[["segment", "people", "share"]], key="ov_segments", anim="grow")

# ================================================================ charts, row 2
left, right = st.columns(2)

with left, ui.card("hours"):
    hrs = filters.filter_days(load("hourly_clean"))
    by_hour = hrs.groupby("hour")["steps"].mean().rename("avg_steps").reset_index()
    by_hour["window"] = by_hour["hour"].between(17, 19).map({True: "5–7 PM peak", False: "Other hours"})
    peak = int(by_hour.loc[by_hour["avg_steps"].idxmax(), "hour"])
    ui.card_title(f"The Day Peaks at {peak % 12 or 12} {'AM' if peak < 12 else 'PM'}",
                  f"Average steps per hour · {hrs.groupby(['user_id', 'date']).ngroups:,} valid days")
    fig = go.Figure()
    for name, color in [("5–7 PM peak", ui.ORANGE), ("Other hours", "#F8B597")]:
        part = by_hour[by_hour["window"] == name]
        fig.add_bar(x=part["hour"], y=part["avg_steps"], name=name, marker_color=color,
                    hovertemplate="%{x}:00 · %{y:,.0f} steps<extra></extra>")
    fig.update_xaxes(tickvals=[0, 3, 6, 9, 12, 15, 18, 21], ticktext=["12a", "3a", "6a", "9a", "12p", "3p", "6p", "9p"])
    fig.update_layout(bargap=.15)
    ui.chart(fig, by_hour, key="ov_hours", anim="rise")

with right, ui.card("sleep"):
    order = ["< 6 h", "6–7 h", "7–9 h", "> 9 h"]
    rel = nights[nights["reliable_night"]]
    bands = (rel["sleep_category"].value_counts().reindex(order, fill_value=0)
             .rename("nights").rename_axis("length").reset_index())
    total = int(bands["nights"].sum())
    bands["share"] = bands["nights"] / max(total, 1)
    bands["label"] = bands["nights"].astype(str) + " (" + bands["share"].map("{:.0%}".format) + ")"
    bands["legend"] = bands["length"].map(lambda b: "Recommended 7–9 h" if b == "7–9 h" else "Other lengths")
    bands["show_legend"] = [False, True, True, False]
    bands["rank"] = bands["length"].map(lambda b: 1 if b == "7–9 h" else 2)
    share79 = bands.loc[bands["length"] == "7–9 h", "share"].iloc[0]
    head = "Half of Nights" if .45 <= share79 <= .55 else f"{share79:.0%} of Nights"
    ui.card_title(f"{head} Hit the Recommended 7–9 Hours",
                  f"Nights by sleep length · {total} reliable nights, {rel['user_id'].nunique()} users")
    ui.chart(track_bars(bands, "length", "nights", {"Recommended 7–9 h": ui.PURPLE, "Other lengths": "#C9B8EC"}),
             bands[["length", "nights", "share"]], key="ov_sleep", anim="grow")

# ================================================================ so what?
st.html("""<div class="sowhat"><div class="icon">💡</div><div><h4>So what?</h4><ul>
<li>Most users are fairly to very active — the bigger opportunity is <b>consistency</b>, not motivation from zero.</li>
<li><b>5–7 PM</b> is the natural moment for activity nudges; weekends shift to late morning.</li>
<li>Only half of nights reach 7–9 h and <b>22% are under 6 hours</b> — a clear hook for the sleep feature.</li>
</ul><small>Based on all 33 users; the cards and charts above follow your filters.</small></div></div>""")

# ================================================================ explore the pages
st.write("")
st.html('<p class="ctitle" style="font-size:1.25rem">Explore the pages</p>')
guide = [
    ("views/activity.py", "Activity", "How active are different users?"),
    ("views/timing.py", "Timing", "When are users most active?"),
    ("views/sleep.py", "Sleep", "How well do users sleep?"),
    ("views/engagement.py", "Engagement & Retention", "Who keeps tracking, who slips?"),
    ("views/body_heart.py", "Body & Heart", "What do body & heart data add?"),
    ("views/personas.py", "Personas", "Which audience groups exist?"),
    ("views/user_explorer.py", "User Explorer", "What does one user look like?"),
    ("views/conclusion.py", "Conclusion", "What should the business do?"),
    ("views/ask_ai.py", "Ask AI", "Ask anything about the project"),
    ("views/about.py", "About the Data", "Source, cleaning, limits"),
]
for row in (guide[:5], guide[5:]):
    cols = st.columns(5)
    for col, (page, title, question) in zip(cols, row):
        with col, st.container(border=True, key=f"explore_{page.split('/')[1][:-3]}"):
            st.html(f'<p class="ctitle" style="font-size:1rem">{title}</p><p class="csub">{question}</p>')
            st.page_link(page, label="Open page →")