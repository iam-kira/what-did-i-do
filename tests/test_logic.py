import shit

Q = '"'


def ev(source):
    """Run source in a fresh scope, returning (last value, error)."""
    result, error = shit.run('<stdin>', source, shit.new_symbol_table())
    if isinstance(result, list):
        result = result[-1] if result else None
    return result, error


def test_boolean_and_null_literals():
    for source, expected in (('based', '1'), ('cringe', '0'), ('ghosted', '0')):
        result, error = ev(source)
        assert error is None
        assert repr(result) == expected


def test_not_operator():
    for source, expected in (('nah based', '0'), ('nah cringe', '1'), ('nah 5', '0'), ('nah 0', '1')):
        result, error = ev(source)
        assert error is None
        assert repr(result) == expected


def test_and_or_truth_table():
    cases = {
        '1 also 1': '1', '1 also 0': '0', '0 also 1': '0', '0 also 0': '0',
        '1 orelse 1': '1', '1 orelse 0': '1', '0 orelse 1': '1', '0 orelse 0': '0',
    }
    for source, expected in cases.items():
        result, error = ev(source)
        assert error is None, source
        assert repr(result) == expected, source


def test_logic_precedence_below_comparison():
    result, error = ev('1 < 2 also 3 > 2')
    assert error is None
    assert repr(result) == '1'


def test_and_binds_tighter_than_or():
    result, error = ev('cringe also cringe orelse based')
    assert error is None
    assert repr(result) == '1'


def test_not_is_right_associative():
    result, error = ev('nah nah 5')
    assert error is None
    assert repr(result) == '1'


def test_exact_int_division_stays_int():
    result, error = ev('4 / 2')
    assert error is None
    assert isinstance(result.value, int)
    assert repr(result) == '2'


def test_inexact_division_is_float():
    result, error = ev('5 / 2')
    assert error is None
    assert repr(result) == '2.5'


def test_illegal_operation_on_function():
    result, error = ev('chore f() ong 1 bet\nf + 1')
    assert result is None
    assert error.error_name == 'Runtime Error'
    assert 'Illegal operation' in error.details


def test_function_compares_unequal_to_number():
    result, error = ev('chore f() ong 1 bet\nf == 1')
    assert error is None
    assert repr(result) == '0'


def test_also_short_circuits():
    """The right side must not run when the left already decides it."""
    result, error = ev('cringe also (1 / 0)')
    assert error is None
    assert repr(result) == '0'


def test_orelse_short_circuits():
    result, error = ev('based orelse (1 / 0)')
    assert error is None
    assert repr(result) == '1'


def test_also_still_evaluates_the_right_when_it_matters():
    result, error = ev('based also (1 / 0)')
    assert result is None
    assert 'Division by zero' in error.details


def test_short_circuit_guards_an_index():
    result, error = ev('stash xs = []\n0 < howmany(xs) also xs[0] == 1')
    assert error is None
    assert repr(result) == '0'

    result, error = ev('stash xs = [1]\n0 < howmany(xs) also xs[0] == 1')
    assert error is None
    assert repr(result) == '1'


def test_logic_operators_always_give_back_1_or_0():
    for source, expected in (('5 also 3', '1'), (Q + 'a' + Q + ' orelse 0', '1'),
                             ('[] orelse []', '0')):
        result, error = ev(source)
        assert error is None, source
        assert repr(result) == expected, source
