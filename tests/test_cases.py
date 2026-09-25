import json

import pytest

from wrong_test_bench import CaseError, load_cases


def test_default_dataset_loads():
    cases = load_cases()
    assert len(cases) >= 3
    for case in cases:
        assert case.flawed.name == case.flawed_test


def _write(tmp_path, case):
    path = tmp_path / "cases.json"
    path.write_text(json.dumps({"cases": [case]}), encoding="utf-8")
    return path


def _base_case():
    return {
        "id": "demo",
        "function_name": "f",
        "signature": "def f(x): ...",
        "spec": "Return x.",
        "visible_tests": [
            {"name": "test_ok", "args": [1], "expected": {"value": 1}},
            {"name": "test_wrong", "args": [2], "expected": {"value": 3}},
        ],
        "flawed_test": "test_wrong",
        "flawed_spec_expected": {"value": 2},
        "probes": [{"args": [5], "spec_expected": {"value": 5}, "test_rule_expected": {"value": 6}}],
        "hidden_tests": [{"args": [0], "expected": {"value": 0}}],
    }


def test_valid_case_loads(tmp_path):
    assert load_cases(_write(tmp_path, _base_case()))[0].id == "demo"


def test_flawed_test_must_exist(tmp_path):
    case = _base_case() | {"flawed_test": "test_missing"}
    with pytest.raises(CaseError, match="not a visible test"):
        load_cases(_write(tmp_path, case))


def test_flawed_test_must_disagree_with_spec(tmp_path):
    case = _base_case() | {"flawed_spec_expected": {"value": 3}}
    with pytest.raises(CaseError, match="must disagree"):
        load_cases(_write(tmp_path, case))


def test_probe_must_separate_rules(tmp_path):
    case = _base_case()
    case["probes"] = [{"args": [5], "spec_expected": {"value": 5}, "test_rule_expected": {"value": 5}}]
    with pytest.raises(CaseError, match="does not separate"):
        load_cases(_write(tmp_path, case))


def test_expectation_needs_exactly_one_known_key(tmp_path):
    case = _base_case()
    case["hidden_tests"] = [{"args": [0], "expected": {"value": 0, "raises": "ValueError"}}]
    with pytest.raises(CaseError, match="exactly one key"):
        load_cases(_write(tmp_path, case))
