"""Activity — how do activity levels differ across users?"""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import filters
import ui
from data import load

# ================================================================ data
profile = load("user_profile")
people = profile[profile["user_id"].isin(filters.selected_users())]
judged = people[~people["low_data_user"]]                       # segments need 7+ clean days
days = filters.filter_days(load("daily_master"))
days = days.merge(profile[["user_id", "activity_segment"]], on="user_id", how="left")

# ================================================================ header
ui.page_header("Activity", "Four Activity Segments — and the Gap Is Exercise, Not Steps",
               "How do activity levels differ across users?")
if days.empty:
    st.info("No days match these filters. Try widening them, or press **Reset**.")
    st.stop()

# ================================================================ segment picker + runner track
seg_days = days.dropna(subset=["activity_segment"])
summary = (seg_days.groupby("activity_segment")
           .agg(steps=("steps", "median"), users=("user_id", "nunique"))
           .reindex(ui.SEGMENT_ORDER).dropna())
all_steps = days["steps"].median()
SCALE = 15_000                                                 # right end of the track


def pct(steps):
    return f"{min(steps / SCALE, 1) * 100:.1f}%"


with ui.card("picker"):
    st.html('<div class="pick-head"><span class="pick-eyebrow">Pick a segment — the runner\'s speed and distance '
            f'follow its typical steps</span><span class="pick-all">All users: {all_steps:,.0f} typical steps · '
            f'{all_steps / 100:.0f}% of 10K</span></div>')

    options = ["All users"] + list(summary.index)
    if st.session_state.get("act_pick") not in options:        # a global filter removed the chosen segment
        st.session_state["act_pick"] = "All users"
    pick = st.segmented_control("Runner follows", options, key="act_pick") or "All users"

    cards = "".join(
        f'<div class="segc{" on" if seg == pick else ""}"><div class="nm" style="color:{ui.SEGMENT_COLORS[seg]}">{seg}</div>'
        f'<div class="v">{r.steps:,.0f} <small>steps on a median day</small></div>'
        f'<div class="m">{int(r.users)} users · {r.steps / 100:.0f}% of 10K</div></div>'
        for seg, r in summary.iterrows())
    st.html(f'<div class="segcards">{cards}</div>')

    steps = all_steps if pick == "All users" else summary.loc[pick, "steps"]
    dur = max(1.2, 4.2 - steps / 4000)                          # more steps = faster runner
    ticks = "".join(f'<span style="left:{pct(t)}">{t / 1000:g}k</span>' for t in range(0, SCALE + 1, 2500))
    with st.container(key="anim_track_activity"):
        st.html(f'<div class="trk"><div class="trk-bar">'
                f'<div class="trk-fill" style="--x:{pct(steps)}; --d:{dur:.1f}s"></div>'
                f'<div class="trk-goal" style="left:{pct(10_000)}"><span>🏁 10K goal</span></div>'
                f'<div class="trk-runner" style="--x:{pct(steps)}; --d:{dur:.1f}s">🏃</div></div>'
                f'<div class="trk-ticks">{ticks}</div></div>')
    st.caption(f"**{pick}** · {steps:,.0f} steps on a median day = {steps / 100:.0f}% of the 10K goal")

# ================================================================ KPI row (5 cards)
st.write("")
mvpa = days["mvpa_min"].median()
meets = judged["meets_activity_guideline"].dropna()
c = st.columns(5)
ui.kpi_card(c[0], "Typical daily steps", f"{all_steps:,.0f}", f"median of {len(days):,} days",
            count=(round(all_steps), 0, ""))
ui.kpi_card(c[1], "Typical active minutes", f"{days['active_min'].median():.0f}", "light + moderate + vigorous",
            count=(round(days["active_min"].median()), 0, ""))
ui.kpi_card(c[2], "Typical exercise (MVPA)", f"{mvpa:.0f} min", "moderate-to-vigorous per day",
            count=(round(mvpa), 0, " min"))
ui.kpi_card(c[3], "10K goal days", f"{days['goal_10k_met'].mean():.0%}", "of clean days",
            count=(round(days["goal_10k_met"].mean() * 100), 0, "%"))
ui.kpi_card(c[4], "Meet exercise guideline", f"{int(meets.sum())} of {len(meets)}", "≥150 MVPA min / week",
            help="WHO guideline, per person over the whole month (users with 7+ clean days).")
