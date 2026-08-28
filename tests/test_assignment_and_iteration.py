import shit

Q = '"'


def ev(source):
    result, error = shit.run('<stdin>', source, shit.new_symbol_table())
    if isinstance(result, list):
        result = result[-1] if result else None
    return result, error


# --- for ... in ---

def test_for_in_over_a_list():
    result, error = ev('var t = 0\nfor x in [1, 2, 3] then\nt = t + x\nend\nt')
    assert error is None
    assert repr(result) == '6'


def test_for_in_over_a_string_yields_characters():
    result, error = ev('var s = ""\nfor c in ' + Q + 'abc' + Q + ' then\ns = c + s\nend\ns')
    assert error is None
    assert result.value == 'cba'


def test_for_in_over_an_empty_list_skips_the_body():
    result, error = ev('var t = 99\nfor x in [] then\nt = 0\nend\nt')
    assert error is None
    assert repr(result) == '99'


def test_for_in_supports_break_and_continue():
    result, error = ev('var t = 0\nfor x in [1, 2, 3, 4] then\nif x == 2 then\ncontinue\nend\n'
                       'if x == 4 then\nbreak\nend\nt = t + x\nend\nt')
    assert error is None
    assert repr(result) == '4'


def test_for_in_over_a_number_is_rejected():
    result, error = ev('for x in 5 then\n1\nend')
    assert result is None
    assert 'Cannot iterate over a number' in error.details


def test_mutating_the_list_during_iteration_does_not_change_the_loop():
    result, error = ev('var xs = [1, 2, 3]\nvar n = 0\nfor x in xs then\nn = n + 1\nxs[0] = 99\nend\nn')
    assert error is None
    assert repr(result) == '3'


# --- index assignment ---

def test_index_assignment():
    result, error = ev('var xs = [1, 2, 3]\nxs[0] = 99\nxs')
    assert error is None
    assert repr(result) == '[99, 2, 3]'


def test_negative_index_assignment():
    result, error = ev('var xs = [1, 2, 3]\nxs[-1] = 9\nxs')
    assert error is None
    assert repr(result) == '[1, 2, 9]'


def test_nested_index_assignment():
    result, error = ev('var g = [[1, 2], [3, 4]]\ng[1][0] = 9\ng')
    assert error is None
    assert repr(result) == '[[1, 2], [9, 4]]'


def test_index_assignment_is_bounds_checked():
    result, error = ev('var xs = [1]\nxs[5] = 1')
    assert result is None
    assert 'out of range' in error.details


def test_assigning_into_a_string_is_rejected():
    result, error = ev('var s = ' + Q + 'abc' + Q + '\ns[0] = ' + Q + 'z' + Q)
    assert result is None
    assert 'Cannot assign into a string' in error.details


def test_lists_keep_value_semantics_across_variables():
    result, error = ev('var a = [1, 2]\nvar b = a\nb[0] = 9\na')
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
        result, error = ev('var n = 5\n' + source + '\nn')
        assert error is None, source
        assert repr(result) == expected, source


def test_compound_assignment_on_an_index():
    result, error = ev('var xs = [1, 2]\nxs[0] += 10\nxs')
    assert error is None
    assert repr(result) == '[11, 2]'


def test_compound_assignment_works_on_strings():
    result, error = ev('var s = ' + Q + 'a' + Q + '\ns += ' + Q + 'b' + Q + '\ns')
    assert error is None
    assert result.value == 'ab'


def test_compound_assignment_needs_a_declared_name():
    result, error = ev('nope += 1')
    assert result is None
    assert "'nope' is not defined" in error.details
