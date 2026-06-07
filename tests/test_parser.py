import shit


def parse_ast(text):
    lexer = shit.Lexer('<stdin>', text)
    tokens, error = lexer.make_tokens()
    assert error is None

    parser = shit.Parser(tokens)
    result = parser.parse()
    assert result.error is None
    return result.node


def first_statement_repr(text):
    ast = parse_ast(text)
    return repr(ast.element_nodes[0])


def test_parser_precedence_multiplication_before_addition():
    assert first_statement_repr('1 + 2 * 3') == '(INT:1, PLUS, (INT:2, MUL, INT:3))'


def test_parser_parentheses_override_precedence():
    assert first_statement_repr('(1 + 2) * 3') == '((INT:1, PLUS, INT:2), MUL, INT:3)'


def test_parser_var_declaration_and_assignment():
    declaration = first_statement_repr('var x = 10')
    assignment = first_statement_repr('x = x + 1')

    assert declaration == '(var IDENTIFIER:x = INT:10)'
    assert assignment == '(IDENTIFIER:x = (IDENTIFIER:x, PLUS, INT:1))'


def test_parser_comparison_expression():
    assert first_statement_repr('5 + 1 >= 3') == '((INT:5, PLUS, INT:1), GTE, INT:3)'


def test_parser_statement_list():
    ast = parse_ast('var x = 10\nx = x + 2\nx')

    assert len(ast.element_nodes) == 3
