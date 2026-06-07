# shit 💩

A tiny interpreted programming language written in Python from scratch.

> 😆OK - I thought I can write some programming language, well it wasn't too easy as expected lol. So, That day I started doing it and completed with lexer and parser part, and thought to move on to the interpreter part.. ok ok still on the way xD.

---

## What is shit?

**shit** is a toy/learning language with a REPL shell. It currently supports arithmetic expressions over integers and floats. The goal is to grow it into a fully interpreted language with variables, control flow, and functions.

---

## Current status

| Component   | Status              |
|-------------|---------------------|
| Lexer       | ✅ Complete          |
| Parser      | 🔧 In progress (AST + precedence parsing scaffolded) |
| Interpreter | ❌ Not implemented yet |

---

## Supported syntax (Lexer)

- **Integer & float literals** — `42`, `3.14`
- **Arithmetic operators** — `+`, `-`, `*`, `/`
- **Parentheses** — `(`, `)`
- **Whitespace** — ignored

---

## Error handling

- `IllegalCharError` — reported with filename and line number for any unrecognized character

---

## Project structure

```
shit.py      # Core language: Lexer, Tokens, Errors, run()
shell.py     # Interactive REPL
```

---

## Run the REPL

```bash
python shell.py
```

Example session:

```
shell :> 1 + 2 * 3
[INT:1, PLUS, INT:2, MUL, INT:3]

shell :> 3.14 + 1
[FLOAT:3.14, PLUS, INT:1]

shell :> $
Illegal Character: '$'
File <stdin>, line 1
```

---

## Run tests

```bash
pytest -q
```

