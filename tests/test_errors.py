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
