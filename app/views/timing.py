"""Timing — when are users most active?"""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

import filters
import ui
from data import load

# ================================================================ data
profile = load("user_profile")
people = profile[profile["user_id"].isin(filters.selected_users())]
hrs = filters.filter_days(load("hourly_clean"))
n_days = hrs.groupby(["user_id", "date"]).ngroups

if hrs.empty:
    ui.page_header("Timing", "When Are Users Most Active?", "When are users most active?")
    st.info("No days match these filters. Try widening them, or press **Reset**.")
    st.stop()

by_hour = hrs.groupby("hour")["steps"].mean().reindex(range(24), fill_value=0)
peak = int(by_hour.idxmax())
win_end = int(by_hour.rolling(3).sum().idxmax())                # busiest 3 hours in a row
prefs = people["preferred_workout_time"].value_counts()
mornings_win = prefs.get("Morning", 0) == prefs.drop("No workouts", errors="ignore").max()

# ================================================================ header
ui.page_header("Timing",
               f"The Day Builds to a {ui.hour_label(peak)} Peak"
               + (" — Mornings Are the Second Window" if mornings_win else ""),
               "When are users most active?")

# ================================================================ hero: 24-hour rhythm
with ui.card("rhythm"):
    top = by_hour.max() or 1
    bars = "".join(
        f'<div class="rb{" peak" if h == peak else " near" if abs(h - peak) == 1 else ""}" '
        f'style="--h:{max(v / top * 100, 2):.0f}%; --d:{h * 35}ms" title="{ui.hour_label(h)} · {v:,.0f} steps/hour"></div>'
        for h, v in by_hour.items())
    ticks = "".join(f'<span>{ui.hour_label(h).replace(" AM", "a").replace(" PM", "p") if h % 3 == 0 else ""}</span>'
                    for h in range(24))
    with st.container(key="anim_rhythm_timing"):
        st.html(f'<div class="rhythm"><div><p class="pick-eyebrow">Activity rhythm</p>'
                f'<div class="rh-title">Energy Builds All Day and Peaks at {ui.hour_label(peak)}</div>'
                f'<p class="rh-sub">Average steps per hour across {n_days:,} valid days. '
                f'The {ui.hour_label(peak)} bar pulses.</p></div>'
                f'<div><div class="rh-bars">{bars}</div><div class="rh-ticks">{ticks}</div></div></div>')

# ================================================================ KPI row (5 cards)
st.write("")
sleepers = people.dropna(subset=["typical_wake_time"])
wake = sleepers["typical_wake_time"].map(ui.to_hours).astype(float).median()
bed = 18 + people["typical_bedtime_hrs_after_6pm"].median()
first, last = ui.hour_label(win_end - 2), ui.hour_label(win_end)
window = f"{first.split()[0]}–{last}" if first[-2:] == last[-2:] else f"{first}–{last}"
c = st.columns(5)
ui.kpi_card(c[0], "Peak hour", ui.hour_label(peak), f"{by_hour[peak]:,.0f} steps/hour on average")
ui.kpi_card(c[1], "Busiest window", window, "3 highest hours in a row")
ui.kpi_card(c[2], "Typical wake-up", ui.clock(wake), f"{len(sleepers)} sleep users", accent=ui.PURPLE)
ui.kpi_card(c[3], "Typical bedtime", ui.clock(bed), f"{len(sleepers)} sleep users", accent=ui.PURPLE)
ui.kpi_card(c[4], "Morning exercisers", f"{prefs.get('Morning', 0)} of {len(people)}",
            "most workout hours before noon", count=(int(prefs.get("Morning", 0)), 0, f" of {len(people)}"))

# ================================================================ row: 24-hour clock · day × hour heatmap
DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def period(h):
    return "Morning" if 5 <= h < 12 else "Afternoon" if 12 <= h < 17 else "Evening" if 17 <= h < 22 else "Night"


st.write("")
col1, col2 = st.columns([1, 1.45])

with col1, ui.card("tim_clock"):
    ui.card_title(f"The 24-Hour Clock Stops at {ui.hour_label(peak)}",
                  f"Average steps per hour around the day · {n_days:,} days · the hand points to the peak")
    fig = go.Figure()
    groups = [(f"Peak {ui.hour_label(peak)}", [peak], ui.ORANGE),
              (f"{ui.hour_label(peak - 1)} & {ui.hour_label(peak + 1)}", [(peak - 1) % 24, (peak + 1) % 24], "#F8B597"),
              ("Other hours", [h for h in range(24) if abs(h - peak) not in (0, 1, 23)], "#CBD5E8")]
    for name, hours, color in groups:
        fig.add_barpolar(r=[by_hour[h] for h in hours], theta=[h * 15 for h in hours], width=[14] * len(hours),
                         name=name, marker_color=color, marker_line_width=0,
                         customdata=[ui.hour_label(h) for h in hours],
                         hovertemplate="%{customdata} · %{r:,.0f} steps/hour<extra></extra>")
    fig.add_scatterpolar(r=[0, by_hour[peak] * .95], theta=[peak * 15] * 2, mode="lines+markers", showlegend=False,
                         line=dict(color="#17191D", width=3), marker=dict(size=[10, 0], color="#17191D"),
                         hoverinfo="skip")
    fig.update_layout(polar=dict(hole=.22, bgcolor="rgba(0,0,0,0)", domain=dict(x=[.1, .9], y=[.06, .9]),
                                 radialaxis=dict(visible=False, range=[0, by_hour.max() * 1.05]),
                                 angularaxis=dict(rotation=90, direction="clockwise", tickmode="array",
                                                  tickvals=[0, 90, 180, 270], ticktext=["Midnight", "6 AM", "Noon", "6 PM"],
                                                  showgrid=False, linecolor="#E6E8EC", tickfont=dict(size=11))),
                      legend=dict(traceorder="normal"))
    clock = by_hour.rename("avg_steps").rename_axis("hour").reset_index().round(0)
    ui.chart(fig, clock, key="tim_clock", height=420, anim="clock")

