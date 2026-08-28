# CONSTANTS
#####################################
DIGITS = '0123456789'
LETTERS = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
LETTERS_DIGITS = LETTERS + DIGITS + '_'
KEYWORDS = [
    'var', 'if', 'then', 'elif', 'else', 'end', 'while', 'fun',
    'and', 'or', 'not', 'true', 'false', 'null',
]


# ERROR
######################################
class Error:
    def __init__(self, pos_start, pos_end, error_name, details):
        self.pos_start = pos_start
        self.pos_end = pos_end
        self.error_name = error_name
        self.details = details

    def as_string(self):
        result = f'{self.error_name}: {self.details}\n'
        result += f'File {self.pos_start.filename}, line {self.pos_start.line + 1}, col {self.pos_start.col + 1}'
        return result


class IllegalCharError(Error):
    def __init__(self, pos_start, pos_end, details):
        super().__init__(pos_start, pos_end, 'Illegal Character', details)


class ExpectedCharError(Error):
    def __init__(self, pos_start, pos_end, details):
        super().__init__(pos_start, pos_end, 'Expected Character', details)


class InvalidSyntaxError(Error):
    def __init__(self, pos_start, pos_end, details='Invalid syntax'):
        super().__init__(pos_start, pos_end, 'Invalid Syntax', details)


class RTError(Error):
    def __init__(self, pos_start, pos_end, details):
        super().__init__(pos_start, pos_end, 'Runtime Error', details)


# POSITION
########################################
class Position:
    def __init__(self, index, line, col, filename, ftxt):
        self.index = index
        self.line = line
        self.col = col
        self.filename = filename
        self.ftxt = ftxt

    def advance(self, current_char):
        self.index += 1

        if current_char == '\n':
            self.line += 1
            self.col = 0
        else:
            self.col += 1

        return self

    def copy(self):
        return Position(self.index, self.line, self.col, self.filename, self.ftxt)


# TOKEN
#######################################
TT_INT = 'INT'
TT_FLOAT = 'FLOAT'
TT_IDENTIFIER = 'IDENTIFIER'
TT_KEYWORD = 'KEYWORD'
TT_PLUS = 'PLUS'
TT_MINUS = 'MINUS'
TT_MUL = 'MUL'
TT_DIV = 'DIV'
TT_EQ = 'EQ'
TT_EE = 'EE'
TT_NE = 'NE'
TT_LT = 'LT'
TT_GT = 'GT'
TT_LTE = 'LTE'
TT_GTE = 'GTE'
TT_LPAREN = 'LPAREN'
TT_RPAREN = 'RPAREN'
TT_COMMA = 'COMMA'
TT_NEWLINE = 'NEWLINE'
TT_EOF = 'EOF'


class Token:
    def __init__(self, type_, value=None, pos_start=None, pos_end=None):
        self.type = type_
        self.value = value

        if pos_start:
            self.pos_start = pos_start.copy()
            self.pos_end = pos_start.copy()
            self.pos_end.advance(None)

        if pos_end:
            self.pos_end = pos_end.copy()

    def matches(self, type_, value):
        return self.type == type_ and self.value == value

    def __repr__(self):
        if self.value is not None:
            return f'{self.type}:{self.value}'
        return f'{self.type}'


