import aura


def ev(source):
    result, error = aura.run('<stdin>', source, aura.SymbolTable())
    if isinstance(result, list):
        result = result[-1] if result else None
    return result, error


def test_for_loop_sums_range_end_exclusive():
    result, error = ev('stash t = 0\ngrind i = 1 til 5 ong\nt = t + i\nbet\nt')
    assert error is None
    assert repr(result) == '10'


def test_for_loop_with_step():
    result, error = ev('stash t = 0\ngrind i = 0 til 10 by 2 ong\nt = t + i\nbet\nt')
    assert error is None
    assert repr(result) == '20'


def test_for_loop_counts_down_with_negative_step():
    result, error = ev('stash t = 0\ngrind i = 5 til 0 by -1 ong\nt = t + i\nbet\nt')
    assert error is None
    assert repr(result) == '15'


def test_for_loop_body_never_runs_when_range_empty():
    result, error = ev('stash t = 99\ngrind i = 5 til 5 ong\nt = 0\nbet\nt')
    assert error is None
    assert repr(result) == '99'


def test_for_loop_variable_is_visible_after_loop():
    result, error = ev('grind i = 0 til 3 ong\n1\nbet\ni')
    assert error is None
    assert repr(result) == '2'


def test_break_stops_the_loop():
    result, error = ev('stash t = 0\ngrind i = 0 til 10 ong\nfr i == 3 ong\nbail\nbet\nt = t + i\nbet\nt')
    assert error is None
    assert repr(result) == '3'


def test_continue_skips_one_iteration():
    result, error = ev('stash t = 0\ngrind i = 0 til 5 ong\nfr i == 2 ong\nskip\nbet\nt = t + i\nbet\nt')
    assert error is None
    assert repr(result) == '8'


def test_break_in_while_loop():
    result, error = ev('stash i = 0\nkeep based ong\ni = i + 1\nfr i > 4 ong\nbail\nbet\nbet\ni')
    assert error is None
    assert repr(result) == '5'


def test_return_exits_function_early():
    result, error = ev('chore f(n) ong\nfr n < 0 ong\nyeet 0\nbet\nyeet n * 2\nbet\nf(-5)')
    assert error is None
    assert repr(result) == '0'


def test_bare_return_yields_zero():
    result, error = ev('chore f() ong\nyeet\nbet\nf()')
    assert error is None
    assert repr(result) == '0'


def test_return_unwinds_out_of_a_loop():
    result, error = ev('chore f() ong\nkeep based ong\nyeet 7\nbet\nbet\nf()')
    assert error is None
    assert repr(result) == '7'


def test_recursion_still_works():
    result, error = ev('chore fib(n) ong\nfr n < 2 ong\nyeet n\nbet\nyeet fib(n-1) + fib(n-2)\nbet\nfib(10)')
    assert error is None
    assert repr(result) == '55'


def test_break_outside_loop_is_an_error():
    result, error = ev('bail')
    assert result is None
    assert "'bail' outside of a loop" in error.details


def test_continue_outside_loop_is_an_error():
    result, error = ev('skip')
    assert result is None
    assert "'skip' outside of a loop" in error.details


def test_return_outside_function_is_an_error():
    result, error = ev('yeet 1')
    assert result is None
    assert "'yeet' outside of a function" in error.details


def test_loop_signal_does_not_escape_a_call():
    result, error = ev('chore f() ong\nyeet 1\nbet\ngrind i = 0 til 3 ong\nf()\nbet\ni')
    assert error is None
    assert repr(result) == '2'


def test_zero_step_is_rejected():
    result, error = ev('grind i = 1 til 3 by 0 ong\n1\nbet')
    assert result is None
    assert "by cannot be 0" in error.details


def test_non_numeric_range_is_rejected():
    result, error = ev('chore f() ong\n1\nbet\ngrind i = 1 til f ong\n1\nbet')
    assert result is None
    assert 'must be a math' in error.details
