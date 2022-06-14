import shit


while True:
    text = input("shit :> ")
    result, error = shit.run('<stdin>', text)
    
    if error: print(error.as_string())
    else: print(result)