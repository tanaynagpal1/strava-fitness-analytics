"""Sleep — how does sleep tracking and sleep behaviour vary?"""
import math

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import filters
import ui
from data import load

# ================================================================ data
profile = load("user_profile")
people = profile[profile["user_id"].isin(filters.selected_users())]
nights = filters.filter_days(load("sleep_nights"))
rel = nights[nights["reliable_night"]].copy()
profiled = people[people["reliable_nights"] >= 7]                # per-user sleep profiles need 7+ nights


def after_6pm(hhmm):
    """'22:20' -> 4.33 hours after 6 PM (so a night reads left to right on one axis)."""
    h, m = map(int, str(hhmm).split(":"))
    return (h + m / 60 - 18) % 24


if rel.empty:
    ui.page_header("Sleep", "How Do Users Sleep?", "How does sleep tracking and sleep behaviour vary?")
    st.info("No reliable sleep nights match these filters. Try widening them, or press **Reset**.")
    st.stop()

in_range = (rel["sleep_category"] == "7–9 h").mean()
short = (rel["sleep_category"] == "< 6 h").mean()
head = "Half of Nights" if .45 <= in_range <= .55 else f"{in_range:.0%} of Nights"
tail = f" — but More Than 1 in {math.ceil(1 / short)} Fall Short of 6" if short > 0 else ""

# ================================================================ header + data note
ui.page_header("Sleep", f"{head} Hit 7–9 Hours{tail}", "How does sleep tracking and sleep behaviour vary?")
st.html(f'<div class="note-warn">⚠️ <b>Sleep data:</b> {int(people["tracks_sleep"].sum())} users tracked sleep; '
        f'per-user profiles use {len(profiled)} users with 7+ reliable nights.</div>')

# ================================================================ hero: one night, replayable
counts = rel.groupby("user_id").size().sort_values(ascending=False)
labels = {u: f"…{u[-5:]} · {k} nights" for u, k in counts.items()}
if st.session_state.get("sl_user") not in labels:
    st.session_state["sl_user"] = counts.index[0]
with ui.card("night"):
    c1, c2 = st.columns([1, 2], vertical_alignment="bottom")
    user = c1.selectbox("User", list(labels), format_func=labels.get, key="sl_user")
    mine = rel[rel["user_id"] == user].sort_values("date")
    dates = list(mine["date"].dt.strftime("%d %b"))
    if st.session_state.get("sl_night") not in dates:
        st.session_state["sl_night"] = dates[0]
    pick = c2.select_slider("Night (wake-up day) — drag to replay any night", dates, key="sl_night") \
        if len(dates) > 1 else dates[0]
    night = mine.iloc[dates.index(pick)]
    bed, wake = after_6pm(night["bedtime"]), after_6pm(night["wake_time"])
    wake = max(wake, bed + .25)
    ticks = "".join(f'<span style="left:{t / 18 * 100:.2f}%">{lab}</span>'
                    for t, lab in zip(range(0, 19, 3), ["6 PM", "9 PM", "Midnight", "3 AM", "6 AM", "9 AM", "Noon"]))
    stars = "".join(f'<i style="left:{x}%; top:{y}%; animation-delay:{d}s"></i>'
                    for x, y, d in [(8, 18, 0), (21, 46, .7), (33, 12, 1.4), (47, 30, .3), (58, 8, 1.1), (66, 40, 1.8),
                                    (74, 16, .5), (83, 34, 1.3), (91, 10, .9), (96, 44, 1.6)])
    with st.container(key="anim_night_sleep"):
        st.html(f'<div class="night"><div class="night-text"><p class="night-eyebrow">One night · user …{user[-5:]} · '
                f'{night["date"]:%d %b}</p><div class="night-time">{ui.clock(bed + 18)} → {ui.clock(wake + 18)}</div>'
                f'<p class="night-asleep">{night["night_hours_asleep"]:.1f} h asleep · '
                f'{night["sleep_efficiency"]:.0%} efficiency</p></div>'
                f'<div class="night-sky">{stars}<div class="moon" style="left:{(bed + wake) / 36 * 100:.1f}%"></div>'
                f'<div class="night-axis"><div class="night-bar" style="left:{bed / 18 * 100:.2f}%; '
                f'width:{(wake - bed) / 18 * 100:.2f}%"></div><div class="night-ticks">{ticks}</div></div></div></div>')

# ================================================================ KPI row (5 cards)
st.write("")
bed_typ = 18 + profiled["typical_bedtime_hrs_after_6pm"].median()
c = st.columns(5)
ui.kpi_card(c[0], "Typical night", ui.fmt_hours(rel["night_hours_asleep"].median()).replace(" m", "m").replace(" h ", "h "),
            f"median · {len(rel)} reliable nights", accent=ui.PURPLE)
