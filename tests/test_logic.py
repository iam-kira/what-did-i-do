import shit


def ev(source):
    """Run source in a fresh scope, returning (last value, error)."""
    result, error = shit.run('<stdin>', source, shit.SymbolTable())
    if isinstance(result, list):
        result = result[-1] if result else None
    return result, error


def test_boolean_and_null_literals():
    for source, expected in (('true', '1'), ('false', '0'), ('null', '0')):
        result, error = ev(source)
        assert error is None
        assert repr(result) == expected


def test_not_operator():
    for source, expected in (('not true', '0'), ('not false', '1'), ('not 5', '0'), ('not 0', '1')):
        result, error = ev(source)
        assert error is None
        assert repr(result) == expected


def test_and_or_truth_table():
    cases = {
        '1 and 1': '1', '1 and 0': '0', '0 and 1': '0', '0 and 0': '0',
        '1 or 1': '1', '1 or 0': '1', '0 or 1': '1', '0 or 0': '0',
    }
    for source, expected in cases.items():
        result, error = ev(source)
        assert error is None, source
        assert repr(result) == expected, source


def test_logic_precedence_below_comparison():
    result, error = ev('1 < 2 and 3 > 2')
    assert error is None
    assert repr(result) == '1'


def test_and_binds_tighter_than_or():
    result, error = ev('false and false or true')
    assert error is None
    assert repr(result) == '1'


def test_not_is_right_associative():
    result, error = ev('not not 5')
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
    result, error = ev('fun f() then 1 end\nf + 1')
    assert result is None
    assert error.error_name == 'Runtime Error'
    assert 'Illegal operation' in error.details


def test_function_compares_unequal_to_number():
    result, error = ev('fun f() then 1 end\nf == 1')
    assert error is None
    assert repr(result) == '0'
