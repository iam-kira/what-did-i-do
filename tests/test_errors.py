import shit


def test_position_resets_column_on_newline():
    pos = shit.Position(0, 0, 5, '<stdin>', 'a\n')
    pos.advance('\n')

    assert pos.line == 1
    assert pos.col == 0


def test_token_repr_keeps_zero_values():
    token_int = shit.Token(shit.TT_INT, 0)
    token_float = shit.Token(shit.TT_FLOAT, 0.0)

    assert repr(token_int) == 'INT:0'
    assert repr(token_float) == 'FLOAT:0.0'


def test_invalid_syntax_error_from_incomplete_input():
    result, error = shit.run('<stdin>', '1 +')

    assert result is None
    assert isinstance(error, shit.InvalidSyntaxError)
    assert 'Invalid Syntax' in error.as_string()


def test_if_missing_then_is_syntax_error():
    result, error = shit.run('<stdin>', 'if 1\n  2\nend')

    assert result is None
    assert "Expected 'then'" in error.as_string()


def test_if_missing_end_is_syntax_error():
    result, error = shit.run('<stdin>', 'if 1 then\n  2')

    assert result is None
    assert "Expected 'end'" in error.as_string()


def test_while_missing_then_is_syntax_error():
    result, error = shit.run('<stdin>', 'while 1\n  2\nend')

    assert result is None
    assert "Expected 'then'" in error.as_string()


def test_call_with_wrong_arg_count_is_runtime_error():
    result, error = shit.run('<stdin>', 'fun add(a, b) then\n  a + b\nend\nadd(1)')

    assert result is None
    assert 'takes 2 argument(s), got 1' in error.as_string()


def test_calling_a_number_is_runtime_error():
    result, error = shit.run('<stdin>', 'var x = 3\nx(1)')

    assert result is None
    assert 'is not a function' in error.as_string()


def test_arithmetic_on_a_function_is_runtime_error():
    result, error = shit.run('<stdin>', 'fun f() then\n  1\nend\nf + 1')

    assert result is None
    assert 'Illegal operation' in error.as_string()