# LEXER
######################################
class Lexer:
    def __init__(self, filename, text):
        self.text = text
        self.filename = filename
        self.pos = Position(-1, 0, -1, filename, text)
        self.current_char = None
        self.advance()

    def advance(self):
        self.pos.advance(self.current_char)
        self.current_char = self.text[self.pos.index] if self.pos.index < len(self.text) else None

    def make_tokens(self):
        tokens = []

        while self.current_char is not None:
            if self.current_char in ' \t':
                self.advance()
            elif self.current_char in '\n;':
                tokens.append(Token(TT_NEWLINE, pos_start=self.pos))
                self.advance()
            elif self.current_char == '#':
                while self.current_char is not None and self.current_char != '\n':
                    self.advance()
            elif self.current_char in DIGITS:
                tokens.append(self.make_number())
            elif self.current_char in LETTERS or self.current_char == '_':
                tokens.append(self.make_identifier())
            elif self.current_char == '+':
                tokens.append(Token(TT_PLUS, pos_start=self.pos))
                self.advance()
            elif self.current_char == '-':
                tokens.append(Token(TT_MINUS, pos_start=self.pos))
                self.advance()
            elif self.current_char == '*':
                tokens.append(Token(TT_MUL, pos_start=self.pos))
                self.advance()
            elif self.current_char == '/':
                tokens.append(Token(TT_DIV, pos_start=self.pos))
                self.advance()
            elif self.current_char == '(':
                tokens.append(Token(TT_LPAREN, pos_start=self.pos))
                self.advance()
            elif self.current_char == ')':
                tokens.append(Token(TT_RPAREN, pos_start=self.pos))
                self.advance()
            elif self.current_char == ',':
                tokens.append(Token(TT_COMMA, pos_start=self.pos))
                self.advance()
            elif self.current_char == '!':
                token, error = self.make_not_equals()
                if error:
                    return [], error
                tokens.append(token)
            elif self.current_char == '=':
                tokens.append(self.make_equals())
            elif self.current_char == '<':
                tokens.append(self.make_less_than())
            elif self.current_char == '>':
                tokens.append(self.make_greater_than())
            else:
                pos_start = self.pos.copy()
                char = self.current_char
                self.advance()
                return [], IllegalCharError(pos_start, self.pos.copy(), f"'{char}'")

        tokens.append(Token(TT_EOF, pos_start=self.pos))
        return tokens, None

    def make_number(self):
        num_str = ''
        dot_count = 0
        pos_start = self.pos.copy()

        while self.current_char is not None and self.current_char in DIGITS + '.':
            if self.current_char == '.':
                if dot_count == 1:
                    break
                dot_count += 1
            num_str += self.current_char
            self.advance()

        if dot_count == 0:
            return Token(TT_INT, int(num_str), pos_start, self.pos)
        return Token(TT_FLOAT, float(num_str), pos_start, self.pos)

    def make_identifier(self):
        ident = ''
        pos_start = self.pos.copy()

        while self.current_char is not None and self.current_char in LETTERS_DIGITS:
            ident += self.current_char
            self.advance()

        token_type = TT_KEYWORD if ident in KEYWORDS else TT_IDENTIFIER
        return Token(token_type, ident, pos_start, self.pos)

    def make_not_equals(self):
        pos_start = self.pos.copy()
        self.advance()

        if self.current_char == '=':
            self.advance()
            return Token(TT_NE, pos_start=pos_start, pos_end=self.pos), None

        return None, ExpectedCharError(pos_start, self.pos.copy(), "'=' (after '!')")

    def make_equals(self):
        token_type = TT_EQ
        pos_start = self.pos.copy()
        self.advance()

        if self.current_char == '=':
            self.advance()
            token_type = TT_EE

        return Token(token_type, pos_start=pos_start, pos_end=self.pos)

    def make_less_than(self):
        token_type = TT_LT
        pos_start = self.pos.copy()
        self.advance()

        if self.current_char == '=':
            self.advance()
            token_type = TT_LTE

        return Token(token_type, pos_start=pos_start, pos_end=self.pos)

    def make_greater_than(self):
        token_type = TT_GT
        pos_start = self.pos.copy()
        self.advance()

        if self.current_char == '=':
            self.advance()
            token_type = TT_GTE

        return Token(token_type, pos_start=pos_start, pos_end=self.pos)


# NODES
######################################
class NumberNode:
    def __init__(self, tok):
        self.tok = tok
        self.pos_start = self.tok.pos_start
        self.pos_end = self.tok.pos_end

    def __repr__(self):
        return f'{self.tok}'


class VarAccessNode:
    def __init__(self, var_name_tok):
        self.var_name_tok = var_name_tok
        self.pos_start = self.var_name_tok.pos_start
        self.pos_end = self.var_name_tok.pos_end

    def __repr__(self):
        return f'{self.var_name_tok}'


class VarAssignNode:
    def __init__(self, var_name_tok, value_node, is_declaration=False):
        self.var_name_tok = var_name_tok
        self.value_node = value_node
        self.is_declaration = is_declaration
        self.pos_start = self.var_name_tok.pos_start
        self.pos_end = self.value_node.pos_end

    def __repr__(self):
        prefix = 'var ' if self.is_declaration else ''
        return f'({prefix}{self.var_name_tok} = {self.value_node})'


