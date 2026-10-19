"""Run each screen headlessly with Streamlit's test runner."""

from pathlib import Path

import pytest

AppTest = pytest.importorskip("streamlit.testing.v1").AppTest
ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(autouse=True)
def temp_db(tmp_path, monkeypatch):
    from pulse import storage
    monkeypatch.setattr(storage, "DB_PATH", tmp_path / "pulse.db")


def page(name):
    script = f"""
import sys
sys.path.insert(0, {str(ROOT)!r})
from pulse import storage
storage.DB_PATH = __import__('pathlib').Path({str(ROOT)!r}) / 'data' / '_test_pulse.db'
from views import {name}
{name}.render()
"""
    return AppTest.from_string(script, default_timeout=60)


def errors(at):
    return [e.value for e in at.exception]


@pytest.mark.parametrize("name", ["home", "dashboard", "help_page", "about", "checkin"])
def test_pages_render(name):
    at = page(name).run()
    assert not errors(at)


def test_checkin_requires_neighborhood():
    at = page("checkin").run()
    at.button[0].click().run()
    assert any("neighborhood" in w.value.lower() for w in at.warning)


def test_checkin_saves():
    at = page("checkin").run()
    at.selectbox[0].set_value("Old Town")
    for r in at.radio[:4]:
        r.set_value("Agree")
    at.radio[4].set_value("Yes")
    at.radio[5].set_value("Yes")
    at.button[0].click().run()
    assert not errors(at)
    assert any("Thank you" in m.value for m in at.markdown)
    assert any("1-800-985-5990" in m.value for m in at.markdown)
