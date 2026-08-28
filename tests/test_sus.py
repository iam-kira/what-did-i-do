import aura

Q = '"'


def ev(source):
    result, error = aura.run('<stdin>', source, aura.new_symbol_table())
    if isinstance(result, list):
        result = result[-1] if result else None
    return result, error


def test_a_runtime_error_is_caught():
    result, error = ev('sus ong\n1 / 0\nwhoops e ong\n"caught"\nbet')
    assert error is None
    assert result.value == 'caught'


def test_the_body_value_survives_when_nothing_goes_wrong():
    result, error = ev('sus ong\n41 + 1\nwhoops e ong\n0\nbet')
    assert error is None
    assert repr(result) == '42'


def test_the_whoops_bag_carries_why_kind_file_and_line():
    result, error = ev('sus ong\n\n1 / 0\nwhoops e ong\ne\nbet')
    assert error is None
    assert repr(result) == (
        '{"why": "Division by zero", "kind": "math", "file": "<stdin>", "line": 3}'
    )


def test_oops_raises_a_yap():
    result, error = ev('oops ' + Q + 'nope' + Q)
    assert result is None
    assert error.details == 'nope'


def test_oops_can_raise_anything():
    result, error = ev('oops 42')
    assert result is None
    assert error.details == '42'


def test_oops_is_catchable():
    result, error = ev('sus ong\noops ' + Q + 'boom' + Q + '\nwhoops e ong\ne[' + Q + 'why' + Q + ']\nbet')
    assert error is None
    assert result.value == 'boom'


def test_catching_inside_a_chore_and_returning_from_the_whoops():
    source = ('chore safe(a, b) ong\nsus ong\nyeet a / b\nwhoops e ong\nyeet -1\nbet\nbet\n'
              'safe(10, 0)')
    result, error = ev(source)
    assert error is None
    assert repr(result) == '-1'


def test_returning_from_the_risky_body_still_works():
    source = 'chore safe(a, b) ong\nsus ong\nyeet a / b\nwhoops e ong\nyeet -1\nbet\nbet\nsafe(10, 2)'
    result, error = ev(source)
    assert error is None
    assert repr(result) == '5'


def test_bail_inside_a_risky_still_breaks_the_loop():
    source = ('stash n = 0\ngrind i = 0 til 5 ong\nsus ong\nfr i == 2 ong\nbail\nbet\n'
              'n += 1\nwhoops e ong\n0\nbet\nbet\nn')
    result, error = ev(source)
    assert error is None
    assert repr(result) == '2'


def test_errors_in_the_whoops_are_not_caught_by_it():
    result, error = ev('sus ong\n1 / 0\nwhoops e ong\nnope_at_all\nbet')
    assert result is None
    assert "'nope_at_all' is not defined" in error.details


def test_nested_risky_catches_at_the_inner_level():
    source = ('sus ong\nsus ong\n1 / 0\nwhoops inner ong\noops ' + Q + 'rethrown' + Q + '\nbet\n'
              'whoops outer ong\nouter[' + Q + 'why' + Q + ']\nbet')
    result, error = ev(source)
    assert error is None
    assert result.value == 'rethrown'


def test_a_caught_program_keeps_going():
    source = 'sus ong\n1 / 0\nwhoops e ong\n0\nbet\n7'
    result, error = ev(source)
    assert error is None
    assert repr(result) == '7'


def test_missing_whoops_is_a_syntax_error():
    result, error = ev('sus ong\n1\nbet')
    assert result is None
    assert "Expected 'whoops'" in error.details


def test_whoops_needs_a_name():
    result, error = ev('sus ong\n1\nwhoops ong\n2\nbet')
    assert result is None
    assert 'Expected a name for the whoops' in error.details


def test_undefined_name_is_catchable():
    result, error = ev('sus ong\nmystery\nwhoops e ong\ne[' + Q + 'why' + Q + ']\nbet')
    assert error is None
    assert "'mystery' is not defined" in result.value


def test_runaway_recursion_is_catchable():
    source = ('chore boom(n) ong\nyeet boom(n + 1)\nbet\n'
              'sus ong\nboom(0)\nwhoops e ong\n' + Q + 'stopped' + Q + '\nbet')
    result, error = ev(source)
    assert error is None
    assert result.value == 'stopped'
