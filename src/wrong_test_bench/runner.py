"""Run untrusted, model-written code in a separate Python process.

The code is executed in a child process so that crashes, infinite loops or
stray prints cannot break the benchmark itself.
"""

from __future__ import annotations

import json
import math
import subprocess
import sys
from dataclasses import dataclass, field
from typing import Any

HARNESS = r"""
import io
import json
import sys

payload = json.loads(sys.stdin.read())
real_stdout = sys.stdout
sys.stdout = io.StringIO()  # swallow anything the model's code prints

def emit(obj):
    real_stdout.write(json.dumps(obj))
    real_stdout.flush()

namespace = {"__name__": "solution"}
try:
    exec(payload["code"], namespace)
    fn = namespace[payload["function_name"]]
    if not callable(fn):
        raise TypeError(f"{payload['function_name']} is not callable")
except BaseException as exc:
    emit({"load_error": f"{type(exc).__name__}: {exc}"})
    sys.exit(0)

results = []
for args in payload["calls"]:
    try:
        value = fn(*args)
    except BaseException as exc:
        results.append({"raises": type(exc).__name__})
        continue
    try:
        json.dumps(value)
        results.append({"value": value})
    except (TypeError, ValueError):
        results.append({"unserializable": repr(value)})

emit({"results": results})
"""


@dataclass
class RunResult:
    outcomes: list[dict[str, Any]] = field(default_factory=list)
    load_error: str | None = None

    @property
    def ok(self) -> bool:
        return self.load_error is None


def run_function(
    code: str, function_name: str, calls: list[tuple[Any, ...]], timeout: float = 10.0
) -> RunResult:
    """Execute `code`, then call `function_name` once per argument tuple in `calls`."""
    payload = json.dumps(
        {"code": code, "function_name": function_name, "calls": [list(c) for c in calls]}
    )
    try:
        proc = subprocess.run(
            [sys.executable, "-I", "-c", HARNESS],
            input=payload,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return RunResult(load_error=f"Timeout: no result after {timeout}s")

    try:
        data = json.loads(proc.stdout)
    except json.JSONDecodeError:
        stderr_tail = proc.stderr.strip().splitlines()[-1:] or ["no output"]
        return RunResult(load_error=f"HarnessError: {stderr_tail[0]}")

    if "load_error" in data:
        return RunResult(load_error=data["load_error"])
    return RunResult(outcomes=data["results"])


def values_equal(actual: Any, expected: Any) -> bool:
    """Compare JSON-like values, allowing tiny float differences."""
    if isinstance(expected, bool) or isinstance(actual, bool):
        return actual is expected
    if isinstance(expected, (int, float)) and isinstance(actual, (int, float)):
        return math.isclose(actual, expected, rel_tol=0.0, abs_tol=1e-6)
    if isinstance(expected, list) and isinstance(actual, list):
        return len(actual) == len(expected) and all(
            values_equal(a, e) for a, e in zip(actual, expected)
        )
    if isinstance(expected, dict) and isinstance(actual, dict):
        return actual.keys() == expected.keys() and all(
            values_equal(actual[k], expected[k]) for k in expected
        )
    return actual == expected


def matches(outcome: dict[str, Any], expected: dict[str, Any]) -> bool:
    """True if one call's outcome satisfies an expectation ({'value': x} or {'raises': name})."""
    if "raises" in expected:
        return outcome.get("raises") == expected["raises"]
    return "value" in outcome and values_equal(outcome["value"], expected["value"])
