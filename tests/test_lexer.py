import aura


def token_types(tokens):
    return [token.type for token in tokens]


def test_lexer_basic_tokens_and_eof():
    lexer = aura.Lexer('<stdin>', '1 + 2')
    tokens, error = lexer.make_tokens()

    assert error is None
    assert token_types(tokens) == [aura.TT_INT, aura.TT_PLUS, aura.TT_INT, aura.TT_EOF]


def test_lexer_identifiers_keywords_and_ops():
    lexer = aura.Lexer('<stdin>', 'stash x = 10 >= 2')
    tokens, error = lexer.make_tokens()

    assert error is None
    assert token_types(tokens) == [
        aura.TT_KEYWORD,
        aura.TT_IDENTIFIER,
        aura.TT_EQ,
        aura.TT_INT,
        aura.TT_GTE,
        aura.TT_INT,
        aura.TT_EOF,
    ]


def test_lexer_newline_tokenization():
    lexer = aura.Lexer('<stdin>', '1\n2')
    tokens, error = lexer.make_tokens()

    assert error is None
    assert token_types(tokens) == [
        aura.TT_INT,
        aura.TT_NEWLINE,
        aura.TT_INT,
        aura.TT_EOF,
    ]


def test_lexer_illegal_char_error():
    lexer = aura.Lexer('<stdin>', '1 $ 2')
    tokens, error = lexer.make_tokens()

    assert tokens == []
    assert isinstance(error, aura.IllegalCharError)


def test_lexer_skips_comments_but_keeps_newline():
    lexer = aura.Lexer('<stdin>', '1 # a comment\n2')
    tokens, error = lexer.make_tokens()

    assert error is None
    assert token_types(tokens) == ['INT', 'NEWLINE', 'INT', 'EOF']


def test_lexer_comment_only_source():
    lexer = aura.Lexer('<stdin>', '# nothing but a comment')
    tokens, error = lexer.make_tokens()

    assert error is None
    assert token_types(tokens) == ['EOF']
