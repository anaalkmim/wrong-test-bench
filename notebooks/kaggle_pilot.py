# Pilot run for Kaggle Benchmarks.
# Paste each "# %%" block into its own cell of a notebook created at
# https://www.kaggle.com/benchmarks/tasks/new (Internet must be ON in the
# notebook settings so the repository can be cloned).

# %% Cell 1 - get the project code into the notebook
import subprocess
import sys
from pathlib import Path

REPO_URL = "https://github.com/anaalkmim/wrong-test-bench.git"
REPO_DIR = Path("wrong-test-bench")

if not REPO_DIR.exists():
    subprocess.run(["git", "clone", "--depth", "1", REPO_URL, str(REPO_DIR)], check=True)
sys.path.insert(0, str((REPO_DIR / "src").resolve()))

# %% Cell 2 - define the per-case task
import kaggle_benchmarks as kbench
import pandas as pd

from wrong_test_bench import CONDITIONS, Submission, build_prompt, classify, load_cases

CASES = {case.id: case for case in load_cases()}


@kbench.task(store_task=False)
def wrong_test_case(llm, case_id: str, condition: str) -> dict:
    case = CASES[case_id]
    with kbench.chats.new(f"{case_id}-{condition}"):
        answer = llm.prompt(build_prompt(case, condition), schema=Submission)
    verdict = classify(case, answer.code, answer.suspect_tests)
    return {
        "case_id": case_id,
        "condition": condition,
        "behavior": verdict.behavior.value,
        "flagged": verdict.flagged,
        "false_flags": verdict.false_flags,
        "neutral_pass": verdict.neutral_pass,
        "ideal": verdict.ideal,
        "code": answer.code,
        "suspect_tests": list(answer.suspect_tests),
    }


# %% Cell 3 - run every case in both conditions with the default model
rows = pd.DataFrame(
    [{"case_id": case_id, "condition": condition} for case_id in CASES for condition in CONDITIONS]
)
runs = wrong_test_case.evaluate(llm=[kbench.llm], evaluation_data=rows)
results = pd.DataFrame(list(runs.as_dataframe()["result"]))
results[["case_id", "condition", "behavior", "flagged", "false_flags", "neutral_pass", "ideal"]]

# %% Cell 4 - read what the model actually wrote for any row
row = 0
print(results.loc[row, "suspect_tests"])
print(results.loc[row, "code"])
