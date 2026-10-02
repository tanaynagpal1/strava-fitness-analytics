"""User Explorer — what does an individual user's behaviour look like?"""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import filters
import ui
from data import load

# ================================================================ data
profile = load("user_profile")
people = profile[profile["user_id"].isin(filters.selected_users())]
days_all = filters.filter_days(load("daily_master"))
wear = filters.filter_days(load("wear_log"))
DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
ICON = {"Committed Movers": "🏆", "On-and-Off Movers": "🔁", "Daily Strollers": "🚶",
        "Slipping Starters": "📉", "Fading Users": "💤"}

ui.page_header("User Explorer", "Drill Into One User and Compare Them With the Group",
               "What does an individual user's behaviour look like?")
if people.empty or days_all.empty:
    st.info("No users or days match these filters. Try widening them, or press **Reset**.")
    st.stop()

# ================================================================ user chooser
order = people.sort_values("clean_days", ascending=False)
labels = {r.user_id: f"User …{r.user_id[-5:]} · {r.activity_segment if pd.notna(r.activity_segment) else 'Too little data'}"
                     f" · {r.engagement_tier} · {r.persona}" for r in order.itertuples()}
with st.container(border=True, key="card_ux_pick"):
    c0, c1, c2 = st.columns([1, 1.4, 1.5], vertical_alignment="bottom")
    query = c0.text_input("Search by user ID", placeholder="e.g. 8378563200 or 63200", key="ux_query",
                          help="Type all or part of a user ID — the list on the right narrows to matching users.")
    query = "".join(ch for ch in query if ch.isdigit())                  # ignore spaces, dots and the "…"
    options = [u for u in labels if query in u] if query else list(labels)
    no_match = bool(query) and not options
    if no_match:
        c2.warning(f"No user ID contains **{query}** in the current filter — showing everyone.")
        options = list(labels)
    if st.session_state.get("ux_user") not in options:
        st.session_state["ux_user"] = options[0]
    user = c1.selectbox(f"Choose a user ({len(options)} match{'es' if len(options) != 1 else ''})", options,
                        format_func=labels.get, key="ux_user")
    if not no_match:
        c2.caption("Their data is highlighted; the group median (everyone in the current filter) is shown in grey. "
                   "Users are sorted by clean days, most first. You can also type inside the list to search.")

me = profile.set_index("user_id").loc[user]
mine = days_all[days_all["user_id"] == user].sort_values("date")
st.write("")
col1, col2, col3 = st.columns([1, 1, 1.2])

# ---------------------------------------------------------------- profile card
with col1, ui.card("ux_profile"):
    seg, tier, trend = me["activity_segment"], me["engagement_tier"], me["activity_trend"]
    if pd.isna(seg):
        title = "A User With Too Little Data for a Full Profile"
    else:
        habit = {"Consistent": "Consistent", "Irregular": "Irregular", "Barely using": "Rarely-Worn"}[tier]
        move = {"Falling": "Is Slowing Down", "Rising": "Is Picking Up", "Stable": "Holds Steady"}.get(trend, "")
        article = "An" if seg[0] in "AEIOU" else "A"
        title = f"{article} {seg.title()}, {habit} Wearer Who {move}".strip()
    ui.card_title(title, "Profile card · from user_profile")
    color = ui.PERSONA_COLORS.get(me["persona"], ui.ORANGE)
    sleep_txt = (f"{me['typical_sleep_hours']:.1f} h · {int(me['reliable_nights'])} nights"
                 if pd.notna(me["typical_sleep_hours"]) else
                 f"no profile ({int(me['reliable_nights'])} reliable nights)" if me["tracks_sleep"] else "not tracked")
    feats = [f for f, on in [("sleep", me["tracks_sleep"]), ("weight", me["logs_weight"]),
                             ("workouts", me["logs_workouts"])] if on]
    rows = [("Persona", me["persona"]),
            ("Typical steps", f"{me['typical_steps']:,.0f}" if pd.notna(me["typical_steps"]) else "–"),
            ("Typical exercise (MVPA)", f"{me['typical_mvpa_min']:.0f} min" if pd.notna(me["typical_mvpa_min"]) else "–"),
            ("Activity trend", {"Falling": "Falling (2nd half lower)", "Rising": "Rising (2nd half higher)",
                                "Stable": "Stable"}.get(trend, "–")),
            ("Week pattern", me["week_pattern"] if pd.notna(me["week_pattern"]) else "–"),
            ("Typical sleep", sleep_txt),
            ("Optional features", f"{len(feats)} ({', '.join(feats)})" if feats else "0")]
    st.html(f'<div class="ux-head"><div class="ux-badge" style="background:{color}" title="{me["persona"]}">{ICON.get(me["persona"], "👤")}</div>'
            f'<div><div class="pc-name">User …{user[-5:]}</div><div class="pc-rule">'
            f'{seg if pd.notna(seg) else "Too little data"} · {tier} · {int(me["clean_days"])} clean days</div></div></div>'
            '<div class="ux-rows">' + "".join(f"<div><span>{k}</span><b>{v}</b></div>" for k, v in rows) + "</div>")
    with st.container(horizontal=True, horizontal_alignment="right"):
        with st.popover("Show data", icon=":material/table_view:"):
            st.dataframe(me.rename("value").astype(str).reset_index().rename(columns={"index": "field"}), hide_index=True)

