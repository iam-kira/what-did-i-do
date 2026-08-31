# Copyright (c) 2026 iam-kira (Vijay Biradar)
# Licensed under the MIT License. See LICENSE for the full text.

import aura

Q = '"'


def ev(source):
    result, error = aura.run('<stdin>', source, aura.new_symbol_table())
    if isinstance(result, list):
        result = result[-1] if result else None
    return result, error


def cook(text):
    """Wrap text in aura yap quotes."""
    return Q + text + Q


def test_a_name_in_a_hole():
    result, error = ev('stash n = 5\n' + cook('n is {n}'))
    assert error is None
    assert result.value == 'n is 5'


def test_any_expression_in_a_hole():
    for source, expected in ((cook('{1 + 2}'), '3'), (cook('{smol(4, 2)}'), '2')):
        result, error = ev(source)
        assert error is None, source
        assert result.value == expected, source


def test_several_holes_and_surrounding_text():
    result, error = ev(cook('a{1}b{2}c'))
    assert error is None
    assert result.value == 'a1b2c'


def test_adjacent_holes():
    result, error = ev('stash a = 1\nstash b = 2\n' + cook('{a}{b}'))
    assert error is None
    assert result.value == '12'


def test_non_yap_values_are_shown_as_they_repr():
    result, error = ev('stash xs = [1, 2]\n' + cook('{xs}'))
    assert error is None
    assert result.value == '[1, 2]'


def test_a_yap_inside_a_hole_keeps_no_quotes():
    result, error = ev('stash s = ' + cook('hi') + '\n' + cook('say {s}'))
    assert error is None
    assert result.value == 'say hi'


def test_a_yap_literal_inside_a_hole():
    result, error = ev(cook('{' + cook('inner') + '}'))
    assert error is None
    assert result.value == 'inner'


def test_a_bag_lookup_inside_a_hole():
    result, error = ev('stash d = {' + cook('a') + ': 1}\n' + cook('{d[' + cook('a') + ']}'))
    assert error is None
    assert result.value == '1'


def test_a_call_inside_a_hole():
    result, error = ev('chore f(n) ong\nyeet n * 2\nbet\n' + cook('doubled {f(4)}'))
    assert error is None
    assert result.value == 'doubled 8'


def test_doubled_braces_are_literal():
    result, error = ev(cook('literal {{brace}}'))
    assert error is None
    assert result.value == 'literal {brace}'


def test_a_yap_without_holes_is_untouched():
    result, error = ev(cook('no holes'))
    assert error is None
    assert result.value == 'no holes'


def test_escapes_still_work_alongside_holes():
    result, error = ev(cook('tab' + chr(92) + 'there {1}'))
    assert error is None
    assert result.value == 'tab\there 1'


def test_an_interpolated_yap_is_still_a_yap():
    result, error = ev('howmany(' + cook('{1}{2}') + ')')
    assert error is None
    assert repr(result) == '2'

    result, error = ev(cook('{1} {2}') + '[0]')
    assert error is None
    assert result.value == '1'


def test_an_empty_hole_is_rejected():
    result, error = ev(cook('{ }'))
    assert result is None
    assert 'Empty {} in a yap' in error.details


def test_a_broken_expression_in_a_hole_is_a_syntax_error():
    result, error = ev(cook('{1 +}'))
    assert result is None
    assert error.error_name == 'Invalid Syntax'


def test_two_statements_in_one_hole_are_rejected():
    result, error = ev(cook('{1; 2}'))
    assert result is None
    assert 'exactly one expression' in error.details


def test_an_unclosed_hole_reports_and_asks_for_more():
    result, error = ev(cook('unclosed {1')[:-1])
    assert result is None
    assert 'unterminated' in error.details
    assert aura.wants_more('<stdin>', Q + 'a {1')


def test_a_runtime_error_inside_a_hole_propagates():
    result, error = ev(cook('{1 / 0}'))
    assert result is None
    assert 'Division by zero' in error.details


def test_a_hole_error_is_catchable():
    result, error = ev('sus ong\n' + cook('{mystery}') + '\nwhoops e ong\ne[' + cook('why') + ']\nbet')
    assert error is None
    assert "'mystery' is not defined" in result.value
