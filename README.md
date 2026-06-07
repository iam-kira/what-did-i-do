# shit 💩 - what-did-i-do 🤔

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

---

## Supported syntax

- **Integer & float literals** — `42`, `3.14`
- **Identifiers & declarations** — `x`, `var x = 10`, `x = x + 1`
- **Arithmetic operators** — `+`, `-`, `*`, `/`
- **Comparisons** — `==`, `!=`, `<`, `<=`, `>`, `>=`
- **Parentheses** — `(`, `)`
- **Multiple statements** — newline or `;` separated
- **Whitespace** — ignored (except newline as statement separator)

---

## Error handling

- `IllegalCharError` — unrecognized character in lexer
- `InvalidSyntaxError` — parse-time grammar error
- `RTError` — runtime error (undefined variable, division by zero)

---

## Project structure

```text
shit.py      # Core language: Lexer, Parser, AST, Interpreter, run()
shell.py     # Interactive REPL
tests/       # Pytest suite for lexer/parser/interpreter
```

---

## Run the REPL

```bash
python shell.py
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
pytest -q
```

