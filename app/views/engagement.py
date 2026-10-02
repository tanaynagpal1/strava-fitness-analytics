"""Engagement & Retention — which users consistently engage with tracking?"""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import filters
import ui
from data import load

# ================================================================ data
profile = load("user_profile")
people = profile[profile["user_id"].isin(filters.selected_users())]
judged = people[~people["low_data_user"]]
wear = filters.filter_days(load("wear_log"))
in_study = wear[~wear["wear_status"].isin(["stopped", "last_day"])]
RED = "#D9534F"

if people.empty or wear.empty:
    ui.page_header("Engagement & Retention", "Who Keeps Tracking?", "Which users consistently engage with tracking?")
    st.info("No users or days match these filters. Try widening them, or press **Reset**.")
    st.stop()

consistent = int((people["engagement_tier"] == "Consistent").sum())
falling = int((judged["activity_trend"] == "Falling").sum())
headline = ("Most Users Stick With the Band" if consistent >= len(people) / 2 else "Many Users Drift Away From the Band")
headline += f" — but {falling} of {len(judged)} Are Quietly Slowing Down" if falling else ""

# ================================================================ header + KPIs
ui.page_header("Engagement & Retention", headline, "Which users consistently engage with tracking?")
wear_rate = (in_study["wear_status"] == "worn").mean()
c = st.columns(5)
ui.kpi_card(c[0], "Wear rate", f"{wear_rate:.1%}", "worn days ÷ days in study", accent=ui.TEAL,
            count=(round(wear_rate * 100, 1), 1, "%"),
            help="Each person's export-cut last day and days after they stopped are excluded.")
ui.kpi_card(c[1], "Consistent users", f"{consistent} of {len(people)}", "≥80% clean days", accent="#C2410C",
            count=(consistent, 0, f" of {len(people)}"))
ui.kpi_card(c[2], "Early drop-outs", f"{int(people['stopped_early'].sum())}",
            f"+{int(people['stopped_final_week'].sum())} uncertain in final week", accent=RED,
            count=(int(people["stopped_early"].sum()), 0, ""))
ui.kpi_card(c[3], "Activity falling", f"{falling} of {len(judged)}", "2nd half vs 1st half −10%+", accent=RED,
            count=(falling, 0, f" of {len(judged)}"))
multi = int((people["features_used"] >= 2).sum())
ui.kpi_card(c[4], "Use 2+ features", f"{multi} of {len(people)}", "sleep · weight · workout logging",
            count=(multi, 0, f" of {len(people)}"))

# ================================================================ wear calendar
STATUS = [("worn", "Worn", ui.TEAL), ("partial", "Partial", "#E0A526"), ("not_worn", "Not worn", RED),
          ("last_day", "Last day", "#C9CDD4"), ("stopped", "Stopped", "#EEF0F3")]
