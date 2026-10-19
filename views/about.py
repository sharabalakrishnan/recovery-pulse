"""About & privacy, plus organizer settings."""

from datetime import date

import streamlit as st

from pulse import scoring, storage
from pulse.survey import WEIGHTS
from views.common import get_con, setting, using_sample
from views.style import page_header, section


def render():
    page_header("About", "About Recovery Pulse.", "Built for towns rebuilding after floods, storms and fires.")

    section("Why it exists")
    st.write("After a disaster, aid focuses on buildings. But people who feel cut off from neighbors recover more "
             "slowly, and isolated neighborhoods are easy to miss. Recovery Pulse gives organizers a weekly, "
             "anonymous read on how connected each neighborhood feels and what help people need most.")

    section("How the connection score works")
    st.write("Each check-in is scored with **belonginglab**, an open-source Python library for measuring belonging "
             "(pypi.org/project/belonginglab). It standardizes each answer, applies a weight and ranks the total "
             "from 0 to 100 across all check-ins.")
    st.dataframe(
        [{"Answer": k.replace("_", " ").capitalize(), "Weight": v,
          "Effect": "raises connection" if v > 0 else "lowers connection"} for k, v in WEIGHTS.items()],
        hide_index=True, use_container_width=True)
    st.caption("The score describes neighborhoods, never individuals. It is not a mental health screening.")

    section("Privacy")
    st.markdown(f"""
- No names, emails, addresses, accounts or tracking.
- Check-ins are stored by week, not exact time, so answers can't be matched to a person by when they were sent.
- Any neighborhood or week with fewer than {scoring.MIN_GROUP} check-ins is hidden from every chart and download.
""")

    organizer_settings()


def organizer_settings():
    with st.expander("Organizer settings"):
        try:
            code = st.secrets.get("ORGANIZER_CODE", "")
        except Exception:  # no secrets file
            code = ""
        if code and st.text_input("Organizer code", type="password") != code:
            st.caption("Enter the organizer code to change settings.")
            return
        con = get_con()
        with st.form("settings"):
            community = st.text_input("Community name", setting("community"))
            event = st.text_input("Disaster (one word, like flood or hurricane)", setting("event"))
            raw_date = setting("event_date")
            event_date = st.date_input("Date of the disaster", date.fromisoformat(raw_date) if raw_date else None,
                                       max_value=date.today(), format="MM/DD/YYYY")
            hoods = st.text_area("Neighborhoods (separate with commas)", setting("neighborhoods"))
            show = st.checkbox("Include sample check-ins", value=setting("show_sample") == "1")
            if st.form_submit_button("Save settings", type="primary"):
                storage.set_setting(con, "community", community.strip() or "Our community")
                storage.set_setting(con, "event", event.strip() or "disaster")
                storage.set_setting(con, "event_date", event_date.isoformat() if event_date else "")
                storage.set_setting(con, "neighborhoods", hoods)
                storage.set_setting(con, "show_sample", "1" if show else "0")
                st.cache_data.clear()
                st.success("Saved.")
        st.caption(f"Real check-ins: {storage.count(con, sample=False):,} · "
                   f"Sample check-ins: {storage.count(con, sample=True):,}")
        if using_sample() or storage.count(con, sample=True):
            confirm = st.checkbox("I understand this permanently removes the sample check-ins")
            if st.button("Remove sample check-ins", disabled=not confirm):
                storage.clear_sample(con)
                storage.set_setting(con, "show_sample", "0")
                st.cache_data.clear()
                st.success("Sample check-ins removed.")
