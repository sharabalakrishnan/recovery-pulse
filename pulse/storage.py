"""Save and load check-ins in a small SQLite database.

Privacy by design:
  * no name, email, address, IP address or device information is stored
  * the time of a check-in is stored only as "weeks since the disaster",
    so answers can't be matched to a person by when they were sent
"""

from __future__ import annotations

import sqlite3
from datetime import date
from pathlib import Path

import pandas as pd

from .survey import LIKERT, NEEDS, STRESSORS

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "pulse.db"
CODES = [code for code, *_ in LIKERT + STRESSORS]

SCHEMA_SQL = f"""
CREATE TABLE IF NOT EXISTS checkins (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    week INTEGER NOT NULL,
    neighborhood TEXT NOT NULL,
    {", ".join(f"{c} INTEGER" for c in CODES)},
    needs TEXT,
    is_sample INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT);
"""


def connect(path: Path | str | None = None) -> sqlite3.Connection:
    path = DB_PATH if path is None else path
    if str(path) != ":memory:":
        Path(path).parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(path, check_same_thread=False)
    con.executescript(SCHEMA_SQL)
    return con


def get_setting(con, key: str, default: str | None = None) -> str | None:
    row = con.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
    return row[0] if row else default


def set_setting(con, key: str, value: str) -> None:
    con.execute("INSERT INTO settings(key, value) VALUES(?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                (key, value))
    con.commit()


def week_since(event_date: date, today: date | None = None) -> int:
    """Week number since the disaster, starting at 1."""
    today = today or date.today()
    return max(1, (today - event_date).days // 7 + 1)


def validate(answers: dict) -> list[str]:
    """Return a list of problems with a check-in (empty list means it's fine)."""
    problems = []
    if not str(answers.get("neighborhood") or "").strip():
        problems.append("Choose a neighborhood.")
    for code, _, text in LIKERT:
        v = answers.get(code)
        if v is not None and v not in (1, 2, 3, 4, 5):
            problems.append(f"Answer for '{text}' must be 1 to 5.")
    for code, *_ in STRESSORS:
        v = answers.get(code)
        if v is not None and v not in (0, 1):
            problems.append(f"Answer for {code} must be yes or no.")
    answered = sum(answers.get(code) is not None for code in CODES)
    if answered < 3:
        problems.append("Answer at least three questions so your check-in can be counted.")
    unknown = [n for n in answers.get("needs", []) if n not in NEEDS]
    if unknown:
        problems.append("Unknown help option.")
    return problems


def save_checkin(con, answers: dict, week: int, is_sample: bool = False) -> None:
    problems = validate(answers)
    if problems:
        raise ValueError(" ".join(problems))
    cols = ["week", "neighborhood", *CODES, "needs", "is_sample"]
    values = [int(week), str(answers["neighborhood"]).strip(),
              *[answers.get(c) for c in CODES], "|".join(answers.get("needs", [])), int(is_sample)]
    con.execute(f"INSERT INTO checkins({', '.join(cols)}) VALUES({', '.join('?' * len(cols))})", values)
    con.commit()


def save_many(con, rows: list[dict]) -> None:
    cols = ["week", "neighborhood", *CODES, "needs", "is_sample"]
    con.executemany(
        f"INSERT INTO checkins({', '.join(cols)}) VALUES({', '.join('?' * len(cols))})",
        [[r["week"], r["neighborhood"], *[r.get(c) for c in CODES], r.get("needs", ""), int(r.get("is_sample", 1))]
         for r in rows],
    )
    con.commit()


def load(con, include_sample: bool = True) -> pd.DataFrame:
    sql = "SELECT * FROM checkins" + ("" if include_sample else " WHERE is_sample = 0")
    return pd.read_sql_query(sql, con)


def count(con, sample: bool | None = None) -> int:
    if sample is None:
        return con.execute("SELECT COUNT(*) FROM checkins").fetchone()[0]
    return con.execute("SELECT COUNT(*) FROM checkins WHERE is_sample = ?", (int(sample),)).fetchone()[0]


def clear_sample(con) -> None:
    con.execute("DELETE FROM checkins WHERE is_sample = 1")
    con.commit()
