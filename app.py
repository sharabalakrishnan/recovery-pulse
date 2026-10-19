"""Community Recovery Pulse - anonymous check-ins that show how connected a community feels after a disaster.

Run locally:   streamlit run app.py
"""

import streamlit as st

st.set_page_config(page_title="Recovery Pulse", page_icon="💜", layout="wide", initial_sidebar_state="auto")

from views import about, checkin, dashboard, help_page, home, style  # noqa: E402

style.apply()

pages = {
    "home": st.Page(home.render, title="Home", icon=":material/home:", url_path="home", default=True),
    "checkin": st.Page(checkin.render, title="Check in", icon=":material/task_alt:", url_path="checkin"),
    "dash": st.Page(dashboard.render, title="Community pulse", icon=":material/monitoring:", url_path="pulse"),
    "help": st.Page(help_page.render, title="Get help", icon=":material/volunteer_activism:", url_path="help"),
    "about": st.Page(about.render, title="About & privacy", icon=":material/info:", url_path="about"),
}
home.PAGES = pages
nav = st.navigation(list(pages.values()))

with st.sidebar:
    st.caption("In an emergency, call **911**. For emotional support after a disaster, call or text **1-800-985-5990**.")

nav.run()