with col2, ui.card("tim_heat"):
    heat = (hrs.pivot_table(index="day_of_week", columns="hour", values="steps", aggfunc="mean")
            .reindex([d for d in DAYS if d in set(hrs["day_of_week"])]).reindex(columns=range(24)))
    top_day, top_hour = heat.stack().idxmax()
    weekday_peaks = heat.loc[[d for d in DAYS[:5] if d in heat.index]].idxmax(axis=1)
    evenings = len(weekday_peaks) and (weekday_peaks >= 17).mean() >= .5
    if top_day in ("Saturday", "Sunday") and period(top_hour) != "Evening" and evenings:
        title = f"{top_day} {period(top_hour)}s and Weekday Evenings Are the Hot Spots"
    else:
        title = f"The Busiest Slot Is {top_day} at {ui.hour_label(top_hour)}"
    ui.card_title(title, f"Average steps per hour · day of week × hour · {n_days:,} days · darkest box = busiest slot")
    fig = go.Figure(go.Heatmap(z=heat.values, x=list(range(24)), y=[d[:3] for d in heat.index], xgap=3, ygap=3,
                               colorscale=[[0, "#FFF4EE"], [.35, "#FDC3A5"], [.65, "#FC7A3A"], [1, "#9A3412"]],
                               colorbar=dict(title=dict(text="steps/hr", side="top"), thickness=10, len=.9,
                                             outlinewidth=0),
                               customdata=[[ui.hour_label(h) for h in range(24)]] * len(heat),
                               hovertemplate="%{y} %{customdata} · %{z:,.0f} steps/hour<extra></extra>"))
    yi = [d[:3] for d in heat.index].index(top_day[:3])
    fig.add_shape(type="rect", x0=top_hour - .5, x1=top_hour + .5, y0=yi - .5, y1=yi + .5,
                  line=dict(color="#17191D", width=2.5))
    fig.update_xaxes(tickvals=[0, 3, 6, 9, 12, 15, 18, 21], ticktext=["12a", "3a", "6a", "9a", "12p", "3p", "6p", "9p"],
                     showgrid=False)
    fig.update_yaxes(autorange="reversed", showgrid=False, title=None)
    table = heat.round(0).reset_index().rename(columns={"day_of_week": "day"})
    table.columns = [str(c) for c in table.columns]
    ui.chart(fig, table, key="tim_heat", height=420, anim="wipe")

    # ================================================================ row: hourly line · preferred workout time
col1, col2 = st.columns([1.45, 1])

with col1, ui.card("tim_line"):
    start = next((h for h in range(4, 24) if by_hour[h] >= .25 * by_hour.max()), 6)
    falls = by_hour.diff(-1).loc[peak:22]                          # fall from each hour to the next
    drop = int(falls.idxmax()) + 1 if len(falls) else peak + 1
    ui.card_title(f"Activity Climbs From {ui.hour_label(start)} and Drops Sharply at {ui.hour_label(drop)}",
                  f"Average steps per hour · hover any point · n = {n_days:,} days")
    fig = go.Figure(go.Scatter(x=list(range(24)), y=by_hour.values, mode="lines+markers", fill="tozeroy",
                               line=dict(color=ui.ORANGE, width=2.5), marker=dict(size=6),
                               fillcolor="rgba(252,82,0,.10)", customdata=[ui.hour_label(h) for h in range(24)],
                               hovertemplate="%{customdata} · %{y:,.0f} steps/hour<extra></extra>"))
    fig.add_vline(x=peak, line=dict(color="#17191D", width=1, dash="dot"))
    fig.add_annotation(x=peak, y=by_hour[peak], text=f"<b>{ui.hour_label(peak)}</b> · {by_hour[peak]:,.0f} steps/hour",
                       showarrow=False, yshift=18, bgcolor="#17191D", font=dict(color="#FFFFFF", size=11), borderpad=4)
    fig.update_xaxes(tickvals=list(range(0, 24, 2)),
                     ticktext=[ui.hour_label(h).replace(" AM", "a").replace(" PM", "p") for h in range(0, 24, 2)])
    fig.update_yaxes(rangemode="tozero", tickformat=",", range=[0, by_hour.max() * 1.25])
    ui.chart(fig, by_hour.rename("avg_steps").rename_axis("hour").reset_index().round(0), key="tim_line",
             height=340, anim="draw")

