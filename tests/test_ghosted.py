"""ghosted is a value of its own, not another spelling of 0.

Copyright (c) 2026 iam-kira (Vijay Biradar)
Licensed under the MIT License. See LICENSE for the full text.
"""

import aura

Q = '"'


def ev(source):
    result, error = aura.run('<stdin>', source, aura.new_symbol_table())
    if isinstance(result, list):
        result = result[-1] if result else None
    return result, error


def check(cases):
    for source, expected in cases.items():
        result, error = ev(source)
        assert error is None, (source, error.details if error else None)
        assert repr(result) == expected, (source, repr(result), expected)


def test_it_prints_as_itself():
    check({'ghosted': 'ghosted'})


def test_it_is_not_zero_and_not_false():
    check({
        'ghosted == 0': '0',
        'ghosted == cringe': '0',
        'ghosted != 0': '1',
        '0 == ghosted': '0',
        'cringe == ghosted': '0',
    })


def test_it_equals_only_itself():
    check({'ghosted == ghosted': '1', 'ghosted != ghosted': '0'})


def test_it_is_not_equal_to_other_types():
    check({
        'ghosted == ' + Q + Q: '0',
        'ghosted == []': '0',
        'ghosted == {}': '0',
        Q + Q + ' == ghosted': '0',
        '[] == ghosted': '0',
    })


def test_it_is_falsy():
    check({
        'nah ghosted': '1',
        'ghosted also 1': '0',
        'ghosted orelse 5': '1',
    })

    result, error = ev('fr ghosted ong\n1\nwhatever\n2\nbet')
    assert error is None
    assert repr(result) == '2'


def test_whatis_tells_the_truth_about_it():
    check({'whatis(ghosted)': '"ghosted"'})


def test_is_ghosted_asks_the_question():
    check({
        'is_ghosted(ghosted)': '1',
        'is_ghosted(0)': '0',
        'is_ghosted(' + Q + Q + ')': '0',
        'is_ghosted([])': '0',
        'is_math(ghosted)': '0',
    })


def test_arithmetic_on_it_is_an_error_not_a_silent_zero():
    """The whole point: a missing value surfaces where it went missing."""
    for source in ('ghosted + 1', '1 + ghosted', 'ghosted * 2', 'ghosted - 1', 'ghosted / 1'):
        result, error = ev(source)
        assert result is None, source
        assert error.kind == 'type', source
        assert 'ghosted' in error.details, source


def test_ordering_it_is_an_error():
    for source in ('ghosted < 1', 'ghosted > 1', '1 <= ghosted'):
        result, error = ev(source)
        assert result is None, source
        assert error.kind == 'type', source


def test_it_lives_happily_in_piles_and_bags():
    check({
        '[ghosted]': '[ghosted]',
        '[ghosted] == [ghosted]': '1',
        '[ghosted] == [0]': '0',
        '{' + Q + 'a' + Q + ': ghosted}': '{"a": ghosted}',
        'howmany([ghosted, ghosted])': '2',
    })


def test_a_bag_can_hold_it_and_give_it_back():
    result, error = ev('stash b = {}\nb.missing = ghosted\nis_ghosted(b.missing)')
    assert error is None
    assert repr(result) == '1'


def test_it_can_be_stashed_and_returned():
    check({'stash x = ghosted\nx': 'ghosted'})

    result, error = ev('chore nothing() ong\nyeet ghosted\nbet\nis_ghosted(nothing())')
    assert error is None
    assert repr(result) == '1'


def test_yapify_names_it():
    check({'yapify(ghosted)': '"ghosted"'})


def test_it_cannot_be_a_bag_label():
    result, error = ev('stash b = {}\nb[ghosted] = 1')
    assert result is None
    assert error.kind == 'label'


def test_it_is_not_indexable_and_has_no_length():
    for source in ('ghosted[0]', 'howmany(ghosted)'):
        result, error = ev(source)
        assert result is None, source
        assert error.kind in ('index', 'type'), source


def test_it_survives_a_round_trip_through_a_chore():
    source = ('chore pass_through(x) ong\nyeet x\nbet\n'
              '[is_ghosted(pass_through(ghosted)), is_ghosted(pass_through(0))]')
    result, error = ev(source)
    assert error is None
    assert repr(result) == '[1, 0]'


def test_missing_and_zero_are_finally_distinguishable():
    """The reason this type exists at all."""
    source = (
        'stash scores = {' + Q + 'ana' + Q + ': 0, ' + Q + 'bo' + Q + ': ghosted}\n'
        'chore describe(v) ong\n'
        'fr is_ghosted(v) ong\n'
        'yeet ' + Q + 'did not play' + Q + '\n'
        'bet\n'
        'yeet ' + Q + 'scored nothing' + Q + '\n'
        'bet\n'
        '[describe(scores.ana), describe(scores.bo)]'
    )
    result, error = ev(source)
    assert error is None
    assert repr(result) == '["scored nothing", "did not play"]'