# ================================================================ chart row 1: segments · guideline · daily spread
n = len(judged)
st.write("")
if judged.empty or seg_days.empty:
    st.info("No users with 7+ clean days match these filters, so the segment charts are hidden. Try widening them.")
    st.stop()
col1, col2, col3 = st.columns(3)

with col1, ui.card("act_segments"):
    seg = (judged["activity_segment"].value_counts().reindex(ui.SEGMENT_ORDER).fillna(0).astype(int)
           .rename("people").rename_axis("segment").reset_index())
    seg["share"] = seg["people"] / max(n, 1)
    seg["label"] = seg["people"].astype(str) + " (" + seg["share"].map("{:.0%}".format) + ")"
    seg["legend"], seg["show_legend"], seg["rank"] = seg["segment"], False, range(1, 5)
    largest = seg.loc[seg["people"].idxmax(), "segment"]
    ui.card_title(f"{largest.title()} Users Make Up the Largest Group", f"Users per activity segment · n = {n}")
    ui.chart(ui.track_bars(seg, "segment", "people", ui.SEGMENT_COLORS, room=1.6),
             seg[["segment", "people", "share"]], key="act_segments", anim="grow")

with col2, ui.card("act_guideline"):
    g = (judged.dropna(subset=["meets_activity_guideline"])
         .groupby("activity_segment")["meets_activity_guideline"]
         .agg(meets="mean", people="size").reindex(ui.SEGMENT_ORDER).dropna().reset_index())
    g["Meets guideline"] = g["meets"].astype(float)
    g["Does not meet"] = 1 - g["Meets guideline"]
    zero = [s.title() for s in g.loc[g["meets"] == 0, "activity_segment"]]
    title = (f"No {' or '.join(zero)} User Meets the Guideline" if zero
             else f"{g.loc[g['meets'].idxmax(), 'activity_segment'].title()} Users Lead on Exercise")
    ui.card_title(title, f"Share meeting 150 MVPA min/week, per segment · n = {int(g['people'].sum())}")
    fig = ui.stacked_share(g, "activity_segment", ["Meets guideline", "Does not meet"],
                           {"Meets guideline": "#C2410C", "Does not meet": "#E6E8EC"}, list(g["activity_segment"]))
    ui.chart(fig, g[["activity_segment", "people", "Meets guideline"]].rename(columns={"activity_segment": "segment"}),
             key="act_guideline", anim="stack")

with col3, ui.card("act_spread"):
    rows = []
    for s in ui.SEGMENT_ORDER:
        d = seg_days.loc[seg_days["activity_segment"] == s, "steps"]
        if len(d):
            q = d.quantile([.05, .25, .5, .75, .95])
            rows.append({"segment": s, "days": len(d), "p5": q[.05], "q1": q[.25], "median": q[.5],
                         "q3": q[.75], "p95": q[.95], "under_10k": (d < 10_000).mean()})
    spread = pd.DataFrame(rows)
    top = spread.iloc[-1]                                           # most active segment shown
    one_in = max(1, round(1 / top["under_10k"])) if top["under_10k"] > 0 else None
    title = (f"Even {top['segment'].title()} Users Have 1 in {one_in} Days Under 10K" if one_in
             else f"{top['segment'].title()} Users Clear 10K Every Day")
    ui.card_title(title, "Daily steps by segment · box = middle 50%, line = median, whiskers = 5th–95th pct")
    fig = go.Figure()
    for _, r in spread.iterrows():
        fig.add_trace(go.Box(y=[r["segment"]], q1=[r["q1"]], median=[r["median"]], q3=[r["q3"]],
                             lowerfence=[r["p5"]], upperfence=[r["p95"]], orientation="h", name=r["segment"],
                             marker_color=ui.SEGMENT_COLORS[r["segment"]], fillcolor=ui.SEGMENT_COLORS[r["segment"]] + "8C",
                             line=dict(width=2), showlegend=False, hoverinfo="x"))
    fig.add_vline(x=10_000, line=dict(color="#C2410C", width=1.5, dash="dash"),
                  annotation_text="10K goal", annotation_font=dict(color="#C2410C", size=11))
    fig.update_yaxes(categoryorder="array", categoryarray=list(spread["segment"])[::-1], title=None)
    fig.update_xaxes(tickformat="~s", title=None, rangemode="tozero")
    show = spread.round(0).assign(under_10k=spread["under_10k"].round(2))
    ui.chart(fig, show, key="act_spread", anim="box")
# ================================================================ chart row 2: segment table · exercise share
col1, col2 = st.columns([1.3, 1])