ui.kpi_card(c[1], "Sleep efficiency", f"{rel['sleep_efficiency'].median():.0%}", "asleep ÷ time in bed",
            accent=ui.PURPLE, count=(round(rel["sleep_efficiency"].median() * 100), 0, "%"))
ui.kpi_card(c[2], "Nights in 7–9 h", f"{in_range:.0%}", f"{int(round(in_range * len(rel)))} of {len(rel)}",
            accent=ui.PURPLE, count=(round(in_range * 100), 0, "%"))
ui.kpi_card(c[3], "Nights under 6 h", f"{short:.0%}", f"{int(round(short * len(rel)))} of {len(rel)}",
            accent="#D9534F", count=(round(short * 100), 0, "%"))
ui.kpi_card(c[4], "Typical bedtime", ui.clock(bed_typ), f"{len(profiled)} users with 7+ nights", accent=ui.PURPLE)
# ================================================================ row: hours-asleep histogram · sleep categories
st.write("")
col1, col2 = st.columns([1.6, 1])

with col1, ui.card("sl_hist"):
    hours = rel["night_hours_asleep"]
    q1, q3 = (round(hours.quantile(q) * 2) / 2 for q in (.25, .75))
    ui.card_title(f"Most Nights Cluster Between {q1:g} and {q3:g} Hours",
                  f"Nights by hours asleep (half-hour bins) · middle half of nights in that range · "
                  f"{len(rel)} reliable nights · {rel['user_id'].nunique()} users")
    bins = (hours * 2).apply(math.floor) / 2                          # 7.0 = 7:00–7:29 asleep
    hist = bins.value_counts().sort_index().rename("nights").rename_axis("from_hours").reset_index()
    hist["band"] = hist["from_hours"].between(7, 8.5).map({True: "Within 7–9 h", False: "Outside"})
    fig = go.Figure()
    fig.add_vrect(x0=7, x1=9, fillcolor="#EDE7FB", line_width=0, layer="below",
                  annotation_text="<b>Recommended 7–9 h</b>", annotation_position="top",
                  annotation_font=dict(color="#6D4FC4", size=11))
    for band, color in [("Within 7–9 h", "#6D4FC4"), ("Outside", "#B9A8EC")]:
        part = hist[hist["band"] == band]
        fig.add_bar(x=part["from_hours"] + .25, y=part["nights"], width=.45, name=band, marker_color=color,
                    customdata=[f"{h:g}–{h + .5:g} h" for h in part["from_hours"]],
                    hovertemplate="%{customdata} asleep · %{y} nights<extra></extra>")
    fig.update_xaxes(dtick=1, title=None)
    fig.update_yaxes(title=None, range=[0, hist["nights"].max() * 1.18])
    fig.update_layout(legend=dict(traceorder="normal"))
    ui.chart(fig, hist, key="sl_hist", height=340, anim="rise")

with col2, ui.card("sl_cats"):
    order = ["< 6 h", "6–7 h", "7–9 h", "> 9 h"]
    cats = (rel["sleep_category"].value_counts().reindex(order, fill_value=0)
            .rename("nights").rename_axis("length").reset_index())
    cats["share"] = cats["nights"] / max(len(rel), 1)
    cats["label"] = cats["nights"].astype(str) + " (" + cats["share"].map("{:.0%}".format) + ")"
    cats["legend"] = cats["length"].map({"< 6 h": "Short", "7–9 h": "Recommended"}).fillna("Other")
    cats["show_legend"], cats["rank"] = False, range(4)
    ui.card_title(f"More Than 1 in {math.ceil(1 / short)} Nights Are Under 6 Hours" if short > 0
                  else "No Nights Under 6 Hours",
                  f"Nights per sleep category · n = {len(rel)}")
    ui.chart(ui.track_bars(cats, "length", "nights",
                           {"Short": "#E58A8A", "Recommended": "#6D4FC4", "Other": "#B9A8EC"}, room=1.45),
             cats[["length", "nights", "share"]], key="sl_cats", height=340, anim="grow")
# ================================================================ row: one user's nights · efficiency per user
TICKS = dict(tickvals=list(range(0, 19, 3)), ticktext=["6 PM", "9 PM", "12 AM", "3 AM", "6 AM", "9 AM", "12 PM"])
col1, col2 = st.columns([1.6, 1])

