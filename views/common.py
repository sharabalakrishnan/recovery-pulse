"""Shared helpers: database connection, cached scoring, settings and colors."""

from datetime import date

import streamlit as st

from pulse import sample, scoring, storage

# Neutral purple ramp for data (red/blue data maps read as election maps).
DATA_RAMP = ["#bba6dc", "#a088cf", "#8669bf", "#6c4daa", "#53368e", "#3b236c"]
DATA = "#6c4daa"
DATA_DARK = "#3b236c"
GREY = "#9aa0ad"
NAVY = "#002868"
RED = "#BF0A30"

DEFAULTS = {
    "community": sample.TOWN,
    "event": "flood",
    "event_date": "",
    "neighborhoods": ", ".join(sample.NEIGHBORHOODS),
    "show_sample": "1",
}


@st.cache_resource
def get_con():
    con = storage.connect()
    if storage.get_setting(con, "seeded") is None:     # first run: add the sample town
        storage.save_many(con, sample.make_sample())
        storage.set_setting(con, "seeded", "1")
    return con


def setting(key: str) -> str:
    return storage.get_setting(get_con(), key, DEFAULTS[key]) or DEFAULTS[key]


def neighborhoods() -> list[str]:
    return [h.strip() for h in setting("neighborhoods").split(",") if h.strip()]


def using_sample() -> bool:
    return setting("show_sample") == "1" and storage.count(get_con(), sample=True) > 0


@st.cache_data(show_spinner=False)
def _scored(version: int, include_sample: bool):
    return scoring.score(storage.load(get_con(), include_sample=include_sample))


def scored():
    """All check-ins, scored. Re-scored whenever a check-in is added."""
    con = get_con()
    return _scored(storage.count(con), using_sample())


def current_week() -> int:
    raw = setting("event_date")
    if raw:
        try:
            return storage.week_since(date.fromisoformat(raw))
        except ValueError:
            pass
    df = scored()
    return int(df["week"].max()) if not df.empty else 1


def sample_banner() -> None:
    if using_sample():
        st.info(
            f"**Sample data.** The check-ins shown are made up for a fictional town ({sample.TOWN}). "
            "An organizer can remove them on the About page once real check-ins arrive.",
            icon="ℹ️",
        )