# ---------------------------------------------------------------- calendar: steps per day
with col2, ui.card("ux_calendar"):
    cal = wear[wear["user_id"] == user][["date", "wear_status"]].merge(mine[["date", "steps"]], on="date", how="left")
    if cal.empty:
        ui.card_title("No Days in This Selection", "Daily steps, one square per day")
    else:
        cal["dow"] = cal["date"].dt.dayofweek
        cal["week"] = ((cal["date"] - pd.Timestamp(filters.START)).dt.days // 7) + 1
        by_dow = mine.groupby(mine["date"].dt.dayofweek)["steps"].median().sort_values(ascending=False)
        best = [DAYS[d] for d in by_dow.index[:2]]
        ui.card_title(f"Biggest Days Fall on {best[0]}s and {best[1]}s" if len(best) == 2
                      else "Daily Steps Through the Month",
                      "Daily steps, one square per day · columns = weeks · grey = no clean data (removed or not worn)")
        grid = cal.pivot_table(index="dow", columns="week", values="steps", aggfunc="first").reindex(range(7))
        seen = cal.pivot_table(index="dow", columns="week", values="date", aggfunc="first").reindex(range(7))
        fig = go.Figure()
        fig.add_heatmap(z=seen.notna().astype(float).where(seen.notna()).values, x=[f"Wk {w}" for w in seen.columns],
                        y=[d[:3] for d in DAYS], colorscale=[[0, "#EEF0F3"], [1, "#EEF0F3"]], showscale=False,
                        xgap=5, ygap=5, hoverinfo="skip")
        fig.add_heatmap(z=grid.values, x=[f"Wk {w}" for w in grid.columns], y=[d[:3] for d in DAYS], xgap=5, ygap=5,
                        colorscale=[[0, "#FFE4D6"], [.5, "#FC7A3A"], [1, "#9A3412"]], zmin=0, zmax=18_000,
                        colorbar=dict(thickness=8, len=.8, tickformat="~s", outlinewidth=0, title=dict(text="steps", side="top")),
                        customdata=seen.map(lambda d: f"{d:%a %d %b}" if pd.notna(d) else "").values,
                        hovertemplate="%{customdata}: %{z:,.0f} steps<extra></extra>")
        fig.update_yaxes(autorange="reversed", title=None)
        table = cal[["date", "wear_status", "steps"]]
        ui.chart(fig, table, key="ux_calendar", height=320, anim="wipe")

# ---------------------------------------------------------------- user vs group median, with a day picker
with col3, ui.card("ux_line"):
    group = days_all.groupby("date")["steps"].median().rename("group_median")
    both = mine[["date", "steps"]].merge(group.reset_index(), on="date", how="left")
    if both.empty:
        ui.card_title("No Clean Days in This Selection", "Daily steps: user vs group median")
    else:
        above = (both["steps"] > both["group_median"]).mean()
        ui.card_title(f"{'Above' if above >= .5 else 'Below'} the Group Median on {max(above, 1 - above):.0%} of Days",
                      "Daily steps: user vs group median · drag the slider to inspect a day")
        dates = list(both["date"].dt.strftime("%a %d %b"))
        if st.session_state.get("ux_day") not in dates:
            st.session_state["ux_day"] = dates[len(dates) // 2]
        day = st.select_slider("Day", dates, key="ux_day", label_visibility="collapsed") if len(dates) > 1 else dates[0]
        row = both.iloc[dates.index(day)]
        fig = go.Figure()
        fig.add_scatter(x=group.index, y=group.values, mode="lines", name="Group median", line=dict(color="#9CA3AF", width=2),
                        hovertemplate="%{x|%d %b}: group %{y:,.0f}<extra></extra>")
        fig.add_scatter(x=both["date"], y=both["steps"], mode="lines", name=f"User …{user[-5:]}",
                        line=dict(color=ui.ORANGE, width=2.5), hovertemplate="%{x|%d %b}: %{y:,.0f} steps<extra></extra>")
        fig.add_vline(x=row["date"], line=dict(color="#17191D", width=1, dash="dot"))
        fig.add_scatter(x=[row["date"]], y=[row["steps"]], mode="markers", showlegend=False, hoverinfo="skip",
                        marker=dict(size=11, color=ui.ORANGE, line=dict(color="#FFFFFF", width=2)))
        fig.update_yaxes(rangemode="tozero", tickformat=",")
        fig.update_xaxes(tickformat="%d %b")
        st.html(f'<p class="ux-day"><b>{day}:</b> {row["steps"]:,.0f} steps vs group median {row["group_median"]:,.0f}</p>')
        ui.chart(fig, both.round({"steps": 0, "group_median": 0}), key="ux_line", height=280, anim="draw")

# ================================================================ sleep: every reliable night of this user
with ui.card("ux_sleep"):
    nights = filters.filter_days(load("sleep_nights"))
    sl = nights[(nights["user_id"] == user) & nights["reliable_night"]].sort_values("date")
    if sl.empty:
        ui.card_title("No Reliable Sleep Nights for This User",
                      "This user didn't track sleep, or no tracked night passed the reliability checks in this filter")
    else:
        typical = sl["night_hours_asleep"].median()
        in_range = sl["sleep_category"].eq("7–9 h").sum()
        ui.card_title(f"Sleep Holds Near {round(typical * 2) / 2:g} Hours — {in_range} of {len(sl)} Nights in the 7–9 h Range",
                      f"Hours asleep per reliable night · {len(sl)} nights · group typical night shown as a dashed line")
        st.html(f'<div class="chips"><span><i style="background:#6D4FC4"></i>7–9 h</span>'
                '<span><i style="background:#B9A8EC"></i>Other lengths</span></div>')
        group_typ = nights.loc[nights["reliable_night"], "night_hours_asleep"].median()
        fig = go.Figure(go.Bar(x=sl["date"], y=sl["night_hours_asleep"],
                               marker_color=["#6D4FC4" if c == "7–9 h" else "#B9A8EC" for c in sl["sleep_category"]],
                               customdata=sl["bedtime"] + " → " + sl["wake_time"],
                               hovertemplate="%{x|%a %d %b}: %{y:.1f} h asleep · %{customdata}<extra></extra>"))
        fig.add_hline(y=group_typ, line=dict(color="#17191D", width=1, dash="dash"),
                      annotation_text=f"group typical {group_typ:.1f} h", annotation_position="top left",
                      annotation_font=dict(size=11, color="#4B5563"))
        fig.update_yaxes(ticksuffix=" h", range=[0, max(12, sl["night_hours_asleep"].max() + 1)])
        fig.update_xaxes(tickformat="%d %b")
        fig.update_layout(bargap=.18)
        ui.chart(fig, sl[["date", "bedtime", "wake_time", "night_hours_asleep", "sleep_category"]], key="ux_sleep",
                 height=300, anim="rise")

# ================================================================ so what?
persona = me["persona"]
st.html(f"""<div class="sowhat"><div class="icon">💡</div><div><h4>So what?</h4><ul>
<li>Use this page to sanity-check the personas: does this <b>{persona}</b> really look like one, day by day?</li>
<li>Spot the moments a nudge would have helped — a quiet week, a gap in wearing, or a run of short nights.</li>
</ul><small>Numbers follow your filters.</small></div></div>""")