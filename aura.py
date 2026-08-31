"""aura - a small interpreted language.

Copyright (c) 2026 iam-kira (Vijay Biradar)
Licensed under the MIT License. See LICENSE for the full text.

You may use, modify and sell this software, including inside closed-source
products, but the copyright notice above must travel with every copy.
"""

import sys

__version__ = '0.1.1'
__author__ = 'Vijay Biradar'
__handle__ = 'iam-kira'
__url__ = 'https://github.com/iam-kira/what-did-i-do'

BANNER = 'aura %s - by %s' % (__version__, __author__)
CREDIT = 'aura by %s' % __author__

# A aura-level call costs roughly 20 Python frames, so MAX_CALL_DEPTH calls need
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
    'sus', 'whoops', 'oops',
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
        result += (
            f'File {self.pos_start.filename}, '
            f'line {self.pos_start.line + 1}, col {self.pos_start.col + 1}'
        )

        excerpt = self.excerpt()
        if excerpt:
            result += '\n' + excerpt
        return result

    def excerpt(self):
        """The offending line with a caret under it, the way a compiler shows it."""
        pos = self.pos_start
        if pos is None or not getattr(pos, 'ftxt', None):
            return ''

        lines = pos.ftxt.splitlines()
        if not 0 <= pos.line < len(lines):
            return ''

        raw = lines[pos.line]
        # a tab is one column but shows as four, so re-measure the offset
        shown = raw.replace('\t', '    ')
        start = len(raw[:pos.col].replace('\t', '    '))

        end = start + 1
        if self.pos_end is not None and self.pos_end.line == pos.line:
            end = max(end, len(raw[:self.pos_end.col].replace('\t', '    ')))
        width = max(1, min(end - start, max(1, len(shown) - start)))

        return '  ' + shown + '\n' + '  ' + ' ' * start + '^' * width


class IllegalCharError(Error):
    def __init__(self, pos_start, pos_end, details):
        super().__init__(pos_start, pos_end, 'Illegal Character', details)


class ExpectedCharError(Error):
    def __init__(self, pos_start, pos_end, details):
        super().__init__(pos_start, pos_end, 'Expected Character', details)


class InvalidSyntaxError(Error):
    def __init__(self, pos_start, pos_end, details='Invalid syntax'):
        super().__init__(pos_start, pos_end, 'Invalid Syntax', details)


class BounceError(Error):
    """Raised by bounce(). Unwinds like an error but no sus may catch it."""

    def __init__(self, pos_start, pos_end, code):
        super().__init__(pos_start, pos_end, 'Bounced', f'exit code {code}')
        self.code = code


class RTError(Error):
    """A runtime failure. `kind` is a short slug aura code can branch on."""

    KINDS = frozenset({
        'runtime', 'math', 'name', 'index', 'label', 'type', 'arity',
        'file', 'depth', 'flow', 'unpack', 'custom',
    })

    def __init__(self, pos_start, pos_end, details, kind='runtime'):
        super().__init__(pos_start, pos_end, 'Runtime Error', details)
        assert kind in self.KINDS, kind
        self.kind = kind
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
TT_FSTRING = 'FSTRING'
TT_LCURLY = 'LCURLY'
TT_RCURLY = 'RCURLY'
TT_COLON = 'COLON'
TT_DOT = 'DOT'
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
    OPENERS = '(['
    CLOSERS = ')]'

    def __init__(self, filename, text):
        self.text = text
        self.filename = filename
        self.pos = Position(-1, 0, -1, filename, text)
        self.current_char = None
        # how deep inside brackets we are; newlines in here join lines instead
        # of ending statements, the way every other language does it
        self.depth = 0
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
                if not (self.depth and self.current_char == '\n'):
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
                self.depth += 1
                self.advance()
            elif self.current_char == '}':
                tokens.append(Token(TT_RCURLY, pos_start=self.pos))
                self.depth = max(0, self.depth - 1)
                self.advance()
            elif self.current_char == ':':
                tokens.append(Token(TT_COLON, pos_start=self.pos))
                self.advance()
            elif self.current_char == '.':
                tokens.append(Token(TT_DOT, pos_start=self.pos))
                self.advance()
            elif self.current_char == '[':
                tokens.append(Token(TT_LSQUARE, pos_start=self.pos))
                self.depth += 1
                self.advance()
            elif self.current_char == ']':
                tokens.append(Token(TT_RSQUARE, pos_start=self.pos))
                self.depth = max(0, self.depth - 1)
                self.advance()
            elif self.current_char == '(':
                tokens.append(Token(TT_LPAREN, pos_start=self.pos))
                self.depth += 1
                self.advance()
            elif self.current_char == ')':
                tokens.append(Token(TT_RPAREN, pos_start=self.pos))
                self.depth = max(0, self.depth - 1)
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
        """A yap. {expr} inside one interpolates; {{ is a literal brace."""
        segments = []          # ('text', str) / ('code', str)
        text = ''
        pos_start = self.pos.copy()
        escapes = {'n': '\n', 't': '\t', 'r': '\r',
                   '\\': '\\', '"': '"',
                   '{': '{', '}': '}'}
        self.advance()

        escaped = False
        while self.current_char is not None:
            if escaped:
                text += escapes.get(self.current_char, self.current_char)
                escaped = False
            elif self.current_char == '\\':
                escaped = True
            elif self.current_char == '{':
                self.advance()
                if self.current_char == '{':
                    text += '{'
                else:
                    code, error = self.read_interpolation(pos_start)
                    if error:
                        return None, error
                    if text:
                        segments.append(('text', text))
                        text = ''
                    segments.append(('code', code))
                    continue
            elif self.current_char == '}':
                self.advance()
                text += '}'
                if self.current_char == '}':
                    self.advance()
                continue
            elif self.current_char == '"':
                self.advance()
                if text or not segments:
                    segments.append(('text', text))
                if len(segments) == 1 and segments[0][0] == 'text':
                    return Token(TT_STRING, segments[0][1], pos_start, self.pos), None
                return Token(TT_FSTRING, segments, pos_start, self.pos), None
            else:
                text += self.current_char
            self.advance()

        error = ExpectedCharError(pos_start, self.pos.copy(), 'unterminated string')
        error.incomplete = True
        return None, error

    def read_interpolation(self, pos_start):
        """Read up to the matching '}', tracking nested braces and quotes."""
        code = ''
        depth = 1
        in_yap = False

        while self.current_char is not None:
            char = self.current_char
            if in_yap:
                code += char
                if char == '\\':
                    self.advance()
                    if self.current_char is not None:
                        code += self.current_char
                        self.advance()
                    continue
                if char == '"':
                    in_yap = False
                self.advance()
                continue

            if char == '"':
                in_yap = True
            elif char == '{':
                depth += 1
            elif char == '}':
                depth -= 1
                if depth == 0:
                    self.advance()
                    if not code.strip():
                        return None, InvalidSyntaxError(
                            pos_start, self.pos.copy(), 'Empty {} in a yap - write {{ or a backslash-brace for a literal one'
                        )
                    return code, None
            code += char
            self.advance()

        error = ExpectedCharError(pos_start, self.pos.copy(), "unterminated {} in a yap - write {{ or a backslash-brace for a literal one")
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