st.write("")
with ui.card("eng_calendar"):
    gaps = in_study[in_study["wear_status"] != "worn"].groupby("user_id").size().sort_values(ascending=False)
    top = max(1, round(len(people) / 4))
    clustered = len(gaps) and gaps.head(top).sum() >= .5 * gaps.sum()
    ui.card_title("Most Users Wear the Band Daily — Gaps Cluster in a Few People" if clustered
                  else f"{wear_rate:.0%} of Study Days Are Fully Worn",
                  f"Wear status per user per day · {wear['user_id'].nunique()} users × {wear['date'].nunique()} days · "
                  f"sorted by days worn{f' · {top} users hold {gaps.head(top).sum() / gaps.sum():.0%} of all gaps' if len(gaps) else ''}")
    st.html('<div class="chips">' + "".join(f'<span><i style="background:{col}"></i>{lab}</span>' for _, lab, col in STATUS)
            + "</div>")
    code = {s: i for i, (s, _, _) in enumerate(STATUS)}
    order = (wear.assign(w=wear["wear_status"] == "worn").groupby("user_id")["w"].sum()
             .sort_values(ascending=False).index)
    grid = wear.pivot_table(index="user_id", columns="date", values="wear_status", aggfunc="first").reindex(order)
    z = grid.apply(lambda col: col.map(code))
    scale = []
    for i, (_, _, col) in enumerate(STATUS):                      # stepped colour scale: one solid colour per status
        scale += [[i / len(STATUS), col], [(i + 1) / len(STATUS), col]]
    fig = go.Figure(go.Heatmap(z=z.values, x=[d.strftime("%d %b") for d in grid.columns], y=["…" + u[-5:] for u in grid.index],
                               zmin=-.5, zmax=len(STATUS) - .5, colorscale=scale, showscale=False, xgap=2, ygap=2,
                               customdata=grid.fillna("–").map(lambda s: s.replace("_", " ")).values,
                               hovertemplate="%{y} · %{x}: %{customdata}<extra></extra>"))
    fig.update_yaxes(autorange="reversed", tickfont=dict(size=9), title=None)
    fig.update_xaxes(side="top", tickfont=dict(size=10), nticks=12)
    table = grid.reset_index()
    table.columns = ["user"] + [d.strftime("%d %b") for d in grid.columns]
    ui.chart(fig, table, key="eng_calendar", height=max(320, 15 * len(grid) + 60), anim="wipe")
    # ================================================================ row: retention · weekly wear · weekday gaps
DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
col1, col2, col3 = st.columns([1.3, 1, 1.1])

with col1, ui.card("eng_retention"):
    ret = (wear.groupby("date")["wear_status"].apply(lambda s: (s != "stopped").mean())
           .rename("still_recording").reset_index())
    day21 = filters.START + pd.Timedelta(days=21)
    at = ret[ret["date"].dt.date == day21]
    if len(at):
        title = f"{at['still_recording'].iloc[0]:.0%} of Users Were Still Recording 3 Weeks In"
    else:
        title = f"{ret['still_recording'].iloc[-1]:.0%} of Users Still Recording on {ret['date'].iloc[-1]:%d %b}"
    ui.card_title(title, f"Share of users still in the study each day · n = {wear['user_id'].nunique()}")
    fig = go.Figure(go.Scatter(x=ret["date"], y=ret["still_recording"] * 100, mode="lines", fill="tozeroy",
                               line=dict(color=ui.ORANGE, width=2.5, shape="hv"), fillcolor="rgba(252,82,0,.10)",
                               hovertemplate="%{x|%d %b}: %{y:.0f}% still recording<extra></extra>"))
    fig.update_yaxes(range=[0, 105], ticksuffix="%")
    fig.update_xaxes(tickformat="%d %b")
    ui.chart(fig, ret.assign(still_recording=ret["still_recording"].round(3)), key="eng_retention", height=300,
             anim="draw")

with col2, ui.card("eng_weekly"):
    wk = (in_study[in_study["week_no"] <= 4].groupby("week_no")
          .agg(rate=("wear_status", lambda s: (s == "worn").mean()), users=("user_id", "nunique")).reset_index())
    if wk.empty:
        title = "Weekly Wear Rate"
    elif len(wk) >= 2 and wk["rate"].iloc[-1] < wk["rate"].iloc[0] - .01:
        title = f"Wear Rate Slips From {wk['rate'].iloc[0]:.0%} to {wk['rate'].iloc[-1]:.0%} Over the Month"
    else:
        title = f"Wear Rate Holds Steady at About {wk['rate'].astype(float).mean():.0%} Every Week"
    ui.card_title(title, "Share of recorded days fully worn · weeks 1–4 · users per week under each bar")
    if wk.empty:
        st.caption("No recorded days from weeks 1–4 in the current filter.")
    fig = go.Figure(go.Bar(x=[f"Week {w}<br><sub>n = {u}</sub>" for w, u in zip(wk["week_no"], wk["users"])],
                           y=wk["rate"] * 100, marker_color=ui.TEAL, text=[f"{v:.0%}" for v in wk["rate"]],
                           textposition="outside", hovertemplate="%{x}: %{y:.1f}% worn<extra></extra>"))
    fig.update_yaxes(range=[0, 110], ticksuffix="%")
    fig.update_layout(bargap=.3)
    ui.chart(fig, wk.round(3), key="eng_weekly", height=300, anim="rise")