with col1, ui.card("sl_timeline"):
    tl = mine.assign(bed=mine["bedtime"].map(after_6pm), wake=mine["wake_time"].map(after_6pm),
                     day=mine["date"].dt.strftime("%d %b"))
    tl["wake"] = tl["wake"].where(tl["wake"] > tl["bed"], tl["bed"] + .25)      # keep every bar at least 15 min wide
    lo, hi = (round(tl["bed"].quantile(q)) for q in (.1, .9))
    ui.card_title(f"User …{user[-5:]} Goes to Bed Between {ui.hour_label(lo + 18)} and {ui.hour_label(hi + 18)}",
                  f"Each night from bedtime to wake-up · {len(tl)} reliable nights · 8 in 10 bedtimes in that window · "
                  "pick another user or night in the box at the top")
    fig = go.Figure()
    for chosen, color in [(False, "#B9A8EC"), (True, "#5B3FB0")]:
        part = tl[(tl["day"] == pick) == chosen]
        fig.add_bar(y=part["day"], x=part["wake"] - part["bed"], base=part["bed"], orientation="h",
                    marker=dict(color=color, line=dict(color="#17191D" if chosen else color, width=1.5 if chosen else 0)),
                    name="Selected night" if chosen else "Other nights", showlegend=False,
                    customdata=list(zip(part["bedtime"], part["wake_time"], part["night_hours_asleep"])),
                    hovertemplate="%{y}: %{customdata[0]} → %{customdata[1]} · %{customdata[2]:.1f} h asleep<extra></extra>")
    fig.update_layout(bargap=.35)
    fig.update_xaxes(range=[0, 18], **TICKS)
    fig.update_yaxes(categoryorder="array", categoryarray=list(tl["day"])[::-1], tickfont=dict(size=9), title=None)
    ui.chart(fig, tl[["day", "bedtime", "wake_time", "night_hours_asleep"]], key="sl_timeline",
             height=max(340, 14 * len(tl) + 80), anim="stack")

with col2, ui.card("sl_eff"):
    eff = (rel[rel["user_id"].isin(profiled["user_id"])].groupby("user_id")["sleep_efficiency"]
           .quantile([.25, .5, .75]).unstack().rename(columns={.25: "q1", .5: "median", .75: "q3"})
           .sort_values("median"))
    eff["who"] = "…" + eff.index.str[-5:]
    low_eff = int((eff["median"] < .85).sum())
    word = {0: None, 1: "One User Is"}.get(low_eff, f"{low_eff} Users Are")
    ui.card_title(f"{word} Restless in Bed Most Nights" if word else "Everyone Sleeps Efficiently Most Nights",
                  f"Sleep efficiency per user · dot = median, bar = middle 50% · red = below 85% · {len(eff)} users")
    xs, ys = [], []
    for _, r in eff.iterrows():
        xs += [r["q1"] * 100, r["q3"] * 100, None]
        ys += [r["who"], r["who"], None]
    fig = go.Figure()
    fig.add_scatter(x=xs, y=ys, mode="lines", line=dict(color="#D5CBF4", width=7), hoverinfo="skip", showlegend=False)
    fig.add_scatter(x=eff["median"] * 100, y=eff["who"], mode="markers", showlegend=False,
                    marker=dict(size=10, color=["#D9534F" if v < .85 else "#6D4FC4" for v in eff["median"]]),
                    hovertemplate="%{y} · median %{x:.0f}%<extra></extra>")
    fig.update_xaxes(ticksuffix="%", range=[min(50, eff["q1"].min() * 100 - 3) if len(eff) else 50, 100])
    fig.update_yaxes(categoryorder="array", categoryarray=list(eff["who"])[::-1], tickfont=dict(size=10), title=None)
    ui.chart(fig, eff[["who", "q1", "median", "q3"]].round(3), key="sl_eff",
             height=max(340, 14 * len(tl) + 80), anim="draw")

# ================================================================ row: weekend lie-ins · naps · activity → sleep
col1, col2, col3 = st.columns([.85, 1, 1.25])

with col1, ui.card("sl_weekend"):
    wk = (rel.groupby("is_weekend_morning")["night_hours_asleep"].agg(["median", "size"])
          .reindex([False, True]).rename(index={False: "Weekday", True: "Weekend"}))
    gain = (wk.loc["Weekend", "median"] - wk.loc["Weekday", "median"]) * 60 if wk["median"].notna().all() else float("nan")
    ui.card_title(f"Weekend Lie-Ins Add About {round(gain / 5) * 5:.0f} Minutes" if gain >= 5
                  else "No Real Weekend Lie-In",
                  f"Median hours asleep · {int(wk['size'].fillna(0).iloc[0])} weekday vs "
                  f"{int(wk['size'].fillna(0).iloc[1])} weekend nights")
    fig = go.Figure(go.Bar(x=wk.index, y=wk["median"], marker_color=["#B9A8EC", "#6D4FC4"],
                           text=[f"{v:.1f} h" if pd.notna(v) else "" for v in wk["median"]], textposition="outside",
                           hovertemplate="%{x}: %{y:.2f} h<extra></extra>"))
    fig.update_yaxes(range=[0, (wk["median"].max() or 8) * 1.2], ticksuffix=" h")
    fig.update_layout(bargap=.25)
    ui.chart(fig, wk.reset_index().rename(columns={"is_weekend_morning": "night", "size": "nights"}).round(2),
             key="sl_weekend", height=300, anim="rise")