class BinOpNode:
    def __init__(self, left_node, op_tok, right_node):
        self.left_node = left_node
        self.op_tok = op_tok
        self.right_node = right_node
        self.pos_start = self.left_node.pos_start
        self.pos_end = self.right_node.pos_end

    def __repr__(self):
        return f'({self.left_node}, {self.op_tok}, {self.right_node})'


class UnaryOpNode:
    def __init__(self, op_tok, node):
        self.op_tok = op_tok
        self.node = node
        self.pos_start = self.op_tok.pos_start
        self.pos_end = node.pos_end

    def __repr__(self):
        return f'({self.op_tok}, {self.node})'


class IfNode:
    def __init__(self, cases, else_case, pos_start, pos_end):
        self.cases = cases  # list of (condition_node, body_node)
        self.else_case = else_case
        self.pos_start = pos_start
        self.pos_end = pos_end

    def __repr__(self):
        return f'(if {self.cases} else {self.else_case})'


class WhileNode:
    def __init__(self, condition_node, body_node, pos_start, pos_end):
        self.condition_node = condition_node
        self.body_node = body_node
        self.pos_start = pos_start
        self.pos_end = pos_end

    def __repr__(self):
        return f'(while {self.condition_node} then {self.body_node})'


class FuncDefNode:
    def __init__(self, var_name_tok, arg_name_toks, body_node, pos_start, pos_end):
        self.var_name_tok = var_name_tok
        self.arg_name_toks = arg_name_toks
        self.body_node = body_node
        self.pos_start = pos_start
        self.pos_end = pos_end

    def __repr__(self):
        args = ', '.join(str(tok.value) for tok in self.arg_name_toks)
        return f'(fun {self.var_name_tok.value}({args}))'


class CallNode:
    def __init__(self, node_to_call, arg_nodes, pos_end):
        self.node_to_call = node_to_call
        self.arg_nodes = arg_nodes
        self.pos_start = self.node_to_call.pos_start
        self.pos_end = pos_end

    def __repr__(self):
        return f'({self.node_to_call} call {self.arg_nodes})'


class ListNode:
    def __init__(self, element_nodes, pos_start, pos_end):
        self.element_nodes = element_nodes
        self.pos_start = pos_start
        self.pos_end = pos_end

    def __repr__(self):
        return f'{self.element_nodes}'


# PARSE RESULT
######################################
class ParseResult:
    def __init__(self):
        self.error = None
        self.node = None

    def register(self, res):
        if res.error:
            self.error = res.error
        return res.node

    def success(self, node):
        self.node = node
        return self

    def failure(self, error):
        self.error = error
        return self


