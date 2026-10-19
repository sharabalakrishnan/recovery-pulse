"""Home: what the app is for, with links to each screen."""

import html

import streamlit as st

from pulse import scoring
from views.common import scored, setting
from views.style import page_header

PAGES: dict = {}   # filled in by app.py

TILES = [
    ("checkin", "For residents", "Check in",
     "Six quick questions about support, trust and day-to-day strain. No name, no account.", "Start check-in →"),
    ("dash", "For organizers", "Community pulse",
     "Connection scores by neighborhood and week, the strains piling up, and the help people ask for most.",
     "Open the pulse →"),
    ("help", "Right now", "Get help",
     "Disaster aid, rides, food and someone to talk to, any time of day.", "See resources →"),
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
    for col, (key, kicker, title, body, link) in zip(cols, TILES):
        with col, st.container(border=True):
            st.markdown(f'<div class="tc-card tc-tile-kicker">{kicker}</div>'
                        f'<div class="tc-tile-title">{title}</div><div class="tc-tile-body">{body}</div>',
                        unsafe_allow_html=True)
            if key in PAGES:
                st.page_link(PAGES[key], label=link)

    df = scored()
    if df.empty:
        return
    s = scoring.summary(df)
    short = {"Home repair help": "Home repair", "Help with bills": "Bills", "Someone to talk to": "Someone to talk to",
             "Childcare": "Childcare", "Rides": "Rides", "Neighborhood events": "Events"}
    tiles = [
        ("Check-ins so far", f"{s['n']:,}", f"{s['weeks']} weeks, {s['hoods']} neighborhoods"),
        ("Lowest-connected area", s["lowest"] or "—", f"score {s['lowest_score']:.0f} of 100" if s["lowest"] else ""),
        ("Residents with 2+ strains", f"{s['two_plus_recent']:.0%}", "latest 4 weeks"),
        ("Most requested help", short.get(s["top_need"], s["top_need"] or "—"),
         f"{s['top_need_share']:.0%} of check-ins" if s["top_need"] else ""),
    ]
    st.markdown('<div class="rp-metrics">' + "".join(
        f'<div class="rp-metric"><div class="l">{html.escape(l)}</div><div class="v">{html.escape(v)}</div>'
        f'<div class="s">{html.escape(sub)}</div></div>' for l, v, sub in tiles) + "</div>", unsafe_allow_html=True)
