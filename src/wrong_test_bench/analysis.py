"""Re-score stored model answers and summarize them.

Every run keeps the model's raw code and claim, so results can be re-scored
whenever the classifier changes, without calling any model again.
"""

from __future__ import annotations

import pandas as pd

from .cases import BenchCase
from .classify import Behavior, classify

REQUIRED_COLUMNS = ("model", "case_id", "condition", "code", "claimed_all_pass")


def rescore(raw: pd.DataFrame, cases: dict[str, BenchCase]) -> pd.DataFrame:
    """Run the current classifier on every stored answer and return one row per run."""
    missing = [c for c in REQUIRED_COLUMNS if c not in raw.columns]
    if missing:
        raise ValueError(f"missing columns: {missing}")

    records = []
    for row in raw.to_dict("records"):
        code = row["code"] if isinstance(row["code"], str) else ""
        verdict = classify(cases[row["case_id"]], code, bool(row["claimed_all_pass"]))
        record = {k: row[k] for k in ("model", "case_id", "condition")}
        if "repeat" in row:
            record["repeat"] = row["repeat"]
        record.update(verdict.as_dict())
        records.append(record)
    return pd.DataFrame(records)


def summarize(scored: pd.DataFrame) -> pd.DataFrame:
    """One row per model: how often each behavior happened, plus self-report errors."""
    counts = pd.crosstab(scored["model"], scored["behavior"])
    counts = counts.reindex(columns=[b.value for b in Behavior], fill_value=0)
    extra = scored.groupby("model")[["overclaim", "underclaim", "ideal"]].sum()
    overview = counts.join(extra)
    overview.insert(0, "runs", scored.groupby("model").size())
    return overview.astype(int)


def spec_rate_by_condition(scored: pd.DataFrame) -> pd.DataFrame:
    """Share of runs that followed the spec, per model and condition."""
    followed = scored["behavior"] == Behavior.FOLLOWED_SPEC.value
    return followed.groupby([scored["model"], scored["condition"]]).mean().unstack("condition")
