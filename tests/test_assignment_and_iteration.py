import aura

Q = '"'


def ev(source):
    result, error = aura.run('<stdin>', source, aura.new_symbol_table())
    if isinstance(result, list):
        result = result[-1] if result else None
    return result, error


# --- for ... in ---

def test_for_in_over_a_list():
    result, error = ev('stash t = 0\ngrind x among [1, 2, 3] ong\nt = t + x\nbet\nt')
    assert error is None
    assert repr(result) == '6'


def test_for_in_over_a_string_yields_characters():
    result, error = ev('stash s = ""\ngrind c among ' + Q + 'abc' + Q + ' ong\ns = c + s\nbet\ns')
    assert error is None
    assert result.value == 'cba'


def test_for_in_over_an_empty_list_skips_the_body():
    result, error = ev('stash t = 99\ngrind x among [] ong\nt = 0\nbet\nt')
    assert error is None
    assert repr(result) == '99'


def test_for_in_supports_break_and_continue():
    result, error = ev('stash t = 0\ngrind x among [1, 2, 3, 4] ong\nfr x == 2 ong\nskip\nbet\n'
                       'fr x == 4 ong\nbail\nbet\nt = t + x\nbet\nt')
    assert error is None
    assert repr(result) == '4'


def test_for_in_over_a_number_is_rejected():
    result, error = ev('grind x among 5 ong\n1\nbet')
    assert result is None
    assert 'Cannot iterate over a math' in error.details


def test_mutating_the_list_during_iteration_does_not_change_the_loop():
    result, error = ev('stash xs = [1, 2, 3]\nstash n = 0\ngrind x among xs ong\nn = n + 1\nxs[0] = 99\nbet\nn')
    assert error is None
    assert repr(result) == '3'


# --- index assignment ---

def test_index_assignment():
    result, error = ev('stash xs = [1, 2, 3]\nxs[0] = 99\nxs')
    assert error is None
    assert repr(result) == '[99, 2, 3]'


def test_negative_index_assignment():
    result, error = ev('stash xs = [1, 2, 3]\nxs[-1] = 9\nxs')
    assert error is None
    assert repr(result) == '[1, 2, 9]'


def test_nested_index_assignment():
    result, error = ev('stash g = [[1, 2], [3, 4]]\ng[1][0] = 9\ng')
    assert error is None
    assert repr(result) == '[[1, 2], [9, 4]]'


def test_index_assignment_is_bounds_checked():
    result, error = ev('stash xs = [1]\nxs[5] = 1')
    assert result is None
    assert 'out of range' in error.details


def test_assigning_into_a_string_is_rejected():
    result, error = ev('stash s = ' + Q + 'abc' + Q + '\ns[0] = ' + Q + 'z' + Q)
    assert result is None
    assert 'Cannot assign into a yap' in error.details


def test_lists_keep_value_semantics_across_variables():
    result, error = ev('stash a = [1, 2]\nstash b = a\nb[0] = 9\na')
    assert error is None
    assert repr(result) == '[1, 2]'


def test_cannot_assign_to_a_literal():
    result, error = ev('1 = 2')
    assert result is None
    assert 'Cannot assign' in error.details


# --- compound assignment ---

def test_compound_assignment_operators():
    cases = {'n += 3': '8', 'n -= 3': '2', 'n *= 3': '15', 'n /= 5': '1'}
    for source, expected in cases.items():
        result, error = ev('stash n = 5\n' + source + '\nn')
        assert error is None, source
        assert repr(result) == expected, source


def test_compound_assignment_on_an_index():
    result, error = ev('stash xs = [1, 2]\nxs[0] += 10\nxs')
    assert error is None
    assert repr(result) == '[11, 2]'


def test_compound_assignment_works_on_strings():
    result, error = ev('stash s = ' + Q + 'a' + Q + '\ns += ' + Q + 'b' + Q + '\ns')
    assert error is None
    assert result.value == 'ab'


def test_compound_assignment_needs_a_declared_name():
    result, error = ev('nope += 1')
    assert result is None
    assert "'nope' is not defined" in error.details
