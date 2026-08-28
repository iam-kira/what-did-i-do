# Contributing to shit

It's a toy language built to learn how interpreters work. PRs welcome — especially
from people learning the same thing.

## Setup

Python 3.9+, no runtime dependencies.

```bash
git clone https://github.com/iam-kira/what-did-i-do
cd what-did-i-do
pip install pytest
```

## Run it

```bash
python shit.py              # REPL
python shit.py example.shit # run a file
python -m pytest -q         # tests
```

## Where the code lives

```text
shit.py    # everything: Lexer -> Parser -> Interpreter -> run()
shell.py   # REPL loop
tests/     # one file per stage
```

The pipeline is `Lexer.make_tokens()` -> `Parser.parse()` -> `Interpreter.visit()`.
Errors never raise; they're returned as `(value, error)` pairs and carry source
positions. Keep it that way.

## Adding a feature

Most language features touch four places, in this order:

1. **Lexer** — new token type + a `make_*` method if it's multi-character
2. **Parser** — an AST node class, and a grammar method (or a new precedence level)
3. **Interpreter** — a `visit_<NodeName>` method
4. **Tests** — one per stage you touched

## What needs doing

Roughly in order:

- [ ] Index assignment: `xs[0] = 1`
- [ ] `for x in xs` iteration over lists and strings
- [ ] Dictionaries / maps
- [ ] Compound assignment: `x += 1`
- [ ] A `run("other.shit")` builtin so files can import each other
- [ ] `else` on loops, or `do ... while`

Known smaller bugs, good first issues:

- [ ] `Token.__init__` leaves `pos_start` undefined when given no positions
- [ ] Assignment inside a function always writes to the local scope, so a function
      shadows an outer name instead of mutating it (see the `ponytail:` note in
      `Function.execute`)

## Pull requests

- One feature per PR
- `python -m pytest -q` green before you open it
- Match the surrounding style — plain classes, no frameworks, no new dependencies
- Update the README's syntax list if you added syntax

## Bugs

Open an issue with the source that broke and what you expected instead. A failing
one-liner is the ideal bug report here.
