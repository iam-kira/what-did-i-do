import sys

# A shit-level call costs roughly 20 Python frames, so MAX_CALL_DEPTH calls need
# headroom above CPython's default 1000 or its limit fires before ours does.
sys.setrecursionlimit(max(sys.getrecursionlimit(), 8000))


# CONSTANTS
#####################################
DIGITS = '0123456789'
LETTERS = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
LETTERS_DIGITS = LETTERS + DIGITS + '_'
KEYWORDS = [
    'stash', 'fr', 'ong', 'orfr', 'whatever', 'bet', 'keep', 'chore',
    'also', 'orelse', 'nah', 'based', 'cringe', 'ghosted',
    'grind', 'til', 'by', 'among', 'bail', 'skip', 'yeet',
    'risky', 'whoops', 'oops',
]


# ERROR
######################################
class Error:
    # set when the input merely stops early, so the REPL knows to keep reading
    incomplete = False

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
        self.frames = []
        self.frames_omitted = 0

    MAX_FRAMES = 12

    def add_frame(self, func_name, pos):
        """Record a call the error unwound through, innermost first."""
        if len(self.frames) < self.MAX_FRAMES:
            self.frames.append((func_name, pos))
        else:
            self.frames_omitted += 1
        return self

    def as_string(self):
        if not self.frames:
            return super().as_string()

        result = 'Traceback (most recent call last):\n'
        if self.frames_omitted:
            result += f'  ... {self.frames_omitted} more frame(s)\n'
        for func_name, pos in reversed(self.frames):
            result += f'  File {pos.filename}, line {pos.line + 1}, in {func_name}\n'
        return result + super().as_string()


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
TT_MOD = 'MOD'
TT_POW = 'POW'
TT_EQ = 'EQ'
TT_PLUS_EQ = 'PLUS_EQ'
TT_MINUS_EQ = 'MINUS_EQ'
TT_MUL_EQ = 'MUL_EQ'
TT_DIV_EQ = 'DIV_EQ'
TT_EE = 'EE'
TT_NE = 'NE'
TT_LT = 'LT'
TT_GT = 'GT'
TT_LTE = 'LTE'
TT_GTE = 'GTE'
TT_STRING = 'STRING'
TT_LCURLY = 'LCURLY'
TT_RCURLY = 'RCURLY'
TT_COLON = 'COLON'
TT_LSQUARE = 'LSQUARE'
TT_RSQUARE = 'RSQUARE'
TT_LPAREN = 'LPAREN'
TT_RPAREN = 'RPAREN'
TT_COMMA = 'COMMA'
TT_NEWLINE = 'NEWLINE'
TT_EOF = 'EOF'


class Token:
    def __init__(self, type_, value=None, pos_start=None, pos_end=None):
        self.type = type_
        self.value = value
        self.pos_start = None
        self.pos_end = None

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
                token, error = self.make_number()
                if error:
                    return [], error
                tokens.append(token)
            elif self.current_char in LETTERS or self.current_char == '_':
                tokens.append(self.make_identifier())
            elif self.current_char == '+':
                tokens.append(self.make_maybe_eq(TT_PLUS, TT_PLUS_EQ))
            elif self.current_char == '-':
                tokens.append(self.make_maybe_eq(TT_MINUS, TT_MINUS_EQ))
            elif self.current_char == '*':
                tokens.append(self.make_maybe_eq(TT_MUL, TT_MUL_EQ))
            elif self.current_char == '/':
                tokens.append(self.make_maybe_eq(TT_DIV, TT_DIV_EQ))
            elif self.current_char == '%':
                tokens.append(Token(TT_MOD, pos_start=self.pos))
                self.advance()
            elif self.current_char == '^':
                tokens.append(Token(TT_POW, pos_start=self.pos))
                self.advance()
            elif self.current_char == '"':
                token, error = self.make_string()
                if error:
                    return [], error
                tokens.append(token)
            elif self.current_char == '{':
                tokens.append(Token(TT_LCURLY, pos_start=self.pos))
                self.advance()
            elif self.current_char == '}':
                tokens.append(Token(TT_RCURLY, pos_start=self.pos))
                self.advance()
            elif self.current_char == ':':
                tokens.append(Token(TT_COLON, pos_start=self.pos))
                self.advance()
            elif self.current_char == '[':
                tokens.append(Token(TT_LSQUARE, pos_start=self.pos))
                self.advance()
            elif self.current_char == ']':
                tokens.append(Token(TT_RSQUARE, pos_start=self.pos))
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
                dot_count += 1
            num_str += self.current_char
            self.advance()

        if dot_count > 1 or num_str.endswith('.'):
            return None, ExpectedCharError(pos_start, self.pos.copy(), f"malformed number '{num_str}'")

        if dot_count == 0:
            return Token(TT_INT, int(num_str), pos_start, self.pos), None
        return Token(TT_FLOAT, float(num_str), pos_start, self.pos), None

    def make_string(self):
        text = ''
        pos_start = self.pos.copy()
        escapes = {'n': '\n', 't': '\t', 'r': '\r',
                   '\\': '\\', '"': '"'}
        self.advance()

        escaped = False
        while self.current_char is not None:
            if escaped:
                text += escapes.get(self.current_char, self.current_char)
                escaped = False
            elif self.current_char == '\\':
                escaped = True
            elif self.current_char == '"':
                self.advance()
                return Token(TT_STRING, text, pos_start, self.pos), None
            else:
                text += self.current_char
            self.advance()

        error = ExpectedCharError(pos_start, self.pos.copy(), 'unterminated string')
        error.incomplete = True
        return None, error

    def make_identifier(self):
        ident = ''
        pos_start = self.pos.copy()

        while self.current_char is not None and self.current_char in LETTERS_DIGITS:
            ident += self.current_char
            self.advance()

        token_type = TT_KEYWORD if ident in KEYWORDS else TT_IDENTIFIER
        return Token(token_type, ident, pos_start, self.pos)

    def make_maybe_eq(self, plain_type, eq_type):
        """'+' or '+=' - one method for every operator with a compound form."""
        pos_start = self.pos.copy()
        self.advance()

        token_type = plain_type
        if self.current_char == '=':
            self.advance()
            token_type = eq_type

        return Token(token_type, pos_start=pos_start, pos_end=self.pos)

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


class StringNode:
    def __init__(self, tok):
        self.tok = tok
        self.pos_start = tok.pos_start
        self.pos_end = tok.pos_end

    def __repr__(self):
        return f'{self.tok}'


class ArrayNode:
    """A list literal: [1, 2, 3]."""

    def __init__(self, element_nodes, pos_start, pos_end):
        self.element_nodes = element_nodes
        self.pos_start = pos_start
        self.pos_end = pos_end

    def __repr__(self):
        return f'[{self.element_nodes}]'


class BagNode:
    """A bag literal: {"a": 1}."""

    def __init__(self, pair_nodes, pos_start, pos_end):
        self.pair_nodes = pair_nodes
        self.pos_start = pos_start
        self.pos_end = pos_end

    def __repr__(self):
        return '{' + ', '.join(f'{k}: {v}' for k, v in self.pair_nodes) + '}'


class IndexNode:
    def __init__(self, target_node, index_node, pos_start, pos_end):
        self.target_node = target_node
        self.index_node = index_node
        self.pos_start = pos_start
        self.pos_end = pos_end

    def __repr__(self):
        return f'({self.target_node}[{self.index_node}])'


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
        prefix = 'stash ' if self.is_declaration else ''
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
        return f'(fr {self.cases} whatever {self.else_case})'


class WhileNode:
    def __init__(self, condition_node, body_node, pos_start, pos_end):
        self.condition_node = condition_node
        self.body_node = body_node
        self.pos_start = pos_start
        self.pos_end = pos_end

    def __repr__(self):
        return f'(keep {self.condition_node} ong {self.body_node})'


class ForNode:
    def __init__(self, var_name_tok, start_node, end_node, step_node, body_node, pos_start, pos_end):
        self.var_name_tok = var_name_tok
        self.start_node = start_node
        self.end_node = end_node
        self.step_node = step_node
        self.body_node = body_node
        self.pos_start = pos_start
        self.pos_end = pos_end

    def __repr__(self):
        return f'(grind {self.var_name_tok.value} = {self.start_node} til {self.end_node})'


