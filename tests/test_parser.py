import shit


def parse_expr(text):
    result, error = shit.run('<stdin>', text)
    assert error is None
    return result


def test_parser_precedence_multiplication_before_addition():
    ast = parse_expr('1 + 2 * 3')
    assert repr(ast) == '(INT:1, PLUS, (INT:2, MUL, INT:3))'


def test_parser_parentheses_override_precedence():
    ast = parse_expr('(1 + 2) * 3')
    assert repr(ast) == '((INT:1, PLUS, INT:2), MUL, INT:3)'


def test_parser_var_declaration_and_assignment():
    decl = parse_expr('var x = 10')
    assign = parse_expr('x = x + 1')

    assert repr(decl) == '(var IDENTIFIER:x = INT:10)'
    assert repr(assign) == '(IDENTIFIER:x = (IDENTIFIER:x, PLUS, INT:1))'


def test_parser_comparison_expression():
    ast = parse_expr('5 + 1 >= 3')
    assert repr(ast) == '((INT:5, PLUS, INT:1), GTE, INT:3)'