with col2, ui.card("tim_pref"):
    order = ["Morning", "Afternoon", "Evening", "Late", "Night", "No workouts"]
    pref = (people["preferred_workout_time"].value_counts().reindex(order, fill_value=0)
            .rename("people").rename_axis("slot").reset_index())
    pref = pref[(pref["people"] > 0) | pref["slot"].isin(["Morning", "Afternoon", "Evening", "Late"])]
    pref["share"] = pref["people"] / max(len(people), 1)
    pref["label"] = pref["people"].astype(str) + " (" + pref["share"].map("{:.0%}".format) + ")"
    best = pref[pref["slot"] != "No workouts"].sort_values("people").iloc[-1]
    pref["legend"] = ["Top slot" if s == best["slot"] else "No workouts" if s == "No workouts" else "Other slots"
                      for s in pref["slot"]]
    pref["show_legend"], pref["rank"] = False, range(len(pref))
    when = {"Morning": "Before Noon", "Afternoon": "in the Afternoon", "Evening": "in the Evening",
            "Late": "Late at Night", "Night": "Overnight"}[best["slot"]]
    ui.card_title(f"{best['slot']}s Win: {best['people']} Users Do Most Workouts {when}",
                  f"Time of day with the most workout hours, per user · n = {len(people)}")
    ui.chart(ui.track_bars(pref, "slot", "people",
                           {"Top slot": ui.ORANGE, "Other slots": "#F8B597", "No workouts": "#C9CDD4"}, room=1.45),
             pref[["slot", "people", "share"]], key="tim_pref", height=340, anim="grow")

# ================================================================ small multiples: hourly shape per segment
with ui.card("tim_segments"):
    seg_h = hrs.merge(profile.loc[~profile["low_data_user"], ["user_id", "activity_segment"]], on="user_id")
    shape = seg_h.pivot_table(index="hour", columns="activity_segment", values="steps", aggfunc="mean")
    segs = [s for s in ui.SEGMENT_ORDER if s in shape.columns]
    peaks = {s: int(shape[s].idxmax()) for s in segs}
    evening_all = all(17 <= h <= 19 for h in peaks.values())
    if evening_all and len(segs) > 1:
        title = "Every Segment Shares the Evening Peak — Active Users Just Go Higher"
    elif len(segs) > 1:
        ratio = shape[segs[-1]].max() / max(shape[segs[0]].max(), 1)
        title = f"{segs[-1].title()} Users Hit {ratio:.1f}× the Hourly Peak of {segs[0].title()} Users"
    else:
        title = "Daily Rhythm of the Selected Segment"
    ui.card_title(title, "Average steps per hour by activity segment · same scale on all charts · peak hour in each title")
    if segs:
        fig = make_subplots(rows=1, cols=len(segs), shared_yaxes=True, horizontal_spacing=.04,
                            subplot_titles=[f"<b>{s}</b> · peak {ui.hour_label(peaks[s])}" for s in segs])
        for i, s in enumerate(segs, start=1):
            c_ = ui.SEGMENT_COLORS[s]
            fig.add_scatter(x=shape.index, y=shape[s], mode="lines", line=dict(color=c_, width=2.2), fill="tozeroy",
                            fillcolor=c_ + "26", name=s, showlegend=False, row=1, col=i,
                            hovertemplate=s + " · %{x}:00 · %{y:,.0f} steps/hour<extra></extra>")
            fig.update_xaxes(tickvals=[0, 6, 12, 18], ticktext=["12a", "6a", "12p", "6p"], row=1, col=i)
        fig.update_yaxes(rangemode="tozero", tickformat=",")
        for a in fig.layout.annotations:
            a.update(font=dict(size=12, color="#17191D"), x=a.x, xanchor="center")
        ui.chart(fig, shape.round(0).reset_index(), key="tim_segments", height=260, anim="draw")
    else:
        st.caption("No segment data in the current filter.")

# ================================================================ so what?
wk_end = heat.loc[[d for d in ("Saturday", "Sunday") if d in heat.index]]
wk_line = (f"<li><b>{wk_end.stack().idxmax()[0]} {period(wk_end.stack().idxmax()[1]).lower()}</b> is the strongest "
           "weekend slot — good for weekend challenges.</li>") if not wk_end.empty else ""
counts = ", ".join(f"{k} {s.lower()}" for s, k in zip(pref["slot"], pref["people"]) if s != "No workouts" and k)
st.html(f"""<div class="sowhat"><div class="icon">💡</div><div><h4>So what?</h4><ul>
<li>Send activity nudges around <b>{ui.clock(peak - 1.5)}–{ui.clock(peak - 1)}</b>, just before the {ui.hour_label(peak)} peak.</li>
<li>Use each user's <b>preferred workout time</b> ({counts}) for personal reminders.</li>
{wk_line}
</ul><small>Numbers follow your filters.</small></div></div>""")