class NothingNode:
    def __init__(self, pos_start, pos_end):
        self.pos_start = pos_start
        self.pos_end = pos_end

    def __repr__(self):
        return 'ghosted'


class StringNode:
    def __init__(self, tok):
        self.tok = tok
        self.pos_start = tok.pos_start
        self.pos_end = tok.pos_end

    def __repr__(self):
        return f'{self.tok}'


class FStringNode:
    """A yap with {expr} holes: a list of ('text', StringNode) / ('code', node)."""

    def __init__(self, parts, pos_start, pos_end):
        self.parts = parts
        self.pos_start = pos_start
        self.pos_end = pos_end

    def __repr__(self):
        return '(yap ' + ' + '.join(str(node) for _, node in self.parts) + ')'


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


class DestructureNode:
    """stash a, b = <pile>"""

    def __init__(self, var_name_toks, value_node, is_declaration):
        self.var_name_toks = var_name_toks
        self.value_node = value_node
        self.is_declaration = is_declaration
        self.pos_start = var_name_toks[0].pos_start
        self.pos_end = value_node.pos_end

    def __repr__(self):
        prefix = 'stash ' if self.is_declaration else ''
        names = ', '.join(tok.value for tok in self.var_name_toks)
        return f'({prefix}{names} = {self.value_node})'


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
    def __init__(self, var_name_toks, iterable_node, body_node, pos_start, pos_end):
        self.var_name_toks = var_name_toks
        self.var_name_tok = var_name_toks[0]
        self.iterable_node = iterable_node
        self.body_node = body_node
        self.pos_start = pos_start
        self.pos_end = pos_end

    def __repr__(self):
        names = ', '.join(tok.value for tok in self.var_name_toks)
        return f'(grind {names} among {self.iterable_node})'


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
        return f'(sus {self.body_node} whoops {self.catch_name_tok.value})'


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
                InvalidSyntaxError(
                    self.current_tok.pos_start, self.current_tok.pos_end, self.leftover_hint()
                )
            )
        return res

    def leftover_hint(self):
        """Two things in a row where one was expected.

        `cook "hi"` is the classic - natural coming from a shell or Ruby, and
        'Expected end of input' says nothing about the missing brackets.
        """
        previous = self.peek(-1)
        if previous is not None and previous.type == TT_IDENTIFIER:
            if self.current_tok.type in (TT_STRING, TT_FSTRING, TT_INT, TT_FLOAT, TT_IDENTIFIER):
                return (
                    'Expected end of input - to call a chore, put the arguments '
                    'in brackets: %s(...)' % previous.value
                )
        return 'Expected end of input'

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

        if self.current_tok.matches(TT_KEYWORD, 'sus'):
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
                return self.expected_name('identifier')

            var_names = [self.current_tok]
            self.advance()

            while self.current_tok.type == TT_COMMA:
                self.advance()
                if self.current_tok.type != TT_IDENTIFIER:
                    return self.expected_name('identifier')
                var_names.append(self.current_tok)
                self.advance()

            if self.current_tok.type != TT_EQ:
                return res.failure(
                    InvalidSyntaxError(self.current_tok.pos_start, self.current_tok.pos_end, "Expected '='")
                )

            self.advance()
            expr = res.register(self.expr())
            if res.error:
                return res

            if len(var_names) == 1:
                return res.success(VarAssignNode(var_names[0], expr, is_declaration=True))
            return res.success(DestructureNode(var_names, expr, is_declaration=True))

        expr = res.register(self.expr())
        if res.error:
            return res

        if self.current_tok.type == TT_COMMA and isinstance(expr, VarAccessNode):
            return self.destructure(res, expr)

        if self.current_tok.type in ASSIGN_OPS:
            return self.assignment(res, expr)

        return res.success(expr)

    def destructure(self, res, first):
        var_names = [first.var_name_tok]

        while self.current_tok.type == TT_COMMA:
            self.advance()
            if self.current_tok.type != TT_IDENTIFIER:
                return self.expected_name('identifier')
            var_names.append(self.current_tok)
            self.advance()

        if self.current_tok.type != TT_EQ:
            return res.failure(
                InvalidSyntaxError(self.current_tok.pos_start, self.current_tok.pos_end, "Expected '='")
            )
        self.advance()

        value = res.register(self.expr())
        if res.error:
            return res
        return res.success(DestructureNode(var_names, value, is_declaration=False))

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
            return self.expected_name('a name for the whoops')
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
            return self.expected_name('identifier')
        var_name_toks = [self.current_tok]
        var_name_tok = self.current_tok
        self.advance()

        while self.current_tok.type == TT_COMMA:
            self.advance()
            if self.current_tok.type != TT_IDENTIFIER:
                return self.expected_name('identifier')
            var_name_toks.append(self.current_tok)
            self.advance()

        if len(var_name_toks) > 1 and not self.current_tok.matches(TT_KEYWORD, 'among'):
            return res.failure(
                InvalidSyntaxError(self.current_tok.pos_start, self.current_tok.pos_end, "Expected 'among'")
            )

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
            return res.success(ForInNode(var_name_toks, iterable_node, body, pos_start, pos_end))

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
            return self.expected_name('function name')
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
                    return self.expected_name('parameter name')
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

        if tok.type == TT_FSTRING:
            self.advance()
            parts = []
            for kind, chunk in tok.value:
                if kind == 'text':
                    parts.append(('text', StringNode(Token(TT_STRING, chunk, tok.pos_start, tok.pos_end))))
                    continue
                node = res.register(self.sub_parse(chunk, tok))
                if res.error:
                    return res
                parts.append(('code', node))
            return self.postfix_result(res, FStringNode(parts, tok.pos_start, tok.pos_end))

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

        if tok.type == TT_KEYWORD and tok.value == 'ghosted':
            self.advance()
            return self.postfix_result(res, NothingNode(tok.pos_start, tok.pos_end))

        if tok.type == TT_KEYWORD and tok.value in ('based', 'cringe'):
            self.advance()
            literal = 1 if tok.value == 'based' else 0
            return res.success(NumberNode(Token(TT_INT, literal, tok.pos_start, tok.pos_end)))

        if tok.type == TT_IDENTIFIER:
            self.advance()
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

    def sub_parse(self, source, tok):
        """Parse one {expr} fragment. Its errors point at the yap that holds it."""
        res = ParseResult()

        tokens, error = Lexer(tok.pos_start.filename, source).make_tokens()
        if error:
            return res.failure(InvalidSyntaxError(tok.pos_start, tok.pos_end, error.details))

        parsed = Parser(tokens).statements()
        if parsed.error:
            return res.failure(InvalidSyntaxError(tok.pos_start, tok.pos_end, parsed.error.details))

        statements = parsed.node.element_nodes
        if len(statements) != 1:
            return res.failure(
                InvalidSyntaxError(tok.pos_start, tok.pos_end, 'A {} in a yap needs exactly one expression')
            )
        return res.success(statements[0])

    def expected_name(self, what='identifier'):
        """The error for 'a name should be here'.

        Says outright when the offending token is a keyword, because
        `chore shift(text, by)` is an easy thing to write and a baffling
        thing to debug otherwise.
        """
        tok = self.current_tok
        detail = 'Expected %s' % what
        if tok.type == TT_KEYWORD:
            detail += ", but '%s' is a keyword" % tok.value

        return ParseResult().failure(InvalidSyntaxError(tok.pos_start, tok.pos_end, detail))

    def skip_newlines(self):
        while self.current_tok.type == TT_NEWLINE:
            self.advance()

    def postfix_result(self, res, node):
        """Attach any trailing [index] and (call) suffixes to a parsed atom.

        One loop, so d["go"](), fs[0](), f()[0] and mk()() all chain.
        """
        while True:
            if self.current_tok.type == TT_LSQUARE:
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

            elif self.current_tok.type == TT_LPAREN:
                node = res.register(self.call(node))
                if res.error:
                    return res

            elif self.current_tok.type == TT_DOT:
                self.advance()
                if self.current_tok.type not in (TT_IDENTIFIER, TT_KEYWORD):
                    return res.failure(
                        InvalidSyntaxError(
                            self.current_tok.pos_start, self.current_tok.pos_end, "Expected a label after '.'"
                        )
                    )
                label = self.current_tok
                pos_end = label.pos_end.copy()
                self.advance()
                # d.name is exactly d["name"], so assignment and calls come free
                key = StringNode(Token(TT_STRING, label.value, label.pos_start, label.pos_end))
                node = IndexNode(node, key, node.pos_start, pos_end)

            else:
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
        """Names both sides: '1 + ghosted' blaming only 'math' helps nobody."""
        other = other if other is not None else self

        if other is self or other.TYPE_NAME == self.TYPE_NAME:
            detail = f'Illegal operation for {self.TYPE_NAME}'
        else:
            detail = f'Illegal operation between {self.TYPE_NAME} and {other.TYPE_NAME}'

        return None, RTError(self.pos_start, other.pos_end, detail, kind='type')

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
            self.pos_start, index.pos_end, f'{self.TYPE_NAME} is not indexable', kind='index'
        )

    def set_index(self, index, value):
        return RTError(
            self.pos_start, index.pos_end, f'Cannot assign into a {self.TYPE_NAME}', kind='index'
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
            return None, RTError(other.pos_start, other.pos_end, 'Division by zero', kind='math')
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
            return None, RTError(other.pos_start, other.pos_end, 'Modulo by zero', kind='math')
        return Number(self.value % other.value), None

    def powed_by(self, other):
        if not isinstance(other, Number):
            return self.illegal_operation(other)
        try:
            result = self.value ** other.value
        except (OverflowError, ZeroDivisionError) as exc:
            return None, RTError(self.pos_start, other.pos_end, str(exc), kind='math')
        if isinstance(result, complex):
            return None, RTError(self.pos_start, other.pos_end, 'Result is not a real number', kind='math')
        return Number(result), None

    def is_true(self):
        return self.value != 0

    def __repr__(self):
        if isinstance(self.value, float) and self.value.is_integer():
            return str(int(self.value))
        return str(self.value)


class Nothing(Value):
    """The absence of a value. Falsy, equal only to itself, and refuses to
    pretend it is a number - so `ghosted + 1` is an error rather than 1."""

    TYPE_NAME = 'ghosted'

    def copy(self):
        return Nothing().set_pos(self.pos_start, self.pos_end)

    def compare_eq(self, other):
        return Number(1 if isinstance(other, Nothing) else 0), None

    def compare_ne(self, other):
        return Number(0 if isinstance(other, Nothing) else 1), None

    def is_true(self):
        return False

    def __repr__(self):
        return 'ghosted'


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
    if isinstance(index, String):
        return None, RTError(
            index.pos_start,
            index.pos_end,
            f'A {container.TYPE_NAME} is indexed by whole maths, not labels', kind='index',
        )

    """Shared bounds-checked indexing for String and List.

    Negative indices count from the end, as in Python.
    """
    if not isinstance(index, Number) or not isinstance(index.value, int):
        return None, RTError(index.pos_start, index.pos_end, 'Index must be a whole math', kind='index')

    i = index.value
    if i < 0:
        i += len(sequence)
    if not 0 <= i < len(sequence):
        return None, RTError(
            index.pos_start, index.pos_end, f'Index {index.value} out of range (length {len(sequence)})', kind='index'
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
            f"'{self.name}' takes {wanted} argument(s), got {len(args)}", kind='arity',
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
            return None, RTError(index.pos_start, index.pos_end, 'A bag label must be a math or a yap', kind='label')
        if key not in self.pairs:
            return None, RTError(index.pos_start, index.pos_end, f'No label {index!r} in this bag', kind='label')
        return self.pairs[key][1], None

    def set_index(self, index, value):
        key = self.key_of(index)
        if key is None:
            return RTError(index.pos_start, index.pos_end, 'A bag label must be a math or a yap', kind='label')
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
                    f'Maximum call depth of {MAX_CALL_DEPTH} exceeded', kind='depth',
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
    return None, RTError(node.pos_start, node.pos_end, message, kind='type')


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
            number = float(text)
        except ValueError:
            return _type_error(node, f'Cannot convert "{value.value}" to a math')

        if number != number or number in (float('inf'), float('-inf')):
            return _type_error(node, f'Cannot convert "{value.value}" to a math')
        return Number(number), None
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
            return None, RTError(node.pos_start, node.pos_end, f'No label {index!r} in this bag', kind='label')
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
        return RTError(node.pos_start, node.pos_end, f"'{who}' needs a {what}, got {value.TYPE_NAME}", kind='type')
    return None


def _numbers(args, node, who):
    """Flatten a single pile argument, or loose maths, into Python numbers."""
    values = args[0].elements if len(args) == 1 and isinstance(args[0], List) else args
    if not values:
        return None, RTError(node.pos_start, node.pos_end, f"'{who}' needs at least one math", kind='type')
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


def _round_half_away(value, places=0):
    """2.5 -> 3, not python's round-half-to-even 2."""
    import math

    factor = 10 ** places
    scaled = value * factor
    whole = math.floor(scaled + 0.5) if scaled >= 0 else math.ceil(scaled - 0.5)
    if places <= 0:
        return int(whole / factor) if factor != 1 else int(whole)
    return whole / factor


def bi_roundish(args, node):
    error = _need(node, args[0], Number, 'math', 'roundish')
    if error:
        return None, error

    places = 0
    if args[1] is not None:
        error = _need(node, args[1], Number, 'math', 'roundish')
        if error:
            return None, error
        places = int(args[1].value)

    return Number(_round_half_away(args[0].value, places)), None


def bi_total(args, node):
    values, error = _numbers([a for a in args if a is not None], node, 'total')
    return (None, error) if error else (Number(sum(values)), None)


def bi_chunk(args, node):
    target = args[0]
    if not isinstance(target, (String, List)):
        return None, RTError(node.pos_start, node.pos_end, "'chunk' needs a yap or pile", kind='type')

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
    return None, RTError(node.pos_start, node.pos_end, "'flip' needs a yap or pile", kind='type')


def bi_glue(args, node):
    error = _need(node, args[0], List, 'pile', 'glue')
    if error:
        return None, error

    if args[1] is None:
        separator = ''
    elif isinstance(args[1], String):
        separator = args[1].value
    else:
        return None, RTError(node.pos_start, node.pos_end, "'glue' separator must be a yap", kind='type')

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
    target, needle = args[0], args[1]

    # a yap is searched by substring, not character by character
    if isinstance(target, String):
        if not isinstance(needle, String):
            return None, RTError(
                node.pos_start, node.pos_end,
                f"'where' in a yap needs a yap to look for, got {needle.TYPE_NAME}", kind='type',
            )
        return Number(target.value.find(needle.value)), None

    members = _members(target)
    if members is None:
        return None, RTError(node.pos_start, node.pos_end, "'where' needs a yap, pile or bag", kind='type')
    for i, item in enumerate(members):
        equal, error = item.compare_eq(needle)
        if error:
            return None, error
        if equal.is_true():
            return Number(i), None
    return Number(-1), None


def bi_gotit(args, node):
    index, error = bi_where(args, node)
    if error:
        return None, error
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
        return None, RTError(node.pos_start, node.pos_end, "'sortof' needs a pile of all maths or all yaps", kind='type')
    return List(items), None


def call_chore(func, call_args, node, interpreter):
    """Call a aura chore from inside a builtin. Returns (value, error)."""
    if not isinstance(func, BaseFunction):
        return None, RTError(node.pos_start, node.pos_end, f'{func} is not a chore', kind='type')

    error = func.check_args(call_args, node.pos_start, node.pos_end)
    if error:
        return None, error

    result = func.execute(call_args, interpreter, node)
    if result.error:
        return None, result.error

    value = result.func_return_value if result.func_return_value is not None else result.value
    # the signals belong to that call, not to whatever we are in the middle of
    result.func_return_value = None
    result.loop_should_break = False
    result.loop_should_continue = False
    return value, None


def bi_eachof(args, node, interpreter):
    pile, func = args
    error = _need(node, pile, List, 'pile', 'eachof')
    if error:
        return None, error

    out = []
    for item in pile.elements:
        value, error = call_chore(func, [item.copy()], node, interpreter)
        if error:
            return None, error
        out.append(value)
    return List(out), None


def bi_keepif(args, node, interpreter):
    pile, func = args
    error = _need(node, pile, List, 'pile', 'keepif')
    if error:
        return None, error

    out = []
    for item in pile.elements:
        value, error = call_chore(func, [item.copy()], node, interpreter)
        if error:
            return None, error
        if value.is_true():
            out.append(item.copy())
    return List(out), None


def bi_smoosh(args, node, interpreter):
    pile, func, start = args
    error = _need(node, pile, List, 'pile', 'smoosh')
    if error:
        return None, error

    items = list(pile.elements)
    if start is not None:
        carried = start.copy()
    elif items:
        carried = items.pop(0).copy()
    else:
        return None, RTError(node.pos_start, node.pos_end, "'smoosh' needs a starting value for an empty pile", kind='type')

    for item in items:
        carried, error = call_chore(func, [carried, item.copy()], node, interpreter)
        if error:
            return None, error
    return carried, None


def bi_sortof_by(args, node, interpreter):
    pile, func = args
    error = _need(node, pile, List, 'pile', 'sortof')
    if error:
        return None, error

    if func is None:
        return bi_sortof([pile], node)

    # decorate-sort-undecorate, so the chore runs once per item
    decorated = []
    for item in pile.elements:
        key, error = call_chore(func, [item.copy()], node, interpreter)
        if error:
            return None, error
        if not isinstance(key, (Number, String)):
            return None, RTError(
                node.pos_start, node.pos_end, f'A sort key must be a math or a yap, got {key.TYPE_NAME}', kind='type'
            )
        decorated.append((key, item.copy()))

    if len({type(key) for key, _ in decorated}) > 1:
        return None, RTError(node.pos_start, node.pos_end, 'Sort keys must be all maths or all yaps', kind='type')

    decorated.sort(key=lambda pair: pair[0].value)
    return List([item for _, item in decorated]), None


def bi_swap(args, node):
    for value in args[:3]:
        error = _need(node, value, String, 'yap', 'swap')
        if error:
            return None, error
    if args[1].value == '':
        return None, RTError(node.pos_start, node.pos_end, "'swap' cannot look for an empty yap", kind='type')
    return String(args[0].value.replace(args[1].value, args[2].value)), None


def bi_starts(args, node):
    for value in args[:2]:
        error = _need(node, value, String, 'yap', 'starts')
        if error:
            return None, error
    return Number(1 if args[0].value.startswith(args[1].value) else 0), None


def bi_ends(args, node):
    for value in args[:2]:
        error = _need(node, value, String, 'yap', 'ends')
        if error:
            return None, error
    return Number(1 if args[0].value.endswith(args[1].value) else 0), None


def bi_code(args, node):
    error = _need(node, args[0], String, 'yap', 'code')
    if error:
        return None, error
    if len(args[0].value) != 1:
        return None, RTError(
            node.pos_start, node.pos_end, "'code' needs exactly one character", kind='type'
        )
    return Number(ord(args[0].value)), None


def bi_letter(args, node):
    error = _need(node, args[0], Number, 'math', 'letter')
    if error:
        return None, error
    point = int(args[0].value)
    if not 0 <= point <= 0x10FFFF:
        return None, RTError(node.pos_start, node.pos_end, f'{point} is not a character', kind='type')
    return String(chr(point)), None


def bi_numbered(args, node):
    """[a, b] -> [[0, a], [1, b]], so `grind i, x among numbered(xs)` works."""
    target = args[0]
    members = _members(target)
    if members is None:
        return None, RTError(node.pos_start, node.pos_end, "'numbered' needs a yap or pile", kind='type')
    return List([List([Number(i), item.copy()]) for i, item in enumerate(members)]), None


def bi_pair(args, node):
    """Two piles into one pile of pairs, stopping at the shorter."""
    for value in args[:2]:
        error = _need(node, value, List, 'pile', 'pair')
        if error:
            return None, error
    left, right = args[0].elements, args[1].elements
    return List([List([a.copy(), b.copy()]) for a, b in zip(left, right)]), None


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
        return None, RTError(node.pos_start, node.pos_end, f"'{target}' is summoning itself", kind='file')

    try:
        with open(full, encoding='utf-8') as handle:
            source = handle.read()
    except OSError as exc:
        return None, RTError(node.pos_start, node.pos_end, f"Cannot summon '{target}': {exc.strerror}", kind='file')

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


# set by main() so a program can see what it was handed
SCRIPT_ARGS = []


def _path_of(args, node, who):
    error = _need(node, args[0], String, 'yap', who)
    if error:
        return None, error
    return args[0].value, None


def bi_slurp(args, node):
    target, error = _path_of(args, node, 'slurp')
    if error:
        return None, error
    try:
        with open(target, encoding='utf-8') as handle:
            return String(handle.read()), None
    except OSError as exc:
        return None, RTError(node.pos_start, node.pos_end, f"Cannot slurp '{target}': {exc.strerror}", kind='file')
    except UnicodeDecodeError:
        return None, RTError(node.pos_start, node.pos_end, f"'{target}' is not text", kind='file')


def _write(args, node, who, mode):
    target, error = _path_of(args, node, who)
    if error:
        return None, error
    error = _need(node, args[1], String, 'yap', who)
    if error:
        return None, error
    try:
        with open(target, mode, encoding='utf-8') as handle:
            handle.write(args[1].value)
    except OSError as exc:
        return None, RTError(node.pos_start, node.pos_end, f"Cannot {who} '{target}': {exc.strerror}", kind='file')
    return Number(len(args[1].value)), None


def bi_spill(args, node):
    return _write(args, node, 'spill', 'w')


def bi_dribble(args, node):
    return _write(args, node, 'dribble', 'a')


def bi_isthere(args, node):
    import os

    target, error = _path_of(args, node, 'isthere')
    if error:
        return None, error
    return Number(1 if os.path.exists(target) else 0), None


def bi_rummage(args, node):
    import os

    target = '.' if args[0] is None else None
    if target is None:
        target, error = _path_of(args, node, 'rummage')
        if error:
            return None, error

    try:
        names = sorted(os.listdir(target))
    except OSError as exc:
        return None, RTError(
            node.pos_start, node.pos_end, f"Cannot rummage '{target}': {exc.strerror}", kind='file'
        )
    return List([String(name) for name in names]), None


def bi_isfolder(args, node):
    import os

    target, error = _path_of(args, node, 'isfolder')
    if error:
        return None, error
    return Number(1 if os.path.isdir(target) else 0), None


def bi_stitch(args, node):
    import os

    parts = []
    for value in args:
        if value is None:
            continue
        if not isinstance(value, String):
            return None, RTError(
                node.pos_start, node.pos_end, f"'stitch' needs yaps, got {value.TYPE_NAME}", kind='type'
            )
        parts.append(value.value)

    if not parts:
        return None, RTError(node.pos_start, node.pos_end, "'stitch' needs at least one yap", kind='type')
    # forward slashes everywhere, so a aura program reads the same on any box
    return String(os.path.join(*parts).replace(os.sep, '/')), None


def bi_handed(args, node):
    return List([String(arg) for arg in SCRIPT_ARGS]), None


def bi_bounce(args, node):
    code = 0
    if args[0] is not None:
        error = _need(node, args[0], Number, 'math', 'bounce')
        if error:
            return None, error
        code = int(args[0].value)
    return None, BounceError(node.pos_start, node.pos_end, code)


def bi_whatis(args, node):
    return String(args[0].TYPE_NAME), None


def bi_is_ghosted(args, node):
    return Number(1 if isinstance(args[0], Nothing) else 0), None


def bi_is_num(args, node):
    return Number(1 if isinstance(args[0], Number) else 0), None


def bi_is_str(args, node):
    return Number(1 if isinstance(args[0], String) else 0), None


def bi_is_list(args, node):
    return Number(1 if isinstance(args[0], List) else 0), None


def bi_is_fun(args, node):
    return Number(1 if isinstance(args[0], BaseFunction) else 0), None


BUILTINS = {
    'cook': (['value'], bi_print),
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
    'sortof': (['pile', '?by'], bi_sortof_by),
    'swap': (['yap', 'find', 'replace'], bi_swap),
    'starts': (['yap', 'prefix'], bi_starts),
    'ends': (['yap', 'suffix'], bi_ends),
    'code': (['letter'], bi_code),
    'letter': (['code'], bi_letter),
    'numbered': (['value'], bi_numbered),
    'pair': (['left', 'right'], bi_pair),
    'eachof': (['pile', 'chore'], bi_eachof),
    'keepif': (['pile', 'chore'], bi_keepif),
    'smoosh': (['pile', 'chore', '?start'], bi_smoosh),
    'labels': (['bag'], bi_labels),
    'goods': (['bag'], bi_goods),
    'summon': (['path'], bi_summon),
    'slurp': (['path'], bi_slurp),
    'spill': (['path', 'text'], bi_spill),
    'dribble': (['path', 'text'], bi_dribble),
    'isthere': (['path'], bi_isthere),
    'handed': ([], bi_handed),
    'rummage': (['?path'], bi_rummage),
    'isfolder': (['path'], bi_isfolder),
    'stitch': (['part', '*more'], bi_stitch),
    'bounce': (['?code'], bi_bounce),
    'whatis': (['value'], bi_whatis),
    'is_ghosted': (['value'], bi_is_ghosted),
    'is_math': (['value'], bi_is_num),
    'is_yap': (['value'], bi_is_str),
    'is_pile': (['value'], bi_is_list),
    'is_chore': (['value'], bi_is_fun),
}


NEEDS_INTERPRETER = {'summon', 'eachof', 'keepif', 'smoosh', 'sortof'}


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

    def visit_NothingNode(self, node):
        return RTResult().success(Nothing().set_pos(node.pos_start, node.pos_end))

    def visit_StringNode(self, node):
        return RTResult().success(String(node.tok.value).set_pos(node.pos_start, node.pos_end))

    def visit_FStringNode(self, node):
        res = RTResult()
        pieces = []

        for _, part in node.parts:
            value = res.register(self.visit(part))
            if res.error:
                return res
            pieces.append(str(value) if isinstance(value, String) else repr(value))

        return res.success(String(''.join(pieces)).set_pos(node.pos_start, node.pos_end))

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
            return res.failure(RTError(node.pos_start, node.pos_end, f"'{var_name}' is not defined", kind='name'))

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
                RTError(node.pos_start, node.pos_end, f"Cannot assign to undefined variable '{var_name}'", kind='name')
            )
        return res.success(value)

    def visit_DestructureNode(self, node):
        res = RTResult()

        value = res.register(self.visit(node.value_node))
        if res.error:
            return res

        error = self.unpack(node, node.var_name_toks, value)
        if error:
            return res.failure(error)
        return res.success(value)

    def unpack(self, node, name_toks, value):
        """Bind a pile's elements to several names. Returns an error, or None."""
        if not isinstance(value, List):
            return RTError(
                node.pos_start, node.pos_end, f'Can only unpack a pile, got {value.TYPE_NAME}', kind='unpack'
            )
        if len(value.elements) != len(name_toks):
            return RTError(
                node.pos_start,
                node.pos_end,
                f'Need {len(name_toks)} things to unpack, got {len(value.elements)}', kind='unpack',
            )

        declaring = getattr(node, 'is_declaration', True)
        for tok, item in zip(name_toks, value.elements):
            if declaring:
                self.symbol_table.set(tok.value, item.copy())
            elif not self.symbol_table.set_existing(tok.value, item.copy()):
                return RTError(
                    node.pos_start, node.pos_end, f"Cannot assign to undefined variable '{tok.value}'", kind='name'
                )
        return None

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

        # also / orelse short-circuit: the right side is only looked at when it
        # can still change the answer, so `i < howmany(xs) also xs[i]` is safe
        if node.op_tok.matches(TT_KEYWORD, 'also'):
            if not left.is_true():
                return res.success(Number(0).set_pos(node.pos_start, node.pos_end))
            right = res.register(self.visit(node.right_node))
            if res.error:
                return res
            return res.success(
                Number(1 if right.is_true() else 0).set_pos(node.pos_start, node.pos_end)
            )

        if node.op_tok.matches(TT_KEYWORD, 'orelse'):
            if left.is_true():
                return res.success(Number(1).set_pos(node.pos_start, node.pos_end))
            right = res.register(self.visit(node.right_node))
            if res.error:
                return res
            return res.success(
                Number(1 if right.is_true() else 0).set_pos(node.pos_start, node.pos_end)
            )

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
        else:
            return res.failure(RTError(node.pos_start, node.pos_end, 'Unknown binary operator', kind='type'))

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
                    RTError(node.pos_start, node.pos_end, f"'grind' {name} value must be a math", kind='type')
                )

        if step_value.value == 0:
            return res.failure(RTError(node.pos_start, node.pos_end, "'grind' by cannot be 0", kind='math'))

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
            if len(node.var_name_toks) > 1:
                items = [List([key.copy(), value.copy()]) for key, value in iterable.pairs.values()]
            else:
                items = iterable.labels()
        else:
            return res.failure(
                RTError(
                    node.iterable_node.pos_start,
                    node.iterable_node.pos_end,
                    f'Cannot iterate over a {iterable.TYPE_NAME}',
                    kind='type',
                )
            )

        names = node.var_name_toks
        var_name = names[0].value
        value = Number(0).set_pos(node.pos_start, node.pos_end)

        self.loop_depth += 1
        try:
            for item in items:
                if len(names) > 1:
                    error = self.unpack(node, names, item)
                    if error:
                        return res.failure(error)
                else:
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
                return res.failure(RTError(node.pos_start, node.pos_end, f"'{var_name}' is not defined", kind='name'))
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
            RTError(node.pos_start, node.pos_end, 'Cannot assign into this expression', kind='index')
        )

    def visit_OopsNode(self, node):
        res = RTResult()

        value = res.register(self.visit(node.node_to_raise))
        if res.error:
            return res

        detail = str(value) if isinstance(value, String) else repr(value)
        return res.failure(RTError(node.pos_start, node.pos_end, detail, kind='custom'))

    def visit_RiskyNode(self, node):
        res = RTResult()

        value = self.run_block(res, node.body_node)
        if res.error is None:
            return res.success(value)

        caught = res.error
        if isinstance(caught, BounceError) or not isinstance(caught, RTError):
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
            ('kind', String(getattr(error, 'kind', 'runtime'))),
            ('file', String(pos.filename if pos else '?')),
            ('line', Number(pos.line + 1 if pos else 0)),
        ):
            bag.set_index(String(label), value)
        return bag

    def visit_ReturnNode(self, node):
        res = RTResult()

        if self.func_depth == 0:
            return res.failure(RTError(node.pos_start, node.pos_end, "'yeet' outside of a function", kind='flow'))

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
            return res.failure(RTError(node.pos_start, node.pos_end, "'skip' outside of a loop", kind='flow'))
        return res.success_continue()

    def visit_BreakNode(self, node):
        res = RTResult()
        if self.loop_depth == 0:
            return res.failure(RTError(node.pos_start, node.pos_end, "'bail' outside of a loop", kind='flow'))
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
            return res.failure(RTError(node.pos_start, node.pos_end, f'{func} is not a chore', kind='type'))

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
        return None, RTError(ast.node.pos_start, ast.node.pos_end, 'Expression nested too deeply', kind='depth')

    if result.error:
        return None, result.error

    values = result.value
    if len(values) == 1:
        return values[0], None
    return values, None



