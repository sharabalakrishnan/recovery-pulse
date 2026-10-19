"""Get help: free support for anyone affected."""

import streamlit as st

from views.style import page_header

RESOURCES = [
    ("Disaster Distress Helpline", "1-800-985-5990",
     "Call or text, 24/7. Free, confidential crisis counseling after a disaster, in English and Spanish.",
     "https://www.samhsa.gov/find-help/helplines/disaster-distress-helpline"),
    ("988 Suicide & Crisis Lifeline", "988",
     "Call or text any time if you or someone you know is in crisis.", "https://988lifeline.org/"),
    ("FEMA disaster assistance", "1-800-621-3362",
     "Apply for help with housing, repairs and other losses.", "https://www.disasterassistance.gov/"),
    ("2-1-1 Texas", "2-1-1",
     "Food, shelter, rides, utility help and local recovery groups near you.", "https://www.211texas.org/"),
]


def render():
    page_header("Get help", "Help is available now.",
                "Free, confidential and open to everyone affected, whether or not you check in.")
    cols = st.columns(2, gap="medium")
    for i, (name, number, body, url) in enumerate(RESOURCES):
        with cols[i % 2], st.container(border=True):
            st.markdown(f'<div class="tc-card tc-card-name">{name}</div>'
                        f'<div class="tc-stat" style="font-size:1.6rem">{number}</div>', unsafe_allow_html=True)
            st.write(body)
            st.link_button("Website", url)
    st.caption("In an emergency, call 911.")