class ForInNode:
    def __init__(self, var_name_tok, iterable_node, body_node, pos_start, pos_end):
        self.var_name_tok = var_name_tok
        self.iterable_node = iterable_node
        self.body_node = body_node
        self.pos_start = pos_start
        self.pos_end = pos_end

    def __repr__(self):
        return f'(grind {self.var_name_tok.value} among {self.iterable_node})'


class IndexAssignNode:
    def __init__(self, index_node, value_node):
        self.index_node = index_node
        self.value_node = value_node
        self.pos_start = index_node.pos_start
        self.pos_end = value_node.pos_end

    def __repr__(self):
        return f'({self.index_node} = {self.value_node})'


class RiskyNode:
    def __init__(self, body_node, catch_name_tok, catch_body_node, pos_start, pos_end):
        self.body_node = body_node
        self.catch_name_tok = catch_name_tok
        self.catch_body_node = catch_body_node
        self.pos_start = pos_start
        self.pos_end = pos_end

    def __repr__(self):
        return f'(risky {self.body_node} whoops {self.catch_name_tok.value})'


class OopsNode:
    def __init__(self, node_to_raise, pos_start, pos_end):
        self.node_to_raise = node_to_raise
        self.pos_start = pos_start
        self.pos_end = pos_end

    def __repr__(self):
        return f'(oops {self.node_to_raise})'


class ReturnNode:
    def __init__(self, node_to_return, pos_start, pos_end):
        self.node_to_return = node_to_return
        self.pos_start = pos_start
        self.pos_end = pos_end

    def __repr__(self):
        return f'(yeet {self.node_to_return})'


class ContinueNode:
    def __init__(self, pos_start, pos_end):
        self.pos_start = pos_start
        self.pos_end = pos_end

    def __repr__(self):
        return '(skip)'


class BreakNode:
    def __init__(self, pos_start, pos_end):
        self.pos_start = pos_start
        self.pos_end = pos_end

    def __repr__(self):
        return '(bail)'


class FuncDefNode:
    def __init__(self, var_name_tok, arg_name_toks, body_node, pos_start, pos_end):
        self.var_name_tok = var_name_tok
        self.arg_name_toks = arg_name_toks
        self.body_node = body_node
        self.pos_start = pos_start
        self.pos_end = pos_end

    def __repr__(self):
        args = ', '.join(str(tok.value) for tok in self.arg_name_toks)
        return f'(chore {self.var_name_tok.value}({args}))'


class CallNode:
    def __init__(self, node_to_call, arg_nodes, pos_end):
        self.node_to_call = node_to_call
        self.arg_nodes = arg_nodes
        self.pos_start = self.node_to_call.pos_start
        self.pos_end = pos_end

    def __repr__(self):
        return f'({self.node_to_call} call {self.arg_nodes})'


