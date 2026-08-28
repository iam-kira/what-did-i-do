import shit

PROMPT = 'shell :> '
CONTINUED = '   ...  > '


def main():
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
            return

        if not buffer:
            clean = line.strip()
            if not clean:
                continue
            if clean.lower() in ('quit', 'exit', ':q'):
                print('bye!')
                return

        buffer.append(line)
        source = '\n'.join(buffer)

        # a blank line forces the block to end, so a typo cannot trap you
        if line.strip() and shit.wants_more('<stdin>', source):
            continue
        buffer = []

        result, error = shit.run('<stdin>', source)

        if error:
            print(error.as_string())
        elif result is not None:
            # repr, so a string echoes as "1" and a number as 1
            if isinstance(result, list):
                for value in result:
                    print(repr(value))
            else:
                print(repr(result))


main()
