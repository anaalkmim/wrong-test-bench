"""Re-score every stored model answer with the current classifier and print the summary."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from wrong_test_bench import load_cases, rescore, spec_rate_by_condition, summarize

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-dir", type=Path, default=ROOT / "outputs" / "raw")
    parser.add_argument("--out", type=Path, default=ROOT / "outputs" / "scored_all.csv")
    args = parser.parse_args()

    files = sorted(args.raw_dir.glob("raw_*.csv"))
    if not files:
        raise SystemExit(f"no raw_*.csv files found in {args.raw_dir}")

    raw = pd.concat([pd.read_csv(path) for path in files], ignore_index=True)
    scored = rescore(raw, {case.id: case for case in load_cases()})
    args.out.parent.mkdir(parents=True, exist_ok=True)
    scored.to_csv(args.out, index=False)

    with pd.option_context("display.width", 200, "display.max_columns", None):
        print(summarize(scored))
        print()
        print("Share of runs that followed the spec, by condition:")
        print(spec_rate_by_condition(scored).round(2))
    print(f"\nScored {len(scored)} runs from {len(files)} files -> {args.out}")


if __name__ == "__main__":
    main()
