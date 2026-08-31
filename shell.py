"""The aura REPL.

Kept so `python shell.py` still works. The REPL itself lives in aura.py, so a
published package ships one module rather than claiming the name `shell`.

Copyright (c) 2026 iam-kira (Vijay Biradar)
Licensed under the MIT License. See LICENSE for the full text.
"""

from aura import repl

main = repl   # the old name, for anything that imported it

if __name__ == '__main__':
    raise SystemExit(repl())