with col1, ui.card("act_table"):
    tab = (judged.groupby("activity_segment")
           .agg(users=("user_id", "size"), steps=("typical_steps", "median"), mvpa=("typical_mvpa_min", "median"),
                km=("typical_distance_km", "median"), calories=("typical_calories", "median"),
                meets=("meets_activity_guideline", "sum"),
                consistent=("engagement_tier", lambda t: (t == "Consistent").sum()))
           .reindex(ui.SEGMENT_ORDER).dropna(subset=["users"]))
    rising = tab["mvpa"].is_monotonic_increasing and tab["mvpa"].iloc[-1] > tab["mvpa"].iloc[0]
    ui.card_title("Each Step Up in Segment Adds Exercise, Not Just Walking" if rising
                  else "How the Segments Compare on a Typical Day",
                  f"Typical (median) day per segment · n = {n}")
    body = "".join(
        f'<tr><td><span class="sw" style="background:{ui.SEGMENT_COLORS[s]}"></span>{s}</td>'
        f'<td>{r.users:.0f}</td><td>{r.steps:,.0f}</td><td>{r.mvpa:.0f}</td><td>{r.km:.1f}</td>'
        f'<td>{r.calories:,.0f}</td><td>{r.meets:.0f}/{r.users:.0f}</td><td>{r.consistent:.0f}/{r.users:.0f}</td></tr>'
        for s, r in tab.iterrows())
    st.html('<div class="segwrap"><table class="segtable"><thead><tr><th>Segment</th><th>Users</th><th>Steps</th>'
            '<th>MVPA min</th><th>km</th><th>kcal</th><th title="Meet the 150 MVPA min/week guideline">Guideline</th>'
            '<th title="Engagement tier = Consistent">Consistent</th></tr></thead>'
            f'<tbody>{body}</tbody></table></div>')
    with st.container(horizontal=True, horizontal_alignment="right"):
        with st.popover("Show data", icon=":material/table_view:"):
            st.dataframe(tab.round(1).reset_index().rename(columns={"activity_segment": "segment"}), hide_index=True)

with col2, ui.card("act_effort"):
    both = seg_days.dropna(subset=["mvpa_min", "active_min"])
    mix = both.groupby("activity_segment")[["mvpa_min", "active_min"]].sum().reindex(ui.SEGMENT_ORDER).dropna()
    mix["Moderate-to-vigorous"] = mix["mvpa_min"] / mix["active_min"]
    mix["Light"] = 1 - mix["Moderate-to-vigorous"]
    mix = mix.reset_index()
    top = mix.iloc[-1]
    one_in = round(1 / top["Moderate-to-vigorous"]) if top["Moderate-to-vigorous"] > 0 else None
    ui.card_title(f"{top['activity_segment'].title()} Users Spend 1 in {one_in} Active Minutes Exercising Hard"
                  if one_in else "Almost All Active Minutes Are Light Movement",
                  "Share of active minutes: moderate-to-vigorous vs light · per segment")
    fig = ui.stacked_share(mix, "activity_segment", ["Moderate-to-vigorous", "Light"],
                           {"Moderate-to-vigorous": "#C2410C", "Light": "#FAD3C0"}, list(mix["activity_segment"]))
    ui.chart(fig, mix[["activity_segment", "Moderate-to-vigorous", "Light"]].round(3)
             .rename(columns={"activity_segment": "segment"}), key="act_effort", anim="stack")
    # ================================================================ chart row 3: weekday vs weekend · effort · step-free
col1, col2 = st.columns([1.55, 1])