# PARSER
######################################
class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.token_idx = -1
        self.current_tok = None
        self.advance()

    def advance(self):
        self.token_idx += 1
        if self.token_idx < len(self.tokens):
            self.current_tok = self.tokens[self.token_idx]
        return self.current_tok

    def peek(self, offset=1):
        idx = self.token_idx + offset
        if 0 <= idx < len(self.tokens):
            return self.tokens[idx]
        return None

    def parse(self):
        res = self.statements()
        if not res.error and self.current_tok.type != TT_EOF:
            return res.failure(
                InvalidSyntaxError(self.current_tok.pos_start, self.current_tok.pos_end, 'Expected end of input')
            )
        return res

    def statements(self, stop_keywords=()):
        res = ParseResult()
        statements = []
        pos_start = self.current_tok.pos_start.copy()

        while self.current_tok.type == TT_NEWLINE:
            self.advance()

        if self.at_block_end(stop_keywords):
            return res.success(ListNode([], pos_start, self.current_tok.pos_end.copy()))

        statement = res.register(self.statement())
        if res.error:
            return res
        statements.append(statement)

        while self.current_tok.type == TT_NEWLINE:
            self.advance()
            while self.current_tok.type == TT_NEWLINE:
                self.advance()
            if self.at_block_end(stop_keywords):
                break
            statement = res.register(self.statement())
            if res.error:
                return res
            statements.append(statement)

        return res.success(ListNode(statements, pos_start, self.current_tok.pos_end.copy()))

    def at_block_end(self, stop_keywords):
        if self.current_tok.type == TT_EOF:
            return True
        return self.current_tok.type == TT_KEYWORD and self.current_tok.value in stop_keywords

    def statement(self):
        res = ParseResult()

        if self.current_tok.matches(TT_KEYWORD, 'if'):
            return self.if_expr()

        if self.current_tok.matches(TT_KEYWORD, 'while'):
            return self.while_expr()

        if self.current_tok.matches(TT_KEYWORD, 'fun'):
            return self.func_def()

        if self.current_tok.matches(TT_KEYWORD, 'var'):
            self.advance()
            if self.current_tok.type != TT_IDENTIFIER:
                return res.failure(
                    InvalidSyntaxError(self.current_tok.pos_start, self.current_tok.pos_end, 'Expected identifier')
                )

            var_name = self.current_tok
            self.advance()

            if self.current_tok.type != TT_EQ:
                return res.failure(
                    InvalidSyntaxError(self.current_tok.pos_start, self.current_tok.pos_end, "Expected '='")
                )

            self.advance()
            expr = res.register(self.expr())
            if res.error:
                return res
            return res.success(VarAssignNode(var_name, expr, is_declaration=True))

        if self.current_tok.type == TT_IDENTIFIER and self.peek() and self.peek().type == TT_EQ:
            var_name = self.current_tok
            self.advance()
            self.advance()

            expr = res.register(self.expr())
            if res.error:
                return res
            return res.success(VarAssignNode(var_name, expr, is_declaration=False))

        expr = res.register(self.expr())
        if res.error:
            return res
        return res.success(expr)

    def if_expr(self):
        res = ParseResult()
        cases = []
        else_case = None
        pos_start = self.current_tok.pos_start.copy()

        while True:
            self.advance()  # past 'if' / 'elif'

            condition = res.register(self.expr())
            if res.error:
                return res

            if not self.current_tok.matches(TT_KEYWORD, 'then'):
                return res.failure(
                    InvalidSyntaxError(self.current_tok.pos_start, self.current_tok.pos_end, "Expected 'then'")
                )
            self.advance()

            body = res.register(self.statements(('elif', 'else', 'end')))
            if res.error:
                return res
            cases.append((condition, body))

            if not self.current_tok.matches(TT_KEYWORD, 'elif'):
                break

        if self.current_tok.matches(TT_KEYWORD, 'else'):
            self.advance()
            else_case = res.register(self.statements(('end',)))
            if res.error:
                return res

        if not self.current_tok.matches(TT_KEYWORD, 'end'):
            return res.failure(
                InvalidSyntaxError(self.current_tok.pos_start, self.current_tok.pos_end, "Expected 'end'")
            )

        pos_end = self.current_tok.pos_end.copy()
        self.advance()
        return res.success(IfNode(cases, else_case, pos_start, pos_end))

    def while_expr(self):
        res = ParseResult()
        pos_start = self.current_tok.pos_start.copy()
        self.advance()

        condition = res.register(self.expr())
        if res.error:
            return res

        if not self.current_tok.matches(TT_KEYWORD, 'then'):
            return res.failure(
                InvalidSyntaxError(self.current_tok.pos_start, self.current_tok.pos_end, "Expected 'then'")
            )
        self.advance()

        body = res.register(self.statements(('end',)))
        if res.error:
            return res

        if not self.current_tok.matches(TT_KEYWORD, 'end'):
            return res.failure(
                InvalidSyntaxError(self.current_tok.pos_start, self.current_tok.pos_end, "Expected 'end'")
            )

        pos_end = self.current_tok.pos_end.copy()
        self.advance()
        return res.success(WhileNode(condition, body, pos_start, pos_end))

    def func_def(self):
        res = ParseResult()
        pos_start = self.current_tok.pos_start.copy()
        self.advance()

        if self.current_tok.type != TT_IDENTIFIER:
            return res.failure(
                InvalidSyntaxError(self.current_tok.pos_start, self.current_tok.pos_end, 'Expected function name')
            )
        var_name_tok = self.current_tok
        self.advance()

        if self.current_tok.type != TT_LPAREN:
            return res.failure(
                InvalidSyntaxError(self.current_tok.pos_start, self.current_tok.pos_end, "Expected '('")
            )
        self.advance()

        arg_name_toks = []
        if self.current_tok.type == TT_IDENTIFIER:
            arg_name_toks.append(self.current_tok)
            self.advance()

            while self.current_tok.type == TT_COMMA:
                self.advance()
                if self.current_tok.type != TT_IDENTIFIER:
                    return res.failure(
                        InvalidSyntaxError(
                            self.current_tok.pos_start, self.current_tok.pos_end, 'Expected parameter name'
                        )
                    )
                arg_name_toks.append(self.current_tok)
                self.advance()

        if self.current_tok.type != TT_RPAREN:
            return res.failure(
                InvalidSyntaxError(self.current_tok.pos_start, self.current_tok.pos_end, "Expected ',' or ')'")
            )
        self.advance()

        if not self.current_tok.matches(TT_KEYWORD, 'then'):
            return res.failure(
                InvalidSyntaxError(self.current_tok.pos_start, self.current_tok.pos_end, "Expected 'then'")
            )
        self.advance()

        body = res.register(self.statements(('end',)))
        if res.error:
            return res

        if not self.current_tok.matches(TT_KEYWORD, 'end'):
            return res.failure(
                InvalidSyntaxError(self.current_tok.pos_start, self.current_tok.pos_end, "Expected 'end'")
            )

        pos_end = self.current_tok.pos_end.copy()
        self.advance()
        return res.success(FuncDefNode(var_name_tok, arg_name_toks, body, pos_start, pos_end))

    def call(self, node):
        res = ParseResult()
        self.advance()  # past '('

        arg_nodes = []
        if self.current_tok.type != TT_RPAREN:
            arg_nodes.append(res.register(self.expr()))
            if res.error:
                return res

            while self.current_tok.type == TT_COMMA:
                self.advance()
                arg_nodes.append(res.register(self.expr()))
                if res.error:
                    return res

        if self.current_tok.type != TT_RPAREN:
            return res.failure(
                InvalidSyntaxError(self.current_tok.pos_start, self.current_tok.pos_end, "Expected ',' or ')'")
            )

        pos_end = self.current_tok.pos_end.copy()
        self.advance()
        return res.success(CallNode(node, arg_nodes, pos_end))

    def expr(self):
        return self.bin_op(self.and_expr, ((TT_KEYWORD, 'or'),))

    def and_expr(self):
        return self.bin_op(self.not_expr, ((TT_KEYWORD, 'and'),))

    def not_expr(self):
        res = ParseResult()

        if self.current_tok.matches(TT_KEYWORD, 'not'):
            op_tok = self.current_tok
            self.advance()
            node = res.register(self.not_expr())
            if res.error:
                return res
            return res.success(UnaryOpNode(op_tok, node))

        return self.comp_expr()

    def comp_expr(self):
        return self.bin_op(self.arith_expr, (TT_EE, TT_NE, TT_LT, TT_GT, TT_LTE, TT_GTE))

    def arith_expr(self):
        return self.bin_op(self.term, (TT_PLUS, TT_MINUS))

    def term(self):
        return self.bin_op(self.factor, (TT_MUL, TT_DIV))

    def factor(self):
        res = ParseResult()
        tok = self.current_tok

        if tok.type in (TT_PLUS, TT_MINUS):
            self.advance()
            factor = res.register(self.factor())
            if res.error:
                return res
            return res.success(UnaryOpNode(tok, factor))

        return self.atom()

    def atom(self):
        res = ParseResult()
        tok = self.current_tok

        if tok.type in (TT_INT, TT_FLOAT):
            self.advance()
            return res.success(NumberNode(tok))

        if tok.type == TT_KEYWORD and tok.value in ('true', 'false', 'null'):
            self.advance()
            literal = 1 if tok.value == 'true' else 0
            return res.success(NumberNode(Token(TT_INT, literal, tok.pos_start, tok.pos_end)))

        if tok.type == TT_IDENTIFIER:
            self.advance()
            if self.current_tok.type == TT_LPAREN:
                return self.call(VarAccessNode(tok))
            return res.success(VarAccessNode(tok))

        if tok.type == TT_LPAREN:
            self.advance()
            expr = res.register(self.expr())
            if res.error:
                return res
            if self.current_tok.type == TT_RPAREN:
                self.advance()
                return res.success(expr)
            return res.failure(
                InvalidSyntaxError(self.current_tok.pos_start, self.current_tok.pos_end, "Expected ')'")
            )

        return res.failure(
            InvalidSyntaxError(
                tok.pos_start, tok.pos_end, "Expected int, float, identifier, 'not', '+', '-' or '('"
            )
        )

    def op_matches(self, ops):
        for op in ops:
            if isinstance(op, tuple):
                if self.current_tok.matches(op[0], op[1]):
                    return True
            elif self.current_tok.type == op:
                return True
        return False

    def bin_op(self, func, ops):
        res = ParseResult()
        left = res.register(func())
        if res.error:
            return res

        while self.op_matches(ops):
            op_tok = self.current_tok
            self.advance()
            right = res.register(func())
            if res.error:
                return res
            left = BinOpNode(left, op_tok, right)

        return res.success(left)


