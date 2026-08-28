# aura — language reference

Everything the language currently does. For how the interpreter is built, see
[ARCHITECTURE.md](ARCHITECTURE.md).

---

## Vocabulary

aura does not speak Python. Same ideas, worse names — the name itself being
the one straight face in the room.

| aura | means | aura | means |
|---|---|---|---|
| `stash` | declare a variable | `chore` | define a function |
| `fr` | if | `yeet` | return |
| `orfr` | else if | `bail` | break |
| `whatever` | else | `skip` | continue |
| `ong` | then (opens a block) | `also` | and |
| `bet` | end (closes a block) | `orelse` | or |
| `keep` | while | `nah` | not |
| `sus` | try | `whoops` | catch |
| `oops` | raise | | |
| `grind` | for | `based` | true |
| `til` | to | `cringe` | false |
| `by` | step | `ghosted` | null |
| `among` | in | | |

Every block opens with `ong` and closes with `bet`. No exceptions, no braces,
no significant whitespace.

A newline ends a statement, except inside `(`, `[` or `{` — so a long call or
pile can spread over as many lines as it likes:

```text
stash total = smol(
    1,
    2 + 3,
    4
)
```

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

cook("hi {name}, you have {scores[name]} points")
cook("{1 + 2} and {smol(9, 4)}")
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
cook(howmany(scores))      # 2
cook(labels(scores))       # ["ana", "bo"]
cook(goods(scores))        # [4, 5]
cook(gotit(scores, "cy"))  # 0
stash fewer = yoink(scores, "ana")
```

`+` merges two bags, right-hand side winning. `==` compares by value. An empty
bag is falsy.

`d.name` is shorthand for `d["name"]` — the same thing everywhere, so it reads
and it assigns:

```text
stash player = {"name": "ana", "score": 0}
player.score += 10
player.title = "champ"
cook(player.name)
```

Only bags have labels; dotting a pile or yap says so.

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
| Index | `xs[0]`, `xs[-1]`, `bag["label"]`, `bag.label` |

Precedence, loosest first: `orelse` → `also` → `nah` → comparison → `+ -` →
`* / %` → unary `+ -` → `^` → call/index.

`also` and `orelse` short-circuit — the right side only runs when it can still
change the answer, so this is safe on an empty pile:

```text
fr i < howmany(xs) also xs[i] == 1 ong
    cook("found it")
bet
```

Both always give back `1` or `0`, never the operand.

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
    cook("big")
orfr x > 5 ong
    cook("medium")
whatever
    cook("small")
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
    cook(i)
bet

grind word among ["a", "b"] ong
    cook(word)
bet
```

```text
grind label, value among scores ong
    cook("{label}: {value}")
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
cook(c())   # 1
cook(c())   # 2
```

A chore with no `yeet` evaluates to its last statement. Call depth is capped at
200.

### Things that look like objects

There is no `class`. A chore that captures state and hands back a bag of chores
does the same job, and each call gets its own state:

```text
chore counter() ong
    stash n = 0

    chore bump() ong
        n += 1
        yeet n
    bet

    chore peek() ong
        yeet n
    bet

    yeet {"bump": bump, "peek": peek}
bet

stash a = counter()
a["bump"]()
a["bump"]()
cook(a["peek"]())
```

Suffixes chain, so `a.bump()`, `fs[0]()`, `f()[0]` and `mk()()` all work — which
is what makes the bag above read like an object.

**Shared state has to be captured, not passed.** Arguments are copies, so a
chore cannot change a pile or bag its caller holds:

```text
chore spoil(b) ong
    b["x"] = 99
bet

stash mine = {"x": 1}
spoil(mine)
cook(mine)          # still {"x": 1}
```

Return the new value, or keep the state in a closure like `counter` above.
[examples/calc.aura](../examples/calc.aura) uses a closure for exactly this.

---

## Built-in chores

**In and out**

| Chore | Does |
|---|---|
| `cook(value)` | print a line, gives back `0` |
| `beg(prompt?)` | read a line as a yap; the prompt is optional |
| `summon(path)` | run another file here, so its chores and stashes land in this scope |
| `slurp(path)` | read a whole file as a yap |
| `spill(path, text)` | write a file, replacing it; gives back how much it wrote |
| `dribble(path, text)` | same, but appends |
| `isthere(path)` | `1` if the path exists |
| `isfolder(path)` | `1` if it is a folder |
| `rummage(path?)` | sorted names inside a folder; defaults to here |
| `stitch(part, ...)` | join path parts with `/` |
| `handed()` | a pile of the arguments the program was given |
| `bounce(code?)` | stop the program with an exit code; no `sus` catches it |

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
| `sortof(pile, by?)` | sorted; `by` is a chore giving each item's sort key |
| `glue(pile, separator?)` | join into a yap |
| `shred(yap, separator?)` | split into a pile; no separator splits on whitespace |
| `shout` `whisper` `trim` | upper, lower, strip |
| `labels(bag)` `goods(bag)` | a bag's labels or its values, as a pile |