with col3, ui.card("eng_weekday"):
    wd = (in_study.groupby("day_of_week")["wear_status"].apply(lambda s: (s != "worn").mean())
          .reindex([d for d in DAYS if d in set(in_study["day_of_week"])]).rename("not_fully_worn").reset_index())
    worst = wd.loc[wd["not_fully_worn"].astype(float).idxmax(), "day_of_week"] if len(wd) else None
    ui.card_title(f"{worst}s Have the Most Not-Worn or Partial Days" if worst else "Not-Worn Days by Weekday",
                  "Share of recorded days not fully worn, by weekday")
    if wd.empty:
        st.caption("No recorded days in the current filter.")
    fig = go.Figure(go.Bar(x=[d[:3] for d in wd["day_of_week"]], y=wd["not_fully_worn"] * 100,
                           marker_color=[RED if d == worst else "#F2A7A5" for d in wd["day_of_week"]],
                           text=[f"{v:.0%}" for v in wd["not_fully_worn"]], textposition="outside",
                           hovertemplate="%{x}: %{y:.1f}% not fully worn<extra></extra>"))
    fig.update_yaxes(range=[0, (wd["not_fully_worn"].astype(float).max() if len(wd) else .2) * 125], ticksuffix="%")
    fig.update_layout(bargap=.25)
    ui.chart(fig, wd.round(3), key="eng_weekday", height=300, anim="rise")
    # ================================================================ row: segment × tier · 1st vs 2nd half · tiers
TIERS = ["Consistent", "Irregular", "Barely using"]
col1, col2, col3 = st.columns([1, 1.25, 1])

with col1, ui.card("eng_grid"):
    grid2 = (pd.crosstab(judged["activity_segment"], judged["engagement_tier"])
             .reindex(index=[s for s in ui.SEGMENT_ORDER if s in set(judged["activity_segment"])], columns=TIERS,
                      fill_value=0))
    if grid2.empty:
        ui.card_title("Segments × Engagement Tiers", "No users with 7+ clean days in the current filter")
    else:
        loose = (1 - grid2["Consistent"] / grid2.sum(axis=1).replace(0, 1))
        ui.card_title(f"{loose.idxmax().title()} Users Are the Most Irregular Wearers",
                      f"Users by activity segment × engagement tier · n = {len(judged)}")
        fig = go.Figure(go.Heatmap(z=grid2.values, x=["Consistent", "Irregular", "Barely<br>using"], y=list(grid2.index),
                                   colorscale=[[0, "#FFF1EA"], [.5, "#FC9A62"], [1, "#B33A0A"]], showscale=False,
                                   xgap=5, ygap=5, texttemplate="<b>%{z}</b>", textfont=dict(size=16),
                                   hovertemplate="%{y} · %{x}: %{z} users<extra></extra>"))
        fig.update_yaxes(autorange="reversed", title=None)
        fig.update_xaxes(side="bottom")
        ui.chart(fig, grid2.reset_index().rename(columns={"activity_segment": "segment"}), key="eng_grid",
                 height=320, anim="wipe")

