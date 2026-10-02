"""Personas — how can activity and engagement combine into actionable audience groups?"""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import filters
import ui
from data import load

# ================================================================ data
profile = load("user_profile")
people = profile[profile["user_id"].isin(filters.selected_users())]
TIERS = ["Consistent", "Irregular", "Barely using"]
SEGS = ["Active", "Somewhat active", "Low active", "Sedentary"]

ICON = {"Committed Movers": "🏆", "On-and-Off Movers": "🔁", "Daily Strollers": "🚶",
        "Slipping Starters": "📉", "Fading Users": "💤"}
RULE = {"Committed Movers": "Active or Somewhat active · Consistent",
        "On-and-Off Movers": "Active or Somewhat active · Irregular",
        "Daily Strollers": "Low active or Sedentary · Consistent",
        "Slipping Starters": "Low active or Sedentary · Irregular",
        "Fading Users": "Any segment · Barely using (incl. users with too little data)"}
PLAY = {   # message · feature to promote · KPI to track (timing is computed from the members' own data)
    "Committed Movers": ("Challenges & milestones — chase a new personal best", "Challenges & leaderboards",
                         "Weekly exercise minutes"),
    "On-and-Off Movers": ("Keep-the-streak nudge on quiet days", "Streaks", "Active days per week"),
    "Daily Strollers": ('"Add one brisk 10-minute walk" — step up to 7,500', "Goal ladder & guided walks",
                        "Exercise (MVPA) minutes"),
    "Slipping Starters": ("Habit nudge: a small daily goal, 10 minutes counts", "Band-off / charging reminders",
                          "Wear rate"),
    "Fading Users": ("Win-back: easy goal, welcome back", "Win-back check-in + charging reminders",
                     "Returns within 7 days"),
}

if people.empty:
    ui.page_header("Personas", "Audience Personas", "How can activity and engagement combine into actionable audience groups?")
    st.info("No users match these filters. Try widening them, or press **Reset**.")
    st.stop()

sizes = people["persona"].value_counts().reindex(ui.PERSONA_ORDER).dropna().astype(int)
top, top_n = sizes.idxmax(), int(sizes.max())
share = top_n / len(people)
how_many = "Half the Users" if .45 <= share <= .55 else f"{share:.0%} of Users"

# ================================================================ header
ui.page_header("Personas", f"{len(sizes)} Personas From Activity × Engagement — {top} Are {how_many}",
               "How can activity and engagement combine into actionable audience groups?")

# ================================================================ persona picker
options = list(sizes.index)
if st.session_state.get("ps_pick") not in options:
    st.session_state["ps_pick"] = top
pick = st.segmented_control("Pick a persona", options, key="ps_pick",
                            format_func=lambda p: f"{ICON[p]} {p} · {sizes[p]}") or top
members = people[people["persona"] == pick]

col1, col2 = st.columns([1, 1.15])

# ---------------------------------------------------------------- matrix: segment × tier, coloured by persona
with col1, ui.card("ps_matrix"):
    ui.card_title("Engagement, Not Just Steps, Decides the Persona",
                  "Persona matrix: activity segment × engagement tier · selected persona outlined · "
                  f"n = {len(people)}")
    head = "".join(f'<div class="pm-h">{t}</div>' for t in TIERS)
    rows = ""
    groups = [(s, people[people["activity_segment"] == s]) for s in SEGS]
    groups.append(("Too little data", people[people["activity_segment"].isna()]))
    for seg, grp in groups:
        if seg == "Too little data" and grp.empty:
            continue
        rows += f'<div class="pm-r" style="color:{ui.SEGMENT_COLORS.get(seg, "#8B8F98")}">{seg}</div>'
        for t in TIERS:
            cell = grp[grp["engagement_tier"] == t]
            if cell.empty:
                rows += '<div class="pm-c empty">–</div>'
                continue
            p = cell["persona"].iloc[0]
            col = ui.PERSONA_COLORS[p]
            rows += (f'<div class="pm-c{" on" if p == pick else ""}" style="--pc:{col}">'
                     f'<b>{len(cell)}</b><span>{ICON[p]} {p}</span></div>')
    st.html(f'<div class="pmatrix"><div></div>{head}{rows}</div>')
    table = (people.groupby(["activity_segment", "engagement_tier"], dropna=False)
             .agg(users=("user_id", "size"), persona=("persona", "first")).reset_index()
             .fillna({"activity_segment": "Too little data"}))
    with st.container(horizontal=True, horizontal_alignment="right"):
        with st.popover("Show data", icon=":material/table_view:"):
            st.dataframe(table, hide_index=True)

