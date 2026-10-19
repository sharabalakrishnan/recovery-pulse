"""Check in: the anonymous resident survey."""

import streamlit as st

from pulse import storage
from pulse.survey import LIKERT, NEEDS, SCALE_LABELS, STRESSORS
from views.common import current_week, get_con, neighborhoods, setting
from views.style import page_header

YES_NO = {"Yes": 1, "No": 0}


def render():
    page_header("Check in", "How is your neighborhood doing?",
                "About one minute. Your answers are combined with your neighbors' and never shown on their own.")

    if st.session_state.get("checked_in"):
        thank_you(st.session_state.get("strain_total", 0))
        return

    with st.form("checkin", clear_on_submit=False):
        hood = st.selectbox(f"Where do you live now, or where did you live before the {setting('event')}?",
                            neighborhoods() + ["Somewhere else"], index=None, placeholder="Choose a neighborhood")
        st.markdown("**How much do you agree?**")
        likert = {}
        for code, _, text in LIKERT:
            choice = st.radio(text, SCALE_LABELS, index=None, horizontal=True, key=code)
            likert[code] = None if choice is None else SCALE_LABELS.index(choice) + 1
        st.markdown(f"**Since the {setting('event')}…**")
        strains = {}
        for code, _, _, text in STRESSORS:
            choice = st.radio(text, ["Yes", "No", "Skip"], index=None, horizontal=True, key=code)
            strains[code] = YES_NO.get(choice)
        needs = st.multiselect("What would help most right now? Pick any.", NEEDS, placeholder="Choose any that apply")
        st.info("We don't ask for your name, email or address, and we don't track you. Neighborhoods with fewer "
                "than 10 check-ins stay hidden so no one can be singled out.", icon="🔒")
        sent = st.form_submit_button("Send my check-in", type="primary")

    if sent:
        answers = {"neighborhood": hood, **likert, **strains, "needs": needs}
        problems = storage.validate(answers)
        if problems:
            for p in problems:
                st.warning(p)
            return
        storage.save_checkin(get_con(), answers, week=current_week())
        st.session_state["checked_in"] = True
        st.session_state["strain_total"] = sum(v for v in strains.values() if v)
        st.rerun()


def thank_you(strain_total: int):
    with st.container(border=True):
        st.markdown('<div class="tc-card tc-card-name">Thank you. Your check-in was counted.</div>', unsafe_allow_html=True)
        st.write("It joins your neighborhood's weekly pulse. Organizers only ever see totals.")
        if strain_total >= 2:
            st.write("You mentioned several strains at once. That's common after a disaster, and help is available: "
                     "the **Disaster Distress Helpline** (call or text **1-800-985-5990**) is free and open 24/7.")
        else:
            st.write("If things get harder, the **Get help** page lists free support any time.")
    if st.button("Check in again"):
        st.session_state["checked_in"] = False
        for code, *_ in LIKERT + STRESSORS:
            st.session_state.pop(code, None)
        st.rerun()
