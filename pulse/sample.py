"""Sample check-ins for a made-up town, Riverbend, TX, after a flood.

Used so the dashboard has something to show before real check-ins arrive.
Every sample row is marked ``is_sample = 1`` and the app labels it clearly.
"""

from __future__ import annotations

import numpy as np

from .survey import LIKERT, NEEDS, STRESSORS

TOWN = "Riverbend, TX"
EVENT = "flood"

# neighborhood: (check-ins per week, starting connection 0-1, weekly recovery rate, flood damage 0-1)
NEIGHBORHOODS = {
    "Hillcrest":    (14, 0.62, 0.012, 0.15),
    "Old Town":     (12, 0.55, 0.014, 0.25),
    "Mill Creek":   (11, 0.45, 0.020, 0.40),
    "Southside":    (9, 0.42, 0.015, 0.50),
    "Cypress Bend": (7, 0.35, 0.008, 0.65),
    "River Flats":  (10, 0.28, 0.010, 0.80),
    "Pecan Grove":  (1, 0.40, 0.010, 0.45),   # too few check-ins: stays hidden
}


def make_sample(weeks: int = 12, seed: int = 7) -> list[dict]:
    rng = np.random.default_rng(seed)
    rows = []
    for hood, (per_week, base, rate, damage) in NEIGHBORHOODS.items():
        for week in range(1, weeks + 1):
            n = max(0, int(rng.poisson(per_week)))
            connected = min(0.95, base + rate * (week - 1))
            strain = max(0.05, damage - 0.025 * (week - 1) * (1 - damage / 2))
            for _ in range(n):
                person = rng.normal(0, 0.12)
                row = {"week": week, "neighborhood": hood, "is_sample": 1}
                for code, *_ in LIKERT:
                    p = np.clip(connected + person + rng.normal(0, 0.10), 0, 1)
                    row[code] = int(np.clip(round(1 + 4 * p), 1, 5))
                    if rng.random() < 0.03:
                        row[code] = None          # someone skipped a question
                for code, canon, *_ in STRESSORS:
                    p = np.clip(strain + (0.15 if canon == "money_strain" else 0) - person / 2, 0.02, 0.95)
                    row[code] = int(rng.random() < p)
                    if rng.random() < 0.03:
                        row[code] = None
                wants = [need for need, base_p in zip(NEEDS, (0.55 * damage + 0.05, 0.40, 0.28, 0.20, 0.15, 0.15))
                         if rng.random() < base_p]
                row["needs"] = "|".join(wants)
                rows.append(row)
    return rows