with col2, ui.card("sl_naps"):
    nap = nights.groupby("user_id")["took_nap"].agg(rate="mean", days="size")
    nap = nap[(nap["days"] >= 7) & (nap["rate"] > 0)].sort_values("rate", ascending=False).reset_index()
    nap["who"] = "…" + nap["user_id"].str[-5:]
    if nap.empty:
        ui.card_title("No Regular Nappers in This Selection", "Share of sleep days with a nap · users with 7+ sleep days")
        st.caption("Nobody with 7+ tracked sleep days took a nap in the current filter.")
    else:
        ui.card_title(f"{len(nap)} Users Nap; the Most Frequent Nap on 1 in {round(1 / nap['rate'].iloc[0])} Days",
                      "Share of sleep days with a nap · users with 7+ sleep days who napped at least once")
        nap["pct"], nap["label"] = nap["rate"] * 100, nap["rate"].map("{:.0%}".format)
        nap["legend"], nap["show_legend"], nap["rank"] = "Nap days", False, range(len(nap))
        ui.chart(ui.track_bars(nap, "who", "pct", {"Nap days": "#6D4FC4"}, room=1.35),
                 nap[["who", "rate", "days"]].round(3), key="sl_naps", height=300, anim="grow")

with col3, ui.card("sl_active"):
    dm = filters.filter_days(load("daily_master"))
    x = dm[dm["sleep_tonight_reliable_night"] == True].copy()       # noqa: E712  (column may hold NaN)
    x["more_active"] = x["steps"] > x.groupby("user_id")["steps"].transform("median")
    g = x.groupby(["user_id", "more_active"]).agg(n=("steps", "size"), h=("sleep_tonight_night_hours_asleep", "median")).unstack()
    if g.empty or ("n", True) not in g or ("n", False) not in g:
        g = pd.DataFrame()
    else:
        g = g[(g[("n", True)] >= 3) & (g[("n", False)] >= 3)]
    if g.empty:
        ui.card_title("Activity and Sleep", "Not enough nights in this selection to compare each user with themselves")
        st.caption("Each user needs 3+ nights after quieter days and 3+ after more active days.")
    else:
        pair = pd.DataFrame({"quiet": g[("h", False)], "active": g[("h", True)]})
        pair["diff_min"] = (pair["active"] - pair["quiet"]) * 60
        pair = pair.sort_values("diff_min").reset_index()
        pair["who"] = "…" + pair["user_id"].str[-5:]
        longer, med = int((pair["diff_min"] > 0).sum()), pair["diff_min"].median()
        ui.card_title(f"{longer} of {len(pair)} Users Sleep a Little Longer After More Active Days"
                      if longer > len(pair) / 2 and med > 0 else "No Clear Link Between Active Days and Sleep Length",
                      f"Each user compared with themselves · median difference {med:+.0f} min · linked with, not caused by")
        xs, ys = [], []
        for _, r in pair.iterrows():
            xs += [r["quiet"], r["active"], None]
            ys += [r["who"], r["who"], None]
        fig = go.Figure()
        fig.add_scatter(x=xs, y=ys, mode="lines", line=dict(color="#D5CBF4", width=3), hoverinfo="skip", showlegend=False)
        fig.add_scatter(x=pair["quiet"], y=pair["who"], mode="markers", name="After quieter days",
                        marker=dict(size=9, color="#9CA3AF"), hovertemplate="%{y} · quieter days: %{x:.1f} h<extra></extra>")
        fig.add_scatter(x=pair["active"], y=pair["who"], mode="markers", name="After more active days",
                        marker=dict(size=9, color="#6D4FC4"), hovertemplate="%{y} · more active days: %{x:.1f} h<extra></extra>")
        fig.update_xaxes(ticksuffix=" h")
        fig.update_yaxes(categoryorder="array", categoryarray=list(pair["who"]), tickfont=dict(size=10), title=None)
        ui.chart(fig, pair[["who", "quiet", "active", "diff_min"]].round(2), key="sl_active", height=300, anim="draw")

# ================================================================ so what?
st.html(f"""<div class="sowhat"><div class="icon">💡</div><div><h4>So what?</h4><ul>
<li>Target the <b>{short:.0%} of short nights</b> with a gentle wind-down reminder ~30 min before each user's typical bedtime.</li>
<li>Irregular bedtimes and frequent naps are good hooks for the <b>sleep-tracking feature</b>.</li>
<li>More active days are only <i>linked</i> with slightly longer sleep — a soft "move more, sleep better" story, not a promise.</li>
</ul><small>Numbers follow your filters.</small></div></div>""")