# ---------------------------------------------------------------- selected persona card
with col2, ui.card("ps_card"):
    def med(col, fmt):
        v = members[col].median()
        return fmt.format(v) if pd.notna(v) else "–"

    judged = members["meets_activity_guideline"].dropna()
    times = members["preferred_workout_time"].value_counts()
    when = times.drop("No workouts", errors="ignore")
    timing = f"{when.idxmax()} (their most common workout time)" if len(when) else "Evening peak (5–7 PM)"
    mix = " · ".join(f"{k} {n}" for k, n in times.items())
    color = ui.PERSONA_COLORS[pick]
    msg, feat, kpi = PLAY[pick]
    tiles = [("Typical steps", med("typical_steps", "{:,.0f}")), ("Exercise / day", med("typical_mvpa_min", "{:.0f} min")),
             ("Meet guideline", f"{int(judged.sum())} of {len(judged)}" if len(judged) else "–"),
             ("10K days", med("goal_10k_rate", "{:.0%}"))]
    st.html(f'<div class="pc-head"><div class="pc-icon" style="background:{color}">{ICON[pick]}</div>'
            f'<div><div class="pc-name">{pick}</div><div class="pc-rule">{RULE[pick]} · {len(members)} users</div></div></div>'
            '<div class="pc-tiles">' + "".join(f'<div><small>{k}</small><b>{v}</b></div>' for k, v in tiles) + '</div>'
            f'<div class="pc-tiles two"><div><small>Workout time</small><b>{mix or "–"}</b></div>'
            f'<div><small>Sleep tracking</small><b>{int(members["tracks_sleep"].sum())} of {len(members)} track sleep</b></div></div>'
            '<div class="pc-play">'
            f'<div><i style="--pc:{color}">M</i><span>Message</span><b>{msg}</b></div>'
            f'<div><i style="--pc:{color}">T</i><span>Timing</span><b>{timing}</b></div>'
            f'<div><i style="--pc:{color}">F</i><span>Feature to promote</span><b>{feat}</b></div>'
            f'<div><i style="--pc:{color}">K</i><span>KPI to track</span><b>{kpi}</b></div></div>'
            f'<p class="pc-note">Based on {len(members)} user{"s" if len(members) != 1 else ""}'
            f'{" — low confidence, treat as a hypothesis" if len(members) < 4 else ""}.</p>')
    show = members[["user_id", "activity_segment", "engagement_tier", "typical_steps", "typical_mvpa_min",
                    "goal_10k_rate", "preferred_workout_time", "tracks_sleep"]]
    with st.container(horizontal=True, horizontal_alignment="right"):
        with st.popover("Show data", icon=":material/table_view:"):
            st.dataframe(show, hide_index=True)
# ================================================================ row: radar vs all users · playbook for every persona
AXES = [("Steps", "typical_steps"), ("Exercise Minutes", "typical_mvpa_min"), ("10K-Goal Rate", "goal_10k_rate"),
        ("Features Used", "features_used"), ("Wear Consistency", "clean_day_share")]
col1, col2 = st.columns([1, 1.45])