# RUNTIME RESULT
######################################
class RTResult:
    def __init__(self):
        self.value = None
        self.error = None

    def register(self, res):
        if res.error:
            self.error = res.error
        return res.value

    def success(self, value):
        self.value = value
        return self

    def failure(self, error):
        self.error = error
        return self


# VALUES
######################################
class Value:
    """Base for every runtime value.

    Operations default to an 'illegal operation' error, so a new type only has
    to override what it actually supports.
    """

    def __init__(self):
        self.pos_start = None
        self.pos_end = None

    def set_pos(self, pos_start=None, pos_end=None):
        self.pos_start = pos_start
        self.pos_end = pos_end
        return self

    def copy(self):
        raise NotImplementedError(f'{type(self).__name__} has no copy method')

    def is_true(self):
        return False

    def illegal_operation(self, other=None):
        other = other if other is not None else self
        return None, RTError(
            self.pos_start,
            other.pos_end,
            f'Illegal operation for {type(self).__name__.lower()}',
        )

    def added_to(self, other):
        return self.illegal_operation(other)

    def subbed_by(self, other):
        return self.illegal_operation(other)

    def multed_by(self, other):
        return self.illegal_operation(other)

    def dived_by(self, other):
        return self.illegal_operation(other)

    def compare_lt(self, other):
        return self.illegal_operation(other)

    def compare_gt(self, other):
        return self.illegal_operation(other)

    def compare_lte(self, other):
        return self.illegal_operation(other)

    def compare_gte(self, other):
        return self.illegal_operation(other)

    def compare_eq(self, other):
        return Number(1 if self is other else 0), None

    def compare_ne(self, other):
        equal, error = self.compare_eq(other)
        if error:
            return None, error
        return Number(0 if equal.is_true() else 1), None

    def notted(self):
        return Number(0 if self.is_true() else 1), None


