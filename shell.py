"""The aura REPL.

Copyright (c) 2026 iam-kira (Vijay Biradar)
Licensed under the MIT License. See LICENSE for the full text.
"""

import aura

PROMPT = 'shell :> '
CONTINUED = '   ...  > '
QUIT_WORDS = ('quit', 'exit', ':q')

HELP = """aura - a language with regrettable keywords

  stash x = 1        declare            chore f(a) ong ... bet     define
  x = 2              assign             yeet v                     return
  fr c ong           if                 cook(v)                    print
  orfr c ong         else if            grind i = 0 til 3 ong      count
  whatever           else               grind x among xs ong       walk
  keep c ong         while              sus ong ... whoops e ong   try / catch
  bet                closes any block   bail / skip                break / continue

  types    math   yap   pile   bag   chore   ghosted
  values   based  cringe  ghosted        ("{x}" interpolates)

at this prompt:
  help       this            builtins   list every built-in chore
  clear      clear screen    exit       leave (or ctrl-d)

a block keeps prompting with '...  >' until it closes; a blank line ends it,
and ctrl-c throws away what you were typing.

full reference: docs/BOOK.md
"""


def show_builtins():
    """The built-in chores, in columns, because there are a lot of them."""
    names = sorted(aura.BUILTINS)
    width = max(len(n) for n in names) + 2
    per_row = max(1, 76 // width)

    print('%d built-in chores:' % len(names))
    for i in range(0, len(names), per_row):
        print('  ' + ''.join(n.ljust(width) for n in names[i:i + per_row]).rstrip())
    print("\ncall one with brackets, e.g. cook(\"hi\") or howmany([1, 2])")


def clear_screen():
    import os
    os.system('cls' if os.name == 'nt' else 'clear')


def show(result):
    """Echo a statement's value the way the REPL does: repr, so "1" and 1 differ."""
    if result is None:
        return
    for value in (result if isinstance(result, list) else [result]):
        print(repr(value))


def main(symbol_table=None):
    table = aura.global_symbol_table if symbol_table is None else symbol_table
    buffer = []

    while True:
        try:
            line = input(CONTINUED if buffer else PROMPT)
        except KeyboardInterrupt:
            if buffer:
                buffer = []
                print('\nDropped that.')
            else:
                print("\nInterrupted. Type 'exit' to quit.")
            continue
        except EOFError:
            print('\nbye!')
            return 0

        if not buffer:
            clean = line.strip()
            if not clean:
                continue
            # a name you defined always wins over a shell convenience
            shadowed = aura.global_symbol_table.exists(clean)

            if clean.lower() == 'help' and not shadowed:
                print(HELP, end='')
                continue

            if clean.lower() == 'builtins' and not shadowed:
                show_builtins()
                continue

            if clean.lower() == 'clear' and not shadowed:
                clear_screen()
                continue

            if clean.lower() in QUIT_WORDS:
                print('bye!')
                return 0

        buffer.append(line)
        source = '\n'.join(buffer)

        # a blank line forces the block to end, so a typo cannot trap you
        if line.strip() and aura.wants_more('<stdin>', source):
            continue
        buffer = []

        result, error = aura.run('<stdin>', source, table)

        if isinstance(error, aura.BounceError):
            return error.code
        if error:
            print(error.as_string())
        else:
            show(result)


if __name__ == '__main__':
    raise SystemExit(main())
