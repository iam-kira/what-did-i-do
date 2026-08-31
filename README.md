# aura

[![tests](https://github.com/iam-kira/what-did-i-do/actions/workflows/tests.yml/badge.svg)](https://github.com/iam-kira/what-did-i-do/actions/workflows/tests.yml)
[![Python](https://img.shields.io/badge/python-3.9%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green)](https://github.com/iam-kira/what-did-i-do/blob/master/LICENSE)
[![Stars](https://img.shields.io/github/stars/iam-kira/what-did-i-do?style=flat)](https://github.com/iam-kira/what-did-i-do/stargazers)

**A programming language with a serious name and no seriousness whatsoever.**

Written in Python from scratch — lexer, parser, tree-walking interpreter, zero
dependencies. It has closures, dictionaries, string interpolation, error
handling and a 42-function standard library.

It also does not contain a single normal keyword.

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
    cook(label(i))
bet
```

`ong` opens a block and `bet` closes it. `chore` defines a function, `yeet`
returns, `stash` declares, `cook` prints. That is the entire joke, and it is
load-bearing.

---

## Try it in thirty seconds

Python 3.9 or newer. Nothing else to install.

```bash
pip install auralang
aura
```

Or as a **standalone binary** — no Python, no pip, nothing installed:

```bash
pip install pyinstaller
python build_exe.py
```

That writes `build-exe/aura` (or `aura.exe`), a single ~9 MB file you can copy
to any machine and run. Python is how aura is *built*, not what you need to
*use* it.

Or straight from the source, with nothing installed at all:

```bash
git clone https://github.com/iam-kira/what-did-i-do
cd what-did-i-do
python aura.py
```

That opens the REPL, and it reads multi-line blocks:

```text
shell :> stash xs = [1, 2, 3]
[1, 2, 3]

shell :> xs[-1] * 10
30

shell :> chore sq(n) ong
   ...  >     yeet n ^ 2
   ...  > bet
<chore sq>

shell :> sq(9)
81
```

Or run a file:

```bash
python aura.py example.aura        # a tour of the language
python aura.py prog.aura a b       # a and b arrive in handed()
python aura.py --ast prog.aura     # show the parse tree
python aura.py --help
```

---

## What it can actually do

Not a calculator with silly words. A real small language:

```text
# closures, and state that outlives the call
chore counter() ong
    stash n = 0
    chore tick() ong
        n += 1
        yeet n
    bet
    yeet tick
bet

stash next = counter()
cook("{next()} then {next()}")

# bags, dot access, and yap holes
stash player = {"name": "ana", "score": 0}
player.score += 10
cook("{player.name} is on {player.score}")

# errors you can catch and branch on
sus ong
    stash text = slurp("notes.txt")
whoops e ong
    fr e.kind == "file" ong
        cook("no notes yet, carrying on")
    bet
bet
```

| | |
|---|---|
| **Types** | numbers (`math`), strings (`yap`), lists (`pile`), dicts (`bag`), first-class functions (`chore`) |
| **Control flow** | `fr`/`orfr`/`whatever`, `keep`, `grind ... til`, `grind ... among`, `bail`, `skip`, `yeet` |
| **Scoping** | lexical, with real closures and outer-variable mutation |
| **Yap holes** | `"hi {name}, {1 + 2} points"` |
| **Destructuring** | `stash a, b = [1, 2]`, `grind k, v among bag` |
| **Errors** | `sus` / `whoops` / `oops`, a `kind` on every error, tracebacks, and a caret under the offending code |
| **Higher-order** | `eachof`, `keepif`, `smoosh`, `sortof` with a key chore |
| **Scriptable** | `handed()` for arguments, `slurp`/`spill` for files, `rummage` for folders, `bounce(code)` for exit status |
| **Imports** | `summon("lib.aura")`, with cycle detection |

When something breaks, it tells you exactly where:

```text
Runtime Error: 'nope' is not defined
File prog.aura, line 3, col 14
      total += nope
               ^^^^
```

---

## Read it

| | |
|---|---|
| **[docs/BOOK.md](https://github.com/iam-kira/what-did-i-do/blob/master/docs/BOOK.md)** | **The book** — the whole language, then the whole interpreter, in the order you would learn them. Start here. |
| [docs/LANGUAGE.md](https://github.com/iam-kira/what-did-i-do/blob/master/docs/LANGUAGE.md) | Quick reference — vocabulary, operators, builtins, errors |
| [docs/ARCHITECTURE.md](https://github.com/iam-kira/what-did-i-do/blob/master/docs/ARCHITECTURE.md) | How the interpreter works, and where to add things |
| [CONTRIBUTING.md](https://github.com/iam-kira/what-did-i-do/blob/master/CONTRIBUTING.md) | Setup, workflow, and what needs doing |
| [editors/](https://github.com/iam-kira/what-did-i-do/tree/master/editors/) | VS Code syntax highlighting for `.aura` files |

**Programs written in aura:** [example.aura](https://github.com/iam-kira/what-did-i-do/blob/master/example.aura) tours the language,
[examples/calc.aura](https://github.com/iam-kira/what-did-i-do/blob/master/examples/calc.aura) is a calculator with its own tokeniser
and precedence-climbing parser, [examples/wc.aura](https://github.com/iam-kira/what-did-i-do/blob/master/examples/wc.aura) is a word
counter that walks folders, and [examples/json.aura](https://github.com/iam-kira/what-did-i-do/blob/master/examples/json.aura) is a
JSON parser — closures hold the read position, `sus` handles bad input, and
JSON `null` arrives as `ghosted`.

---

## Why "aura"

Every keyword in the language is a joke. The name is the straight man — it
lets the contents be the punchline, and it will still read fine when the slang
has moved on.

The repo is called `what-did-i-do` for the same reason.

---

## Under the hood

One file, 3,600 lines, no dependencies. `Lexer` → `Parser` → `Interpreter`,
readable top to bottom.

Errors are values, never exceptions: every stage returns a `(result, error)`
pair carrying a source position, which is why a runtime failure can print the
line it happened on.

**500 tests**, including a fuzz sweep asserting no input ever escapes as a
Python traceback, a checker that executes every code snippet in these docs, and
a test that diffs the syntax highlighting against the real keyword list.

```bash
python -m venv .venv
.venv/Scripts/activate       # Windows; use source .venv/bin/activate elsewhere
pip install pytest
python -m pytest -q
```

Running aura needs nothing installed. The venv is only for `pytest`.

---

## Status

Works. Not finished — no type system, and no concern for speed. Rough edges are
listed at the end of [docs/LANGUAGE.md](https://github.com/iam-kira/what-did-i-do/blob/master/docs/LANGUAGE.md) and in
[CONTRIBUTING.md](https://github.com/iam-kira/what-did-i-do/blob/master/CONTRIBUTING.md).

---

## Credit and licence

aura was created by **Vijay Biradar** ([iam-kira](https://github.com/iam-kira)).

Released under the [MIT Licence](https://github.com/iam-kira/what-did-i-do/blob/master/LICENSE), which lets anyone use, modify and
sell it — including inside closed-source products — on one condition:

> The above copyright notice and this permission notice shall be included in
> all copies or substantial portions of the Software.

So if you ship aura, or anything substantially built from it, the copyright
notice comes with it. That is not optional, and it applies to commercial use
too.

Contributions are accepted under the same licence.
