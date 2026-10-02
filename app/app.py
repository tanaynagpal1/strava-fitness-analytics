import streamlit as st

import filters
import ui

st.set_page_config(page_title="Strava Fitness Analytics", page_icon=str(ui.ASSETS / "strava_icon.png"), layout="wide")
st.logo(str(ui.ASSETS / "strava_header_logo.png"), size="large")
ui.apply_style(motion=st.session_state.get("motion", True))

pages = [
    st.Page("views/overview.py",      title="Overview",      icon=":material/dashboard:", default=True),
    st.Page("views/activity.py",      title="Activity",      icon=":material/directions_run:"),
    st.Page("views/timing.py",        title="Timing",        icon=":material/schedule:"),
    st.Page("views/sleep.py",         title="Sleep",         icon=":material/bedtime:"),
    st.Page("views/engagement.py",    title="Engagement",    icon=":material/event_repeat:"),
    st.Page("views/body_heart.py",    title="Body & Heart",  icon=":material/favorite:"),
    st.Page("views/personas.py",      title="Personas",      icon=":material/groups:"),
    st.Page("views/user_explorer.py", title="User Explorer", icon=":material/person_search:"),
    st.Page("views/conclusion.py",    title="Conclusion",    icon=":material/lightbulb:"),
    st.Page("views/ask_ai.py",        title="Ask AI",        icon=":material/smart_toy:"),
    st.Page("views/about.py",         title="About",         icon=":material/info:"),
]

pg = st.navigation(pages, position="top")
filters.render()
pg.run()
ui.footer()