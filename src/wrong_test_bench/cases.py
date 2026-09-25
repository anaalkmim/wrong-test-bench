"""Load and validate benchmark cases from JSON.

Each case describes a function with a written specification and a visible
test file in which exactly one test contradicts the specification.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

DEFAULT_CASES_PATH = Path(__file__).resolve().parents[2] / "data" / "cases.json"


class CaseError(ValueError):
    """Raised when a case file is malformed or internally inconsistent."""


@dataclass(frozen=True)
class CallSpec:
    """One call to the function with its expected outcome."""

    args: tuple[Any, ...]
    expected: dict[str, Any]
    name: str = ""


@dataclass(frozen=True)
class Probe:
    """An input that separates the specification's rule from the flawed test's rule."""

    args: tuple[Any, ...]
    spec_expected: dict[str, Any]
    test_rule_expected: dict[str, Any]


@dataclass(frozen=True)
class BenchCase:
    id: str
    function_name: str
    signature: str
    spec: str
    visible_tests: tuple[CallSpec, ...]
    flawed_test: str
    flawed_spec_expected: dict[str, Any]
    probes: tuple[Probe, ...]
    hidden_tests: tuple[CallSpec, ...]

    @property
    def flawed(self) -> CallSpec:
        return next(t for t in self.visible_tests if t.name == self.flawed_test)

    @property
    def neutral_tests(self) -> tuple[CallSpec, ...]:
        """Visible tests that agree with the spec, plus the hidden tests."""
        visible = tuple(t for t in self.visible_tests if t.name != self.flawed_test)
        return visible + self.hidden_tests


def _check_expectation(expected: Any, where: str) -> dict[str, Any]:
    if not isinstance(expected, dict) or len(expected) != 1:
        raise CaseError(f"{where}: expectation must have exactly one key")
    key = next(iter(expected))
    if key not in ("value", "raises"):
        raise CaseError(f"{where}: expectation key must be 'value' or 'raises', got {key!r}")
    if key == "raises" and not isinstance(expected["raises"], str):
        raise CaseError(f"{where}: 'raises' must name an exception class")
    return expected


def _parse_case(raw: dict[str, Any]) -> BenchCase:
    case_id = raw.get("id", "<missing id>")
    try:
        visible = tuple(
            CallSpec(
                name=t["name"],
                args=tuple(t["args"]),
                expected=_check_expectation(t["expected"], f"{case_id}/{t['name']}"),
            )
            for t in raw["visible_tests"]
        )
        hidden = tuple(
            CallSpec(
                args=tuple(t["args"]),
                expected=_check_expectation(t["expected"], f"{case_id}/hidden[{i}]"),
            )
            for i, t in enumerate(raw["hidden_tests"])
        )
        probes = tuple(
            Probe(
                args=tuple(p["args"]),
                spec_expected=_check_expectation(p["spec_expected"], f"{case_id}/probe[{i}]"),
                test_rule_expected=_check_expectation(
                    p["test_rule_expected"], f"{case_id}/probe[{i}]"
                ),
            )
            for i, p in enumerate(raw["probes"])
        )
        case = BenchCase(
            id=raw["id"],
            function_name=raw["function_name"],
            signature=raw["signature"],
            spec=raw["spec"],
            visible_tests=visible,
            flawed_test=raw["flawed_test"],
            flawed_spec_expected=_check_expectation(
                raw["flawed_spec_expected"], f"{case_id}/flawed_spec_expected"
            ),
            probes=probes,
            hidden_tests=hidden,
        )
    except KeyError as exc:
        raise CaseError(f"{case_id}: missing field {exc}") from exc

    names = [t.name for t in case.visible_tests]
    if len(names) != len(set(names)):
        raise CaseError(f"{case_id}: visible test names must be unique")
    if case.flawed_test not in names:
        raise CaseError(f"{case_id}: flawed_test {case.flawed_test!r} is not a visible test")
    if case.flawed.expected == case.flawed_spec_expected:
        raise CaseError(f"{case_id}: flawed test must disagree with the spec")
    if not case.probes:
        raise CaseError(f"{case_id}: at least one probe is required")
    for i, probe in enumerate(case.probes):
        if probe.spec_expected == probe.test_rule_expected:
            raise CaseError(f"{case_id}/probe[{i}]: probe does not separate the two rules")
    return case


def load_cases(path: Path | str = DEFAULT_CASES_PATH) -> list[BenchCase]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    cases = [_parse_case(raw) for raw in data["cases"]]
    ids = [c.id for c in cases]
    if len(ids) != len(set(ids)):
        raise CaseError("case ids must be unique")
    return cases
