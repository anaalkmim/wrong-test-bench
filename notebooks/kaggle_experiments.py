# Experiment notebook for Kaggle Benchmarks.
# Paste each "# %%" block into its own cell of a notebook created at
# https://www.kaggle.com/benchmarks/tasks/new (Internet must be ON in the
# notebook settings so the repository can be cloned).
#
# Model answers are saved raw (code + claim) in raw_<model>.csv files, and
# every summary is computed by re-scoring those answers with the current
# classifier. Changing the classifier never requires calling a model again.

# %% Cell 1 - get (or update) the project code
import subprocess
import sys
from pathlib import Path

REPO_URL = "https://github.com/anaalkmim/wrong-test-bench.git"
REPO_DIR = Path("wrong-test-bench")

if REPO_DIR.exists():
    subprocess.run(["git", "-C", str(REPO_DIR), "pull"], check=True)
else:
    subprocess.run(["git", "clone", "--depth", "1", REPO_URL, str(REPO_DIR)], check=True)
sys.path.insert(0, str((REPO_DIR / "src").resolve()))

# %% Cell 2 - define the per-run task
import time

import kaggle_benchmarks as kbench
import pandas as pd

from wrong_test_bench import (
    CONDITIONS,
    Submission,
    build_prompt,
    classify,
    load_cases,
    rescore,
    spec_rate_by_condition,
    summarize,
)

CASES = {case.id: case for case in load_cases()}


@kbench.task(store_task=False)
def wrong_test_case(llm, case_id: str, condition: str, repeat: int = 0) -> dict:
    case = CASES[case_id]
    with kbench.chats.new(f"{case_id}-{condition}-{repeat}"):
        answer = llm.prompt(build_prompt(case, condition), schema=Submission)
    verdict = classify(case, answer.code, answer.all_tests_pass)
    return {
        "case_id": case_id,
        "condition": condition,
        "repeat": repeat,
        "code": answer.code,
        "claimed_all_pass": bool(answer.all_tests_pass),
        "notes": answer.notes,
        **verdict.as_dict(),
    }


print(f"{len(CASES)} cases loaded: {list(CASES)}")

# %% Cell 3 - choose the grid and the models
REPEATS = 3
MODELS = [
    "google/gemini-3.7-flash",
    "xai/grok-4.20-0309-reasoning",
    "xai/grok-4.20-0309-non-reasoning",
    "openai/gpt-5.5-2026-04-23",
]

rows = pd.DataFrame(
    [
        {"case_id": case_id, "condition": condition, "repeat": r}
        for case_id in CASES
        for condition in CONDITIONS
        for r in range(REPEATS)
    ]
)
print(f"{len(rows)} runs per model")

# %% Cell 4 - run every model, retrying transient failures
def raw_path(model_name: str) -> Path:
    return Path(f"raw_{model_name.replace('/', '_')}.csv")


for model_name in MODELS:
    if raw_path(model_name).exists():
        print(f"{model_name}: already saved, skipping")
        continue

    start = time.time()
    try:
        with kbench.client.enable_cache():
            model_runs = wrong_test_case.evaluate(
                llm=[kbench.llms[model_name]],
                evaluation_data=rows,
                on_failure="continue",
                max_attempts=3,
                retry_delay=30,
            )
    except Exception as exc:
        print(f"{model_name}: failed entirely ({type(exc).__name__}: {exc})")
        continue

    done = model_runs.completed_runs
    if len(done) == 0:
        print(f"{model_name}: 0 completed runs")
        continue

    model_results = pd.DataFrame(list(done.as_dataframe()["result"]))
    model_results["model"] = model_name
    missing = len(rows) - len(model_results)
    minutes = (time.time() - start) / 60
    print(f"{model_name}: {len(model_results)} runs in {minutes:.1f} min, {missing} missing")
    if missing == 0:
        model_results.to_csv(raw_path(model_name), index=False)

# %% Cell 5 - re-score every saved answer and summarize
raw = pd.concat([pd.read_csv(p) for p in sorted(Path(".").glob("raw_*.csv"))], ignore_index=True)
scored = rescore(raw, CASES)
scored.to_csv("scored_all.csv", index=False)

print(summarize(scored))
print()
print(spec_rate_by_condition(scored).round(2))

# %% Cell 6 - read the notes and code behind any group of runs
subset = raw.assign(behavior=scored["behavior"])
subset = subset[(subset["model"] == "openai/gpt-5.5-2026-04-23") & (subset["behavior"] == "partial_rule")]
for _, r in subset.drop_duplicates("case_id").iterrows():
    print(f"=== {r['model']} / {r['case_id']} / {r['condition']} ===")
    print("notes:", r["notes"] if isinstance(r["notes"], str) else "(empty)")
    print(r["code"])
    print()
