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
| `risky` | try | `whoops` | catch |
| `oops` | raise | | |
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
| Dict | `bag` | `{"a": 1, 2: "b"}` |
| Function | `chore` | `chore f(a) ong ... bet` |

`based`, `cringe` and `ghosted` are `1`, `0` and `0`. There is no separate
boolean type — anything non-zero, non-empty is truthy.

String escapes: `\n` `\t` `\r` `\\` `\"` `{{` `}}`.

### Yap holes

`{...}` inside a yap evaluates and drops the result in. Any expression works —
calls, lookups, arithmetic, even another yap:

```text
stash name = "ana"
stash scores = {"ana": 3}

yap("hi {name}, you have {scores[name]} points")
yap("{1 + 2} and {smol(9, 4)}")
```

Yaps interpolate as their text, everything else as it would print. `{{` and
`}}` give literal braces. A hole holds exactly one expression; an empty `{}` is
an error. An error inside a hole points at the yap that holds it.

Piles and bags may span lines and carry a trailing comma:

```text
stash xs = [
    1,
    2,
]

stash config = {
    "host": "localhost",
    "port": 8080,
}
```

### Bags

Labels may be maths or yaps — nothing else. Reading a label that is not there
is an error, so check first with `gotit`.

```text
stash scores = {"ana": 3}
scores["bo"] = 5          # add
scores["ana"] += 1        # update
yap(howmany(scores))      # 2
yap(labels(scores))       # ["ana", "bo"]
yap(goods(scores))        # [4, 5]
yap(gotit(scores, "cy"))  # 0
stash fewer = yoink(scores, "ana")
```

`+` merges two bags, right-hand side winning. `==` compares by value. An empty
bag is falsy.

---

## Variables

```text
stash x = 10      # declare in the current scope
x = x + 1         # assign - the name must already exist
x += 1            # also -= *= /=
```

Several at once, from a pile:

```text
stash a, b = [1, 2]
a, b = [b, a]              # swap
stash lo, hi = bounds()    # a chore returning a pile
```

The pile must have exactly as many things as there are names.

Assigning a name that was never `stash`ed is an error. `stash` always declares
locally, so a parameter or local never clobbers an outer name.

---

## Operators

| Kind | Operators |
|---|---|
| Arithmetic | `+` `-` `*` `/` `%` `^` |
| Comparison | `==` `!=` `<` `>` `<=` `>=` |
| Logic | `also` `orelse` `nah` |
| Index | `xs[0]`, `xs[-1]`, `bag["label"]` |

Precedence, loosest first: `orelse` → `also` → `nah` → comparison → `+ -` →
`* / %` → unary `+ -` → `^` → call/index.

`^` is right-associative, so `2 ^ 3 ^ 2` is `512`. Unary minus binds looser than
`^`, so `-2 ^ 2` is `-4`.

Exact integer division stays an integer: `4 / 2` is `2`, but `5 / 2` is `2.5`.

`+` joins two yaps or two piles, and merges two bags. `*` repeats a yap or a
pile by a whole math.

Assignment targets may be indexes, and compound assignment works on them:

```text
xs[0] = 99
xs[0] += 1
grid[1][0] = 9
scores["ana"] += 1
```

Yaps are immutable — `s[0] = "z"` is an error.

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

```text
grind label, value among scores ong
    yap("{label}: {value}")
bet
```

`grind ... til` ranges are **end-exclusive**. `by` defaults to `1` and may be
negative; `by 0` is an error. `grind ... among` walks a pile, a yap one
character at a time, or a bag's labels. Two names walk a bag's label/value
pairs, or unpack each element of a pile of piles. `bail` and `skip` work in
both loop kinds.

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

**In and out**

| Chore | Does |
|---|---|
| `yap(value)` | print a line, gives back `0` |
| `beg(prompt?)` | read a line as a yap; the prompt is optional |
| `summon(path)` | run another file here, so its chores and stashes land in this scope |

**Everything**

| Chore | Does |
|---|---|
| `howmany(value)` | length of a yap, pile or bag |
| `whatis(value)` | type name as a yap: `"math"`, `"yap"`, `"pile"`, `"bag"`, `"chore"` |
| `yapify(value)` | anything → yap |
| `mathify(value)` | yap → math, or explode trying |
| `is_math` `is_yap` `is_pile` `is_chore` | type checks, `1` or `0` |

**Maths**

| Chore | Does |
|---|---|
| `smol(a, b, ...)` or `smol(pile)` | smallest |
| `chonk(a, b, ...)` or `chonk(pile)` | biggest |
| `total(a, b, ...)` or `total(pile)` | sum |
| `absolutely(n)` | absolute value |
| `roundish(n, places?)` | round |

**Piles and yaps**

| Chore | Does |
|---|---|
| `chunk(value, start?, stop?)` | slice; out-of-range bounds clamp |
| `flip(value)` | reversed |
| `where(value, needle)` | first index, or `-1` |
| `gotit(value, needle)` | `1` or `0`; on a bag, checks labels |
| `stuff(pile, value)` | new pile with `value` on the end |
| `yoink(pile, index)` | new pile with `index` removed; on a bag, drops a label |
| `sortof(pile)` | sorted; all maths or all yaps |
| `glue(pile, separator?)` | join into a yap |
| `shred(yap, separator?)` | split into a pile; no separator splits on whitespace |
| `shout` `whisper` `trim` | upper, lower, strip |
| `labels(bag)` `goods(bag)` | a bag's labels or its values, as a pile |

Nothing mutates in place — `stuff`, `yoink`, `sortof`, `chunk` and `flip` all
hand back something new. To change a pile or bag where it stands, assign into
it: `xs[0] = 99`.

Builtins live in a scope every program inherits, so you can shadow one:
`stash howmany = 5` is legal, if unwise.

---

## Going wrong on purpose

`oops` raises. `risky ... whoops name ong ... bet` catches, binding a bag with
`why`, `file` and `line`:

```text
chore safe_div(a, b) ong
    risky ong
        yeet a / b
    whoops e ong
        yap("nope: " + e["why"])
        yeet 0
    bet
bet

yap(safe_div(10, 0))   # nope: Division by zero  /  0
```

Every runtime error is catchable, including undefined names, bad indexes and
runaway recursion. Syntax errors are not — those happen before anything runs.
`yeet`, `bail` and `skip` pass straight through a `risky` untouched.

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

## Running things

```bash
python shit.py                 # REPL - it reads multi-line blocks
python shit.py prog.shit       # run a file
python shit.py --tokens f.shit # dump the token stream
python shit.py --ast f.shit    # dump the parse tree
python shit.py --help
```

In the REPL, an unfinished block keeps prompting with `...  >`. A blank line
force-ends it, and ctrl-c throws the buffer away.

File mode prints nothing on its own — use `yap`. The REPL echoes each
statement's value.

---

## Not a thing yet

- No user-defined types
- No `xs[0]` on a yap as an assignment target — yaps are immutable
- No `whatever` branch on a loop
- Call depth caps at 200