with col1, ui.card("act_weekend"):
    wk = judged.dropna(subset=["weekday_steps", "weekend_steps"]).sort_values("weekday_steps").copy()
    wk["who"] = "…" + wk["user_id"].str[-5:]
    more, less = int((wk["weekend_steps"] > wk["weekday_steps"]).sum()), int((wk["weekend_steps"] < wk["weekday_steps"]).sum())
    ui.card_title(f"{more} Users Move More at Weekends, {less} Move Less",
                  f"Typical steps on weekdays vs weekends, one row per user · n = {len(wk)}")
    fig = go.Figure()
    for up, color in [(True, "#F8B597"), (False, "#C9CDD4")]:          # connector lines: orange = weekend higher
        part = wk[(wk["weekend_steps"] > wk["weekday_steps"]) == up]
        xs, ys = [], []
        for _, r in part.iterrows():
            xs += [r["weekday_steps"], r["weekend_steps"], None]
            ys += [r["who"], r["who"], None]
        fig.add_scatter(x=xs, y=ys, mode="lines", line=dict(color=color, width=3), hoverinfo="skip", showlegend=False)
    fig.add_scatter(x=wk["weekday_steps"], y=wk["who"], mode="markers", name="Weekdays",
                    marker=dict(color="#9CA3AF", size=9), hovertemplate="%{y} · weekdays %{x:,.0f}<extra></extra>")
    fig.add_scatter(x=wk["weekend_steps"], y=wk["who"], mode="markers", name="Weekends",
                    marker=dict(color=ui.ORANGE, size=9), hovertemplate="%{y} · weekends %{x:,.0f}<extra></extra>")
    fig.update_yaxes(categoryorder="array", categoryarray=list(wk["who"]), tickfont=dict(size=10), title=None)
    fig.update_xaxes(tickformat="~s", title=None, rangemode="tozero")
    ui.chart(fig, wk[["who", "weekday_steps", "weekend_steps"]].round(0), key="act_weekend",
             height=max(360, 18 * len(wk) + 80), anim="draw")

with col2:
    with ui.card("act_distance"):
        km = (seg_days.groupby("activity_segment")[["very_active_km", "moderate_active_km", "light_active_km"]]
              .sum().reindex(ui.SEGMENT_ORDER).dropna())
        tot = km.sum(axis=1).replace(0, float("nan"))
        km["Very active"], km["Moderate"], km["Light"] = (km["very_active_km"] / tot, km["moderate_active_km"] / tot,
                                                          km["light_active_km"] / tot)
        km = km.dropna(subset=["Light"]).reset_index()
        easy = km.loc[km["Light"].idxmax()]
        ui.card_title(f"{easy['activity_segment'].title()} Users Cover {easy['Light']:.0%} of Their Distance at an Easy Pace",
                      "Distance by effort level · share per segment")
        fig = ui.stacked_share(km, "activity_segment", ["Very active", "Moderate", "Light"],
                               {"Very active": "#C2410C", "Moderate": "#FC5200", "Light": "#FAD3C0"},
                               list(km["activity_segment"]))
        ui.chart(fig, km[["activity_segment", "Very active", "Moderate", "Light"]].round(3)
                 .rename(columns={"activity_segment": "segment"}), key="act_distance", height=280, anim="stack")

    with ui.card("act_stepfree"):
        hrs = filters.filter_days(load("hourly_clean"))
        free = hrs[hrs["stepless_effort"]]
        ranked = profile.assign(r_steps=profile["typical_steps"].rank(ascending=False, method="min"),
                                r_mvpa=profile["typical_mvpa_min"].rank(ascending=False, method="min"))
        ui.card_title("Some Workouts Never Show Up as Steps",
                      f"{len(free)} hours of hard effort with zero steps · {free['user_id'].nunique()} users")
        if free.empty:
            st.caption("No step-free workout hours in the current filter.")
            table = pd.DataFrame(columns=["user", "step-free hours", "rank by steps", "rank by exercise"])
        else:
            per = free.groupby("user_id").agg(hours=("hour", "size"), hour=("hour", lambda h: h.mode()[0]),
                                              days=("date", "nunique"))
            per = per.join(ranked.set_index("user_id")[["r_steps", "r_mvpa"]])
            star = per.assign(gap=per["r_steps"] - per["r_mvpa"]).sort_values(["gap", "hours"]).index[-1]
            s = per.loc[star]
            when = f"{int(s['hour']) % 12 or 12} {'AM' if s['hour'] < 12 else 'PM'}"

            def nth(k):
                k = int(k)
                return f"{k}{'th' if 10 <= k % 100 <= 20 else {1: 'st', 2: 'nd', 3: 'rd'}.get(k % 10, 'th')}"

            st.html(f'<div class="stepfree"><span class="big">{nth(s["r_mvpa"])}</span><span>by exercise minutes — '
                    f'but only <b>{nth(s["r_steps"])}</b> by steps (user …{star[-5:]}, a {when} step-free workout '
                    f'on {int(s["days"])} days)</span></div>'
                    '<p class="stepfree-note">Likely swimming, cycling or gym machines. Step goals under-rate these '
                    'users → count <b>active minutes</b> too.</p>')
            table = per.reset_index().rename(columns={"user_id": "user", "hours": "step-free hours",
                                                      "r_steps": "rank by steps", "r_mvpa": "rank by exercise"})
        with st.container(horizontal=True, horizontal_alignment="right"):
            with st.popover("Show data", icon=":material/table_view:"):
                st.dataframe(table, hide_index=True)