with col2, ui.card("eng_slope"):
    sl = judged.dropna(subset=["steps_1st_half", "steps_2nd_half"]).copy()
    sl["falling"] = sl["activity_trend"] == "Falling"
    n_fall = int(sl["falling"].sum())
    ui.card_title(f"{n_fall} of {len(sl)} Users Walk 10%+ Less in the Second Half",
                  "Typical steps, 1st vs 2nd half of the month · one line per user · falling highlighted")
    st.html(f'<div class="chips"><span><i style="background:{RED}"></i>Falling ({n_fall})</span>'
            f'<span><i style="background:#C9CDD4"></i>Rising or stable ({len(sl) - n_fall})</span></div>')
    fig = go.Figure()
    for fall, color, width in [(False, "#C9CDD4", 1.5), (True, RED, 2.2)]:
        part = sl[sl["falling"] == fall]
        xs, ys = [], []
        for _, r in part.iterrows():
            xs += ["1st half", "2nd half", None]
            ys += [r["steps_1st_half"], r["steps_2nd_half"], None]
        fig.add_scatter(x=xs, y=ys, mode="lines+markers", line=dict(color=color, width=width),
                        marker=dict(size=5, color=color), showlegend=False, hoverinfo="skip")
    fig.update_yaxes(rangemode="tozero", tickformat="~s")
    fig.update_xaxes(range=[-.15, 1.15])
    ui.chart(fig, sl[["user_id", "steps_1st_half", "steps_2nd_half", "activity_trend"]].round(0), key="eng_slope",
             height=320, anim="draw")

with col3, ui.card("eng_tiers"):
    tiers = (people["engagement_tier"].value_counts().reindex(TIERS, fill_value=0)
             .rename("people").rename_axis("tier").reset_index())
    tiers["share"] = tiers["people"] / max(len(people), 1)
    tiers["label"] = tiers["people"].astype(str) + " (" + tiers["share"].map("{:.0%}".format) + ")"
    tiers["legend"], tiers["show_legend"], tiers["rank"] = tiers["tier"], False, range(3)
    ui.card_title(f"{consistent} of {len(people)} Users Are Consistent Wearers",
                  f"Users per engagement tier (by share of clean days) · n = {len(people)}")
    ui.chart(ui.track_bars(tiers, "tier", "people", ui.TIER_COLORS, room=1.5),
             tiers[["tier", "people", "share"]], key="eng_tiers", height=320, anim="grow")
# ================================================================ row: feature funnel · features vs steps · streak
col1, col2, col3 = st.columns([1.25, 1, 1])

with col1, ui.card("eng_funnel"):
    steps = [("Tried sleep tracking", people["tracks_sleep"], "Tried"),
             ("Sleep tracking 7+ nights", people["reliable_nights"] >= 7, "Habit"),
             ("Logged weight", people["logs_weight"], "Tried"),
             ("Weight habit (10+ logs)", people["n_weight_logs"].fillna(0) >= 10, "Habit"),
             ("Logged workouts", people["logs_workouts"], "Tried")]
    fun = pd.DataFrame({"step": [s for s, _, _ in steps], "people": [int(m.sum()) for _, m, _ in steps],
                        "legend": [k for _, _, k in steps]})
    fun["share"] = fun["people"] / max(len(people), 1)
    fun["label"] = fun["people"].astype(str) + " (" + fun["share"].map("{:.0%}".format) + ")"
    fun["show_legend"], fun["rank"] = False, range(len(fun))
    keep_sleep = fun["people"][1] / max(fun["people"][0], 1)
    keep_weight = fun["people"][3] / max(fun["people"][2], 1)
    ui.card_title("Features Lose Most Users After the First Try" if min(keep_sleep, keep_weight) < .75
                  else "Users Who Try a Feature Mostly Keep It",
                  f"Users per feature step · tried → became a habit · n = {len(people)}")
    st.html(f'<div class="chips"><span><i style="background:{ui.ORANGE}"></i>Tried</span>'
            '<span><i style="background:#9A3412"></i>Became a habit</span></div>')
    ui.chart(ui.track_bars(fun, "step", "people", {"Tried": ui.ORANGE, "Habit": "#9A3412"}, room=1.35),
             fun[["step", "people", "share"]], key="eng_funnel", height=300, anim="grow")

