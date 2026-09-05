"""Render docs/demo.svg - the terminal shot at the top of the README.

Copyright (c) 2026 iam-kira (Vijay Biradar)
Licensed under the MIT License. See LICENSE for the full text.

    python build_demo.py

Every line of output in the image is produced by actually running the line
through aura, so the picture cannot drift away from the language. A static
SVG, so it renders on GitHub and on PyPI without a proxy stripping anything.
"""

import html
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import aura

OUT = os.path.join(HERE, 'docs', 'demo.svg')

SESSION = [
    'stash squad = ["ana", "bo", "cy"]',
    '"we have {howmany(squad)} in the {squad[0]} era"',
    'eachof(squad, howmany)',
    'chore add(a, b) ong yeet a + b bet',
    'smoosh(eachof(squad, howmany), add)',
    '1 + ghosted',
]

# terminal palette
BG, CHROME = '#16181d', '#22252c'
PROMPT, INPUT, OUTPUT, ERROR, DIM = '#7ee787', '#e6edf3', '#79c0ff', '#ff7b72', '#6e7681'

FONT = ('ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, '
        '"Liberation Mono", monospace')
LINE = 22          # line height
PAD = 22           # inner padding
TOP = 46           # window chrome height
WIDTH = 780


def evaluate():
    """Run the session for real and pair each line with what aura said."""
    table = aura.new_symbol_table()
    rows = []

    for source in SESSION:
        rows.append((PROMPT, aura.PROMPT + source))
        result, error = aura.run('<stdin>', source, table)

        if error:
            for line in error.as_string().strip().splitlines():
                rows.append((ERROR, line))
            continue

        if isinstance(result, list):
            result = result[-1] if result else None
        if result is None or isinstance(result, aura.Nothing):
            continue
        text = repr(result)
        if text not in ('', 'ghosted'):
            rows.append((OUTPUT, text))

    return rows


def render(rows):
    height = TOP + PAD + len(rows) * LINE + PAD
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" '
        'viewBox="0 0 %d %d" font-family=\'%s\' font-size="14">'
        % (WIDTH, height, WIDTH, height, FONT),
        '<rect width="%d" height="%d" rx="10" fill="%s"/>' % (WIDTH, height, BG),
        '<path d="M0 10a10 10 0 0 1 10-10h760a10 10 0 0 1 10 10v26H0z" fill="%s"/>'
        % CHROME,
    ]

    for i, colour in enumerate(('#ff5f57', '#febc2e', '#28c840')):
        parts.append('<circle cx="%d" cy="18" r="6" fill="%s"/>' % (22 + i * 20, colour))

    parts.append('<text x="%d" y="23" fill="%s" font-size="12">%s</text>'
                 % (WIDTH // 2 - 34, DIM, html.escape(aura.BANNER.split(' - ')[0])))

    y = TOP + PAD + 4
    for colour, text in rows:
        parts.append('<text x="%d" y="%d" fill="%s" xml:space="preserve">%s</text>'
                     % (PAD, y, colour, html.escape(text)))
        y += LINE

    parts.append('</svg>')
    return '\n'.join(parts)


def main():
    rows = evaluate()
    with open(OUT, 'w', encoding='utf-8') as handle:
        handle.write(render(rows))
    print('wrote %s (%d lines)' % (OUT, len(rows)))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
