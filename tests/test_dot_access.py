import shit

Q = '"'


def ev(source):
    result, error = shit.run('<stdin>', source, shit.new_symbol_table())
    if isinstance(result, list):
        result = result[-1] if result else None
    return result, error


BAG = 'stash d = {' + Q + 'a' + Q + ': 1}\n'


def test_dot_reads_a_label():
    result, error = ev(BAG + 'd.a')
    assert error is None
    assert repr(result) == '1'


def test_dot_is_the_same_as_bracket_lookup():
    result, error = ev(BAG + 'd.a == d[' + Q + 'a' + Q + ']')
    assert error is None
    assert repr(result) == '1'


def test_dot_adds_a_label():
    result, error = ev(BAG + 'd.b = 2\nd')
    assert error is None
    assert repr(result) == '{"a": 1, "b": 2}'


def test_compound_assignment_through_a_dot():
    result, error = ev(BAG + 'd.a += 5\nd.a')
    assert error is None
    assert repr(result) == '6'


def test_calling_a_chore_through_a_dot():
    result, error = ev('chore f() ong\nyeet 7\nbet\nstash d = {' + Q + 'go' + Q + ': f}\nd.go()')
    assert error is None
    assert repr(result) == '7'


def test_dots_nest():
    source = ('stash d = {' + Q + 'in' + Q + ': {' + Q + 'deep' + Q + ': 3}}\nd.in.deep')
    result, error = ev(source)
    assert error is None
    assert repr(result) == '3'


def test_nested_dot_assignment():
    source = ('stash d = {' + Q + 'in' + Q + ': {' + Q + 'deep' + Q + ': 3}}\nd.in.deep = 9\nd.in.deep')
    result, error = ev(source)
    assert error is None
    assert repr(result) == '9'


def test_a_keyword_may_be_a_label():
    result, error = ev('stash d = {' + Q + 'chore' + Q + ': 1}\nd.chore')
    assert error is None
    assert repr(result) == '1'


def test_a_missing_label_still_reports():
    result, error = ev(BAG + 'd.nope')
    assert result is None
    assert 'No label' in error.details


def test_a_dot_with_no_label_is_a_syntax_error():
    result, error = ev(BAG + 'd.')
    assert result is None
    assert "Expected a label after '.'" in error.details


def test_dotting_a_pile_explains_itself():
    result, error = ev('stash xs = [1]\nxs.foo')
    assert result is None
    assert 'A pile is indexed by whole maths, not labels' in error.details


def test_float_literals_are_unaffected():
    for source, expected in (('1.5', '1.5'), ('0.25 * 4', '1'), ('1.5 + 1.5', '3')):
        result, error = ev(source)
        assert error is None, source
        assert repr(result) == expected, source


def test_dot_access_on_an_object_bag():
    source = (
        'chore counter() ong\n'
        'stash n = 0\n'
        'chore bump() ong\nn += 1\nyeet n\nbet\n'
        'yeet {' + Q + 'bump' + Q + ': bump}\n'
        'bet\n'
        'stash c = counter()\nc.bump()\nc.bump()'
    )
    result, error = ev(source)
    assert error is None
    assert repr(result) == '2'