with col1, ui.card("ps_radar"):
    top_val = {c: profile[c].max() or 1 for _, c in AXES}                  # each axis scaled to the highest user
    mine = [members[c].median() / top_val[c] * 100 for _, c in AXES]
    everyone = [people[c].median() / top_val[c] * 100 for _, c in AXES]
    gaps = [abs(a - b) if pd.notna(a) and pd.notna(b) else 0 for a, b in zip(mine, everyone)]
    i = max(range(len(AXES)), key=gaps.__getitem__)                         # axis with the biggest difference
    standout, higher = AXES[i][0], mine[i] > everyone[i]
    ui.card_title(f"{pick} Stand Out Most on {standout} — {'Above' if higher else 'Below'} the Typical User",
                  "Persona median vs all users (median) · each axis scaled to the highest user (0–100%)")
    labels = [a for a, _ in AXES] + [AXES[0][0]]
    fig = go.Figure()
    fig.add_scatterpolar(r=everyone + everyone[:1], theta=labels, name="All users (median)", fill="toself",
                         line=dict(color="#9CA3AF", width=2), fillcolor="rgba(156,163,175,.18)",
                         hovertemplate="All users · %{theta}: %{r:.0f}%<extra></extra>")
    fig.add_scatterpolar(r=mine + mine[:1], theta=labels, name=pick, fill="toself",
                         line=dict(color=ui.PERSONA_COLORS[pick], width=2.5),
                         fillcolor=ui.PERSONA_COLORS[pick] + "40", hovertemplate=pick + " · %{theta}: %{r:.0f}%<extra></extra>")
    fig.update_layout(polar=dict(bgcolor="rgba(0,0,0,0)", domain=dict(x=[.22, .78], y=[.06, .9]),
                                 radialaxis=dict(range=[0, 100], showticklabels=False, showline=False, ticks="",
                                                 gridcolor="#EEF0F3"),
                                 angularaxis=dict(rotation=90, direction="clockwise", gridcolor="#EEF0F3",
                                                  linecolor="#E1E4EA", tickfont=dict(size=11, color="#374151"))),
                      legend=dict(traceorder="reversed"))
    table = pd.DataFrame({"axis": [a for a, _ in AXES], pick: [round(v, 1) for v in mine],
                          "all users": [round(v, 1) for v in everyone]})
    ui.chart(fig, table, key="ps_radar", height=380, anim="fade")

with col2, ui.card("ps_playbook"):
    ui.card_title("A Message, a Moment and a Feature for Every Persona",
                  "Playbook per persona · timing = members' most common workout time · selected persona highlighted")
    rows = ""
    for p in sizes.index:
        grp = people[people["persona"] == p]
        w = grp["preferred_workout_time"].value_counts().drop("No workouts", errors="ignore")
        msg, feat, kpi = PLAY[p]
        rows += (f'<tr class="{"on" if p == pick else ""}" style="--pc:{ui.PERSONA_COLORS[p]}">'
                 f'<td><i></i>{ICON[p]} {p}</td><td>{sizes[p]}</td><td>{msg}</td>'
                 f'<td>{w.idxmax() if len(w) else "Evening peak"}</td><td>{feat}</td><td>{kpi}</td></tr>')
    st.html('<div class="segwrap"><table class="playbook"><thead><tr><th>Persona</th><th>Users</th><th>Message</th>'
            f'<th>Timing</th><th>Feature</th><th>KPI</th></tr></thead><tbody>{rows}</tbody></table></div>')
    book = pd.DataFrame([{"persona": p, "users": int(sizes[p]), "message": PLAY[p][0], "feature": PLAY[p][1],
                          "kpi": PLAY[p][2]} for p in sizes.index])
    with st.container(horizontal=True, horizontal_alignment="right"):
        with st.popover("Show data", icon=":material/table_view:"):
            st.dataframe(book, hide_index=True)

# ================================================================ so what?
big = sizes.sort_values(ascending=False)
small = [p for p, n in sizes.items() if n < 4]
others = ", ".join(f"{p} ({n})" for p, n in big.iloc[1:3].items())
line1 = (f"The biggest persona, <b>{big.index[0]} ({big.iloc[0]})</b>, is best served by "
         f"<b>{PLAY[big.index[0]][1].lower()}</b>" + (f" — while <b>{others}</b> need different, simpler nudges" if others else ""))
line2 = (f"Small personas ({', '.join(small)}) are shown for completeness — treat their playbook as <b>low confidence</b>."
         if small else "Every persona has 4+ users, so each playbook rests on a few people at least.")
st.html(f"""<div class="sowhat"><div class="icon">💡</div><div><h4>So what?</h4><ul>
<li>{line1}.</li>
<li>{line2}</li>
</ul><small>Numbers follow your filters.</small></div></div>""")
