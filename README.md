# shit 💩 - what-did-i-do 🤔

[![Python](https://img.shields.io/badge/python-3.10%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![Status](https://img.shields.io/badge/status-WIP-orange)](https://github.com/iam-kira/what-did-i-do)
[![Stars](https://img.shields.io/github/stars/iam-kira/what-did-i-do?style=flat)](https://github.com/iam-kira/what-did-i-do/stargazers)
[![Last commit](https://img.shields.io/github/last-commit/iam-kira/what-did-i-do)](https://github.com/iam-kira/what-did-i-do/commits)

A tiny interpreted programming language written in Python from scratch.

> 😆OK - I thought I can write some programming language, well it wasn't too easy as expected lol. So, That day I started doing it and completed with lexer and parser part, and thought to move on to the interpreter part.. ok ok still on the way xD.

---

## What is shit?

A tiny interpreted language written in Python from scratch — lexer, parser, and
tree-walking interpreter, no dependencies. It has numbers, strings, lists,
closures, control flow, and a builtin library. It also refuses to use a single
normal keyword.

```text
chore label(n) ong
    fr n % 15 == 0 ong
        yeet "fizzbuzz"
    orfr n % 3 == 0 ong
        yeet "fizz"
    orfr n % 5 == 0 ong
        yeet "buzz"
    bet
    yeet yapify(n)
bet

grind i = 1 til 16 ong
    yap(label(i))
bet
```

Yes, `ong` opens a block and `bet` closes it. `chore` defines a function,
`yeet` returns, `stash` declares, `yap` prints. The full vocabulary is in
[docs/LANGUAGE.md](docs/LANGUAGE.md).

---

## Install and run

Python 3.9+, nothing else.

```bash
git clone https://github.com/iam-kira/what-did-i-do
cd what-did-i-do
python shit.py example.shit
```

Bare `python shit.py` opens the REPL:

```text
shell :> stash xs = [1, 2, 3]
[1, 2, 3]

shell :> xs[-1] * 10
30

shell :> {"a": 1, "b": 2}
{"a": 1, "b": 2}

shell :> chore sq(n) ong
   ...  >     yeet n ^ 2
   ...  > bet
<chore sq>

shell :> sq(9)
81
```

It reads multi-line blocks — an unfinished one keeps prompting with `...  >`.
Other ways in:

```bash
python shit.py --tokens prog.shit   # token stream
python shit.py --ast prog.shit      # parse tree
python shit.py --help
```

---

## Docs

| | |
|---|---|
| [docs/LANGUAGE.md](docs/LANGUAGE.md) | The language — vocabulary, values, operators, control flow, closures, builtins, errors |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | How the interpreter works, and where to add things |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Setup, workflow, and what needs doing |
| [example.shit](example.shit) | A program using most of the language |

---

## What it can do

- **Types** — numbers (`math`), strings (`yap`), lists (`pile`), dicts (`bag`), first-class functions (`chore`)
- **Control flow** — `fr`/`orfr`/`whatever`, `keep`, `grind ... til`, `grind ... among`, `bail`, `skip`, `yeet`
- **Scoping** — lexical, with working closures and outer-variable mutation
- **Operators** — `+ - * / % ^`, comparisons, `also`/`orelse`/`nah`, indexing, compound assignment
- **27 builtins** — printing, input, maths, slicing, sorting, splitting, joining, type checks
- **Imports** — `summon("lib.shit")`, with cycle detection
- **Error handling** — `risky` / `whoops` / `oops`, catching anything the runtime throws
- **Errors** — returned as values with file/line/column and a call-stack traceback
- **205 tests** covering every stage

---

## Status

Works. Not finished. Missing: user-defined types, destructuring.
Known rough edges are listed at the end of
[docs/LANGUAGE.md](docs/LANGUAGE.md) and in [CONTRIBUTING.md](CONTRIBUTING.md).

---

## Run tests

```bash
pip install pytest
python -m pytest -q
```

---

## License

[MIT](LICENSE)
