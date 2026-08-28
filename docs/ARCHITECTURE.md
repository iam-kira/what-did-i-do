# How shit works

One file, `shit.py`, in pipeline order. Read it top to bottom and it tells the
whole story.

```text
source text
   |  Lexer.make_tokens()
tokens
   |  Parser.parse()
AST
   |  Interpreter.visit()
values
```

---

## The rule that shapes everything

**Errors are returned, never raised.** Every stage hands back a pair:

```python
tokens, error = lexer.make_tokens()
```

The parser and interpreter wrap that pair in `ParseResult` and `RTResult` so it
can ride along with a value:

```python
node = res.register(self.expr())
if res.error:
    return res
```

`register` unwraps a child result and absorbs its error. The caller checks once
and returns early. Keep this shape when you add anything — a stray `raise` will
skip every position-tracking and traceback mechanism in the file.

---

## Positions

`Position` tracks index, line, and column, and every token, node, and value
carries `pos_start` / `pos_end`. That is the only reason errors can say
`line 4, col 12`. When you build a node, thread the positions through; when you
build a value, `set_pos` it.

---

## Lexer

Character loop, one `make_*` method per multi-character token: numbers, yaps,
identifiers/keywords, and the `=`-suffixed operators (`!=`, `>=`, `+=` …) via
`make_maybe_eq`.

An identifier becomes `TT_KEYWORD` if it is in `KEYWORDS`, otherwise
`TT_IDENTIFIER`. That list is the entire vocabulary — adding a keyword starts
there.

`;` and newline both produce `TT_NEWLINE`, so statement separation costs the
parser nothing. `#` runs to end of line and is dropped.

---

## Parser

Recursive descent, one method per precedence level, loosest at the top:

```text
statements -> statement -> expr -> and_expr -> not_expr -> comp_expr
           -> arith_expr -> term -> factor -> power -> atom
```

`bin_op(func, ops)` builds every left-associative level; pass `right=` for a
right-associative one (that is how `^` works). Operators are matched by token
type, or by `(TT_KEYWORD, 'also')` tuples for word operators.

`statement()` dispatches the keyword forms (`fr`, `keep`, `grind`, `chore`,
`stash`, `yeet`, `bail`, `skip`), then falls through to parsing an expression.
If an `=` (or `+=` …) follows that expression, `assignment()` decides what it
was: a `VarAccessNode` becomes a `VarAssignNode`, an `IndexNode` becomes an
`IndexAssignNode`, anything else is a syntax error. Compound assignment
desugars — `x += 1` is built as `x = x + 1`.

Blocks are `statements(stop_keywords)`; every block form passes the keywords
that legally end it, then checks for `bet` itself.

---

## Values

`Value` is the base. Every operation — `added_to`, `compare_lt`, `get_index`,
`length` — defaults to an illegal-operation error, so a new type overrides only
what it supports and touches no interpreter code. Each subclass sets
`TYPE_NAME`, which is what error messages print.

`Number`, `String`, `List`, `Bag`, and `BaseFunction` (→ `Function`,
`BuiltInFunction`) live here. Operations return `(value, error)`, same shape as
everything else.

`Bag` keys its Python dict on `('math', 3)` / `('yap', 'a')` tuples so maths and
yaps can both be labels without colliding, and keeps the original key `Value`
alongside each entry so `labels()` and `repr` can hand it back.

Values are copied on read, so assigning a pile to a second name gives it its own
copy. `IndexAssignNode` is the deliberate exception: it resolves the *live*
container via `resolve_container` rather than a copy, or the write would land on
a temporary.

---

## Interpreter

`visit(node)` dispatches to `visit_<NodeName>` by class name. No node type
needs registering; the method name is the wiring.

**Scopes.** `SymbolTable` chains to a parent. `set` declares locally,
`set_existing` walks outward to assign where a name was declared — that split is
what makes `stash` local and plain assignment able to mutate an enclosing scope.
A `Function` captures its defining scope and parents each call on that, which is
what makes scoping lexical and closures work.

**Control flow.** `RTResult` carries `func_return_value`,
`loop_should_break`, and `loop_should_continue` beside the value and error.
`should_return()` tells a statement list to stop; loops consume and clear the
loop signals; `Function.execute` consumes the return signal and clears all three
so nothing escapes a call. This is why `bail` inside a chore called from a loop
cannot break the caller's loop.

**Depth.** `loop_depth` and `func_depth` make `bail` outside a loop and `yeet`
outside a chore real errors, and cap recursion at `MAX_CALL_DEPTH`.

---

## Incomplete input

`wants_more(filename, text)` lexes and parses without running, and reports
whether the input failed only because it stopped early — that is what lets the
REPL keep reading a half-typed block. Parse errors are judged by position (did
it fail at the end?); lexer errors carry an explicit `incomplete` flag, because
an unterminated yap reports at its opening quote, not at the end.

---

## Adding a feature

Most changes touch four places, in order:

1. **Lexer** — a token type, plus a `make_*` method if it is multi-character
2. **Parser** — an AST node class, and a grammar method or precedence level
3. **Interpreter** — a `visit_<NodeName>` method
4. **Tests** — one per stage you touched

A new *value type* is smaller: subclass `Value`, set `TYPE_NAME`, override the
operations it supports. A new *builtin* is smaller still: write
`bi_yourthing(args, node) -> (value, error)` and add one row to `BUILTINS`.

Builtin arg names carry prefixes: `?name` is optional and arrives as `None`,
`*name` soaks up any number more. A builtin that needs the interpreter itself
(`summon` does, to run a file in the caller's scope) goes in
`NEEDS_INTERPRETER` and receives it as a third argument.

---

## Layout

| Where | What |
|---|---|
| `shit.py` | constants, errors, `Position`, `Token`, `Lexer` |
| | AST nodes, `ParseResult`, `Parser` |
| | `RTResult`, `Value` and friends, builtins, `SymbolTable`, `Interpreter` |
| | `run()`, `main()` |
| `shell.py` | REPL loop, buffering until `wants_more` says the input is complete. `main(symbol_table=None)` is importable, so the REPL is testable with a fake `input` |
| `tests/` | one file per concern |
