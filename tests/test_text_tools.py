"""The text and pairing builtins, including the edges that bite.

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


def yap(text):
    return Q + text + Q


# --- where / gotit: substrings on yaps, elements on piles ---

def test_where_finds_a_substring():
    check({
        'where(' + yap('hello') + ', ' + yap('ll') + ')': '2',
        'where(' + yap('hello world') + ', ' + yap('o w') + ')': '4',
        'where(' + yap('hello') + ', ' + yap('h') + ')': '0',
        'where(' + yap('hello') + ', ' + yap('zz') + ')': '-1',
    })


def test_an_empty_needle_is_found_at_the_start():
    """Matches every other language: "".find("") is 0."""
    check({'where(' + yap('abc') + ', ' + yap('') + ')': '0'})


def test_a_needle_longer_than_the_haystack():
    check({'where(' + yap('ab') + ', ' + yap('abcdef') + ')': '-1'})


def test_gotit_finds_a_substring():
    check({
        'gotit(' + yap('hello world') + ', ' + yap('lo w') + ')': '1',
        'gotit(' + yap('hello') + ', ' + yap('zz') + ')': '0',
    })


def test_searching_a_yap_needs_a_yap():
    result, error = ev('where(' + yap('abc') + ', 1)')
    assert result is None
    assert error.kind == 'type'
    assert 'needs a yap to look for' in error.details


def test_piles_still_search_by_element():
    check({
        'where([1, 2, 3], 2)': '1',
        'where([[1], [2]], [2])': '1',
        'gotit([1, 2], 9)': '0',
    })


def test_bags_still_search_by_label():
    check({'gotit({' + yap('a') + ': 1}, ' + yap('a') + ')': '1'})


def test_gotit_reports_the_real_error_not_its_own():
    result, error = ev('gotit(1, 2)')
    assert result is None
    assert 'needs a yap, pile or bag' in error.details


# --- swap ---

def test_swap_replaces_every_occurrence():
    check({
        'swap(' + yap('a-b-c') + ', ' + yap('-') + ', ' + yap('+') + ')': '"a+b+c"',
        'swap(' + yap('aaa') + ', ' + yap('aa') + ', ' + yap('b') + ')': '"ba"',
        'swap(' + yap('abc') + ', ' + yap('z') + ', ' + yap('!') + ')': '"abc"',
    })


def test_swap_can_delete():
    check({'swap(' + yap('a b c') + ', ' + yap(' ') + ', ' + yap('') + ')': '"abc"'})


def test_swap_refuses_an_empty_needle():
    """Otherwise it would splice between every character."""
    result, error = ev('swap(' + yap('abc') + ', ' + yap('') + ', ' + yap('x') + ')')
    assert result is None
    assert 'empty yap' in error.details


def test_swap_needs_yaps():
    result, error = ev('swap(1, ' + yap('a') + ', ' + yap('b') + ')')
    assert result is None
    assert error.kind == 'type'


# --- starts / ends ---

def test_starts_and_ends():
    check({
        'starts(' + yap('hello') + ', ' + yap('he') + ')': '1',
        'starts(' + yap('hello') + ', ' + yap('lo') + ')': '0',
        'ends(' + yap('hello') + ', ' + yap('lo') + ')': '1',
        'ends(' + yap('hello') + ', ' + yap('he') + ')': '0',
    })


def test_everything_starts_and_ends_with_nothing():
    check({
        'starts(' + yap('abc') + ', ' + yap('') + ')': '1',
        'ends(' + yap('abc') + ', ' + yap('') + ')': '1',
    })


def test_a_yap_starts_and_ends_with_itself():
    check({
        'starts(' + yap('abc') + ', ' + yap('abc') + ')': '1',
        'ends(' + yap('abc') + ', ' + yap('abc') + ')': '1',
    })


# --- code / letter ---

def test_code_and_letter_round_trip():
    check({
        'code(' + yap('A') + ')': '65',
        'letter(65)': '"A"',
        'letter(code(' + yap('z') + '))': '"z"',
        'code(' + yap(' ') + ')': '32',
    })


def test_code_needs_exactly_one_character():
    for source in ('code(' + yap('ab') + ')', 'code(' + yap('') + ')'):
        result, error = ev(source)
        assert result is None, source
        assert 'exactly one character' in error.details


def test_letter_rejects_impossible_numbers():
    for source in ('letter(0 - 1)', 'letter(9999999)'):
        result, error = ev(source)
        assert result is None, source
        assert 'not a character' in error.details


def test_letter_handles_non_ascii():
    result, error = ev('code(letter(233))')
    assert error is None
    assert repr(result) == '233'


def test_code_and_letter_enable_a_caesar_shift():
    source = (
        'chore shift(text, step) ong\n'
        'stash out = ""\n'
        'grind c among text ong\n'
        'out += letter(code(c) + step)\n'
        'bet\n'
        'yeet out\n'
        'bet\n'
        'shift(shift(' + yap('abc') + ', 1), 0 - 1)'
    )
    result, error = ev(source)
    assert error is None
    assert result.value == 'abc'


# --- numbered / pair ---

def test_numbered_indexes_a_pile():
    check({
        'numbered([' + yap('a') + ', ' + yap('b') + '])': '[[0, "a"], [1, "b"]]',
        'numbered([])': '[]',
    })


def test_numbered_works_on_a_yap():
    check({'numbered(' + yap('ab') + ')': '[[0, "a"], [1, "b"]]'})


def test_numbered_feeds_a_two_name_grind():
    source = ('stash out = []\ngrind i, x among numbered([' + yap('a') + ', ' + yap('b') + ']) ong\n'
              'out = stuff(out, "{i}{x}")\nbet\nout')
    result, error = ev(source)
    assert error is None
    assert repr(result) == '["0a", "1b"]'


def test_pair_zips_two_piles():
    check({
        'pair([1, 2], [' + yap('a') + ', ' + yap('b') + '])': '[[1, "a"], [2, "b"]]',
        'pair([], [1])': '[]',
    })


def test_pair_stops_at_the_shorter_pile():
    check({
        'pair([1, 2, 3], [' + yap('a') + '])': '[[1, "a"]]',
        'pair([1], [' + yap('a') + ', ' + yap('b') + '])': '[[1, "a"]]',
    })


def test_pair_needs_two_piles():
    result, error = ev('pair([1], ' + yap('ab') + ')')
    assert result is None
    assert error.kind == 'type'
    assert 'needs a pile' in error.details


def test_numbered_and_pair_copy_their_input():
    result, error = ev('stash xs = [[1]]\nstash n = numbered(xs)\nn[0][1][0] = 9\nxs')
    assert error is None
    assert repr(result) == '[[1]]'


# --- the brace escape, which a JSON-shaped program needs ---

def test_a_literal_brace_can_be_written():
    for source, expected in (('"{{"', '"{"'), ('"}}"', '"}"'), (Q + chr(92) + '{' + Q, '"{"')):
        result, error = ev(source)
        assert error is None, source
        assert repr(result) == expected, source


def test_the_brace_error_says_how_to_fix_it():
    result, error = ev('"{"')
    assert result is None
    assert 'literal one' in error.details


# --- keywords cannot be names, and the error says so ---

def test_a_keyword_as_a_name_explains_itself():
    cases = {
        'chore shift(text, by) ong@yeet 1@bet': "'by' is a keyword",
        'stash keep = 1': "'keep' is a keyword",
        'chore bet() ong@1@bet': "'bet' is a keyword",
        'grind among = 1 til 2 ong@1@bet': "'among' is a keyword",
        'stash x, also = [1, 2]': "'also' is a keyword",
        'sus ong@1@whoops bet ong@1@bet': "'bet' is a keyword",
    }
    for source, expected in cases.items():
        result, error = ev(source.replace('@', chr(10)))
        assert result is None, source
        assert expected in error.details, (source, error.details)


def test_a_builtin_name_is_still_usable_as_a_variable():
    """Builtins live in a scope you can shadow; keywords you cannot."""
    result, error = ev('stash code = 5@code'.replace('@', chr(10)))
    assert error is None
    assert repr(result) == '5'
