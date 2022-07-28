import shit

while True:
    text = input("shell :> ")
    result, error = shit.run('<stdin>', text)
    
    if error: print(error.as_string())
    else: print(result)
