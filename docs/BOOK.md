# aura: the book

The complete reference for the language and the interpreter behind it.

[LANGUAGE.md](LANGUAGE.md) is the quick lookup. [ARCHITECTURE.md](ARCHITECTURE.md)
is the short tour of the code. This is the long version of both, in the order
you would learn them.

---

## Contents

**Part I — the language**

1. [Five minutes](#1-five-minutes)
2. [The vocabulary](#2-the-vocabulary)
3. [Values](#3-values)
4. [Names and scope](#4-names-and-scope)
5. [Expressions](#5-expressions)
6. [Control flow](#6-control-flow)
7. [Chores](#7-chores)
8. [Yaps in detail](#8-yaps-in-detail)
9. [When things go wrong](#9-when-things-go-wrong)
10. [Programs](#10-programs)
11. [The standard library](#11-the-standard-library)

**Part II — the interpreter**

12. [The pipeline](#12-the-pipeline)
13. [The lexer](#13-the-lexer)
14. [The parser](#14-the-parser)
15. [Values at runtime](#15-values-at-runtime)
16. [The interpreter](#16-the-interpreter)
17. [Extending it](#17-extending-it)

**Appendices**

- [A. Grammar](#a-grammar)
- [B. Keywords](#b-keywords)
- [C. Builtins](#c-builtins)
- [D. Error kinds](#d-error-kinds)
- [E. If you know Python](#e-if-you-know-python)

---

# Part I — the language

## 1. Five minutes

You need Python 3.9 or newer. Nothing else.

```bash
git clone https://github.com/iam-kira/what-did-i-do
cd what-did-i-do
python aura.py
```

That opens the REPL. Type something:

```text
shell :> 1 + 2 * 3
7
```

The REPL echoes each statement's value. Strings echo with their quotes, so you
can tell `1` from `"1"`. It also reads multi-line blocks — an unfinished one
keeps prompting with `...  >` until it is complete:

```text
shell :> chore double(n) ong
   ...  >     yeet n * 2
   ...  > bet
<chore double>

shell :> double(21)
42
```

A blank line force-ends a block, so a typo can never trap you, and ctrl-c
throws away what you were typing without quitting.

Put the same thing in a file:

```text
chore double(n) ong
    yeet n * 2
bet

cook(double(21))
```

Run it:

```bash
python aura.py double.aura
```

File mode prints nothing on its own — `cook` is how a program speaks. The REPL
echoes; files do not.

---

## 2. The vocabulary

aura does not use a single normal keyword. This is the whole trick, and the
whole joke. The semantics underneath are ordinary; only the words changed.

| aura | usual name | aura | usual name |
|---|---|---|---|
| `stash` | `var` / `let` | `chore` | `def` / `function` |
| `fr` | `if` | `yeet` | `return` |
| `orfr` | `elif` | `bail` | `break` |
| `whatever` | `else` | `skip` | `continue` |
| `ong` | `then` / `{` | `also` | `and` |
| `bet` | `end` / `}` | `orelse` | `or` |
| `keep` | `while` | `nah` | `not` |
| `grind` | `for` | `based` | `true` |
| `til` | `to` | `cringe` | `false` |
| `by` | `step` | `ghosted` | `null` |
| `among` | `in` | `sus` | `try` |
| `oops` | `raise` | `whoops` | `catch` |

Every block opens with `ong` and closes with `bet`. There are no braces and
whitespace means nothing — indent however you like.

The types are renamed too, and the names show up in error messages:

| type | called | why |
|---|---|---|
| number | `math` | it is |
| string | `yap` | it talks |
| list | `pile` | things heaped up |
| dict | `bag` | things with labels |
| function | `chore` | work you would rather not do twice |

---

## 3. Values

### Maths

Integers and floats, written the obvious way.

```text
stash count = 42
stash ratio = 3.14
```

There is one rule worth knowing: **exact integer division stays an integer.**
`4 / 2` is `2`, not `2.0`. `5 / 2` is `2.5`. This means `/` does what you meant
in both cases without a second operator.

`based`, `cringe` and `ghosted` are `1`, `0` and `0`. There is no separate
boolean type — anything non-zero and non-empty is true.

### Yaps

```text
stash greeting = "hello"
stash multi = "line one\nline two"
```

Escapes: `\n` `\t` `\r` `\\` `\"`, plus `{{` and `}}` for literal braces.
Yaps are immutable — `s[0] = "z"` is an error. See
[chapter 8](#8-yaps-in-detail) for the interesting part.

### Piles

```text
stash xs = [1, "two", [3]]
stash spread = [
    1,
    2,
]
```

Trailing commas are fine, and a pile can span lines.

### Bags

```text
stash player = {"name": "ana", "score": 0}
```

Labels may be maths or yaps; nothing else. Reading a label that is not there is
an error, so check first with `gotit`. `d.name` is shorthand for `d["name"]` —
identical in every position, so it reads and it assigns:

```text
player.score += 10
player.title = "champ"
cook(player.name)
```

### Truthiness

| value | true when |
|---|---|
| math | not zero |
| yap | not empty |
| pile | not empty |
| bag | not empty |
| chore | always |

### Values are copied

This is the rule that surprises people, so it gets its own heading. **Reading a
value copies it.** Passing one to a chore copies it. So a chore cannot reach
back and change what its caller holds:

```text
chore spoil(b) ong
    b.x = 99
bet

stash mine = {"x": 1}
spoil(mine)
cook(mine)
```

That prints `{"x": 1}`. The bag inside `spoil` was a copy. Return the new value,
or keep shared state in a closure — see [chapter 7](#7-chores).

The same applies between names:

```text
stash a = [1, 2]
stash b = a
b[0] = 9
cook(a)
```

`a` is still `[1, 2]`.

---

## 4. Names and scope

```text
stash x = 10      # declare
x = x + 1         # assign; the name must already exist
x += 1            # also -= *= /=
```

Assigning a name that was never `stash`ed is an error. That is deliberate: a
typo becomes a message instead of a silent new variable.

Several at once, from a pile:

```text
stash a, b = [1, 2]
a, b = [b, a]
```

The pile must have exactly as many things as there are names.

### Scope is lexical

A chore sees the scope it was **written** in, not the one it was called from.

```text
chore show() ong
    yeet secret
bet

chore caller() ong
    stash secret = 1
    yeet show()
bet
```

`caller()` fails with `'secret' is not defined`, which is the correct answer.
Under dynamic scoping it would print `1`, and every chore would be at the mercy
of whoever called it.

`stash` always declares in the current scope. Plain assignment walks outward to
wherever the name was declared — which is what lets a chore update state that
outlives it.

---

## 5. Expressions

### Operators

| kind | operators |
|---|---|
| arithmetic | `+` `-` `*` `/` `%` `^` |
| comparison | `==` `!=` `<` `>` `<=` `>=` |
| logic | `also` `orelse` `nah` |
| index | `xs[0]` `xs[-1]` `bag["label"]` `bag.label` |

Precedence, loosest binding first:

```
orelse  <  also  <  nah  <  comparison  <  + -  <  * / %  <  unary + -  <  ^  <  call / index
```

`^` is right-associative, so `2 ^ 3 ^ 2` is `512`, not `64`. Unary minus binds
looser than `^`, so `-2 ^ 2` is `-4` — the same as everywhere else.

`+` joins two yaps or two piles, and merges two bags with the right-hand side
winning. `*` repeats a yap or a pile by a whole math.

### Logic short-circuits

`also` and `orelse` only look at their right side when it can still change the
answer. That makes the standard guard safe:

```text
stash xs = []
fr howmany(xs) > 0 also xs[0] == 1 ong
    cook("found it")
bet
```

Both always give back `1` or `0`, never the operand.

### Lines

A newline ends a statement, and `;` does too. Inside `(`, `[` or `{` newlines
are ignored, so anything bracketed can spread out:

```text
stash total = smol(
    1,
    2 + 3,
    4
)
```

Comments run from `#` to end of line.

---

## 6. Control flow

```text
fr score > 10 ong
    cook("big")
orfr score > 5 ong
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

`grind` counts, or walks:

```text
grind i = 0 til 10 by 2 ong
    cook(i)
bet

grind word among ["a", "b"] ong
    cook(word)
bet

grind label, value among scores ong
    cook("{label}: {value}")
bet
```

Counting ranges are **end-exclusive**: `0 til 3` gives `0, 1, 2`. `by` defaults
to `1` and may be negative; `by 0` is an error rather than a hang.

`grind ... among` walks a pile, a yap one character at a time, or a bag's
labels. Two names walk a bag's label/value pairs, or unpack each element of a
pile of piles.

`bail` leaves the loop, `skip` starts the next turn. Both work in either loop
kind, and both are errors outside a loop.

---

## 7. Chores

```text
chore fib(n) ong
    fr n < 2 ong
        yeet n
    bet
    yeet fib(n - 1) + fib(n - 2)
bet
```

A chore with no `yeet` evaluates to its last statement. Recursion works. Call
depth is capped at 200, and hitting the cap is a catchable error rather than a
crash.

Chores are values — pass them, return them, stash them in a pile or a bag.

### Closures

A chore defined inside another captures the scope it was written in, and keeps
it alive:

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
cook(c())
cook(c())
```

That prints `1` then `2`. Two counters do not interfere — each call to
`counter()` makes its own `n`.

### Chores that take chores

```text
chore dbl(n) ong yeet n * 2 bet
chore odd(n) ong yeet n % 2 == 1 bet
chore add(a, b) ong yeet a + b bet

cook(eachof([1, 2, 3], dbl))
cook(keepif([1, 2, 3, 4], odd))
cook(smoosh([1, 2, 3, 4], add))
```

`sortof` takes an optional key chore, run once per item.

### Things that look like objects

There is no `class`. A chore that captures state and returns a bag of chores
does the same job, and dot access makes it read like one:

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

stash c = counter()
c.bump()
c.bump()
cook(c.peek())
```

Suffixes chain, so `c.bump()`, `fs[0]()`, `f()[0]` and `mk()()` all work.

Because values copy on pass, this closure-captured state is the *only* way to
share mutable state between chores. Handing a bag around will not do it.

---

## 8. Yaps in detail

`{...}` inside a yap evaluates and drops the result in:

```text
stash name = "ana"
stash scores = {"ana": 3}

cook("hi {name}, you have {scores[name]} points")
cook("{1 + 2} and {smol(9, 4)}")
```

Any expression works — arithmetic, calls, lookups, even another yap:
`"{"inner"}"` is fine, because the lexer tracks quoting and brace depth while
it reads the hole.

Yaps interpolate as their text; everything else as it would print. `{{` and
`}}` give literal braces. A hole holds exactly one expression — `{}` alone is
an error, and so is `{1; 2}`. Errors inside a hole point at the yap holding it.

A yap with no holes is an ordinary string token, so nothing pays for the
feature unless it uses it.

---

## 9. When things go wrong

Errors are values, not exceptions. Every stage returns a `(result, error)`
pair, and every error knows where it came from:

```text
Runtime Error: 'nope' is not defined
File prog.aura, line 3, col 14
      total += nope
               ^^^^
```

Inside chores you get a traceback as well, innermost call last.

### Catching

```text
chore safe_div(a, b) ong
    sus ong
        yeet a / b
    whoops e ong
        cook("nope: {e.why}")
        yeet 0
    bet
bet
```

The `whoops` name is bound to a bag with `why`, `kind`, `file` and `line`.

### Kinds

`kind` is a short slug, so you branch on it instead of matching the message:

| kind | when |
|---|---|
| `math` | `/ 0`, `% 0`, a power with no real answer, `by 0` |
| `name` | undefined name, or assigning to one |
| `index` | out of range, wrong index type, assigning into a yap |
| `label` | no such label in a bag, or a label that is not a math or yap |
| `type` | wrong type for an operator or a builtin |
| `arity` | wrong number of arguments |
| `flow` | `bail`/`skip` outside a loop, `yeet` outside a chore |
| `unpack` | destructuring the wrong shape |
| `depth` | recursion past the call cap |
| `file` | `slurp`, `spill`, `rummage` or `summon` could not do it |
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

### Raising

`oops` raises. A yap raises its text; anything else raises its printed form.

Everything the runtime throws is catchable — undefined names, bad indexes, even
runaway recursion. Syntax errors are not, because they happen before anything
runs. `yeet`, `bail`, `skip` and `bounce` pass straight through a `sus`
untouched: only errors are caught.

---

## 10. Programs

```bash
python aura.py                  # REPL
python aura.py prog.aura        # run a file
python aura.py prog.aura a b    # a and b land in handed()
python aura.py --tokens f.aura  # token stream
python aura.py --ast f.aura     # parse tree
python aura.py --help
```

A program reads its arguments with `handed()`, its files with `slurp`, and sets
its exit status with `bounce(code)`. `bounce` is not catchable — it means stop.

```text
stash targets = handed()

fr howmany(targets) == 0 ong
    cook("give me a file")
    bounce(2)
bet
```

`summon("lib.aura")` runs another file in the current scope, so its chores and
stashes land here. Paths resolve relative to the file doing the summoning, and
a cycle is reported rather than followed forever.

---

## 11. The standard library

42 builtins. They live in a scope every program inherits, so you can shadow one
if you insist.

**Talking and reading**

| chore | does |
|---|---|
| `cook(value)` | print a line, gives back `0` |
| `beg(prompt?)` | read a line as a yap |
| `slurp(path)` | read a whole file |
| `spill(path, text)` | write a file, replacing it |
| `dribble(path, text)` | append to a file |
| `isthere(path)` | `1` if it exists |
| `isfolder(path)` | `1` if it is a folder |
| `rummage(path?)` | sorted names in a folder, defaulting to here |
| `stitch(part, ...)` | join path parts with `/` |
| `summon(path)` | run another file here |
| `handed()` | the program's arguments |
| `bounce(code?)` | stop, with an exit status |

**Anything**

| chore | does |
|---|---|
| `howmany(value)` | length of a yap, pile or bag |
| `whatis(value)` | type name as a yap |
| `yapify(value)` | anything to a yap |
| `mathify(value)` | a yap to a math, or an error |
| `is_math` `is_yap` `is_pile` `is_chore` | `1` or `0` |

**Maths**

| chore | does |
|---|---|
| `smol(a, ...)` / `smol(pile)` | smallest |
| `chonk(a, ...)` / `chonk(pile)` | biggest |
| `total(a, ...)` / `total(pile)` | sum |
| `absolutely(n)` | absolute value |
| `roundish(n, places?)` | round, half away from zero |

**Piles, yaps and bags**

| chore | does |
|---|---|
| `chunk(value, start?, stop?)` | slice; out-of-range bounds clamp |
| `flip(value)` | reversed |
| `where(value, needle)` | first index, or `-1` |
| `gotit(value, needle)` | `1` or `0`; on a bag, checks labels |
| `stuff(pile, value)` | new pile with `value` added |
| `yoink(pile, index)` | new pile without `index`; on a bag, drops a label |
| `sortof(pile, by?)` | sorted, optionally by a key chore |
| `glue(pile, separator?)` | join into a yap |
| `shred(yap, separator?)` | split into a pile |
| `shout` `whisper` `trim` | upper, lower, strip |
| `labels(bag)` `goods(bag)` | a bag's labels or values |
| `eachof(pile, chore)` | map |
| `keepif(pile, chore)` | filter |
| `smoosh(pile, chore, start?)` | fold |

Nothing mutates in place. To change a pile or bag where it stands, assign into
it: `xs[0] = 99`.

---

# Part II — the interpreter

Everything lives in `aura.py`, in pipeline order. Read it top to bottom and it
tells the whole story.

## 12. The pipeline

```
source text
   |  Lexer.make_tokens()
tokens
   |  Parser.parse()
AST
   |  Interpreter.visit()
values
```

### The rule that shapes everything

**Errors are returned, never raised.** Every stage hands back a pair:

```python
tokens, error = lexer.make_tokens()
```

The parser and interpreter wrap that pair in `ParseResult` and `RTResult` so it
can ride along with a value:

```python
node = res.register(self.expr())
if res.error:
    return res
```

`register` unwraps a child result and absorbs its error; the caller checks once
and returns early. Keep this shape when you add anything. A stray `raise` skips
every position-tracking and traceback mechanism in the file.

The two deliberate exceptions are `RecursionError`, caught once in `run()` as a
safety net, and `BounceError`, which unwinds like an error precisely so that
nothing catches it.

### Positions

`Position` carries index, line, column, the filename, and `ftxt` — the whole
source text. Every token, node and value carries `pos_start` / `pos_end`. That
is the only reason an error can say `line 4, col 12` *and* print the line with
a caret under it: `Error.excerpt()` slices `ftxt` using those positions.

When you build a node, thread the positions through. When you build a value,
`set_pos` it, or its errors will point at nothing.

---

## 13. The lexer

A character loop with one `make_*` method per multi-character token.

- `make_number` — digits and dots, rejecting `1.5.5` as a malformed literal
- `make_identifier` — a word becomes `TT_KEYWORD` if it is in `KEYWORDS`,
  otherwise `TT_IDENTIFIER`. That list is the entire vocabulary.
- `make_string` — escapes, and `{...}` holes. When a yap has holes it becomes a
  `TT_FSTRING` carrying a list of `('text', ...)` / `('code', ...)` segments;
  without holes it stays a plain `TT_STRING`, so nothing pays for the feature.
- `read_interpolation` — reads to the matching `}`, tracking brace depth and
  quoting so `{d["a"]}` and `{"inner"}` both work.
- `make_maybe_eq` — one method for every operator with an `=` form: `!=`, `>=`,
  `+=`, and friends.

Two details that are easy to miss:

`;` and newline both produce `TT_NEWLINE`, so statement separation costs the
parser nothing. And the lexer tracks bracket depth: inside `(`, `[` or `{` a
newline produces no token at all, which is what makes implicit line joining
work.

---

## 14. The parser

Recursive descent, one method per precedence level, loosest at the top:

```
statements -> statement -> expr -> and_expr -> not_expr -> comp_expr
           -> arith_expr -> term -> factor -> power -> atom
```

`bin_op(func, ops)` builds every left-associative level. Pass `right=` for a
right-associative one — that is how `^` works. Operators match by token type,
or by `(TT_KEYWORD, 'also')` tuples for word operators.

`statement()` dispatches the keyword forms — `fr`, `keep`, `grind`, `chore`,
`stash`, `sus`, `oops`, `yeet`, `bail`, `skip` — then falls through to
parsing an expression. If an `=` or `+=` follows that expression,
`assignment()` decides what it was:

- a `VarAccessNode` becomes a `VarAssignNode`
- an `IndexNode` becomes an `IndexAssignNode`
- anything else is a syntax error

Compound assignment desugars: `x += 1` is built as `x = x + 1`. Dot access
desugars too: `d.name` becomes exactly the `IndexNode` that `d["name"]` builds,
which is why assignment, compound assignment and calls through a dot all work
without another line of interpreter code.

`postfix_result` runs one loop over trailing `[index]` and `(call)` suffixes,
so any chain works: `d.go()`, `fs[0]()`, `f()[0]`, `mk()()`.

Blocks are `statements(stop_keywords)`. Every block form passes the keywords
that may legally end it, then checks for `bet` itself.

---

## 15. Values at runtime

`Value` is the base. Every operation — `added_to`, `compare_lt`, `get_index`,
`length` — defaults to an illegal-operation error, so a new type overrides only
what it supports and touches no interpreter code. Each subclass sets
`TYPE_NAME`, which is the word error messages use.

`Number`, `String`, `List`, `Bag`, and `BaseFunction` (→ `Function`,
`BuiltInFunction`) live here. Operations return `(value, error)`, the same
shape as everything else.

`Bag` keys its Python dict on `('math', 3)` / `('yap', 'a')` tuples, so maths
and yaps can both be labels without colliding, and keeps the original key
`Value` beside each entry so `labels()` and `repr` can hand it back.

Values copy on read, which is where the language's value semantics come from.
`IndexAssignNode` is the deliberate exception: it resolves the *live* container
through `resolve_container`, because a write to a copy would land nowhere.

---

## 16. The interpreter

`visit(node)` dispatches to `visit_<NodeName>` by class name. No node type
needs registering; the method name is the wiring.

### Scopes

`SymbolTable` chains to a parent. `set` declares locally; `set_existing` walks
outward to assign where a name was declared. That split is the whole of
`stash`-versus-assignment.

A `Function` captures its defining scope and parents each call on that. That is
what makes scoping lexical, and closures fall out of it for free.

### Control flow

`RTResult` carries `func_return_value`, `loop_should_break` and
`loop_should_continue` beside the value and error. `should_return()` tells a
statement list to stop. Loops consume and clear the loop signals.
`Function.execute` consumes the return signal and clears all three, so nothing
escapes a call — which is why `bail` inside a chore called from a loop cannot
break the caller's loop.

`loop_depth` and `func_depth` make `bail` outside a loop and `yeet` outside a
chore real errors, and cap recursion at `MAX_CALL_DEPTH`.

### Incomplete input

`wants_more(filename, text)` lexes and parses without running, and reports
whether the input failed only because it stopped early. That is what lets the
REPL keep reading a half-typed block. Parse errors are judged by position — did
it fail at the very end? Lexer errors carry an explicit `incomplete` flag,
because an unterminated yap reports at its opening quote, not at the end.

---

## 17. Extending it

Most language features touch four places, in this order:

1. **Lexer** — a token type, plus a `make_*` method if it is multi-character
2. **Parser** — an AST node class, and a grammar method or precedence level
3. **Interpreter** — a `visit_<NodeName>` method
4. **Tests** — one per stage you touched

### A new builtin

The smallest change there is. Write a function taking `(args, node)` and
returning `(value, error)`, then add one row to `BUILTINS`:

```python
def bi_shouty(args, node):
    error = _need(node, args[0], String, 'yap', 'shouty')
    if error:
        return None, error
    return String(args[0].value.upper() + '!'), None
```

```python
'shouty': (['yap'], bi_shouty),
```

Argument names carry prefixes: `?name` is optional and arrives as `None`,
`*name` soaks up any number more. A builtin that needs the interpreter itself
goes in `NEEDS_INTERPRETER` and receives it as a third argument — that is how
`summon` runs a file in the caller's scope, and how `eachof` calls back into
aura code.

Then add the name to `editors/vscode/syntaxes/aura.tmLanguage.json`; a test
compares the grammar against the real lists and fails if you forget.

### A new value type

Subclass `Value`, set `TYPE_NAME`, override the operations it supports. Nothing
in the interpreter changes.

### A new error

Construct `RTError(pos_start, pos_end, message, kind='...')` with a kind from
`RTError.KINDS`. A test walks `aura.py`'s own AST and fails if any `RTError` is
built without one.

### House rules

- Plain classes, no frameworks, no new dependencies
- Errors returned, never raised
- Type names in messages are dialect (`math`, `yap`); the sentence around them
  is plain English, so errors stay readable
- Update [LANGUAGE.md](LANGUAGE.md) in the same commit if behaviour changed

---

# Appendices

## A. Grammar

```
statements  := NEWLINE* statement (NEWLINE+ statement)* NEWLINE*

statement   := 'stash' IDENT (',' IDENT)* '=' expr
             | 'fr' expr 'ong' statements
                 ('orfr' expr 'ong' statements)*
                 ('whatever' statements)? 'bet'
             | 'keep' expr 'ong' statements 'bet'
             | 'grind' IDENT '=' expr 'til' expr ('by' expr)? 'ong' statements 'bet'
             | 'grind' IDENT (',' IDENT)* 'among' expr 'ong' statements 'bet'
             | 'chore' IDENT '(' (IDENT (',' IDENT)*)? ')' 'ong' statements 'bet'
             | 'sus' 'ong' statements 'whoops' IDENT 'ong' statements 'bet'
             | 'oops' expr
             | 'yeet' expr?
             | 'bail' | 'skip'
             | expr (('=' | '+=' | '-=' | '*=' | '/=') expr)?

expr        := and_expr ('orelse' and_expr)*
and_expr    := not_expr ('also' not_expr)*
not_expr    := 'nah' not_expr | comp_expr
comp_expr   := arith_expr (('==' | '!=' | '<' | '>' | '<=' | '>=') arith_expr)*
arith_expr  := term (('+' | '-') term)*
term        := factor (('*' | '/' | '%') factor)*
factor      := ('+' | '-') factor | power
power       := atom ('^' factor)*

atom        := MATH | YAP | FSTRING
             | 'based' | 'cringe' | 'ghosted'
             | IDENT | '(' expr ')' | pile | bag
             ,  each followed by any number of suffixes

suffix      := '[' expr ']' | '(' args ')' | '.' IDENT
pile        := '[' (expr (',' expr)* ','?)? ']'
bag         := '{' (expr ':' expr (',' expr ':' expr)* ','?)? '}'
```

## B. Keywords

24 words, and they are the whole vocabulary.

```
stash   fr      ong     orfr    whatever  bet
keep    chore   also    orelse  nah       based
cringe  ghosted grind   til     by        among
bail    skip    yeet    sus   whoops    oops
```

## C. Builtins

```
absolutely  beg       bounce    chonk     chunk     dribble
eachof      flip      glue      goods     gotit     handed
howmany     is_chore  is_math   is_pile   is_yap    isfolder
isthere     keepif    labels    mathify   roundish  rummage
shout       shred     slurp     smol      smoosh    sortof
spill       stitch    stuff     summon    total     trim
whatis      where     whisper   yap       yapify    yoink
```

## D. Error kinds

`arity` · `custom` · `depth` · `file` · `flow` · `index` · `label` · `math` ·
`name` · `runtime` · `type` · `unpack`

`runtime` is the default and should be rare — every error site names something
more specific.

## E. If you know Python

Things that will trip you up:

| Python | aura |
|---|---|
| `4 / 2` is `2.0` | `4 / 2` is `2`, `5 / 2` is `2.5` |
| assignment creates a variable | assignment requires `stash` first |
| `def` closes over variables | so does `chore`, but arguments are **copies** |
| a function can mutate a passed list | it cannot; return the new value |
| `x and y` gives back `y` | `x also y` gives back `1` or `0` |
| `round(2.5)` is `2` | `roundish(2.5)` is `3` |
| indentation defines blocks | `ong` and `bet` do; indentation is decoration |
| exceptions | `(result, error)` pairs, and `sus`/`whoops` on top |

And the one that catches everyone: `for i in range(3)` is
`grind i = 0 til 3 ong ... bet`, end-exclusive, same as Python.

---

## Credit

aura was created by **Vijay Biradar** (iam-kira), and is released under the MIT Licence. Use it,
change it, sell it — but the copyright notice travels with every copy.