class Number(Value):
    def __init__(self, value):
        super().__init__()
        self.value = value

    def copy(self):
        return Number(self.value).set_pos(self.pos_start, self.pos_end)

    def added_to(self, other):
        if not isinstance(other, Number):
            return self.illegal_operation(other)
        return Number(self.value + other.value), None

    def subbed_by(self, other):
        if not isinstance(other, Number):
            return self.illegal_operation(other)
        return Number(self.value - other.value), None

    def multed_by(self, other):
        if not isinstance(other, Number):
            return self.illegal_operation(other)
        return Number(self.value * other.value), None

    def dived_by(self, other):
        if not isinstance(other, Number):
            return self.illegal_operation(other)
        if other.value == 0:
            return None, RTError(other.pos_start, other.pos_end, 'Division by zero')
        if isinstance(self.value, int) and isinstance(other.value, int):
            if self.value % other.value == 0:
                return Number(self.value // other.value), None
        return Number(self.value / other.value), None

    def compare_eq(self, other):
        if not isinstance(other, Number):
            return Number(0), None
        return Number(1 if self.value == other.value else 0), None

    def compare_ne(self, other):
        if not isinstance(other, Number):
            return Number(1), None
        return Number(1 if self.value != other.value else 0), None

    def compare_lt(self, other):
        if not isinstance(other, Number):
            return self.illegal_operation(other)
        return Number(1 if self.value < other.value else 0), None

    def compare_gt(self, other):
        if not isinstance(other, Number):
            return self.illegal_operation(other)
        return Number(1 if self.value > other.value else 0), None

    def compare_lte(self, other):
        if not isinstance(other, Number):
            return self.illegal_operation(other)
        return Number(1 if self.value <= other.value else 0), None

    def compare_gte(self, other):
        if not isinstance(other, Number):
            return self.illegal_operation(other)
        return Number(1 if self.value >= other.value else 0), None

    def is_true(self):
        return self.value != 0

    def __repr__(self):
        if isinstance(self.value, float) and self.value.is_integer():
            return str(int(self.value))
        return str(self.value)


class Function(Value):
    def __init__(self, name, arg_names, body_node):
        super().__init__()
        self.name = name
        self.arg_names = arg_names
        self.body_node = body_node

    def copy(self):
        return Function(self.name, self.arg_names, self.body_node).set_pos(self.pos_start, self.pos_end)

    def is_true(self):
        return True

    def __repr__(self):
        return f'<function {self.name}>'


# SYMBOL TABLE
######################################
class SymbolTable:
    def __init__(self, parent=None):
        self.symbols = {}
        self.parent = parent

    def get(self, name):
        if name in self.symbols:
            return self.symbols[name]
        return self.parent.get(name) if self.parent else None

    def set(self, name, value):
        self.symbols[name] = value

    def exists(self, name):
        if name in self.symbols:
            return True
        return self.parent.exists(name) if self.parent else False


# INTERPRETER
######################################
class Interpreter:
    def __init__(self, symbol_table):
        self.symbol_table = symbol_table

    def visit(self, node):
        method_name = f'visit_{type(node).__name__}'
        method = getattr(self, method_name, self.no_visit_method)
        return method(node)

    def no_visit_method(self, node):
        raise Exception(f'No visit_{type(node).__name__} method defined')

    def visit_NumberNode(self, node):
        return RTResult().success(Number(node.tok.value).set_pos(node.pos_start, node.pos_end))

    def visit_VarAccessNode(self, node):
        res = RTResult()
        var_name = node.var_name_tok.value
        value = self.symbol_table.get(var_name)

        if value is None:
            return res.failure(RTError(node.pos_start, node.pos_end, f"'{var_name}' is not defined"))

        return res.success(value.copy().set_pos(node.pos_start, node.pos_end))

    def visit_VarAssignNode(self, node):
        res = RTResult()
        var_name = node.var_name_tok.value
        value = res.register(self.visit(node.value_node))
        if res.error:
            return res

        if not node.is_declaration and not self.symbol_table.exists(var_name):
            return res.failure(
                RTError(node.pos_start, node.pos_end, f"Cannot assign to undefined variable '{var_name}'")
            )

        self.symbol_table.set(var_name, value.copy())
        return res.success(value)

    def visit_UnaryOpNode(self, node):
        res = RTResult()
        number = res.register(self.visit(node.node))
        if res.error:
            return res

        if node.op_tok.type == TT_MINUS:
            number, error = Number(0).set_pos(node.pos_start, node.pos_end).subbed_by(number)
        elif node.op_tok.matches(TT_KEYWORD, 'not'):
            number, error = number.notted()
        else:
            number, error = number, None

        if error:
            return res.failure(error)

        return res.success(number.set_pos(node.pos_start, node.pos_end))

    def visit_BinOpNode(self, node):
        res = RTResult()
        left = res.register(self.visit(node.left_node))
        if res.error:
            return res
        right = res.register(self.visit(node.right_node))
        if res.error:
            return res

        if node.op_tok.type == TT_PLUS:
            result, error = left.added_to(right)
        elif node.op_tok.type == TT_MINUS:
            result, error = left.subbed_by(right)
        elif node.op_tok.type == TT_MUL:
            result, error = left.multed_by(right)
        elif node.op_tok.type == TT_DIV:
            result, error = left.dived_by(right)
        elif node.op_tok.type == TT_EE:
            result, error = left.compare_eq(right)
        elif node.op_tok.type == TT_NE:
            result, error = left.compare_ne(right)
        elif node.op_tok.type == TT_LT:
            result, error = left.compare_lt(right)
        elif node.op_tok.type == TT_GT:
            result, error = left.compare_gt(right)
        elif node.op_tok.type == TT_LTE:
            result, error = left.compare_lte(right)
        elif node.op_tok.type == TT_GTE:
            result, error = left.compare_gte(right)
        elif node.op_tok.matches(TT_KEYWORD, 'and'):
            result, error = (Number(1) if left.is_true() and right.is_true() else Number(0)), None
        elif node.op_tok.matches(TT_KEYWORD, 'or'):
            result, error = (Number(1) if left.is_true() or right.is_true() else Number(0)), None
        else:
            return res.failure(RTError(node.pos_start, node.pos_end, 'Unknown binary operator'))

        if error:
            return res.failure(error)

        return res.success(result.set_pos(node.pos_start, node.pos_end))

    def visit_IfNode(self, node):
        res = RTResult()

        for condition, body in node.cases:
            cond_value = res.register(self.visit(condition))
            if res.error:
                return res
            if cond_value.is_true():
                value = self.run_block(res, body)
                if res.error:
                    return res
                return res.success(value)

        if node.else_case is not None:
            value = self.run_block(res, node.else_case)
            if res.error:
                return res
            return res.success(value)

        return res.success(Number(0).set_pos(node.pos_start, node.pos_end))

    def visit_WhileNode(self, node):
        res = RTResult()
        value = Number(0).set_pos(node.pos_start, node.pos_end)

        while True:
            cond_value = res.register(self.visit(node.condition_node))
            if res.error:
                return res
            if not cond_value.is_true():
                break

            value = self.run_block(res, node.body_node)
            if res.error:
                return res

        return res.success(value)

    def visit_FuncDefNode(self, node):
        res = RTResult()
        func_name = node.var_name_tok.value
        arg_names = [tok.value for tok in node.arg_name_toks]
        func = Function(func_name, arg_names, node.body_node).set_pos(node.pos_start, node.pos_end)

        self.symbol_table.set(func_name, func)
        return res.success(func)

    def visit_CallNode(self, node):
        res = RTResult()

        func = res.register(self.visit(node.node_to_call))
        if res.error:
            return res

        if not isinstance(func, Function):
            return res.failure(RTError(node.pos_start, node.pos_end, f'{func} is not a function'))

        args = []
        for arg_node in node.arg_nodes:
            args.append(res.register(self.visit(arg_node)))
            if res.error:
                return res

        if len(args) != len(func.arg_names):
            return res.failure(
                RTError(
                    node.pos_start,
                    node.pos_end,
                    f"'{func.name}' takes {len(func.arg_names)} argument(s), got {len(args)}",
                )
            )

        # ponytail: assignment inside a call writes to the local scope, so a
        # function shadows outer names instead of mutating them. Add explicit
        # scope resolution in SymbolTable.set if that ever bites.
        call_table = SymbolTable(parent=self.symbol_table)
        for name, value in zip(func.arg_names, args):
            call_table.set(name, value.copy())

        outer_table = self.symbol_table
        self.symbol_table = call_table
        try:
            value = self.run_block(res, func.body_node)
        finally:
            self.symbol_table = outer_table

        if res.error:
            return res
        return res.success(value.set_pos(node.pos_start, node.pos_end))

    def run_block(self, res, body):
        # a block evaluates to its last statement's value, 0 when empty
        values = res.register(self.visit(body))
        if res.error:
            return None
        return values[-1] if values else Number(0).set_pos(body.pos_start, body.pos_end)

    def visit_ListNode(self, node):
        res = RTResult()
        values = []

        for element in node.element_nodes:
            values.append(res.register(self.visit(element)))
            if res.error:
                return res

        return res.success(values)


# RUN
#######################################
global_symbol_table = SymbolTable()


def run(filename, text, symbol_table=None):
    lexer = Lexer(filename, text)
    tokens, error = lexer.make_tokens()
    if error:
        return None, error

    parser = Parser(tokens)
    ast = parser.parse()
    if ast.error:
        return None, ast.error

    interpreter = Interpreter(symbol_table if symbol_table is not None else global_symbol_table)
    result = interpreter.visit(ast.node)
    if result.error:
        return None, result.error

    values = result.value
    if len(values) == 1:
        return values[0], None
    return values, None


# CLI
#######################################
def main(argv=None):
    import sys
    argv = sys.argv[1:] if argv is None else argv

    if not argv:
        import shell  # noqa: F401  (running shell.py starts the REPL)
        return 0

    path = argv[0]
    try:
        with open(path, encoding='utf-8') as f:
            source = f.read()
    except OSError as e:
        print(f'shit: cannot read {path}: {e.strerror}')
        return 1

    result, error = run(path, source)
    if error:
        print(error.as_string())
        return 1

    # ponytail: echoes every statement's value; drop this once there's a print builtin
    for value in (result if isinstance(result, list) else [result]):
        if value is not None:
            print(value)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
