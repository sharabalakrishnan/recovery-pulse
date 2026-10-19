"""Turn raw check-ins into a privacy-safe community pulse.

Uses belonginglab for the scoring itself:
  * ``map_variables``           - rename q1..q8 to canonical names
  * ``compute_belonging_score`` - weighted z-score composite, ranked 0-100
  * ``compare_groups``          - per-neighborhood summary table

Adds what a disaster-recovery setting needs on top:
  * community strain flags and "how many strains at once" counts
  * 90% confidence intervals for group averages
  * small-group suppression: groups under MIN_GROUP check-ins are hidden
"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd
from belonginglab import compare_groups, compute_belonging_score, map_variables

from .survey import NEEDS, SCHEMA, STRESSOR_FLAGS, STRESSORS, WEIGHTS

MIN_GROUP = 10          # hide any group with fewer check-ins than this
SCORE = "connection_score"
Z90 = 1.645


def score(raw: pd.DataFrame) -> pd.DataFrame:
    """Add canonical columns, strain flags and the 0-100 connection score.

    The score is a percentile rank across *all* check-ins passed in, so a
    neighborhood or week can be compared with the community as a whole:
    50 is the overall middle.
    """
    if raw.empty:
        return raw.assign(**{SCORE: pd.Series(dtype=float)})
    df = map_variables(raw.copy(), schema=SCHEMA, keep_unmapped=True)
    for canon in WEIGHTS:
        df[canon] = pd.to_numeric(df[canon], errors="coerce")
    # Only our community weights: zero out belonginglab's youth defaults is not
    # needed because those columns don't exist here and are skipped.
    df = compute_belonging_score(df, weights=WEIGHTS, output_col=SCORE, scale_0_100=True)
    for _, canon, *_ in STRESSORS:
        df[f"strain_{canon}"] = df[canon].astype("Float64")
    df["strain_count"] = df[STRESSOR_FLAGS].sum(axis=1, min_count=1)
    return df


def mean_ci(values: pd.Series) -> tuple[float, float, float, int]:
    """Mean with a 90% confidence interval (normal approximation)."""
    v = pd.to_numeric(values, errors="coerce").dropna()
    n = len(v)
    if n == 0:
        return (math.nan, math.nan, math.nan, 0)
    m = float(v.mean())
    if n < 2:
        return (m, math.nan, math.nan, n)
    half = Z90 * float(v.std(ddof=1)) / math.sqrt(n)
    return (m, max(0.0, m - half), min(100.0, m + half), n)


def neighborhood_table(df: pd.DataFrame, min_group: int = MIN_GROUP) -> pd.DataFrame:
    """One row per neighborhood: n, average score with 90% CI, strain rates.

    Groups below ``min_group`` keep their name and count but every other value
    is blanked and ``hidden`` is True.
    """
    if df.empty:
        return pd.DataFrame(columns=["neighborhood", "n", "mean", "low", "high", "hidden"])
    base = compare_groups(df, by="neighborhood", score_col=SCORE)   # belonginglab
    rows = []
    for hood, sub in df.groupby("neighborhood"):
        m, lo, hi, n = mean_ci(sub[SCORE])
        row = {"neighborhood": hood, "n": n, "mean": m, "low": lo, "high": hi,
               "two_plus": float((sub["strain_count"] >= 2).mean())}
        for flag in STRESSOR_FLAGS:
            row[flag] = float(pd.to_numeric(sub[flag], errors="coerce").mean())
        rows.append(row)
    out = pd.DataFrame(rows)
    out = out.merge(base[["neighborhood", f"{SCORE}_median"]], on="neighborhood", how="left")
    out["hidden"] = out["n"] < min_group
    value_cols = [c for c in out.columns if c not in ("neighborhood", "n", "hidden")]
    out.loc[out["hidden"], value_cols] = np.nan
    return out.sort_values(["hidden", "mean"], ascending=[True, False]).reset_index(drop=True)


def weekly_trend(df: pd.DataFrame, neighborhood: str | None = None, window: int = 1,
                 min_group: int = MIN_GROUP) -> pd.DataFrame:
    """Average score per week, optionally for one neighborhood.

    ``window`` > 1 pools each week with the weeks before it (a rolling average),
    so small neighborhoods reach the privacy minimum without hiding most weeks.
    Weeks that still have fewer than ``min_group`` check-ins are blanked.
    """
    sub = df if neighborhood is None else df[df["neighborhood"] == neighborhood]
    rows = []
    if sub.empty:
        return pd.DataFrame(columns=["week", "n", "mean", "low", "high"])
    for week in range(int(df["week"].min()), int(df["week"].max()) + 1):
        w = sub[(sub["week"] <= week) & (sub["week"] > week - window)]
        m, lo, hi, n = mean_ci(w[SCORE])
        ok = n >= min_group
        rows.append({"week": week, "n": n, "mean": m if ok else np.nan,
                     "low": lo if ok else np.nan, "high": hi if ok else np.nan})
    return pd.DataFrame(rows)


def strain_stack(df: pd.DataFrame) -> pd.Series:
    """Share of check-ins reporting 0, 1, 2, 3 or 4 strains (complete answers only)."""
    complete = df.dropna(subset=STRESSOR_FLAGS)
    if complete.empty:
        return pd.Series(0.0, index=range(len(STRESSOR_FLAGS) + 1))
    counts = complete["strain_count"].astype(int).value_counts(normalize=True)
    return counts.reindex(range(len(STRESSOR_FLAGS) + 1), fill_value=0.0)


def needs_ranking(df: pd.DataFrame) -> pd.Series:
    """Share of check-ins asking for each kind of help, most requested first."""
    if df.empty:
        return pd.Series(dtype=float)
    picked = df["needs"].fillna("").str.split("|")
    shares = {need: float(picked.apply(lambda xs: need in xs).mean()) for need in NEEDS}
    return pd.Series(shares).sort_values(ascending=False)


def recent(df: pd.DataFrame, weeks: int = 4) -> pd.DataFrame:
    """Check-ins from the latest ``weeks`` weeks."""
    if df.empty:
        return df
    last = int(df["week"].max())
    return df[df["week"] > last - weeks]


def summary(df: pd.DataFrame) -> dict:
    """Headline numbers for the dashboard."""
    if df.empty:
        return {"n": 0}
    rec = recent(df)
    table = neighborhood_table(rec)
    shown = table[~table["hidden"]]
    trend = weekly_trend(df)
    first, last = trend.dropna(subset=["mean"]).iloc[[0, -1]]["mean"].tolist() if trend["mean"].notna().sum() >= 2 else (math.nan, math.nan)
    needs = needs_ranking(rec)
    first_week = df[df["week"] == df["week"].min()]
    return {
        "n": int(len(df)),
        "n_recent": int(len(rec)),
        "weeks": int(df["week"].max()),
        "hoods": int(df["neighborhood"].nunique()),
        "avg_recent": float(rec[SCORE].mean()),
        "trend_first": first,
        "trend_last": last,
        "two_plus_recent": float((rec["strain_count"] >= 2).mean()),
        "two_plus_first": float((first_week["strain_count"] >= 2).mean()),
        "lowest": None if shown.empty else shown.iloc[-1]["neighborhood"],
        "lowest_score": None if shown.empty else float(shown.iloc[-1]["mean"]),
        "top_need": None if needs.empty else needs.index[0],
        "top_need_share": None if needs.empty else float(needs.iloc[0]),
    }
