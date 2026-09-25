import pytest

from wrong_test_bench import CONDITIONS, build_prompt, load_cases, render_test_file

CASES = {c.id: c for c in load_cases()}


def test_rendered_test_file_is_valid_python():
    for case in CASES.values():
        compile(render_test_file(case), f"{case.id}_tests.py", "exec")


def test_rendered_file_contains_every_visible_test():
    for case in CASES.values():
        source = render_test_file(case)
        for test in case.visible_tests:
            assert f"def {test.name}():" in source


def test_raises_expectation_uses_pytest_raises():
    source = render_test_file(CASES["duration_no_days"])
    assert "import pytest" in source
    assert "with pytest.raises(ValueError):" in source


def test_prompt_never_reveals_which_test_is_wrong():
    for case in CASES.values():
        for condition in CONDITIONS:
            prompt = build_prompt(case, condition).lower()
            assert "flawed" not in prompt
            assert "wrong test" not in prompt


def test_conditions_differ_only_in_framing():
    case = CASES["chunk_keep_remainder"]
    neutral, pressure = (build_prompt(case, c) for c in ("neutral", "pressure"))
    assert neutral != pressure
    assert neutral.split("Signature:")[1] == pressure.split("Signature:")[1]


def test_unknown_condition_is_rejected():
    with pytest.raises(ValueError):
        build_prompt(CASES["chunk_keep_remainder"], "friendly")
