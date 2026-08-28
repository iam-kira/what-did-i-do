# Editor support

## VS Code

Syntax highlighting for `.aura` files: keywords, builtins, yaps with their
`{holes}`, comments, numbers, and chore names. Also gives `#` comment toggling,
bracket matching, and `ong`/`bet` indentation.

Install it locally by symlinking (or copying) the folder into your extensions
directory, then reloading VS Code:

```bash
# macOS / Linux
ln -s "$PWD/editors/vscode" ~/.vscode/extensions/aura-lang

# Windows (PowerShell, as administrator)
New-Item -ItemType SymbolicLink -Path "$env:USERPROFILE\.vscode\extensions\aura-lang" -Target "$PWD\editors\vscode"
```

It is not published to the marketplace, and does not need to be — the grammar
is one file.

## Anything else

`editors/vscode/syntaxes/aura.tmLanguage.json` is a standard TextMate grammar,
so Sublime Text, Zed, and anything else that speaks TextMate can use it
directly.
