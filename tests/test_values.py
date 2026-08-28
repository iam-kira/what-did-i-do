import aura

Q = '"'


def ev(source):
    result, error = aura.run('<stdin>', source, aura.new_symbol_table())
    if isinstance(result, list):
        result = result[-1] if result else None
    return result, error


# --- strings ---

def test_string_literal_and_escapes():
    result, error = ev(Q + 'a' + chr(92) + 'nb' + chr(92) + 't' + Q)
    assert error is None
    assert result.value == 'a\nb\t'


def test_string_concat_and_repeat():
    result, error = ev(Q + 'ab' + Q + ' + ' + Q + 'cd' + Q)
    assert error is None
    assert result.value == 'abcd'

    result, error = ev(Q + 'ab' + Q + ' * 3')
    assert error is None
    assert result.value == 'ababab'


def test_string_comparison_and_truthiness():
    result, error = ev(Q + 'a' + Q + ' < ' + Q + 'b' + Q)
    assert error is None
    assert repr(result) == '1'

    result, error = ev('nah ' + Q + Q)
    assert error is None
    assert repr(result) == '1'


def test_string_plus_number_is_illegal():
    result, error = ev(Q + 'a' + Q + ' + 1')
    assert result is None
    assert 'Illegal operation' in error.details


def test_unterminated_string_is_a_lex_error():
    result, error = ev(Q + 'oops')
    assert result is None
    assert 'unterminated string' in error.details


# --- lists ---

def test_list_literal_and_concat():
    result, error = ev('[1, 2] + [3]')
    assert error is None
    assert repr(result) == '[1, 2, 3]'


def test_list_equality_is_by_value():
    result, error = ev('[1, [2]] == [1, [2]]')
    assert error is None
    assert repr(result) == '1'


def test_empty_list_is_falsy():
    result, error = ev('nah []')
    assert error is None
    assert repr(result) == '1'


def test_list_literal_may_span_lines():
    result, error = ev('[\n1,\n2,\n]')
    assert error is None
    assert repr(result) == '[1, 2]'


# --- indexing ---

def test_index_list_and_string():
    result, error = ev('[10, 20, 30][1]')
    assert error is None
    assert repr(result) == '20'

    result, error = ev(Q + 'hello' + Q + '[1]')
    assert error is None
    assert result.value == 'e'


def test_negative_index_counts_from_the_end():
    result, error = ev('[1, 2, 3][-1]')
    assert error is None
    assert repr(result) == '3'


def test_chained_indexing():
    result, error = ev('[[1, 2], [3, 4]][1][0]')
    assert error is None
    assert repr(result) == '3'


def test_index_out_of_range():
    result, error = ev('[1, 2][9]')
    assert result is None
    assert 'out of range' in error.details


def test_non_integer_index():
    result, error = ev('[1, 2][1.5]')
    assert result is None
    assert 'must be a whole math' in error.details


def test_indexing_a_number_is_rejected():
    result, error = ev('stash n = 5\nn[0]')
    assert result is None
    assert 'not indexable' in error.details


# --- operators ---

def test_modulo():
    for source, expected in (('7 % 3', '1'), ('8 % 4', '0'), ('-7 % 3', '2')):
        result, error = ev(source)
        assert error is None, source
        assert repr(result) == expected, source


def test_modulo_by_zero():
    result, error = ev('1 % 0')
    assert result is None
    assert 'Modulo by zero' in error.details


def test_power_is_right_associative():
    result, error = ev('2 ^ 3 ^ 2')
    assert error is None
    assert repr(result) == '512'


def test_power_binds_tighter_than_unary_minus():
    result, error = ev('-2 ^ 2')
    assert error is None
    assert repr(result) == '-4'


# --- builtins ---

def test_len_of_string_and_list():
    result, error = ev('howmany(' + Q + 'abc' + Q + ')')
    assert error is None
    assert repr(result) == '3'

    result, error = ev('howmany([1, 2])')
    assert error is None
    assert repr(result) == '2'


def test_len_of_number_is_an_error():
    result, error = ev('howmany(5)')
    assert result is None
    assert 'needs a yap, pile or bag' in error.details


def test_str_and_num_round_trip():
    result, error = ev('mathify(yapify(42)) == 42')
    assert error is None
    assert repr(result) == '1'


def test_num_rejects_nonsense():
    result, error = ev('mathify(' + Q + 'nope' + Q + ')')
    assert result is None
    assert 'Cannot convert' in error.details


def test_append_and_pop_do_not_mutate_the_original():
    result, error = ev('stash a = [1, 2]\nstash b = stuff(a, 3)\na')
    assert error is None
    assert repr(result) == '[1, 2]'

    result, error = ev('yoink([1, 2, 3], 0)')
    assert error is None
    assert repr(result) == '[2, 3]'


def test_pop_index_is_bounds_checked():
    result, error = ev('yoink([1], 5)')
    assert result is None
    assert 'out of range' in error.details


def test_type_predicates():
    cases = {
        'is_math(1)': '1', 'is_math(' + Q + 'a' + Q + ')': '0',
        'is_yap(' + Q + 'a' + Q + ')': '1', 'is_pile([])': '1',
        'is_chore(cook)': '1', 'is_chore(1)': '0',
    }
    for source, expected in cases.items():
        result, error = ev(source)
        assert error is None, source
        assert repr(result) == expected, source


def test_builtin_arity_is_checked():
    result, error = ev('cook(1, 2)')
    assert result is None
    assert 'takes 1 argument(s), got 2' in error.details


def test_print_returns_zero(capsys):
    result, error = ev('cook(' + Q + 'hi' + Q + ')')
    assert error is None
    assert repr(result) == '0'
    assert capsys.readouterr().out == 'hi\n'


def test_builtins_are_available_but_shadowable():
    result, error = ev('stash howmany = 5\nhowmany')
    assert error is None
    assert repr(result) == '5'
