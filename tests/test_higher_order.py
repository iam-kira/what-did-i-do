import shit

Q = '"'

PRELUDE = (
    'chore dbl(n) ong\nyeet n * 2\nbet\n'
    'chore odd(n) ong\nyeet n % 2 == 1\nbet\n'
    'chore add(a, b) ong\nyeet a + b\nbet\n'
    'chore lastchar(s) ong\nyeet s[-1]\nbet\n'
)


def ev(source, prelude=True):
    text = (PRELUDE if prelude else '') + source
    result, error = shit.run('<stdin>', text, shit.new_symbol_table())
    if isinstance(result, list):
        result = result[-1] if result else None
    return result, error


def check(cases):
    for source, expected in cases.items():
        result, error = ev(source)
        assert error is None, (source, error.details if error else None)
        assert repr(result) == expected, source


def test_eachof_maps():
    check({'eachof([1, 2, 3], dbl)': '[2, 4, 6]', 'eachof([], dbl)': '[]'})


def test_eachof_works_with_a_builtin():
    check({'eachof([' + Q + 'a' + Q + '], shout)': '["A"]'})


def test_keepif_filters():
    check({
        'keepif([1, 2, 3, 4, 5], odd)': '[1, 3, 5]',
        'keepif([2, 4], odd)': '[]',
    })


def test_smoosh_reduces():
    check({
        'smoosh([1, 2, 3, 4], add)': '10',
        'smoosh([5], add)': '5',
        'smoosh([1, 2], add, 10)': '13',
    })


def test_smoosh_of_an_empty_pile_needs_a_start():
    check({'smoosh([], add, 0)': '0'})

    result, error = ev('smoosh([], add)')
    assert result is None
    assert 'needs a starting value' in error.details


def test_sortof_still_sorts_without_a_chore():
    check({'sortof([3, 1, 2])': '[1, 2, 3]'})


def test_sortof_takes_a_key_chore():
    check({
        'sortof([' + Q + 'bx' + Q + ', ' + Q + 'az' + Q + ', ' + Q + 'cy' + Q + '], lastchar)':
            '["bx", "cy", "az"]',
    })


def test_sortof_key_must_be_a_math_or_yap():
    result, error = ev('chore boxed(n) ong\nyeet [n]\nbet\nsortof([1, 2], boxed)')
    assert result is None
    assert 'sort key must be a math or a yap' in error.details


def test_sortof_rejects_mixed_key_types():
    source = ('chore mixed(n) ong\nfr n == 1 ong\nyeet 1\nbet\nyeet ' + Q + 'a' + Q + '\nbet\n'
              'sortof([1, 2], mixed)')
    result, error = ev(source)
    assert result is None
    assert 'all maths or all yaps' in error.details


def test_a_closure_can_be_passed_in():
    source = ('chore times(k) ong\nchore go(n) ong\nyeet n * k\nbet\nyeet go\nbet\n'
              'eachof([1, 2, 3], times(10))')
    result, error = ev(source)
    assert error is None
    assert repr(result) == '[10, 20, 30]'


def test_the_pile_is_not_mutated():
    result, error = ev('stash xs = [3, 1]\neachof(xs, dbl)\nsortof(xs)\nxs')
    assert error is None
    assert repr(result) == '[3, 1]'


def test_an_error_inside_the_chore_propagates():
    result, error = ev('eachof([1], howmany)')
    assert result is None
    assert "'howmany' needs a yap, pile or bag" in error.details


def test_wrong_arity_is_reported():
    result, error = ev('smoosh([1, 2], dbl)')
    assert result is None
    assert "'dbl' takes 1 argument(s), got 2" in error.details


def test_passing_something_that_is_not_a_chore():
    result, error = ev('eachof([1], 5)')
    assert result is None
    assert 'is not a chore' in error.details


def test_first_argument_must_be_a_pile():
    for source in ('eachof(5, dbl)', 'keepif(5, odd)', 'smoosh(5, add)'):
        result, error = ev(source)
        assert result is None, source
        assert 'needs a pile' in error.details, source


def test_an_error_inside_a_chore_is_catchable():
    source = ('risky ong\neachof([1], howmany)\nwhoops e ong\n' + Q + 'caught' + Q + '\nbet')
    result, error = ev(source)
    assert error is None
    assert result.value == 'caught'
