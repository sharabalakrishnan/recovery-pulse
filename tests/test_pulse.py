"""Tests for scoring, privacy rules and storage."""

import math

import pandas as pd
import pytest

from pulse import sample, scoring, storage
from pulse.survey import LIKERT, SCHEMA, STRESSOR_FLAGS, STRESSORS, WEIGHTS


@pytest.fixture
def con():
    c = storage.connect(":memory:")
    yield c
    c.close()


def answers(hood="Old Town", agree=4, strain=0, needs=()):
    a = {"neighborhood": hood, "needs": list(needs)}
    a.update({code: agree for code, *_ in LIKERT})
    a.update({code: strain for code, *_ in STRESSORS})
    return a


def people(hood, n, agree, strain, week=1):
    rows = []
    for _ in range(n):
        r = answers(hood, agree, strain)
        r.update(week=week, is_sample=0, needs="")
        rows.append(r)
    return rows


# ---------------- survey definition
def test_schema_and_weights_cover_every_question():
    assert set(SCHEMA) == set(WEIGHTS)
    assert all(WEIGHTS[c] > 0 for _, c, _ in LIKERT)
    assert all(WEIGHTS[c] < 0 for _, c, *_ in STRESSORS)


# ---------------- scoring with belonginglab
def test_connected_people_score_higher_than_strained(con):
    storage.save_many(con, people("Hillcrest", 20, 5, 0) + people("River Flats", 20, 2, 1))
    df = scoring.score(storage.load(con))
    by = df.groupby("neighborhood")["connection_score"].mean()
    assert by["Hillcrest"] > by["River Flats"]
    assert df["connection_score"].between(0, 100).all()


def test_score_handles_skipped_answers(con):
    rows = people("Old Town", 12, 4, 0)
    rows[0]["q1"] = None
    rows[1]["q5"] = None
    storage.save_many(con, rows)
    df = scoring.score(storage.load(con))
    assert df["connection_score"].notna().all()


def test_empty_data_is_safe():
    df = scoring.score(pd.DataFrame())
    assert df.empty
    assert scoring.summary(df) == {"n": 0}


def test_strain_flags_and_counts(con):
    r = answers(strain=1)
    r.update(week=1, is_sample=0, needs="")
    storage.save_many(con, [r] * 3)
    df = scoring.score(storage.load(con))
    assert (df["strain_count"] == len(STRESSORS)).all()
    assert set(STRESSOR_FLAGS) <= set(df.columns)


# ---------------- privacy: small groups hidden
def test_small_neighborhoods_are_hidden(con):
    storage.save_many(con, people("Old Town", 15, 4, 0) + people("Tiny Lane", 4, 2, 1))
    t = scoring.neighborhood_table(scoring.score(storage.load(con)))
    tiny = t.set_index("neighborhood").loc["Tiny Lane"]
    assert bool(tiny["hidden"])
    assert math.isnan(tiny["mean"]) and math.isnan(tiny["two_plus"])
    assert t.iloc[-1]["neighborhood"] == "Tiny Lane"        # hidden rows sort last
    assert not bool(t.set_index("neighborhood").loc["Old Town", "hidden"])


def test_small_weeks_are_hidden_in_trend(con):
    storage.save_many(con, people("Old Town", 12, 4, 0, week=1) + people("Old Town", 3, 4, 0, week=2))
    t = scoring.weekly_trend(scoring.score(storage.load(con))).set_index("week")
    assert not math.isnan(t.loc[1, "mean"])
    assert math.isnan(t.loc[2, "mean"])


def test_confidence_interval_contains_mean():
    m, lo, hi, n = scoring.mean_ci(pd.Series([40, 50, 60, 55, 45]))
    assert lo < m < hi and n == 5
    m, lo, hi, n = scoring.mean_ci(pd.Series([50]))
    assert math.isnan(lo) and n == 1


def test_stack_and_needs(con):
    rows = people("Old Town", 10, 4, 0)
    for r in rows[:5]:
        r["needs"] = "Rides|Childcare"
    storage.save_many(con, rows)
    df = scoring.score(storage.load(con))
    stack = scoring.strain_stack(df)
    assert stack[0] == pytest.approx(1.0)
    needs = scoring.needs_ranking(df)
    assert needs["Rides"] == pytest.approx(0.5)


# ---------------- storage
def test_validate_rejects_bad_checkins():
    assert storage.validate(answers()) == []
    assert storage.validate({**answers(), "neighborhood": ""})
    assert storage.validate({**answers(), "q1": 9})
    assert storage.validate({"neighborhood": "Old Town", "q1": 3})          # too few answers
    assert storage.validate({**answers(), "needs": ["Free pizza"]})


def test_save_and_load_roundtrip(con):
    storage.save_checkin(con, answers(needs=["Rides"]), week=3)
    df = storage.load(con)
    assert len(df) == 1 and df.iloc[0]["week"] == 3 and df.iloc[0]["needs"] == "Rides"
    assert "name" not in df.columns and "email" not in df.columns
    with pytest.raises(ValueError):
        storage.save_checkin(con, {"neighborhood": ""}, week=1)


def test_sample_rows_can_be_removed(con):
    storage.save_many(con, sample.make_sample(weeks=2))
    storage.save_checkin(con, answers(), week=1)
    assert storage.count(con, sample=True) > 0
    storage.clear_sample(con)
    assert storage.count(con, sample=True) == 0 and storage.count(con) == 1
    assert len(storage.load(con, include_sample=False)) == 1


def test_week_since():
    from datetime import date
    assert storage.week_since(date(2026, 7, 4), date(2026, 7, 4)) == 1
    assert storage.week_since(date(2026, 7, 4), date(2026, 7, 11)) == 2
    assert storage.week_since(date(2026, 7, 4), date(2026, 6, 1)) == 1


def test_settings(con):
    storage.set_setting(con, "community", "Kerrville")
    storage.set_setting(con, "community", "Kerr County")
    assert storage.get_setting(con, "community") == "Kerr County"
    assert storage.get_setting(con, "missing", "x") == "x"


# ---------------- sample town
def test_sample_town_tells_the_intended_story(con):
    storage.save_many(con, sample.make_sample())
    df = scoring.score(storage.load(con))
    t = scoring.neighborhood_table(scoring.recent(df)).set_index("neighborhood")
    assert bool(t.loc["Pecan Grove", "hidden"])
    assert t.loc["Hillcrest", "mean"] > t.loc["River Flats", "mean"]
    s = scoring.summary(df)
    assert s["trend_last"] > s["trend_first"]
    assert s["lowest"] == "River Flats"


def test_rolling_window_fills_small_weeks(con):
    rows = []
    for w in range(1, 5):
        rows += people("Old Town", 5, 4, 0, week=w)
    storage.save_many(con, rows)
    df = scoring.score(storage.load(con))
    single = scoring.weekly_trend(df, "Old Town")
    rolled = scoring.weekly_trend(df, "Old Town", window=3).set_index("week")
    assert single["mean"].isna().all()                     # 5 per week is under the minimum
    assert math.isnan(rolled.loc[1, "mean"])               # week 1 has only 5 so far
    assert not math.isnan(rolled.loc[3, "mean"])           # weeks 1-3 pooled = 15