with col2, ui.card("eng_features"):
    fs = (judged.groupby("features_used")["typical_steps"].agg(steps="median", users="size")
          .reindex(range(4)).dropna().reset_index())
    none_ = judged.loc[judged["features_used"] == 0, "typical_steps"].median()
    multi_ = judged.loc[judged["features_used"] >= 2, "typical_steps"].median()
    if pd.notna(none_) and pd.notna(multi_) and multi_ > none_:
        title = f"Using 2+ Features Goes With {multi_ - none_:,.0f} More Daily Steps"
    else:
        title = "Feature Use and Daily Steps Don't Line Up"
    ui.card_title(title, "Typical steps by number of optional features used · users per bar under it · "
                         "linked with, not caused by")
    shades = ["#FAD3C0", "#F8B597", ui.ORANGE, "#9A3412"]
    fig = go.Figure(go.Bar(x=[f"{int(k)} feature{'' if k == 1 else 's'}<br><sub>n = {int(u)}</sub>"
                              for k, u in zip(fs["features_used"], fs["users"])],
                           y=fs["steps"], marker_color=[shades[int(k)] for k in fs["features_used"]],
                           text=[f"{v:,.0f}" for v in fs["steps"]], textposition="outside",
                           hovertemplate="%{x}: %{y:,.0f} steps<extra></extra>"))
    fig.update_yaxes(range=[0, (fs["steps"].max() if len(fs) else 10_000) * 1.2], tickformat="~s")
    fig.update_layout(bargap=.25)
    ui.chart(fig, fs.round(0), key="eng_features", height=300, anim="rise")

with col3, ui.card("eng_streak"):
    days = in_study.sort_values(["user_id", "date"])
    best, broken = {}, {}
    for u, g in days.groupby("user_id"):
        run = longest = 0
        for s in g["wear_status"]:
            run = run + 1 if s == "worn" else 0
            longest = max(longest, run)
        best[u] = longest
        broken[u] = (g["wear_status"] != "worn").any()
    perfect = [u for u in best if not broken[u]]
    gapped = {u: k for u, k in best.items() if broken[u]}
    ui.card_title(f"{len(perfect)} Users Never Broke Their Wear Streak",
                  "Each circle = a recorded day · filled = fully worn · hollow = partial · red = not worn")
    if gapped:
        star = max(gapped, key=gapped.get)
        g = days[days["user_id"] == star]
        first_gap = g.loc[g["wear_status"] != "worn", "date"].iloc[0]
        dots = "".join(f'<i class="d-{s}" style="animation-delay:{i * 30}ms" title="{d:%d %b}: {s.replace("_", " ")}"></i>'
                       for i, (d, s) in enumerate(zip(g["date"], g["wear_status"])))
        with st.container(key="anim_streak_eng"):
            st.html(f'<p class="streak-who">Example: user …{star[-5:]} · longest run {gapped[star]} days</p>'
                    f'<div class="streak">{dots}</div>'
                    f'<p class="streak-note">One {g.loc[g["date"] == first_gap, "wear_status"].iloc[0].replace("_", " ")} '
                    f'day on {first_gap:%d %b} broke the chain. A "keep your streak" nudge targets exactly this.</p>')
    table = pd.DataFrame({"user": list(best), "longest_streak": list(best.values()),
                          "ever_missed": [broken[u] for u in best]}).sort_values("longest_streak", ascending=False)
    with st.container(horizontal=True, horizontal_alignment="right"):
        with st.popover("Show data", icon=":material/table_view:"):
            st.dataframe(table, hide_index=True)

# ================================================================ so what?
st.html(f"""<div class="sowhat"><div class="icon">💡</div><div><h4>So what?</h4><ul>
<li>Flag the <b>{falling} users</b> whose activity fell 10%+ as <b>churn risk</b> and send a re-engagement nudge.</li>
<li>Single-day gaps look like "took it off to charge and forgot" — add <b>band-off / charging reminders</b>
(worst day: <b>{worst or '–'}</b>).</li>
<li>Most users stop at one feature — an onboarding push to <b>try a second feature</b> (sleep or weight) targets the biggest gap.</li>
</ul><small>Numbers follow your filters.</small></div></div>""")