# ================================================================ breakdown: segment → guideline → tier
with ui.card("act_breakdown"):
    b = judged.assign(guide=judged["meets_activity_guideline"].map({True: "Meets", False: "Not"}))
    top_seg = [s for s in ui.SEGMENT_ORDER if s in set(b["activity_segment"])][-1]
    top_cons = (b.loc[b["activity_segment"] == top_seg, "engagement_tier"] == "Consistent").mean()
    all_cons = (b["engagement_tier"] == "Consistent").mean()
    ui.card_title(f"Most {top_seg.title()} Users Are Also Consistent Wearers" if top_cons > all_cons and top_cons >= .5
                  else "How Segments Split by Exercise and Engagement",
                  f"Users broken down by segment → guideline → engagement tier · n = {n} · click a box to zoom in")
    ids, labels, parents, values, colors = ["All users"], ["All users"], [""], [len(b)], ["#FFE4D6"]
    for s in ui.SEGMENT_ORDER:
        bs = b[b["activity_segment"] == s]
        if bs.empty:
            continue
        ids.append(s); labels.append(s); parents.append("All users"); values.append(len(bs)); colors.append(ui.SEGMENT_COLORS[s])
        for g_, gcol in [("Meets", ui.TEAL), ("Not", "#E3E5EA")]:
            bg = bs[bs["guide"] == g_]
            if bg.empty:
                continue
            ids.append(f"{s}/{g_}"); labels.append(g_); parents.append(s); values.append(len(bg)); colors.append(gcol)
            for t in ["Consistent", "Irregular", "Barely using"]:
                k = int((bg["engagement_tier"] == t).sum())
                if k:
                    ids.append(f"{s}/{g_}/{t}"); labels.append(t); parents.append(f"{s}/{g_}"); values.append(k)
                    colors.append(ui.TIER_COLORS[t])
    light = {"#FFE4D6", "#E3E5EA", ui.SEGMENT_COLORS["Sedentary"], ui.TIER_COLORS["Barely using"]}
    fig = go.Figure(go.Icicle(ids=ids, labels=labels, parents=parents, values=values, branchvalues="total",
                              marker=dict(colors=colors, line=dict(color="#FFFFFF", width=2)),
                              textfont=dict(color=["#17191D" if c in light else "#FFFFFF" for c in colors]),
                              texttemplate="<b>%{label}</b> · %{value}", tiling=dict(orientation="v"),
                              leaf=dict(opacity=1), sort=False, hovertemplate="%{id}: %{value} users<extra></extra>"))
    fig.update_layout(margin=dict(t=10, l=0, r=0, b=0), uniformtext=dict(minsize=10, mode="hide"))
    table = (b.groupby(["activity_segment", "guide", "engagement_tier"]).size().rename("users").reset_index()
             .rename(columns={"activity_segment": "segment", "guide": "guideline", "engagement_tier": "tier"}))
    ui.chart(fig, table, key="act_breakdown", height=330,
             note="Rows: all users → activity segment → meets the exercise guideline? → engagement tier (dark = Consistent, mid = Irregular, light = Barely using) · hover tiny boxes to read them")

# ================================================================ so what?
low = judged["activity_segment"].isin(["Sedentary", "Low active"])
low_meet = int(judged.loc[low, "meets_activity_guideline"].fillna(False).sum())
mid = seg_days[seg_days["activity_segment"] == "Somewhat active"]
mid_meet = int(judged.loc[judged["activity_segment"] == "Somewhat active", "meets_activity_guideline"].fillna(False).sum())
mid_10k = f"{mid['goal_10k_met'].mean():.0%}" if len(mid) else "–"
st.html(f"""<div class="sowhat"><div class="icon">💡</div><div><h4>So what?</h4><ul>
<li><b>Sedentary + Low active ({int(low.sum())} users)</b>: {'none' if low_meet == 0 else low_meet} reach the exercise guideline
— message: small, daily walking goals.</li>
<li><b>Somewhat active ({int((judged['activity_segment'] == 'Somewhat active').sum())})</b>: {mid_meet} already meet the guideline,
but only {mid_10k} of their days reach 10K — message: "push one more day over 10K".</li>
<li>Step goals miss swimmers and gym users — show <b>active minutes</b> next to steps in goals and challenges.</li>
</ul><small>Numbers follow your filters.</small></div></div>""")