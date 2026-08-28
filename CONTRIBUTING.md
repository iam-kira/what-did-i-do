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
docs/      # language reference and architecture notes
tests/     # one file per concern
```

[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) explains the pipeline, the
returned-error convention, how scopes and control-flow signals work, and where
each kind of change goes. Read it before your first patch — it is short.

[docs/LANGUAGE.md](docs/LANGUAGE.md) is the language reference. If you change
behaviour, change that file in the same commit.

## Adding a feature

Most language features touch four places, in this order:

1. **Lexer** — new token type + a `make_*` method if it is multi-character
2. **Parser** — an AST node class, and a grammar method (or a new precedence level)
3. **Interpreter** — a `visit_<NodeName>` method
4. **Tests** — one per stage you touched

A new value type is smaller: subclass `Value`, set `TYPE_NAME`, override what it
supports. A new builtin is one function plus one row in `BUILTINS`.

## What needs doing

Roughly in order:

- [ ] Dictionaries / maps (`{"a": 1}`), with `among` iteration over keys
- [ ] A `summon("other.shit")` builtin so files can pull each other in
- [ ] More builtins: `min`, `max`, `abs`, `slice`, `join`, `split`, `upper`, `lower`
- [ ] `whatever` on a loop, or `do ... keep`
- [ ] Multiple return values, or returning a pile and destructuring it
- [ ] A `--tokens` / `--ast` CLI flag for debugging your own programs

Known smaller bugs, good first issues:

- [ ] `Token.__init__` leaves `pos_start` undefined when given no positions
- [ ] `beg` requires a prompt argument; `beg()` should work
- [ ] Yaps are immutable, so `s[0] = "z"` errors — decide whether that stays
- [ ] Error messages mix dialect and English ("Division by zero" vs "not a chore")

## Pull requests

- One feature per PR
- `python -m pytest -q` green before you open it
- Match the surrounding style — plain classes, no frameworks, no new dependencies
- Update [docs/LANGUAGE.md](docs/LANGUAGE.md) in the same commit if you changed behaviour

## Bugs

Open an issue with the source that broke and what you expected instead. A failing
one-liner is the ideal bug report here.
