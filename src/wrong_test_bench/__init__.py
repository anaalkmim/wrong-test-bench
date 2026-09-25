"""wrong-test-bench: what do LLMs do when a test contradicts the spec?"""

from .analysis import rescore, spec_rate_by_condition, summarize
from .cases import BenchCase, CaseError, load_cases
from .classify import Behavior, Verdict, classify
from .prompt import CONDITIONS, Submission, build_prompt, render_test_file

__all__ = [
    "BenchCase",
    "Behavior",
    "CONDITIONS",
    "CaseError",
    "Submission",
    "Verdict",
    "build_prompt",
    "classify",
    "load_cases",
    "render_test_file",
    "rescore",
    "spec_rate_by_condition",
    "summarize",
]