class StatementsNode:
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
ASSIGN_OPS = {
    TT_EQ: None,
    TT_PLUS_EQ: TT_PLUS,
    TT_MINUS_EQ: TT_MINUS,
    TT_MUL_EQ: TT_MUL,
    TT_DIV_EQ: TT_DIV,
}


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
            return res.success(StatementsNode([], pos_start, self.current_tok.pos_end.copy()))

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

        return res.success(StatementsNode(statements, pos_start, self.current_tok.pos_end.copy()))

    def at_statement_end(self):
        """True when nothing more of the current statement can follow."""
        if self.current_tok.type in (TT_NEWLINE, TT_EOF):
            return True
        return self.current_tok.type == TT_KEYWORD and self.current_tok.value in (
            'bet', 'orfr', 'whatever', 'whoops'
        )

    def at_block_end(self, stop_keywords):
        if self.current_tok.type == TT_EOF:
            return True
        return self.current_tok.type == TT_KEYWORD and self.current_tok.value in stop_keywords

    def statement(self):
        res = ParseResult()

        if self.current_tok.matches(TT_KEYWORD, 'fr'):
            return self.if_expr()

        if self.current_tok.matches(TT_KEYWORD, 'keep'):
            return self.while_expr()

        if self.current_tok.matches(TT_KEYWORD, 'grind'):
            return self.for_expr()

        if self.current_tok.matches(TT_KEYWORD, 'risky'):
            return self.risky_expr()

        if self.current_tok.matches(TT_KEYWORD, 'oops'):
            pos_start = self.current_tok.pos_start.copy()
            self.advance()
            value = res.register(self.expr())
            if res.error:
                return res
            return res.success(OopsNode(value, pos_start, value.pos_end.copy()))

        if self.current_tok.matches(TT_KEYWORD, 'yeet'):
            pos_start = self.current_tok.pos_start.copy()
            pos_end = self.current_tok.pos_end.copy()
            self.advance()

            value = None
            if not self.at_statement_end():
                value = res.register(self.expr())
                if res.error:
                    return res
                pos_end = value.pos_end.copy()
            return res.success(ReturnNode(value, pos_start, pos_end))

        if self.current_tok.matches(TT_KEYWORD, 'skip'):
            node = ContinueNode(self.current_tok.pos_start.copy(), self.current_tok.pos_end.copy())
            self.advance()
            return res.success(node)

        if self.current_tok.matches(TT_KEYWORD, 'bail'):
            node = BreakNode(self.current_tok.pos_start.copy(), self.current_tok.pos_end.copy())
            self.advance()
            return res.success(node)

        if self.current_tok.matches(TT_KEYWORD, 'chore'):
            return self.func_def()

        if self.current_tok.matches(TT_KEYWORD, 'stash'):
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

        expr = res.register(self.expr())
        if res.error:
            return res

        if self.current_tok.type in ASSIGN_OPS:
            return self.assignment(res, expr)

        return res.success(expr)

    def assignment(self, res, target):
        """Turn `target = value` into an assignment; `x += 1` desugars to `x = x + 1`."""
        op_tok = self.current_tok
        self.advance()

        value = res.register(self.expr())
        if res.error:
            return res

        if op_tok.type != TT_EQ:
            binop_tok = Token(ASSIGN_OPS[op_tok.type], pos_start=op_tok.pos_start, pos_end=op_tok.pos_end)
            value = BinOpNode(target, binop_tok, value)

        if isinstance(target, VarAccessNode):
            return res.success(VarAssignNode(target.var_name_tok, value, is_declaration=False))

        if isinstance(target, IndexNode):
            return res.success(IndexAssignNode(target, value))

        return res.failure(
            InvalidSyntaxError(target.pos_start, target.pos_end, 'Cannot assign to this expression')
        )

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

            if not self.current_tok.matches(TT_KEYWORD, 'ong'):
                return res.failure(
                    InvalidSyntaxError(self.current_tok.pos_start, self.current_tok.pos_end, "Expected 'ong'")
                )
            self.advance()

            body = res.register(self.statements(('orfr', 'whatever', 'bet')))
            if res.error:
                return res
            cases.append((condition, body))

            if not self.current_tok.matches(TT_KEYWORD, 'orfr'):
                break

        if self.current_tok.matches(TT_KEYWORD, 'whatever'):
            self.advance()
            else_case = res.register(self.statements(('bet',)))
            if res.error:
                return res

        if not self.current_tok.matches(TT_KEYWORD, 'bet'):
            return res.failure(
                InvalidSyntaxError(self.current_tok.pos_start, self.current_tok.pos_end, "Expected 'bet'")
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

        if not self.current_tok.matches(TT_KEYWORD, 'ong'):
            return res.failure(
                InvalidSyntaxError(self.current_tok.pos_start, self.current_tok.pos_end, "Expected 'ong'")
            )
        self.advance()

        body = res.register(self.statements(('bet',)))
        if res.error:
            return res

        if not self.current_tok.matches(TT_KEYWORD, 'bet'):
            return res.failure(
                InvalidSyntaxError(self.current_tok.pos_start, self.current_tok.pos_end, "Expected 'bet'")
            )

        pos_end = self.current_tok.pos_end.copy()
        self.advance()
        return res.success(WhileNode(condition, body, pos_start, pos_end))

    def risky_expr(self):
        res = ParseResult()
        pos_start = self.current_tok.pos_start.copy()
        self.advance()

        if not self.current_tok.matches(TT_KEYWORD, 'ong'):
            return res.failure(
                InvalidSyntaxError(self.current_tok.pos_start, self.current_tok.pos_end, "Expected 'ong'")
            )
        self.advance()

        body = res.register(self.statements(('whoops', 'bet')))
        if res.error:
            return res

        if not self.current_tok.matches(TT_KEYWORD, 'whoops'):
            return res.failure(
                InvalidSyntaxError(self.current_tok.pos_start, self.current_tok.pos_end, "Expected 'whoops'")
            )
        self.advance()

        if self.current_tok.type != TT_IDENTIFIER:
            return res.failure(
                InvalidSyntaxError(
                    self.current_tok.pos_start, self.current_tok.pos_end, 'Expected a name for the whoops'
                )
            )
        catch_name_tok = self.current_tok
        self.advance()

        if not self.current_tok.matches(TT_KEYWORD, 'ong'):
            return res.failure(
                InvalidSyntaxError(self.current_tok.pos_start, self.current_tok.pos_end, "Expected 'ong'")
            )
        self.advance()

        catch_body = res.register(self.statements(('bet',)))
        if res.error:
            return res

        if not self.current_tok.matches(TT_KEYWORD, 'bet'):
            return res.failure(
                InvalidSyntaxError(self.current_tok.pos_start, self.current_tok.pos_end, "Expected 'bet'")
            )

        pos_end = self.current_tok.pos_end.copy()
        self.advance()
        return res.success(RiskyNode(body, catch_name_tok, catch_body, pos_start, pos_end))

    def for_expr(self):
        res = ParseResult()
        pos_start = self.current_tok.pos_start.copy()
        self.advance()

        if self.current_tok.type != TT_IDENTIFIER:
            return res.failure(
                InvalidSyntaxError(self.current_tok.pos_start, self.current_tok.pos_end, 'Expected identifier')
            )
        var_name_tok = self.current_tok
        self.advance()

        if self.current_tok.matches(TT_KEYWORD, 'among'):
            self.advance()
            iterable_node = res.register(self.expr())
            if res.error:
                return res

            if not self.current_tok.matches(TT_KEYWORD, 'ong'):
                return res.failure(
                    InvalidSyntaxError(self.current_tok.pos_start, self.current_tok.pos_end, "Expected 'ong'")
                )
            self.advance()

            body = res.register(self.statements(('bet',)))
            if res.error:
                return res

            if not self.current_tok.matches(TT_KEYWORD, 'bet'):
                return res.failure(
                    InvalidSyntaxError(self.current_tok.pos_start, self.current_tok.pos_end, "Expected 'bet'")
                )
            pos_end = self.current_tok.pos_end.copy()
            self.advance()
            return res.success(ForInNode(var_name_tok, iterable_node, body, pos_start, pos_end))

        if self.current_tok.type != TT_EQ:
            return res.failure(
                InvalidSyntaxError(self.current_tok.pos_start, self.current_tok.pos_end, "Expected 'among' or '='")
            )
        self.advance()

        start_node = res.register(self.expr())
        if res.error:
            return res

        if not self.current_tok.matches(TT_KEYWORD, 'til'):
            return res.failure(
                InvalidSyntaxError(self.current_tok.pos_start, self.current_tok.pos_end, "Expected 'til'")
            )
        self.advance()

        end_node = res.register(self.expr())
        if res.error:
            return res

        step_node = None
        if self.current_tok.matches(TT_KEYWORD, 'by'):
            self.advance()
            step_node = res.register(self.expr())
            if res.error:
                return res

        if not self.current_tok.matches(TT_KEYWORD, 'ong'):
            return res.failure(
                InvalidSyntaxError(self.current_tok.pos_start, self.current_tok.pos_end, "Expected 'ong'")
            )
        self.advance()

        body = res.register(self.statements(('bet',)))
        if res.error:
            return res

        if not self.current_tok.matches(TT_KEYWORD, 'bet'):
            return res.failure(
                InvalidSyntaxError(self.current_tok.pos_start, self.current_tok.pos_end, "Expected 'bet'")
            )

        pos_end = self.current_tok.pos_end.copy()
        self.advance()
        return res.success(ForNode(var_name_tok, start_node, end_node, step_node, body, pos_start, pos_end))

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

        if not self.current_tok.matches(TT_KEYWORD, 'ong'):
            return res.failure(
                InvalidSyntaxError(self.current_tok.pos_start, self.current_tok.pos_end, "Expected 'ong'")
            )
        self.advance()

        body = res.register(self.statements(('bet',)))
        if res.error:
            return res

        if not self.current_tok.matches(TT_KEYWORD, 'bet'):
            return res.failure(
                InvalidSyntaxError(self.current_tok.pos_start, self.current_tok.pos_end, "Expected 'bet'")
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
        return self.bin_op(self.and_expr, ((TT_KEYWORD, 'orelse'),))

    def and_expr(self):
        return self.bin_op(self.not_expr, ((TT_KEYWORD, 'also'),))

    def not_expr(self):
        res = ParseResult()

        if self.current_tok.matches(TT_KEYWORD, 'nah'):
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
        return self.bin_op(self.factor, (TT_MUL, TT_DIV, TT_MOD))

    def factor(self):
        res = ParseResult()
        tok = self.current_tok

        if tok.type in (TT_PLUS, TT_MINUS):
            self.advance()
            factor = res.register(self.factor())
            if res.error:
                return res
            return res.success(UnaryOpNode(tok, factor))

        return self.power()

    def power(self):
        # right-associative: 2 ^ 3 ^ 2 is 2 ^ (3 ^ 2)
        return self.bin_op(self.atom, (TT_POW,), right=self.factor)

    def atom(self):
        res = ParseResult()
        tok = self.current_tok

        if tok.type in (TT_INT, TT_FLOAT):
            self.advance()
            return res.success(NumberNode(tok))

        if tok.type == TT_STRING:
            self.advance()
            return self.postfix_result(res, StringNode(tok))

        if tok.type == TT_LSQUARE:
            array = res.register(self.array_expr())
            if res.error:
                return res
            return self.postfix_result(res, array)

        if tok.type == TT_LCURLY:
            bag = res.register(self.bag_expr())
            if res.error:
                return res
            return self.postfix_result(res, bag)

        if tok.type == TT_KEYWORD and tok.value in ('based', 'cringe', 'ghosted'):
            self.advance()
            literal = 1 if tok.value == 'based' else 0
            return res.success(NumberNode(Token(TT_INT, literal, tok.pos_start, tok.pos_end)))

        if tok.type == TT_IDENTIFIER:
            self.advance()
            if self.current_tok.type == TT_LPAREN:
                called = res.register(self.call(VarAccessNode(tok)))
                if res.error:
                    return res
                return self.postfix_result(res, called)
            return self.postfix_result(res, VarAccessNode(tok))

        if tok.type == TT_LPAREN:
            self.advance()
            expr = res.register(self.expr())
            if res.error:
                return res
            if self.current_tok.type == TT_RPAREN:
                self.advance()
                return self.postfix_result(res, expr)
            return res.failure(
                InvalidSyntaxError(self.current_tok.pos_start, self.current_tok.pos_end, "Expected ')'")
            )

        return res.failure(
            InvalidSyntaxError(
                tok.pos_start, tok.pos_end, "Expected int, float, identifier, 'not', '+', '-' or '('"
            )
        )

    def array_expr(self):
        res = ParseResult()
        pos_start = self.current_tok.pos_start.copy()
        self.advance()  # past '['

        element_nodes = []
        while self.current_tok.type == TT_NEWLINE:
            self.advance()

        if self.current_tok.type != TT_RSQUARE:
            element_nodes.append(res.register(self.expr()))
            if res.error:
                return res

            while self.current_tok.type == TT_COMMA:
                self.advance()
                while self.current_tok.type == TT_NEWLINE:
                    self.advance()
                if self.current_tok.type == TT_RSQUARE:
                    break  # trailing comma
                element_nodes.append(res.register(self.expr()))
                if res.error:
                    return res

        while self.current_tok.type == TT_NEWLINE:
            self.advance()

        if self.current_tok.type != TT_RSQUARE:
            return res.failure(
                InvalidSyntaxError(self.current_tok.pos_start, self.current_tok.pos_end, "Expected ',' or ']'")
            )

        pos_end = self.current_tok.pos_end.copy()
        self.advance()
        return res.success(ArrayNode(element_nodes, pos_start, pos_end))

    def bag_expr(self):
        res = ParseResult()
        pos_start = self.current_tok.pos_start.copy()
        self.advance()  # past '{'

        pair_nodes = []
        self.skip_newlines()

        if self.current_tok.type != TT_RCURLY:
            while True:
                key = res.register(self.expr())
                if res.error:
                    return res

                if self.current_tok.type != TT_COLON:
                    return res.failure(
                        InvalidSyntaxError(self.current_tok.pos_start, self.current_tok.pos_end, "Expected ':'")
                    )
                self.advance()
                self.skip_newlines()

                value = res.register(self.expr())
                if res.error:
                    return res
                pair_nodes.append((key, value))

                self.skip_newlines()
                if self.current_tok.type != TT_COMMA:
                    break
                self.advance()
                self.skip_newlines()
                if self.current_tok.type == TT_RCURLY:
                    break  # trailing comma

        self.skip_newlines()
        if self.current_tok.type != TT_RCURLY:
            return res.failure(
                InvalidSyntaxError(self.current_tok.pos_start, self.current_tok.pos_end, "Expected ',' or '}'")
            )

        pos_end = self.current_tok.pos_end.copy()
        self.advance()
        return res.success(BagNode(pair_nodes, pos_start, pos_end))

    def skip_newlines(self):
        while self.current_tok.type == TT_NEWLINE:
            self.advance()

    def postfix_result(self, res, node):
        """Attach any trailing [index] suffixes to an already-parsed atom."""
        while self.current_tok.type == TT_LSQUARE:
            self.advance()
            index = res.register(self.expr())
            if res.error:
                return res
            if self.current_tok.type != TT_RSQUARE:
                return res.failure(
                    InvalidSyntaxError(self.current_tok.pos_start, self.current_tok.pos_end, "Expected ']'")
                )
            pos_end = self.current_tok.pos_end.copy()
            self.advance()
            node = IndexNode(node, index, node.pos_start, pos_end)
        return res.success(node)

    def op_matches(self, ops):
        for op in ops:
            if isinstance(op, tuple):
                if self.current_tok.matches(op[0], op[1]):
                    return True
            elif self.current_tok.type == op:
                return True
        return False

    def bin_op(self, func, ops, right=None):
        res = ParseResult()
        right_func = right if right is not None else func
        left = res.register(func())
        if res.error:
            return res

        while self.op_matches(ops):
            op_tok = self.current_tok
            self.advance()
            right = res.register(right_func())
            if res.error:
                return res
            left = BinOpNode(left, op_tok, right)

        return res.success(left)


# RUNTIME RESULT
######################################
class RTResult:
    def __init__(self):
        self.reset()

    def reset(self):
        self.value = None
        self.error = None
        self.func_return_value = None
        self.loop_should_continue = False
        self.loop_should_break = False

    def register(self, res):
        if res.error:
            self.error = res.error
        self.func_return_value = res.func_return_value
        self.loop_should_continue = res.loop_should_continue
        self.loop_should_break = res.loop_should_break
        return res.value

    def should_return(self):
        """True when control must unwind: an error, a return, or break/continue."""
        return (
            self.error is not None
            or self.func_return_value is not None
            or self.loop_should_continue
            or self.loop_should_break
        )

    def success(self, value):
        self.value = value
        return self

    def success_return(self, value):
        self.func_return_value = value
        return self

    def success_continue(self):
        self.loop_should_continue = True
        return self

    def success_break(self):
        self.loop_should_break = True
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

    # what this type is called in error messages, in the dialect
    TYPE_NAME = 'thing'

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
            f'Illegal operation for {self.TYPE_NAME}',
        )

    def added_to(self, other):
        return self.illegal_operation(other)

    def subbed_by(self, other):
        return self.illegal_operation(other)

    def multed_by(self, other):
        return self.illegal_operation(other)

    def dived_by(self, other):
        return self.illegal_operation(other)

    def modded_by(self, other):
        return self.illegal_operation(other)

    def powed_by(self, other):
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

    def get_index(self, index):
        return None, RTError(
            self.pos_start, index.pos_end, f'{self.TYPE_NAME} is not indexable'
        )

    def set_index(self, index, value):
        return RTError(
            self.pos_start, index.pos_end, f'Cannot assign into a {self.TYPE_NAME}'
        )

    def length(self):
        return None


class Number(Value):
    TYPE_NAME = 'math'

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

    def modded_by(self, other):
        if not isinstance(other, Number):
            return self.illegal_operation(other)
        if other.value == 0:
            return None, RTError(other.pos_start, other.pos_end, 'Modulo by zero')
        return Number(self.value % other.value), None

    def powed_by(self, other):
        if not isinstance(other, Number):
            return self.illegal_operation(other)
        try:
            result = self.value ** other.value
        except (OverflowError, ZeroDivisionError) as exc:
            return None, RTError(self.pos_start, other.pos_end, str(exc))
        if isinstance(result, complex):
            return None, RTError(self.pos_start, other.pos_end, 'Result is not a real number')
        return Number(result), None

    def is_true(self):
        return self.value != 0

    def __repr__(self):
        if isinstance(self.value, float) and self.value.is_integer():
            return str(int(self.value))
        return str(self.value)


class String(Value):
    TYPE_NAME = 'yap'

    def __init__(self, value):
        super().__init__()
        self.value = value

    def copy(self):
        return String(self.value).set_pos(self.pos_start, self.pos_end)

    def added_to(self, other):
        if not isinstance(other, String):
            return self.illegal_operation(other)
        return String(self.value + other.value), None

    def multed_by(self, other):
        if not isinstance(other, Number) or not isinstance(other.value, int):
            return self.illegal_operation(other)
        return String(self.value * other.value), None

    def compare_eq(self, other):
        if not isinstance(other, String):
            return Number(0), None
        return Number(1 if self.value == other.value else 0), None

    def compare_ne(self, other):
        if not isinstance(other, String):
            return Number(1), None
        return Number(1 if self.value != other.value else 0), None

    def compare_lt(self, other):
        if not isinstance(other, String):
            return self.illegal_operation(other)
        return Number(1 if self.value < other.value else 0), None

    def compare_gt(self, other):
        if not isinstance(other, String):
            return self.illegal_operation(other)
        return Number(1 if self.value > other.value else 0), None

    def compare_lte(self, other):
        if not isinstance(other, String):
            return self.illegal_operation(other)
        return Number(1 if self.value <= other.value else 0), None

    def compare_gte(self, other):
        if not isinstance(other, String):
            return self.illegal_operation(other)
        return Number(1 if self.value >= other.value else 0), None

    def get_index(self, index):
        return index_into(self, self.value, index, String)

    def length(self):
        return len(self.value)

    def is_true(self):
        return len(self.value) > 0

    def __str__(self):
        return self.value

    def __repr__(self):
        return f'"{self.value}"'


class List(Value):
    TYPE_NAME = 'pile'

    def __init__(self, elements):
        super().__init__()
        self.elements = elements

    def copy(self):
        return List(list(self.elements)).set_pos(self.pos_start, self.pos_end)

    def added_to(self, other):
        if not isinstance(other, List):
            return self.illegal_operation(other)
        return List(self.elements + other.elements), None

    def multed_by(self, other):
        if not isinstance(other, Number) or not isinstance(other.value, int):
            return self.illegal_operation(other)
        return List(self.elements * other.value), None

    def compare_eq(self, other):
        if not isinstance(other, List) or len(self.elements) != len(other.elements):
            return Number(0), None
        for mine, theirs in zip(self.elements, other.elements):
            equal, error = mine.compare_eq(theirs)
            if error:
                return None, error
            if not equal.is_true():
                return Number(0), None
        return Number(1), None

    def compare_ne(self, other):
        equal, error = self.compare_eq(other)
        if error:
            return None, error
        return Number(0 if equal.is_true() else 1), None

    def get_index(self, index):
        return index_into(self, self.elements, index, None)

    def set_index(self, index, value):
        _, error = index_into(self, self.elements, index, None)
        if error:
            return error
        i = index.value if index.value >= 0 else index.value + len(self.elements)
        self.elements[i] = value
        return None

    def length(self):
        return len(self.elements)

    def is_true(self):
        return len(self.elements) > 0

    def __repr__(self):
        return '[' + ', '.join(repr(element) for element in self.elements) + ']'


def index_into(container, sequence, index, wrap):
    """Shared bounds-checked indexing for String and List.

    Negative indices count from the end, as in Python.
    """
    if not isinstance(index, Number) or not isinstance(index.value, int):
        return None, RTError(index.pos_start, index.pos_end, 'Index must be a whole math')

    i = index.value
    if i < 0:
        i += len(sequence)
    if not 0 <= i < len(sequence):
        return None, RTError(
            index.pos_start, index.pos_end, f'Index {index.value} out of range (length {len(sequence)})'
        )

    item = sequence[i]
    return (wrap(item) if wrap is not None else item), None


class BaseFunction(Value):
    TYPE_NAME = 'chore'

    def __init__(self, name, arg_names):
        super().__init__()
        self.name = name
        self.arg_names = arg_names

    # arg name prefixes: '?' optional, '*' soaks up any number more
    @property
    def fixed_names(self):
        return [name for name in self.arg_names if not name.startswith('*')]

    @property
    def is_variadic(self):
        return len(self.fixed_names) != len(self.arg_names)

    @property
    def required_count(self):
        return len([name for name in self.fixed_names if not name.startswith('?')])

    def check_args(self, args, pos_start, pos_end):
        low = self.required_count
        high = None if self.is_variadic else len(self.fixed_names)

        if len(args) >= low and (high is None or len(args) <= high):
            return None

        if high is None:
            wanted = f'at least {low}'
        elif low == high:
            wanted = str(low)
        else:
            wanted = f'{low} to {high}'
        return RTError(
            pos_start,
            pos_end,
            f"'{self.name}' takes {wanted} argument(s), got {len(args)}",
        )

    def is_true(self):
        return True


class Bag(Value):
    TYPE_NAME = 'bag'

    def __init__(self, pairs=None):
        super().__init__()
        # python key -> (key Value, value Value); insertion ordered
        self.pairs = dict(pairs) if pairs else {}

    @staticmethod
    def key_of(value):
        """Maths and yaps can be labels; nothing else can."""
        if isinstance(value, Number):
            return ('math', value.value)
        if isinstance(value, String):
            return ('yap', value.value)
        return None

    def copy(self):
        clone = Bag({k: (kv.copy(), vv.copy()) for k, (kv, vv) in self.pairs.items()})
        return clone.set_pos(self.pos_start, self.pos_end)

    def added_to(self, other):
        if not isinstance(other, Bag):
            return self.illegal_operation(other)
        merged = dict(self.pairs)
        merged.update(other.pairs)
        return Bag(merged), None

    def compare_eq(self, other):
        if not isinstance(other, Bag) or len(self.pairs) != len(other.pairs):
            return Number(0), None
        for key, (_, mine) in self.pairs.items():
            if key not in other.pairs:
                return Number(0), None
            equal, error = mine.compare_eq(other.pairs[key][1])
            if error:
                return None, error
            if not equal.is_true():
                return Number(0), None
        return Number(1), None

    def compare_ne(self, other):
        equal, error = self.compare_eq(other)
        if error:
            return None, error
        return Number(0 if equal.is_true() else 1), None

    def get_index(self, index):
        key = self.key_of(index)
        if key is None:
            return None, RTError(index.pos_start, index.pos_end, 'A bag label must be a math or a yap')
        if key not in self.pairs:
            return None, RTError(index.pos_start, index.pos_end, f'No label {index!r} in this bag')
        return self.pairs[key][1], None

    def set_index(self, index, value):
        key = self.key_of(index)
        if key is None:
            return RTError(index.pos_start, index.pos_end, 'A bag label must be a math or a yap')
        self.pairs[key] = (index.copy(), value)
        return None

    def labels(self):
        return [key_value for key_value, _ in self.pairs.values()]

    def goods(self):
        return [value for _, value in self.pairs.values()]

    def length(self):
        return len(self.pairs)

    def is_true(self):
        return len(self.pairs) > 0

    def __repr__(self):
        if not self.pairs:
            return '{}'
        return '{' + ', '.join(f'{k!r}: {v!r}' for k, v in self.pairs.values()) + '}'


class Function(BaseFunction):
    def __init__(self, name, arg_names, body_node, defining_scope=None):
        super().__init__(name, arg_names)
        self.body_node = body_node
        # the scope the function was written in - calls parent off this, not off
        # whoever happens to be calling, so scoping is lexical
        self.defining_scope = defining_scope

    def copy(self):
        return Function(self.name, self.arg_names, self.body_node, self.defining_scope).set_pos(
            self.pos_start, self.pos_end
        )

    def execute(self, args, interpreter, node):
        res = RTResult()

        if interpreter.func_depth >= MAX_CALL_DEPTH:
            return res.failure(
                RTError(
                    node.pos_start,
                    node.pos_end,
                    f'Maximum call depth of {MAX_CALL_DEPTH} exceeded',
                )
            )

        parent_scope = self.defining_scope if self.defining_scope is not None else interpreter.symbol_table
        call_table = SymbolTable(parent=parent_scope)
        for name, value in zip(self.arg_names, args):
            call_table.set(name, value.copy())

        outer_table = interpreter.symbol_table
        outer_loop_depth = interpreter.loop_depth
        interpreter.symbol_table = call_table
        interpreter.loop_depth = 0
        interpreter.func_depth += 1
        try:
            value = interpreter.run_block(res, self.body_node)
        finally:
            interpreter.symbol_table = outer_table
            interpreter.loop_depth = outer_loop_depth
            interpreter.func_depth -= 1

        if res.error:
            return res

        if res.func_return_value is not None:
            value = res.func_return_value

        # signals stop at the call boundary
        res.func_return_value = None
        res.loop_should_break = False
        res.loop_should_continue = False
        return res.success(value)

    def __repr__(self):
        return f'<chore {self.name}>'


class BuiltInFunction(BaseFunction):
    def __init__(self, name, arg_names, fn, wants_interpreter=False):
        super().__init__(name, arg_names)
        self.fn = fn
        self.wants_interpreter = wants_interpreter

    def copy(self):
        return BuiltInFunction(self.name, self.arg_names, self.fn, self.wants_interpreter).set_pos(
            self.pos_start, self.pos_end
        )

    def execute(self, args, interpreter, node):
        res = RTResult()
        count = len(self.fixed_names)
        # missing optionals arrive as None; anything past the fixed names rides along
        args = list(args[:count]) + [None] * (count - len(args)) + list(args[count:])
        if self.wants_interpreter:
            value, error = self.fn(args, node, interpreter)
        else:
            value, error = self.fn(args, node)
        if error:
            return res.failure(error)
        return res.success(value)

    def __repr__(self):
        return f'<built-in chore {self.name}>'


# BUILT-IN FUNCTIONS
######################################
def _type_error(node, message):
    return None, RTError(node.pos_start, node.pos_end, message)


def bi_print(args, node):
    print(str(args[0]) if isinstance(args[0], String) else repr(args[0]))
    return Number(0), None


def bi_input(args, node):
    prompt = '' if args[0] is None else (str(args[0]) if isinstance(args[0], String) else repr(args[0]))
    try:
        return String(input(prompt)), None
    except EOFError:
        return String(''), None


def bi_len(args, node):
    length = args[0].length()
    if length is None:
        return _type_error(node, f"'howmany' needs a yap, pile or bag, got {args[0].TYPE_NAME}")
    return Number(length), None


def bi_str(args, node):
    value = args[0]
    return String(str(value) if isinstance(value, String) else repr(value)), None


def bi_num(args, node):
    value = args[0]
    if isinstance(value, Number):
        return value.copy(), None
    if isinstance(value, String):
        text = value.value.strip()
        try:
            return Number(int(text)), None
        except ValueError:
            pass
        try:
            return Number(float(text)), None
        except ValueError:
            return _type_error(node, f'Cannot convert "{value.value}" to a number')
    return _type_error(node, f"'mathify' cannot convert a {value.TYPE_NAME}")


def bi_append(args, node):
    target, value = args
    if not isinstance(target, List):
        return _type_error(node, "'stuff' needs a pile as its first argument")
    return List(target.elements + [value.copy()]), None


def bi_pop(args, node):
    target, index = args
    if isinstance(target, Bag):
        key = Bag.key_of(index)
        if key is None or key not in target.pairs:
            return None, RTError(node.pos_start, node.pos_end, f'No label {index!r} in this bag')
        remaining = dict(target.pairs)
        del remaining[key]
        return Bag(remaining), None

    if not isinstance(target, List):
        return _type_error(node, "'yoink' needs a pile or bag as its first argument")
    _, error = target.get_index(index)
    if error:
        return None, error
    i = index.value if index.value >= 0 else index.value + len(target.elements)
    remaining = list(target.elements)
    remaining.pop(i)
    return List(remaining), None


def _need(node, value, cls, what, who):
    if not isinstance(value, cls):
        return RTError(node.pos_start, node.pos_end, f"'{who}' needs a {what}, got {value.TYPE_NAME}")
    return None


def _numbers(args, node, who):
    """Flatten a single pile argument, or loose maths, into Python numbers."""
    values = args[0].elements if len(args) == 1 and isinstance(args[0], List) else args
    if not values:
        return None, RTError(node.pos_start, node.pos_end, f"'{who}' needs at least one math")
    out = []
    for value in values:
        error = _need(node, value, Number, 'math', who)
        if error:
            return None, error
        out.append(value.value)
    return out, None


def bi_smol(args, node):
    values, error = _numbers([a for a in args if a is not None], node, 'smol')
    return (None, error) if error else (Number(min(values)), None)


def bi_chonk(args, node):
    values, error = _numbers([a for a in args if a is not None], node, 'chonk')
    return (None, error) if error else (Number(max(values)), None)


def bi_absolutely(args, node):
    error = _need(node, args[0], Number, 'math', 'absolutely')
    return (None, error) if error else (Number(abs(args[0].value)), None)


def bi_roundish(args, node):
    error = _need(node, args[0], Number, 'math', 'roundish')
    if error:
        return None, error
    if args[1] is None:
        return Number(int(round(args[0].value))), None
    error = _need(node, args[1], Number, 'math', 'roundish')
    if error:
        return None, error
    return Number(round(args[0].value, int(args[1].value))), None


def bi_total(args, node):
    values, error = _numbers([a for a in args if a is not None], node, 'total')
    return (None, error) if error else (Number(sum(values)), None)


def bi_chunk(args, node):
    target = args[0]
    if not isinstance(target, (String, List)):
        return None, RTError(node.pos_start, node.pos_end, "'chunk' needs a yap or pile")

    length = target.length()
    bounds = []
    for arg, default in ((args[1], 0), (args[2], length)):
        if arg is None:
            bounds.append(default)
            continue
        error = _need(node, arg, Number, 'whole math', 'chunk')
        if error:
            return None, error
        index = int(arg.value)
        bounds.append(index + length if index < 0 else index)

    start, stop = max(0, bounds[0]), min(length, bounds[1])
    if isinstance(target, String):
        return String(target.value[start:stop]), None
    return List([item.copy() for item in target.elements[start:stop]]), None


def bi_flip(args, node):
    target = args[0]
    if isinstance(target, String):
        return String(target.value[::-1]), None
    if isinstance(target, List):
        return List([item.copy() for item in reversed(target.elements)]), None
    return None, RTError(node.pos_start, node.pos_end, "'flip' needs a yap or pile")


def bi_glue(args, node):
    error = _need(node, args[0], List, 'pile', 'glue')
    if error:
        return None, error

    if args[1] is None:
        separator = ''
    elif isinstance(args[1], String):
        separator = args[1].value
    else:
        return None, RTError(node.pos_start, node.pos_end, "'glue' separator must be a yap")

    parts = [item.value if isinstance(item, String) else repr(item) for item in args[0].elements]
    return String(separator.join(parts)), None


def bi_shred(args, node):
    error = _need(node, args[0], String, 'yap', 'shred')
    if error:
        return None, error

    if args[1] is None:
        pieces = args[0].value.split()
    else:
        error = _need(node, args[1], String, 'yap', 'shred')
        if error:
            return None, error
        pieces = list(args[0].value) if args[1].value == '' else args[0].value.split(args[1].value)
    return List([String(piece) for piece in pieces]), None


def bi_shout(args, node):
    error = _need(node, args[0], String, 'yap', 'shout')
    return (None, error) if error else (String(args[0].value.upper()), None)


def bi_whisper(args, node):
    error = _need(node, args[0], String, 'yap', 'whisper')
    return (None, error) if error else (String(args[0].value.lower()), None)


def bi_trim(args, node):
    error = _need(node, args[0], String, 'yap', 'trim')
    return (None, error) if error else (String(args[0].value.strip()), None)


def _members(container):
    if isinstance(container, List):
        return container.elements
    if isinstance(container, String):
        return [String(char) for char in container.value]
    if isinstance(container, Bag):
        return container.labels()
    return None


def bi_where(args, node):
    members = _members(args[0])
    if members is None:
        return None, RTError(node.pos_start, node.pos_end, "'where' needs a yap or pile")
    for i, item in enumerate(members):
        equal, error = item.compare_eq(args[1])
        if error:
            return None, error
        if equal.is_true():
            return Number(i), None
    return Number(-1), None


def bi_gotit(args, node):
    index, error = bi_where(args, node)
    if error:
        return None, RTError(node.pos_start, node.pos_end, "'gotit' needs a yap or pile")
    return Number(1 if index.value >= 0 else 0), None


def bi_sortof(args, node):
    error = _need(node, args[0], List, 'pile', 'sortof')
    if error:
        return None, error

    items = [item.copy() for item in args[0].elements]
    if all(isinstance(item, Number) for item in items):
        items.sort(key=lambda item: item.value)
    elif all(isinstance(item, String) for item in items):
        items.sort(key=lambda item: item.value)
    elif items:
        return None, RTError(node.pos_start, node.pos_end, "'sortof' needs a pile of all maths or all yaps")
    return List(items), None


def bi_labels(args, node):
    error = _need(node, args[0], Bag, 'bag', 'labels')
    if error:
        return None, error
    return List([key.copy() for key in args[0].labels()]), None


def bi_goods(args, node):
    error = _need(node, args[0], Bag, 'bag', 'goods')
    if error:
        return None, error
    return List([value.copy() for value in args[0].goods()]), None


# files currently being summoned, so a cycle reports instead of recursing forever
_summoning = set()


def bi_summon(args, node, interpreter):
    import os

    error = _need(node, args[0], String, 'yap', 'summon')
    if error:
        return None, error

    target = args[0].value
    here = node.pos_start.filename
    base = os.path.dirname(os.path.abspath(here)) if os.path.exists(here) else os.getcwd()
    full = target if os.path.isabs(target) else os.path.join(base, target)
    full = os.path.normpath(full)

    if full in _summoning:
        return None, RTError(node.pos_start, node.pos_end, f"'{target}' is summoning itself")

    try:
        with open(full, encoding='utf-8') as handle:
            source = handle.read()
    except OSError as exc:
        return None, RTError(node.pos_start, node.pos_end, f"Cannot summon '{target}': {exc.strerror}")

    _summoning.add(full)
    try:
        tokens, error = Lexer(full, source).make_tokens()
        if error:
            return None, error

        ast = Parser(tokens).parse()
        if ast.error:
            return None, ast.error

        # runs in the summoning scope, so its stashes and chores land here
        result = interpreter.visit(ast.node)
        if result.error:
            return None, result.error
    finally:
        _summoning.discard(full)

    return Number(0), None


def bi_whatis(args, node):
    return String(args[0].TYPE_NAME), None


def bi_is_num(args, node):
    return Number(1 if isinstance(args[0], Number) else 0), None


def bi_is_str(args, node):
    return Number(1 if isinstance(args[0], String) else 0), None


def bi_is_list(args, node):
    return Number(1 if isinstance(args[0], List) else 0), None


def bi_is_fun(args, node):
    return Number(1 if isinstance(args[0], BaseFunction) else 0), None


BUILTINS = {
    'yap': (['value'], bi_print),
    'beg': (['?prompt'], bi_input),
    'howmany': (['value'], bi_len),
    'yapify': (['value'], bi_str),
    'mathify': (['value'], bi_num),
    'stuff': (['list', 'value'], bi_append),
    'yoink': (['list', 'index'], bi_pop),
    'smol': (['value', '*more'], bi_smol),
    'chonk': (['value', '*more'], bi_chonk),
    'absolutely': (['value'], bi_absolutely),
    'roundish': (['value', '?places'], bi_roundish),
    'total': (['value', '*more'], bi_total),
    'chunk': (['value', '?start', '?stop'], bi_chunk),
    'flip': (['value'], bi_flip),
    'glue': (['pile', '?separator'], bi_glue),
    'shred': (['yap', '?separator'], bi_shred),
    'shout': (['yap'], bi_shout),
    'whisper': (['yap'], bi_whisper),
    'trim': (['yap'], bi_trim),
    'where': (['value', 'needle'], bi_where),
    'gotit': (['value', 'needle'], bi_gotit),
    'sortof': (['pile'], bi_sortof),
    'labels': (['bag'], bi_labels),
    'goods': (['bag'], bi_goods),
    'summon': (['path'], bi_summon),
    'whatis': (['value'], bi_whatis),
    'is_math': (['value'], bi_is_num),
    'is_yap': (['value'], bi_is_str),
    'is_pile': (['value'], bi_is_list),
    'is_chore': (['value'], bi_is_fun),
}


NEEDS_INTERPRETER = {'summon'}


def install_builtins(symbol_table):
    for name, (arg_names, fn) in BUILTINS.items():
        symbol_table.set(name, BuiltInFunction(name, arg_names, fn, name in NEEDS_INTERPRETER))
    return symbol_table


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
        """Declare or overwrite in THIS scope."""
        self.symbols[name] = value

    def set_existing(self, name, value):
        """Assign where the name was declared, walking outwards. False if unbound."""
        scope = self
        while scope is not None:
            if name in scope.symbols:
                scope.symbols[name] = value
                return True
            scope = scope.parent
        return False

    def exists(self, name):
        if name in self.symbols:
            return True
        return self.parent.exists(name) if self.parent else False


# INTERPRETER
######################################
MAX_CALL_DEPTH = 200


class Interpreter:
    def __init__(self, symbol_table):
        self.symbol_table = symbol_table
        self.loop_depth = 0
        self.func_depth = 0

    def visit(self, node):
        method_name = f'visit_{type(node).__name__}'
        method = getattr(self, method_name, self.no_visit_method)
        return method(node)

    def no_visit_method(self, node):
        raise Exception(f'No visit_{type(node).__name__} method defined')

    def visit_NumberNode(self, node):
        return RTResult().success(Number(node.tok.value).set_pos(node.pos_start, node.pos_end))

    def visit_StringNode(self, node):
        return RTResult().success(String(node.tok.value).set_pos(node.pos_start, node.pos_end))

    def visit_ArrayNode(self, node):
        res = RTResult()
        elements = []

        for element_node in node.element_nodes:
            elements.append(res.register(self.visit(element_node)))
            if res.error:
                return res

        return res.success(List(elements).set_pos(node.pos_start, node.pos_end))

    def visit_BagNode(self, node):
        res = RTResult()
        bag = Bag().set_pos(node.pos_start, node.pos_end)

        for key_node, value_node in node.pair_nodes:
            key = res.register(self.visit(key_node))
            if res.error:
                return res
            value = res.register(self.visit(value_node))
            if res.error:
                return res

            error = bag.set_index(key, value)
            if error:
                return res.failure(error)

        return res.success(bag)

    def visit_IndexNode(self, node):
        res = RTResult()

        target = res.register(self.visit(node.target_node))
        if res.error:
            return res
        index = res.register(self.visit(node.index_node))
        if res.error:
            return res

        value, error = target.get_index(index)
        if error:
            return res.failure(error)
        return res.success(value.copy().set_pos(node.pos_start, node.pos_end))

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

        if node.is_declaration:
            self.symbol_table.set(var_name, value.copy())
            return res.success(value)

        if not self.symbol_table.set_existing(var_name, value.copy()):
            return res.failure(
                RTError(node.pos_start, node.pos_end, f"Cannot assign to undefined variable '{var_name}'")
            )
        return res.success(value)

    def visit_UnaryOpNode(self, node):
        res = RTResult()
        number = res.register(self.visit(node.node))
        if res.error:
            return res

        if node.op_tok.type == TT_MINUS:
            number, error = Number(0).set_pos(node.pos_start, node.pos_end).subbed_by(number)
        elif node.op_tok.matches(TT_KEYWORD, 'nah'):
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
        elif node.op_tok.type == TT_MOD:
            result, error = left.modded_by(right)
        elif node.op_tok.type == TT_POW:
            result, error = left.powed_by(right)
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
        elif node.op_tok.matches(TT_KEYWORD, 'also'):
            result, error = (Number(1) if left.is_true() and right.is_true() else Number(0)), None
        elif node.op_tok.matches(TT_KEYWORD, 'orelse'):
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

        self.loop_depth += 1
        try:
            while True:
                cond_value = res.register(self.visit(node.condition_node))
                if res.error:
                    return res
                if not cond_value.is_true():
                    break

                body_value = self.run_block(res, node.body_node)
                if res.error:
                    return res
                if res.func_return_value is not None:
                    return res
                if res.loop_should_break:
                    res.loop_should_break = False
                    break
                if res.loop_should_continue:
                    res.loop_should_continue = False
                    continue
                value = body_value
        finally:
            self.loop_depth -= 1

        return res.success(value)

    def visit_ForNode(self, node):
        res = RTResult()

        start_value = res.register(self.visit(node.start_node))
        if res.error:
            return res
        end_value = res.register(self.visit(node.end_node))
        if res.error:
            return res

        if node.step_node is not None:
            step_value = res.register(self.visit(node.step_node))
            if res.error:
                return res
        else:
            step_value = Number(1)

        for name, val in (('start', start_value), ('til', end_value), ('by', step_value)):
            if not isinstance(val, Number):
                return res.failure(
                    RTError(node.pos_start, node.pos_end, f"'grind' {name} value must be a math")
                )

        if step_value.value == 0:
            return res.failure(RTError(node.pos_start, node.pos_end, "'grind' by cannot be 0"))

        var_name = node.var_name_tok.value
        i = start_value.value
        value = Number(0).set_pos(node.pos_start, node.pos_end)

        self.loop_depth += 1
        try:
            while (i < end_value.value) if step_value.value > 0 else (i > end_value.value):
                self.symbol_table.set(var_name, Number(i).set_pos(node.pos_start, node.pos_end))
                i += step_value.value

                body_value = self.run_block(res, node.body_node)
                if res.error:
                    return res
                if res.func_return_value is not None:
                    return res
                if res.loop_should_break:
                    res.loop_should_break = False
                    break
                if res.loop_should_continue:
                    res.loop_should_continue = False
                    continue
                value = body_value
        finally:
            self.loop_depth -= 1

        return res.success(value)

    def visit_ForInNode(self, node):
        res = RTResult()

        iterable = res.register(self.visit(node.iterable_node))
        if res.error:
            return res

        if isinstance(iterable, List):
            items = list(iterable.elements)
        elif isinstance(iterable, String):
            items = [String(char) for char in iterable.value]
        elif isinstance(iterable, Bag):
            items = iterable.labels()
        else:
            return res.failure(
                RTError(
                    node.iterable_node.pos_start,
                    node.iterable_node.pos_end,
                    f'Cannot iterate over a {iterable.TYPE_NAME}',
                )
            )

        var_name = node.var_name_tok.value
        value = Number(0).set_pos(node.pos_start, node.pos_end)

        self.loop_depth += 1
        try:
            for item in items:
                self.symbol_table.set(var_name, item.copy().set_pos(node.pos_start, node.pos_end))

                body_value = self.run_block(res, node.body_node)
                if res.error:
                    return res
                if res.func_return_value is not None:
                    return res
                if res.loop_should_break:
                    res.loop_should_break = False
                    break
                if res.loop_should_continue:
                    res.loop_should_continue = False
                    continue
                value = body_value
        finally:
            self.loop_depth -= 1

        return res.success(value)

    def visit_IndexAssignNode(self, node):
        res = RTResult()

        value = res.register(self.visit(node.value_node))
        if res.error:
            return res

        # walk to the container itself rather than a copy, so the write sticks
        container = res.register(self.resolve_container(node.index_node.target_node))
        if res.error:
            return res

        index = res.register(self.visit(node.index_node.index_node))
        if res.error:
            return res

        error = container.set_index(index, value.copy())
        if error:
            return res.failure(error)
        return res.success(value)

    def resolve_container(self, node):
        """Evaluate an assignment target to the live object, not a copy."""
        res = RTResult()

        if isinstance(node, VarAccessNode):
            var_name = node.var_name_tok.value
            value = self.symbol_table.get(var_name)
            if value is None:
                return res.failure(RTError(node.pos_start, node.pos_end, f"'{var_name}' is not defined"))
            return res.success(value)

        if isinstance(node, IndexNode):
            container = res.register(self.resolve_container(node.target_node))
            if res.error:
                return res
            index = res.register(self.visit(node.index_node))
            if res.error:
                return res
            value, error = container.get_index(index)
            if error:
                return res.failure(error)
            return res.success(value)

        return res.failure(
            RTError(node.pos_start, node.pos_end, 'Cannot assign into this expression')
        )

    def visit_OopsNode(self, node):
        res = RTResult()

        value = res.register(self.visit(node.node_to_raise))
        if res.error:
            return res

        detail = str(value) if isinstance(value, String) else repr(value)
        return res.failure(RTError(node.pos_start, node.pos_end, detail))

    def visit_RiskyNode(self, node):
        res = RTResult()

        value = self.run_block(res, node.body_node)
        if res.error is None:
            return res.success(value)

        caught = res.error
        if not isinstance(caught, RTError):
            return res

        # the whoops runs with the error bound to a name, in its own result
        res = RTResult()
        self.symbol_table.set(node.catch_name_tok.value, self.describe(caught, node))

        value = self.run_block(res, node.catch_body_node)
        if res.error:
            return res
        return res.success(value)

    def describe(self, error, node):
        """An RTError as a bag the program can read."""
        bag = Bag().set_pos(node.pos_start, node.pos_end)
        pos = error.pos_start
        for label, value in (
            ('why', String(error.details)),
            ('file', String(pos.filename if pos else '?')),
            ('line', Number(pos.line + 1 if pos else 0)),
        ):
            bag.set_index(String(label), value)
        return bag

    def visit_ReturnNode(self, node):
        res = RTResult()

        if self.func_depth == 0:
            return res.failure(RTError(node.pos_start, node.pos_end, "'yeet' outside of a function"))

        if node.node_to_return is not None:
            value = res.register(self.visit(node.node_to_return))
            if res.error:
                return res
        else:
            value = Number(0).set_pos(node.pos_start, node.pos_end)

        return res.success_return(value)

    def visit_ContinueNode(self, node):
        res = RTResult()
        if self.loop_depth == 0:
            return res.failure(RTError(node.pos_start, node.pos_end, "'skip' outside of a loop"))
        return res.success_continue()

    def visit_BreakNode(self, node):
        res = RTResult()
        if self.loop_depth == 0:
            return res.failure(RTError(node.pos_start, node.pos_end, "'bail' outside of a loop"))
        return res.success_break()

    def visit_FuncDefNode(self, node):
        res = RTResult()
        func_name = node.var_name_tok.value
        arg_names = [tok.value for tok in node.arg_name_toks]
        func = Function(func_name, arg_names, node.body_node, self.symbol_table).set_pos(
            node.pos_start, node.pos_end
        )

        self.symbol_table.set(func_name, func)
        return res.success(func)

    def visit_CallNode(self, node):
        res = RTResult()

        func = res.register(self.visit(node.node_to_call))
        if res.error:
            return res

        if not isinstance(func, BaseFunction):
            return res.failure(RTError(node.pos_start, node.pos_end, f'{func} is not a chore'))

        args = []
        for arg_node in node.arg_nodes:
            args.append(res.register(self.visit(arg_node)))
            if res.error:
                return res

        error = func.check_args(args, node.pos_start, node.pos_end)
        if error:
            return res.failure(error)

        value = res.register(func.execute(args, self, node))
        if res.error:
            if isinstance(res.error, RTError):
                res.error.add_frame(func.name, node.pos_start)
            return res

        # a call is a fresh value; signals never leak past it
        res.func_return_value = None
        res.loop_should_break = False
        res.loop_should_continue = False
        return res.success(value.copy().set_pos(node.pos_start, node.pos_end))

    def run_block(self, res, body):
        # a block evaluates to its last statement's value, 0 when empty
        values = res.register(self.visit(body))
        if res.error:
            return None
        if not values or values[-1] is None:
            return Number(0).set_pos(body.pos_start, body.pos_end)
        return values[-1]

    def visit_StatementsNode(self, node):
        res = RTResult()
        values = []

        for element in node.element_nodes:
            value = res.register(self.visit(element))
            if res.error:
                return res
            values.append(value)
            if res.should_return():
                break

        return res.success(values)


# RUN
#######################################
builtin_symbol_table = install_builtins(SymbolTable())
global_symbol_table = SymbolTable(parent=builtin_symbol_table)


def new_symbol_table():
    """A fresh scope with the builtins available."""
    return SymbolTable(parent=builtin_symbol_table)


def wants_more(filename, text):
    """True when text fails only because it stops early - the REPL should keep reading."""
    tokens, error = Lexer(filename, text).make_tokens()
    if error:
        return error.incomplete

    parsed = Parser(tokens).parse()
    if not parsed.error:
        return False
    return parsed.error.pos_start.index >= len(text.rstrip())


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
    try:
        result = interpreter.visit(ast.node)
    except RecursionError:
        # safety net: a non-call recursion (deeply nested expressions) blew the
        # Python stack before MAX_CALL_DEPTH could catch it
        return None, RTError(ast.node.pos_start, ast.node.pos_end, 'Expression nested too deeply')

    if result.error:
        return None, result.error

    values = result.value
    if len(values) == 1:
        return values[0], None
    return values, None


# CLI
#######################################
USAGE = """shit - a language with regrettable keywords

usage:
  python shit.py                 open the REPL
  python shit.py FILE            run a program
  python shit.py --tokens FILE   show the token stream, then stop
  python shit.py --ast FILE      show the parse tree, then stop
  python shit.py --help          this
"""


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv

    if not argv:
        import shell  # noqa: F401  (importing shell starts the REPL)
        return 0

    flags = [arg for arg in argv if arg.startswith('--')]
    paths = [arg for arg in argv if not arg.startswith('--')]

    if '--help' in flags or '-h' in argv:
        print(USAGE, end='')
        return 0

    unknown = [flag for flag in flags if flag not in ('--tokens', '--ast', '--help')]
    if unknown:
        print(f"shit: unknown option {unknown[0]}")
        print(USAGE, end='')
        return 2

    if len(paths) != 1:
        print('shit: expected exactly one file')
        print(USAGE, end='')
        return 2

    path = paths[0]
    try:
        with open(path, encoding='utf-8') as handle:
            source = handle.read()
    except OSError as exc:
        print(f'shit: cannot read {path}: {exc.strerror}')
        return 1

    if '--tokens' in flags or '--ast' in flags:
        return dump(path, source, ast='--ast' in flags)

    result, error = run(path, source)
    if error:
        print(error.as_string())
        return 1

    return 0


def dump(path, source, ast=False):
    """--tokens / --ast: show an intermediate stage instead of running."""
    tokens, error = Lexer(path, source).make_tokens()
    if error:
        print(error.as_string())
        return 1

    if not ast:
        for token in tokens:
            print(token)
        return 0

    parsed = Parser(tokens).parse()
    if parsed.error:
        print(parsed.error.as_string())
        return 1

    for statement in parsed.node.element_nodes:
        print(statement)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
