import aura


def test_position_resets_column_on_newline():
    pos = aura.Position(0, 0, 5, '<stdin>', 'a\n')
    pos.advance('\n')

    assert pos.line == 1
    assert pos.col == 0


def test_token_repr_keeps_zero_values():
    token_int = aura.Token(aura.TT_INT, 0)
    token_float = aura.Token(aura.TT_FLOAT, 0.0)

    assert repr(token_int) == 'INT:0'
    assert repr(token_float) == 'FLOAT:0.0'


def test_invalid_syntax_error_from_incomplete_input():
    result, error = aura.run('<stdin>', '1 +')

    assert result is None
    assert isinstance(error, aura.InvalidSyntaxError)
    assert 'Invalid Syntax' in error.as_string()


def test_if_missing_then_is_syntax_error():
    result, error = aura.run('<stdin>', 'fr 1\n  2\nbet')

    assert result is None
    assert "Expected 'ong'" in error.as_string()


def test_if_missing_end_is_syntax_error():
    result, error = aura.run('<stdin>', 'fr 1 ong\n  2')

    assert result is None
    assert "Expected 'bet'" in error.as_string()


def test_while_missing_then_is_syntax_error():
    result, error = aura.run('<stdin>', 'keep 1\n  2\nbet')

    assert result is None
    assert "Expected 'ong'" in error.as_string()


def test_call_with_wrong_arg_count_is_runtime_error():
    result, error = aura.run('<stdin>', 'chore add(a, b) ong\n  a + b\nbet\nadd(1)')

    assert result is None
    assert 'takes 2 argument(s), got 1' in error.as_string()


def test_calling_a_number_is_runtime_error():
    result, error = aura.run('<stdin>', 'stash x = 3\nx(1)')

    assert result is None
    assert 'is not a chore' in error.as_string()


def test_arithmetic_on_a_function_is_runtime_error():
    result, error = aura.run('<stdin>', 'chore f() ong\n  1\nbet\nf + 1')

    assert result is None
    assert 'Illegal operation' in error.as_string()
