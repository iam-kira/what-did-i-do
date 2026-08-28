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
        assert repr(result) == expected, source


# --- maths ---

def test_smol_and_chonk_take_loose_args_or_a_pile():
    check({
        'smol(3, 1, 2)': '1',
        'smol([3, 1, 2])': '1',
        'chonk(3, 1, 2)': '3',
        'chonk([4, 9, 2])': '9',
        'smol(5)': '5',
    })


def test_total_absolutely_and_roundish():
    check({
        'total([1, 2, 3])': '6',
        'total(1, 2)': '3',
        'absolutely(-7)': '7',
        'absolutely(7)': '7',
        'roundish(3.7)': '4',
        'roundish(3.14159, 2)': '3.14',
    })


def test_empty_pile_has_no_smallest():
    result, error = ev('smol([])')
    assert result is None
    assert 'at least one math' in error.details


def test_maths_only():
    result, error = ev('smol(' + Q + 'a' + Q + ', 1)')
    assert result is None
    assert "'smol' needs a math, got yap" in error.details


# --- piles and yaps ---

def test_chunk_slices_both_kinds():
    check({
        'chunk([1, 2, 3, 4], 1, 3)': '[2, 3]',
        'chunk([1, 2, 3], 1)': '[2, 3]',
        'chunk(' + Q + 'hello' + Q + ', 1)': '"ello"',
        'chunk(' + Q + 'hello' + Q + ', -2)': '"lo"',
        'chunk(' + Q + 'hello' + Q + ', 0, 2)': '"he"',
    })


def test_chunk_clamps_instead_of_exploding():
    check({'chunk([1, 2], 0, 99)': '[1, 2]', 'chunk([1, 2], -99, 1)': '[1]'})


def test_flip_reverses_both_kinds():
    check({'flip([1, 2, 3])': '[3, 2, 1]', 'flip(' + Q + 'abc' + Q + ')': '"cba"'})


def test_glue_and_shred_round_trip():
    check({
        'glue([' + Q + 'a' + Q + ', ' + Q + 'b' + Q + '], ' + Q + '-' + Q + ')': '"a-b"',
        'glue([1, 2])': '"12"',
        'shred(' + Q + 'a,b' + Q + ', ' + Q + ',' + Q + ')': '["a", "b"]',
        'shred(' + Q + 'one two' + Q + ')': '["one", "two"]',
        'shred(' + Q + 'abc' + Q + ', ' + Q + Q + ')': '["a", "b", "c"]',
    })


def test_yap_case_and_trim():
    check({
        'shout(' + Q + 'hi' + Q + ')': '"HI"',
        'whisper(' + Q + 'HI' + Q + ')': '"hi"',
        'trim(' + Q + '  x  ' + Q + ')': '"x"',
    })


def test_where_and_gotit():
    check({
        'where([1, 2, 3], 2)': '1',
        'where([1, 2, 3], 9)': '-1',
        'where(' + Q + 'hello' + Q + ', ' + Q + 'l' + Q + ')': '2',
        'gotit([1, 2], 2)': '1',
        'gotit([1, 2], 9)': '0',
        'gotit(' + Q + 'hello' + Q + ', ' + Q + 'e' + Q + ')': '1',
    })


def test_sortof_does_not_touch_the_original():
    check({
        'sortof([3, 1, 2])': '[1, 2, 3]',
        'sortof([' + Q + 'b' + Q + ', ' + Q + 'a' + Q + '])': '["a", "b"]',
        'sortof([])': '[]',
    })

    result, error = ev('stash xs = [3, 1]\nsortof(xs)\nxs')
    assert error is None
    assert repr(result) == '[3, 1]'


def test_sortof_refuses_a_mixed_pile():
    result, error = ev('sortof([1, ' + Q + 'a' + Q + '])')
    assert result is None
    assert 'all maths or all yaps' in error.details


def test_whatis_reports_dialect_type_names():
    check({
        'whatis(1)': '"math"',
        'whatis(' + Q + 'x' + Q + ')': '"yap"',
        'whatis([])': '"pile"',
        'whatis(cook)': '"chore"',
    })


# --- arity ---

def test_optional_arguments_may_be_omitted():
    result, error = ev('roundish(2.4)')
    assert error is None
    assert repr(result) == '2'


def test_roundish_rounds_half_away_from_zero():
    check({
        'roundish(2.5)': '3',
        'roundish(3.5)': '4',
        'roundish(-2.5)': '-3',
        'roundish(0.5)': '1',
        'roundish(7)': '7',
    })


def test_mathify_refuses_values_the_language_cannot_write():
    for text in ('nan', 'inf', '-inf'):
        result, error = ev('mathify(' + Q + text + Q + ')')
        assert result is None, text
        assert 'Cannot convert' in error.details, text


def test_mathify_accepts_exponent_notation():
    check({'mathify(' + Q + '1e3' + Q + ')': '1000'})


def test_variadic_builtin_accepts_any_count():
    check({'chonk(1, 2, 3, 4, 5)': '5'})


def test_too_few_arguments_is_reported_with_a_range():
    result, error = ev('chunk()')
    assert result is None
    assert 'takes 1 to 3 argument(s), got 0' in error.details


def test_variadic_arity_message_says_at_least():
    result, error = ev('smol()')
    assert result is None
    assert 'takes at least 1 argument(s), got 0' in error.details


def test_beg_works_without_a_prompt(monkeypatch):
    monkeypatch.setattr('builtins.input', lambda *a: 'typed')
    result, error = ev('beg()')
    assert error is None
    assert result.value == 'typed'


def test_beg_still_accepts_a_prompt(capsys, monkeypatch):
    monkeypatch.setattr('builtins.input', lambda prompt='': 'x')
    result, error = ev('beg(' + Q + 'name? ' + Q + ')')
    assert error is None
    assert result.value == 'x'
