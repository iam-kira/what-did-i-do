import shit


def ev(source):
    result, error = shit.run('<stdin>', source, shit.SymbolTable())
    if isinstance(result, list):
        result = result[-1] if result else None
    return result, error


def test_for_loop_sums_range_end_exclusive():
    result, error = ev('var t = 0\nfor i = 1 to 5 then\nt = t + i\nend\nt')
    assert error is None
    assert repr(result) == '10'


def test_for_loop_with_step():
    result, error = ev('var t = 0\nfor i = 0 to 10 step 2 then\nt = t + i\nend\nt')
    assert error is None
    assert repr(result) == '20'


def test_for_loop_counts_down_with_negative_step():
    result, error = ev('var t = 0\nfor i = 5 to 0 step -1 then\nt = t + i\nend\nt')
    assert error is None
    assert repr(result) == '15'


def test_for_loop_body_never_runs_when_range_empty():
    result, error = ev('var t = 99\nfor i = 5 to 5 then\nt = 0\nend\nt')
    assert error is None
    assert repr(result) == '99'


def test_for_loop_variable_is_visible_after_loop():
    result, error = ev('for i = 0 to 3 then\n1\nend\ni')
    assert error is None
    assert repr(result) == '2'


def test_break_stops_the_loop():
    result, error = ev('var t = 0\nfor i = 0 to 10 then\nif i == 3 then\nbreak\nend\nt = t + i\nend\nt')
    assert error is None
    assert repr(result) == '3'


def test_continue_skips_one_iteration():
    result, error = ev('var t = 0\nfor i = 0 to 5 then\nif i == 2 then\ncontinue\nend\nt = t + i\nend\nt')
    assert error is None
    assert repr(result) == '8'


def test_break_in_while_loop():
    result, error = ev('var i = 0\nwhile true then\ni = i + 1\nif i > 4 then\nbreak\nend\nend\ni')
    assert error is None
    assert repr(result) == '5'


def test_return_exits_function_early():
    result, error = ev('fun f(n) then\nif n < 0 then\nreturn 0\nend\nreturn n * 2\nend\nf(-5)')
    assert error is None
    assert repr(result) == '0'


def test_bare_return_yields_zero():
    result, error = ev('fun f() then\nreturn\nend\nf()')
    assert error is None
    assert repr(result) == '0'


def test_return_unwinds_out_of_a_loop():
    result, error = ev('fun f() then\nwhile true then\nreturn 7\nend\nend\nf()')
    assert error is None
    assert repr(result) == '7'


def test_recursion_still_works():
    result, error = ev('fun fib(n) then\nif n < 2 then\nreturn n\nend\nreturn fib(n-1) + fib(n-2)\nend\nfib(10)')
    assert error is None
    assert repr(result) == '55'


def test_break_outside_loop_is_an_error():
    result, error = ev('break')
    assert result is None
    assert "'break' outside of a loop" in error.details


def test_continue_outside_loop_is_an_error():
    result, error = ev('continue')
    assert result is None
    assert "'continue' outside of a loop" in error.details


def test_return_outside_function_is_an_error():
    result, error = ev('return 1')
    assert result is None
    assert "'return' outside of a function" in error.details


def test_loop_signal_does_not_escape_a_call():
    result, error = ev('fun f() then\nreturn 1\nend\nfor i = 0 to 3 then\nf()\nend\ni')
    assert error is None
    assert repr(result) == '2'


def test_zero_step_is_rejected():
    result, error = ev('for i = 1 to 3 step 0 then\n1\nend')
    assert result is None
    assert "step cannot be 0" in error.details


def test_non_numeric_range_is_rejected():
    result, error = ev('fun f() then\n1\nend\nfor i = 1 to f then\n1\nend')
    assert result is None
    assert 'must be a number' in error.details