# REPL
#######################################
PROMPT = 'shell :> '
CONTINUED = '   ...  > '
QUIT_WORDS = ('quit', 'exit', ':q')

# an actual goodbye - 'bet' only ever meant agreement
FAREWELL = 'aight imma head out\n' + CREDIT

HELP = """aura - a language with regrettable keywords

  stash x = 1        declare            chore f(a) ong ... bet     define
  x = 2              assign             yeet v                     return
  fr c ong           if                 cook(v)                    print
  orfr c ong         else if            grind i = 0 til 3 ong      count
  whatever           else               grind x among xs ong       walk
  keep c ong         while              sus ong ... whoops e ong   try / catch
  bet                closes any block   bail / skip                break / continue

  types    math   yap   pile   bag   chore   ghosted
  values   based  cringe  ghosted        ("{x}" interpolates)

at this prompt:
  help       this            builtins   list every built-in chore
  clear      clear screen    exit       leave (or ctrl-d)

a block keeps prompting with '...  >' until it closes; a blank line ends it,
and ctrl-c throws away what you were typing.

full reference: docs/BOOK.md
"""


def show_builtins():
    """The built-in chores, in columns, because there are a lot of them."""
    names = sorted(BUILTINS)
    width = max(len(n) for n in names) + 2
    per_row = max(1, 76 // width)

    print('%d built-in chores:' % len(names))
    for i in range(0, len(names), per_row):
        print('  ' + ''.join(n.ljust(width) for n in names[i:i + per_row]).rstrip())
    print("\ncall one with brackets, e.g. cook(\"hi\") or howmany([1, 2])")


def clear_screen():
    import os
    os.system('cls' if os.name == 'nt' else 'clear')


def show(result):
    """Echo a statement's value the way the REPL does: repr, so "1" and 1 differ."""
    if result is None:
        return
    for value in (result if isinstance(result, list) else [result]):
        print(repr(value))


def repl(symbol_table=None):
    print(BANNER)
    print("type 'help' for the vocabulary, 'exit' to leave")
    print()

    table = global_symbol_table if symbol_table is None else symbol_table
    buffer = []

    while True:
        try:
            line = input(CONTINUED if buffer else PROMPT)
        except KeyboardInterrupt:
            if buffer:
                buffer = []
                print('\nDropped that.')
            else:
                print("\nInterrupted. Type 'exit' to quit.")
            continue
        except EOFError:
            print('\n' + FAREWELL)
            return 0

        if not buffer:
            clean = line.strip()
            if not clean:
                continue
            # a name you defined always wins over a shell convenience
            shadowed = global_symbol_table.exists(clean)

            if clean.lower() == 'help' and not shadowed:
                print(HELP, end='')
                continue

            if clean.lower() == 'builtins' and not shadowed:
                show_builtins()
                continue

            if clean.lower() == 'clear' and not shadowed:
                clear_screen()
                continue

            if clean.lower() in QUIT_WORDS:
                print(FAREWELL)
                return 0

        buffer.append(line)
        source = '\n'.join(buffer)

        # a blank line forces the block to end, so a typo cannot trap you
        if line.strip() and wants_more('<stdin>', source):
            continue
        buffer = []

        result, error = run('<stdin>', source, table)

        if isinstance(error, BounceError):
            return error.code
        if error:
            print(error.as_string())
        else:
            show(result)

# CLI
#######################################
USAGE = """aura - a language with regrettable keywords

usage:
  python aura.py                 open the REPL
  python aura.py FILE [ARG...]   run a program, passing it the extra args
  python aura.py --tokens FILE   show the token stream, then stop
  python aura.py --ast FILE      show the parse tree, then stop
  python aura.py --help          this
  python aura.py --version       which aura this is

%s
%s
""" % (CREDIT, __url__)


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv

    if not argv:
        return repl()

    flags = [arg for arg in argv if arg.startswith('--')]
    paths = [arg for arg in argv if not arg.startswith('--')]

    if '--version' in flags or '-V' in argv:
        print(BANNER)
        return 0

    if '--help' in flags or '-h' in argv:
        print(USAGE, end='')
        return 0

    unknown = [flag for flag in flags
               if flag not in ('--tokens', '--ast', '--help', '--version')]
    if unknown:
        print(f"aura: unknown option {unknown[0]}")
        print(USAGE, end='')
        return 2

    if not paths:
        print('aura: expected a file')
        print(USAGE, end='')
        return 2

    # everything after the program name belongs to the program
    path = paths[0]
    global SCRIPT_ARGS
    SCRIPT_ARGS = paths[1:]
    try:
        with open(path, encoding='utf-8') as handle:
            source = handle.read()
    except OSError as exc:
        print(f'aura: cannot read {path}: {exc.strerror}')
        return 1

    if '--tokens' in flags or '--ast' in flags:
        return dump(path, source, ast='--ast' in flags)

    result, error = run(path, source)
    if isinstance(error, BounceError):
        return error.code
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