**Chores that take chores**

| Chore | Does |
|---|---|
| `eachof(pile, chore)` | run the chore on each thing, collect the results |
| `keepif(pile, chore)` | keep the things the chore likes |
| `smoosh(pile, chore, start?)` | fold left; without `start` the first thing seeds it |

```text
chore dbl(n) ong yeet n * 2 bet
chore odd(n) ong yeet n % 2 == 1 bet
chore add(a, b) ong yeet a + b bet

cook(eachof([1, 2, 3], dbl))          # [2, 4, 6]
cook(keepif([1, 2, 3, 4], odd))       # [1, 3]
cook(smoosh([1, 2, 3, 4], add))       # 10
cook(sortof(["bx", "az"], lastchar))  # sorted by whatever the chore returns
```

Closures work here, so a chore can build the chore you pass:

```text
chore times(k) ong
    chore go(n) ong
        yeet n * k
    bet
    yeet go
bet

cook(eachof([1, 2, 3], times(10)))    # [10, 20, 30]
```

Nothing mutates in place — `stuff`, `yoink`, `sortof`, `chunk`, `flip`,
`eachof` and `keepif` all hand back something new. To change a pile or bag
where it stands, assign into it: `xs[0] = 99`.

Builtins live in a scope every program inherits, so you can shadow one:
`stash howmany = 5` is legal, if unwise.

---

## Going wrong on purpose

`oops` raises. `sus ... whoops name ong ... bet` catches, binding a bag with
`why`, `kind`, `file` and `line`:

```text
chore safe_div(a, b) ong
    sus ong
        yeet a / b
    whoops e ong
        cook("nope: " + e["why"])
        yeet 0
    bet
bet

cook(safe_div(10, 0))   # nope: Division by zero  /  0
```

`kind` is a short slug you can branch on instead of matching the message:

| kind | when |
|---|---|
| `math` | `/ 0`, `% 0`, a power with no real answer, `by 0` |
| `name` | undefined name, or assigning to one |
| `index` | out of range, wrong index type, assigning into a yap |
| `label` | no such label in a bag, or a label that is not a math or yap |
| `type` | wrong type for an operator or a builtin |
| `arity` | wrong number of arguments |
| `flow` | `bail` or `skip` outside a loop, `yeet` outside a chore |
| `unpack` | destructuring the wrong shape |
| `depth` | recursion past the call cap |
| `file` | `slurp`, `spill` or `summon` could not do it |
| `custom` | whatever `oops` raised |

```text
sus ong
    stash text = slurp(path)
whoops e ong
    fr e.kind == "file" ong
        cook("no such file, carrying on")
    whatever
        oops e.why
    bet
bet
```

Every runtime error is catchable, including undefined names, bad indexes and
runaway recursion. Syntax errors are not — those happen before anything runs.
`yeet`, `bail` and `skip` pass straight through a `sus` untouched, and so
does `bounce`.

---

## Errors

Errors are values, not exceptions. Every stage returns `(result, error)`.

| Error | When |
|---|---|
| `IllegalCharError` | a character the lexer does not know |
| `ExpectedCharError` | unterminated yap, malformed number |
| `InvalidSyntaxError` | grammar broke |
| `RTError` | undefined name, `/ 0`, bad index, wrong arg count, `bail` outside a loop |

Every error names the file, line and column, and shows the line with a caret
under the offending part:

```text
Runtime Error: 'nope' is not defined
File prog.aura, line 3, col 14
      total += nope
               ^^^^
```

Runtime errors inside chores carry a traceback as well:

```text
Traceback (most recent call last):
  File prog.aura, line 7, in outer
  File prog.aura, line 5, in inner
Runtime Error: Division by zero
File prog.aura, line 2, col 14
      yeet n / 0
               ^
```

---

## Running things

```bash
python aura.py                 # REPL - it reads multi-line blocks
python aura.py prog.aura       # run a file
python aura.py --tokens f.aura # dump the token stream
python aura.py --ast f.aura    # dump the parse tree
python aura.py --help
```

In the REPL, an unfinished block keeps prompting with `...  >`. A blank line
force-ends it, and ctrl-c throws the buffer away.

File mode prints nothing on its own — use `cook`. The REPL echoes each
statement's value.

---

## Not a thing yet

- No user-defined types
- No `xs[0]` on a yap as an assignment target — yaps are immutable
- No `whatever` branch on a loop
- Call depth caps at 200
