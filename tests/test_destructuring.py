import aura

Q = '"'


def ev(source):
    result, error = aura.run('<stdin>', source, aura.new_symbol_table())
    if isinstance(result, list):
        result = result[-1] if result else None
    return result, error


def test_declaring_several_names_from_a_pile():
    result, error = ev('stash a, b = [1, 2]\n' + Q + '{a}{b}' + Q)
    assert error is None
    assert result.value == '12'


def test_three_names():
    result, error = ev('stash a, b, c = [1, 2, 3]\nc')
    assert error is None
    assert repr(result) == '3'


def test_assigning_without_stash_needs_existing_names():
    result, error = ev('stash a = 1\nstash b = 2\na, b = [b, a]\n' + Q + '{a}{b}' + Q)
    assert error is None
    assert result.value == '21'


def test_swapping_in_one_line():
    result, error = ev('stash a, b = [1, 2]\na, b = [b, a]\n' + Q + '{a}{b}' + Q)
    assert error is None
    assert result.value == '21'


def test_unpacking_a_chores_return_value():
    result, error = ev('chore pair() ong\nyeet [1, 2]\nbet\nstash x, y = pair()\n' + Q + '{x}-{y}' + Q)
    assert error is None
    assert result.value == '1-2'


def test_too_few_things_to_unpack():
    result, error = ev('stash a, b = [1]')
    assert result is None
    assert 'Need 2 things to unpack, got 1' in error.details


def test_too_many_things_to_unpack():
    result, error = ev('stash a, b = [1, 2, 3]')
    assert result is None
    assert 'Need 2 things to unpack, got 3' in error.details


def test_only_a_pile_can_be_unpacked():
    result, error = ev('stash a, b = 5')
    assert result is None
    assert 'Can only unpack a pile, got math' in error.details


def test_assigning_to_undeclared_names_is_rejected():
    result, error = ev('nope, other = [1, 2]')
    assert result is None
    assert "Cannot assign to undefined variable 'nope'" in error.details


def test_unpacked_values_are_copies():
    result, error = ev('stash x = [1, 2]\nstash a, b = x\nb = 9\nx')
    assert error is None
    assert repr(result) == '[1, 2]'


def test_a_single_name_still_works():
    result, error = ev('stash a = [1, 2]\na')
    assert error is None
    assert repr(result) == '[1, 2]'


def test_missing_name_after_a_comma_is_a_syntax_error():
    result, error = ev('stash a, = [1]')
    assert result is None
    assert 'Expected identifier' in error.details


# --- grind over pairs ---

def test_grind_over_a_bags_pairs():
    source = ('stash d = {' + Q + 'a' + Q + ': 1, ' + Q + 'b' + Q + ': 2}\n'
              'stash t = 0\ngrind k, v among d ong\nt += v\nbet\nt')
    result, error = ev(source)
    assert error is None
    assert repr(result) == '3'


def test_grind_over_pairs_binds_both_names():
    source = ('stash out = []\ngrind k, v among {' + Q + 'a' + Q + ': 1} ong\n'
              'out = stuff(out, ' + Q + '{k}={v}' + Q + ')\nbet\nout')
    result, error = ev(source)
    assert error is None
    assert repr(result) == '["a=1"]'


def test_grind_over_a_pile_of_piles():
    source = ('stash t = 0\ngrind a, b among [[1, 2], [3, 4]] ong\nt += a * b\nbet\nt')
    result, error = ev(source)
    assert error is None
    assert repr(result) == '14'


def test_grind_over_flat_values_with_two_names_is_an_error():
    result, error = ev('grind a, b among [1, 2] ong\n1\nbet')
    assert result is None
    assert 'Can only unpack a pile, got math' in error.details


def test_single_name_grind_over_a_bag_still_walks_labels():
    source = ('stash out = []\ngrind k among {' + Q + 'a' + Q + ': 1} ong\n'
              'out = stuff(out, k)\nbet\nout')
    result, error = ev(source)
    assert error is None
    assert repr(result) == '["a"]'


def test_grind_with_commas_requires_among():
    result, error = ev('grind a, b = 0 til 2 ong\n1\nbet')
    assert result is None
    assert "Expected 'among'" in error.details
