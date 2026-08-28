# shit — language reference

Everything the language currently does. For how the interpreter is built, see
[ARCHITECTURE.md](ARCHITECTURE.md).

---

## Vocabulary

shit does not speak Python. Same ideas, worse names.

| shit | means | shit | means |
|---|---|---|---|
| `stash` | declare a variable | `chore` | define a function |
| `fr` | if | `yeet` | return |
| `orfr` | else if | `bail` | break |
| `whatever` | else | `skip` | continue |
| `ong` | then (opens a block) | `also` | and |
| `bet` | end (closes a block) | `orelse` | or |
| `keep` | while | `nah` | not |
| `grind` | for | `based` | true |
| `til` | to | `cringe` | false |
| `by` | step | `ghosted` | null |
| `among` | in | | |

Every block opens with `ong` and closes with `bet`. No exceptions, no braces,
no significant whitespace.

---

## Values

| Type | Called | Literal |
|---|---|---|
| Number | `math` | `42`, `3.14` |
| String | `yap` | `"hi"`, `"tab\there"` |
| List | `pile` | `[1, "two", [3]]` |
| Function | `chore` | `chore f(a) ong ... bet` |

`based`, `cringe` and `ghosted` are `1`, `0` and `0`. There is no separate
boolean type — anything non-zero, non-empty is truthy.

String escapes: `\n` `\t` `\r` `\` `\"`.

Lists may span lines and may carry a trailing comma:

```text
stash xs = [
    1,
    2,
]
```

---

## Variables

```text
stash x = 10      # declare in the current scope
x = x + 1         # assign - the name must already exist
x += 1            # also -= *= /=
```

Assigning a name that was never `stash`ed is an error. `stash` always declares
locally, so a parameter or local never clobbers an outer name.

---

## Operators

| Kind | Operators |
|---|---|
| Arithmetic | `+` `-` `*` `/` `%` `^` |
| Comparison | `==` `!=` `<` `>` `<=` `>=` |
| Logic | `also` `orelse` `nah` |
| Index | `xs[0]`, `xs[-1]` |

Precedence, loosest first: `orelse` → `also` → `nah` → comparison → `+ -` →
`* / %` → unary `+ -` → `^` → call/index.

`^` is right-associative, so `2 ^ 3 ^ 2` is `512`. Unary minus binds looser than
`^`, so `-2 ^ 2` is `-4`.

Exact integer division stays an integer: `4 / 2` is `2`, but `5 / 2` is `2.5`.

`+` joins two yaps or two piles. `*` repeats either by a whole math.

---

## Control flow

```text
fr x > 10 ong
    yap("big")
orfr x > 5 ong
    yap("medium")
whatever
    yap("small")
bet
```

```text
keep n > 0 ong
    n -= 1
bet
```

```text
grind i = 0 til 10 by 2 ong
    fr i == 6 ong
        skip
    bet
    yap(i)
bet

grind word among ["a", "b"] ong
    yap(word)
bet
```

`grind ... til` ranges are **end-exclusive**. `by` defaults to `1` and may be
negative; `by 0` is an error. `grind ... among` walks a pile, or a yap one
character at a time. `bail` and `skip` work in both loop kinds.

---

## Chores

```text
chore fib(n) ong
    fr n < 2 ong
        yeet n
    bet
    yeet fib(n - 1) + fib(n - 2)
bet
```

Chores are values: pass them, return them, stash them.

Scoping is **lexical** — a chore sees the scope it was written in, not the one
it was called from. Assignment walks outward to wherever the name was declared,
so nested chores are real closures:

```text
chore counter() ong
    stash n = 0
    chore tick() ong
        n += 1
        yeet n
    bet
    yeet tick
bet

stash c = counter()
yap(c())   # 1
yap(c())   # 2
```

A chore with no `yeet` evaluates to its last statement. Call depth is capped at
200.

---

## Built-in chores

| Chore | Does |
|---|---|
| `yap(value)` | print a line, gives back `0` |
| `beg(prompt)` | read a line as a yap |
| `howmany(value)` | length of a yap or pile |
| `yapify(value)` | anything → yap |
| `mathify(value)` | yap → math, or explode trying |
| `stuff(pile, value)` | new pile with `value` on the end |
| `yoink(pile, index)` | new pile with `index` removed |
| `is_math` `is_yap` `is_pile` `is_chore` | type checks, `1` or `0` |

`stuff` and `yoink` return new piles. To change one in place, assign into it:
`xs[0] = 99`.

Builtins live in a scope every program inherits, so you can shadow one:
`stash howmany = 5` is legal, if unwise.

---

## Errors

Errors are values, not exceptions. Every stage returns `(result, error)`.

| Error | When |
|---|---|
| `IllegalCharError` | a character the lexer does not know |
| `ExpectedCharError` | unterminated yap, malformed number |
| `InvalidSyntaxError` | grammar broke |
| `RTError` | undefined name, `/ 0`, bad index, wrong arg count, `bail` outside a loop |

Runtime errors inside chores carry a traceback:

```text
Traceback (most recent call last):
  File prog.shit, line 9, in outer
  File prog.shit, line 6, in inner
Runtime Error: Division by zero
File prog.shit, line 2, col 16
```

---

## Not a thing yet

- No dictionaries
- No modules or imports
- No `xs[0]` on a yap as an assignment target — yaps are immutable
- No user-defined types
