import shit

while True:
    try:
        text = input("shell :> ")
    except KeyboardInterrupt:
        print("\nInterrupted. Type 'exit' to quit.")
        continue
    except EOFError:
        print("\nbye!")
        break

    clean = text.strip()
    if not clean:
        continue

    if clean.lower() in ('quit', 'exit', ':q'):
        print('bye!')
        break

    result, error = shit.run('<stdin>', text)

    if error:
        print(error.as_string())
    elif result is not None:
        if isinstance(result, list):
            for value in result:
                print(value)
        else:
            print(result)
