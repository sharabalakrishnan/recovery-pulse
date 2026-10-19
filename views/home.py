"""Home: what the app is for, with links to each screen."""

import streamlit as st

from pulse import scoring
from views.common import scored, setting
from views.style import page_header

PAGES: dict = {}   # filled in by app.py

TILES = [
    ("checkin", "For residents", "Check in",
     "Six quick questions about support, trust and day-to-day strain. No name, no account."),
    ("dash", "For organizers", "Community pulse",
     "Connection by neighborhood and week, the strains piling up, and the help people ask for most."),
    ("help", "Right now", "Get help",
     "Disaster aid, food, rides and someone to talk to, any time of day."),
]


def render():
    community, event = setting("community"), setting("event")
    page_header(
        f"{community} {event} recovery",
        "Rebuild homes. Rebuild the neighborhood too.",
        "After a disaster, houses get repaired long before people feel connected again. Recovery Pulse is a "
        "one-minute anonymous check-in that shows organizers which neighborhoods feel most cut off and what would help.",
    )
    cols = st.columns(3, gap="medium")
    for col, (key, kicker, title, body) in zip(cols, TILES):
        with col, st.container(border=True):
            st.markdown(f'<div class="tc-card tc-tile-kicker">{kicker}</div>'
                        f'<div class="tc-tile-title">{title}</div><div class="tc-tile-body">{body}</div>',
                        unsafe_allow_html=True)
            if key in PAGES:
                st.page_link(PAGES[key], label="Open")

    df = scored()
    if df.empty:
        return
    s = scoring.summary(df)
    st.write("")
    c = st.columns(3, gap="medium")
    stats = [
        (f"{s['n']:,}", f"check-ins over {s['weeks']} weeks"),
        (s["lowest"] or "—", f"feels least connected (score {s['lowest_score']:.0f} of 100)" if s["lowest"] else "not enough check-ins yet"),
        (f"{s['two_plus_recent']:.0%}", "of recent check-ins report two or more strains"),
    ]
    for col, (value, label) in zip(c, stats):
        col.markdown(f'<div class="tc-stat">{value}</div><div class="tc-stat-label">{label}</div>', unsafe_allow_html=True)
