"""Global filters: one row at the top of every page; choices are remembered across pages."""
import datetime as dt

import pandas as pd
import streamlit as st

from data import load

SEGMENTS = ["Sedentary", "Low active", "Somewhat active", "Active"]
TIERS = ["Consistent", "Irregular", "Barely using"]
DAY_TYPES = ["All days", "Weekdays", "Weekends"]
START, END = dt.date(2016, 4, 12), dt.date(2016, 5, 12)

DEFAULTS = {"f_segments": [], "f_tiers": [], "f_daytype": "All days", "f_dates": (START, END)}


def _reset():
    for key, value in DEFAULTS.items():
        st.session_state[key] = value


def selected_users():
    """User IDs that match the segment and engagement-tier filters (empty filter = everyone)."""
    p = load("user_profile")
    keep = pd.Series(True, index=p.index)
    if st.session_state.f_segments:
        keep &= p["activity_segment"].isin(st.session_state.f_segments)
    if st.session_state.f_tiers:
        keep &= p["engagement_tier"].isin(st.session_state.f_tiers)
    return set(p.loc[keep, "user_id"])


def filter_days(df, date_col="date"):
    """Keep rows for the selected users, date range and day type."""
    start, end = st.session_state.f_dates
    d = df[df["user_id"].isin(selected_users()) & df[date_col].dt.date.between(start, end)]
    if st.session_state.f_daytype == "Weekdays":
        d = d[d[date_col].dt.dayofweek < 5]
    elif st.session_state.f_daytype == "Weekends":
        d = d[d[date_col].dt.dayofweek >= 5]
    return d


def render():
    """Draw the filter row. Called once from app.py, so it appears on every page."""
    for key, value in DEFAULTS.items():
        st.session_state.setdefault(key, value)
    st.session_state.setdefault("motion", True)      # a preference, so Reset doesn't touch it

    with st.container(border=True, key="filters"):
        st.markdown(
            '<div class="fhead"><div class="ficon"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" '
            'stroke="#FFFFFF" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">'
            '<path d="M4 5h16l-6 7.5V18l-4 2v-7.5z"/></svg></div>'
            '<div><p class="ftitle">Filter the dashboard</p>'
            '<p class="fsub">Pick any mix — every page, KPI and chart updates instantly.</p></div></div>',
            unsafe_allow_html=True)

        c1, c2 = st.columns([1.15, 1])
        c1.pills("Activity segment", SEGMENTS, selection_mode="multi", key="f_segments", wrap=True)
        c2.pills("Engagement tier", TIERS, selection_mode="multi", key="f_tiers", wrap=True)

        c3, c4, c5 = st.columns([1.3, 2, 0.6], vertical_alignment="bottom")
        c3.segmented_control("Day type", DAY_TYPES, key="f_daytype")
        c4.slider("Dates", START, END, key="f_dates", format="D MMM")
        c5.button("Reset", on_click=_reset, width="stretch", icon=":material/restart_alt:")

        days = filter_days(load("daily_master"))
        n_users = days["user_id"].nunique()
        who = "person" if n_users == 1 else "people"
        left, right = st.columns([4, 1], vertical_alignment="center")
        left.html(f'<div class="fsummary"><span class="dot"></span>Showing <span class="chip">{n_users} {who}</span>'
                  f'<span class="chip">{len(days):,} days</span><span>· empty filter = everyone</span></div>')
        right.toggle("Animations", key="motion", help="Turn all motion off (charts and numbers appear instantly).")
    if n_users < 3:
        st.warning("Fewer than 3 people match these filters — read the charts as individual stories, not trends.")