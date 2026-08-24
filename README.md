# shit 💩 - what-did-i-do 🤔

[![Python](https://img.shields.io/badge/python-3.10%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![Status](https://img.shields.io/badge/status-WIP-orange)](https://github.com/iam-kira/what-did-i-do)
[![Stars](https://img.shields.io/github/stars/iam-kira/what-did-i-do?style=flat)](https://github.com/iam-kira/what-did-i-do/stargazers)
[![Last commit](https://img.shields.io/github/last-commit/iam-kira/what-did-i-do)](https://github.com/iam-kira/what-did-i-do/commits)

A tiny interpreted programming language written in Python from scratch.

> 😆OK - I thought I can write some programming language, well it wasn't too easy as expected lol. So, That day I started doing it and completed with lexer and parser part, and thought to move on to the interpreter part.. ok ok still on the way xD.

---

## What is shit?

**shit** is a toy/learning language with a REPL shell. It currently supports arithmetic expressions over integers and floats. The goal is to grow it into a fully interpreted language with variables, control flow, and functions.

---

## Current status

- **Lexer** — ✅ Complete
- **Parser** — ✅ Implemented (AST + precedence parsing)
- **Interpreter** — ✅ Implemented (runtime evaluation + variable state)
- **CLI** — ✅ Run `.shit` files or the REPL
- **Control flow & functions** — 🚧 Not yet (`if`, `while`, `fun`)

---

## Supported syntax

- **Integer & float literals** — `42`, `3.14`
- **Identifiers & declarations** — `x`, `var x = 10`, `x = x + 1`
- **Arithmetic operators** — `+`, `-`, `*`, `/`
- **Comparisons** — `==`, `!=`, `<`, `<=`, `>`, `>=`
- **Parentheses** — `(`, `)`
- **Multiple statements** — newline or `;` separated
- **Comments** — `#` to end of line
- **Whitespace** — ignored (except newline as statement separator)

---

## Error handling

- `IllegalCharError` — unrecognized character in lexer
- `InvalidSyntaxError` — parse-time grammar error
- `RTError` — runtime error (undefined variable, division by zero)

---

## Project structure

```text
shit.py        # Core language: Lexer, Parser, AST, Interpreter, run(), CLI
shell.py       # Interactive REPL
example.shit   # Sample program
tests/         # Pytest suite for lexer/parser/interpreter
```

---

## Install

Requires Python 3.9+. No dependencies.

```bash
git clone https://github.com/iam-kira/what-did-i-do
cd what-did-i-do
```

---

## Run a program

Write a file and run it:

```bash
python shit.py example.shit
```

`example.shit`:

```text
var x = 10
var y = 3.5
x + y
x = x * 2
x
x > y
```

Every statement's value is printed, one per line — there is no `print` builtin yet.

---

## Run the REPL

```bash
python shit.py
# or: python shell.py
```

Example session:

```text
shell :> 1 + 2 * 3
7

shell :> 3.14 + 1
4.14

shell :> var x = 10
10

shell :> x = x + 5
15

shell :> x
15

shell :> $
Illegal Character: '$'
File <stdin>, line 1, col 1
```

---

## Run tests

```bash
pip install pytest
pytest -q
```

---

## Contributing

PRs welcome — see [CONTRIBUTING.md](CONTRIBUTING.md) for setup, how the
pipeline fits together, and a list of what needs doing.

---

## License

[MIT](LICENSE)


