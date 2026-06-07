import shit


def token_types(tokens):
    return [token.type for token in tokens]


def test_lexer_basic_tokens_and_eof():
    lexer = shit.Lexer('<stdin>', '1 + 2')
    tokens, error = lexer.make_tokens()

    assert error is None
    assert token_types(tokens) == [shit.TT_INT, shit.TT_PLUS, shit.TT_INT, shit.TT_EOF]


def test_lexer_identifiers_keywords_and_ops():
    lexer = shit.Lexer('<stdin>', 'var x = 10 >= 2')
    tokens, error = lexer.make_tokens()

    assert error is None
    assert token_types(tokens) == [
        shit.TT_KEYWORD,
        shit.TT_IDENTIFIER,
        shit.TT_EQ,
        shit.TT_INT,
        shit.TT_GTE,
        shit.TT_INT,
        shit.TT_EOF,
    ]


def test_lexer_illegal_char_error():
    lexer = shit.Lexer('<stdin>', '1 $ 2')
    tokens, error = lexer.make_tokens()

    assert tokens == []
    assert isinstance(error, shit.IllegalCharError)
