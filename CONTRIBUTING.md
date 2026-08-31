# Contributing to aura

It's a toy language built to learn how interpreters work. PRs welcome — especially
from people learning the same thing.

## Setup

Python 3.9+, no runtime dependencies.

```bash
git clone https://github.com/iam-kira/what-did-i-do
cd what-did-i-do

python -m venv .venv
.venv/Scripts/activate       # Windows
source .venv/bin/activate    # macOS and Linux

pip install pytest
```

aura itself needs nothing installed — the venv is only so `pytest` does not
land in your system Python. `.venv/` is gitignored.

## Run it

```bash
python aura.py              # REPL
python aura.py example.aura # run a file
python -m pytest -q         # tests
```

## Where the code lives

```text
aura.py    # everything: Lexer -> Parser -> Interpreter -> run()
shell.py   # REPL loop
docs/      # language reference and architecture notes
examples/  # programs written in aura
editors/   # VS Code syntax highlighting
tests/     # one file per concern
```

If you add a keyword or a builtin, add it to
`editors/vscode/syntaxes/aura.tmLanguage.json` too - a test compares the
grammar against the real lists and will fail if you forget.

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

- [ ] `whatever` branch on a loop, or `do ... keep`
- [ ] Real user-defined types - a bag of chores with dot access works, but has
      no identity, no whatis name of its own, and no shared behaviour
- [ ] A `--time` flag, or anything resembling a profiler
- [ ] `slurp` reads the whole file; no streaming and no binary
- [ ] Speed: every value copies on read. Measured, it is fine for a toy -
      fib(19) plus a 200k-iteration loop runs in about 1.6s - so measure
      before optimising anything here
- [ ] No reference semantics at all: a chore cannot mutate a pile or bag its
      caller holds. Closures are the workaround. Worth deciding if that is
      the final answer

Known smaller things, good first issues:

- [ ] Error text mixes dialect and English on purpose: type names are dialect
      (`math`, `yap`), the surrounding sentence is plain English so errors stay
      readable. Keep that split if you add messages.

## Releasing

aura ships as a single module, so a release is short:

```bash
pip install build twine
python -m build            # writes dist/*.whl and dist/*.tar.gz
twine check dist/*
twine upload dist/*        # needs a PyPI token
```

Bump `version` in `pyproject.toml` first. PyPI never lets a version be
reused, so test with `twine upload --repository testpypi dist/*` if in doubt.

The distribution is named `auralang`; the module and the command are both
`aura`.

## Pull requests

- One feature per PR
- `python -m pytest -q` green before you open it
- Match the surrounding style — plain classes, no frameworks, no new dependencies
- Update [docs/LANGUAGE.md](docs/LANGUAGE.md) in the same commit if you changed behaviour

## Licensing

aura is copyright iam-kira (Vijay Biradar) and licensed under the
[PolyForm Noncommercial Licence 1.0.0](LICENSE): anyone may use, modify and
share it for noncommercial purposes, and only the copyright holder may sell it
or license it commercially.

By opening a pull request you agree that:

- your contribution is licensed under the same terms as the project, and
- you grant Vijay Biradar the right to license your contribution commercially,
  including under different terms.

That second point is what keeps the commercial rights in one place. Without it,
every merged contribution would add a copyright holder whose permission would
be needed before aura could be licensed commercially — which would make the
licence above unworkable within a few pull requests.

## Bugs

Open an issue with the source that broke and what you expected instead. A failing
one-liner is the ideal bug report here.
