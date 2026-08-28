# shit 💩 - what-did-i-do 🤔

[![Python](https://img.shields.io/badge/python-3.10%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![Status](https://img.shields.io/badge/status-WIP-orange)](https://github.com/iam-kira/what-did-i-do)
[![Stars](https://img.shields.io/github/stars/iam-kira/what-did-i-do?style=flat)](https://github.com/iam-kira/what-did-i-do/stargazers)
[![Last commit](https://img.shields.io/github/last-commit/iam-kira/what-did-i-do)](https://github.com/iam-kira/what-did-i-do/commits)

A tiny interpreted programming language written in Python from scratch.

> 😆OK - I thought I can write some programming language, well it wasn't too easy as expected lol. So, That day I started doing it and completed with lexer and parser part, and thought to move on to the interpreter part.. ok ok still on the way xD.

---

## What is shit?

**shit** is a toy/learning language with a REPL and a file runner. It has numbers,
strings, lists, variables, control flow, and user-defined functions — enough to
write real (small) programs.

---

## Current status

- **Lexer** — done
- **Parser** — done (AST + precedence climbing)
- **Interpreter** — done (tree-walking, lexical scopes)
- **Types** — numbers, strings, lists, functions
- **Control flow** — `if` / `elif` / `else`, `while`, `for`, `break`, `continue`, `return`
- **Builtins** — `print`, `input`, `len`, `str`, `num`, `append`, `pop`, type predicates

---

## A taste

```text
fun label(n) then
    if n % 15 == 0 then
        return "fizzbuzz"
    elif n % 3 == 0 then
        return "fizz"
    elif n % 5 == 0 then
        return "buzz"
    end
    return str(n)
end

for i = 1 to 16 then
    print(label(i))
end
```

See [example.shit](example.shit) for a longer one.

---

## Language reference

### Values

| Type | Literal | Notes |
|---|---|---|
| Number | `42`, `3.14` | ints and floats; `true` / `false` / `null` are `1` / `0` / `0` |
| String | `"hi
"` | escapes: `
` `	` `` `\` `\"` |
| List | `[1, "two", [3]]` | trailing comma allowed, may span lines |
| Function | `fun f(a) then ... end` | first class — pass it, return it |

### Variables

```text
var x = 10      # declare
x = x + 1       # assign (declaring first is required)
```

### Operators

| Kind | Operators | Notes |
|---|---|---|
| Arithmetic | `+` `-` `*` `/` `%` `^` | `^` is right-associative; exact int division stays int |
| Comparison | `==` `!=` `<` `>` `<=` `>=` | |
| Logic | `and` `or` `not` | precedence: `or` < `and` < `not` < comparison |
| Index | `xs[0]`, `xs[-1]` | strings and lists; negative counts from the end |

`+` concatenates two strings or two lists; `*` repeats either by an integer.

### Control flow

```text
if x > 10 then
    print("big")
elif x > 5 then
    print("medium")
else
    print("small")
end

while n > 0 then
    n = n - 1
end

for i = 0 to 10 step 2 then
    if i == 6 then
        continue
    end
    print(i)
end
```

`for` ranges are **end-exclusive**; `step` defaults to `1` and may be negative.
`break` and `continue` work in both loop kinds.

### Functions

```text
fun fib(n) then
    if n < 2 then
        return n
    end
    return fib(n - 1) + fib(n - 2)
end

print(fib(20))
```

Arguments are bound in a fresh child scope, so recursion works and locals do not
leak. A function without `return` evaluates to its last statement.

### Builtins

| Function | Does |
|---|---|
| `print(value)` | writes a line, returns `0` |
| `input(prompt)` | reads a line as a string |
| `len(value)` | length of a string or list |
| `str(value)` / `num(value)` | convert |
| `append(list, value)` | new list with `value` added |
| `pop(list, index)` | new list with `index` removed |
| `is_num` / `is_str` / `is_list` / `is_fun` | type predicates, `1` or `0` |

`append` and `pop` return new lists — values are never mutated in place.

---

## Error handling

Errors are values, not exceptions — every stage returns `(result, error)` and
reports the file, line, and column.

- `IllegalCharError` — unrecognized character
- `ExpectedCharError` — e.g. an unterminated string
- `InvalidSyntaxError` — parse-time grammar error
- `RTError` — runtime error (undefined variable, division by zero, bad index,
  wrong argument count, `break` outside a loop)

---

## Project structure

```text
shit.py        # Core language: Lexer, Parser, AST, Interpreter, builtins, CLI
shell.py       # Interactive REPL
example.shit   # Sample program
tests/         # Pytest suite, one file per stage
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

```bash
python shit.py example.shit
```

Use `print` for output — file mode does not echo statement values.

---

## Run the REPL

```bash
python shit.py
# or: python shell.py
```

The REPL echoes each statement's value:

```text
shell :> 1 + 2 * 3
7

shell :> var xs = [1, 2, 3]
[1, 2, 3]

shell :> xs[-1] * 10
30

shell :> "shit" + "!" * 3
"shit!!!"

shell :> $
Illegal Character: '$'
File <stdin>, line 1, col 1
```

---

## Run tests

```bash
pip install pytest
python -m pytest -q
```

---

## Not there yet

- No `%=`-style compound assignment, no index assignment (`xs[0] = 1`)
- No dictionaries or `for x in xs` iteration
- No modules or imports
- No call-stack traceback on runtime errors — just the innermost position

---

## Contributing

PRs welcome — see [CONTRIBUTING.md](CONTRIBUTING.md) for setup, how the
pipeline fits together, and a list of what needs doing.

---

## License

[MIT](LICENSE)


