import shit

PROMPT = 'shell :> '
CONTINUED = '   ...  > '
QUIT_WORDS = ('quit', 'exit', ':q')


def show(result):
    """Echo a statement's value the way the REPL does: repr, so "1" and 1 differ."""
    if result is None:
        return
    for value in (result if isinstance(result, list) else [result]):
        print(repr(value))


def main(symbol_table=None):
    table = shit.global_symbol_table if symbol_table is None else symbol_table
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
            if clean.lower() in QUIT_WORDS:
                print('bye!')
                return 0

        buffer.append(line)
        source = '\n'.join(buffer)

        # a blank line forces the block to end, so a typo cannot trap you
        if line.strip() and shit.wants_more('<stdin>', source):
            continue
        buffer = []

        result, error = shit.run('<stdin>', source, table)

        if isinstance(error, shit.BounceError):
            return error.code
        if error:
            print(error.as_string())
        else:
            show(result)


if __name__ == '__main__':
    raise SystemExit(main())
