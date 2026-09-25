from wrong_test_bench.runner import matches, run_function, values_equal


def test_returns_values_and_exceptions_per_call():
    code = "def f(x):\n    if x < 0:\n        raise ValueError('neg')\n    return x * 2\n"
    result = run_function(code, "f", [(2,), (-1,)])
    assert result.ok
    assert result.outcomes == [{"value": 4}, {"raises": "ValueError"}]


def test_prints_in_submitted_code_do_not_break_parsing():
    code = "print('hello')\ndef f():\n    print('noise')\n    return 1\n"
    result = run_function(code, "f", [()])
    assert result.outcomes == [{"value": 1}]


def test_syntax_error_is_a_load_error():
    result = run_function("def f(:\n", "f", [()])
    assert not result.ok
    assert result.load_error.startswith("SyntaxError")


def test_infinite_loop_times_out():
    result = run_function("def f():\n    while True:\n        pass\n", "f", [()], timeout=2)
    assert not result.ok
    assert result.load_error.startswith("Timeout")


def test_exit_inside_code_is_contained():
    result = run_function("import sys\nsys.exit(3)\n", "f", [()])
    assert not result.ok


def test_unserializable_return_is_marked():
    result = run_function("def f():\n    return object()\n", "f", [()])
    assert "unserializable" in result.outcomes[0]


def test_values_equal_tolerates_float_noise_only():
    assert values_equal(50.99, 50.990000001)
    assert not values_equal(50.99, 50.9915)
    assert values_equal([[1, 2], [3]], [[1, 2], [3]])
    assert not values_equal([[1, 2]], [[1, 2], [3]])
    assert not values_equal(True, 1)


def test_matches_checks_exception_name():
    assert matches({"raises": "ValueError"}, {"raises": "ValueError"})
    assert not matches({"raises": "TypeError"}, {"raises": "ValueError"})
    assert not matches({"value": 0}, {"raises": "ValueError"})
    assert matches({"value": 5400}, {"value": 5400})
