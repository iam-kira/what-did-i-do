"""Build a standalone aura executable - no Python needed to run it.

Copyright (c) 2026 iam-kira (Vijay Biradar)
Licensed under the MIT License. See LICENSE for the full text.

    pip install pyinstaller
    python build_exe.py

Produces build-exe/aura (or aura.exe on Windows): one file, no installer, no
runtime. Copy it anywhere and run it.
"""

import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'build-exe')
TMP = os.path.join(HERE, 'build-tmp')


def main():
    try:
        import PyInstaller  # noqa: F401
    except ImportError:
        print('PyInstaller is missing. Install it with:\n\n    pip install pyinstaller')
        return 1

    command = [
        sys.executable, '-m', 'PyInstaller',
        '--onefile',              # one file, not a folder of parts
        '--name', 'aura',
        '--console',              # it is a REPL; it needs a terminal
        '--clean',
        '--noconfirm',
        '--distpath', OUT,
        '--workpath', TMP,
        '--specpath', TMP,
        os.path.join(HERE, 'aura.py'),
    ]

    print('building a standalone aura...')
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    if result.returncode != 0:
        sys.stdout.write(result.stdout.decode('utf-8', 'replace')[-2000:])
        return result.returncode

    shutil.rmtree(TMP, ignore_errors=True)

    name = 'aura.exe' if os.name == 'nt' else 'aura'
    binary = os.path.join(OUT, name)
    size = os.path.getsize(binary) / (1024 * 1024)

    print('\nbuilt %s (%.1f MB)' % (binary, size))
    print('\nit needs nothing installed. try:')
    print('    %s --version' % binary)
    print('    %s example.aura' % binary)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
