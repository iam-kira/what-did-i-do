"""Every shit snippet in the docs has to actually run.

Docs drift silently; this makes them fail loudly instead.
"""

import io
import os
import re

import shit

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS = ['README.md', 'CONTRIBUTING.md', os.path.join('docs', 'LANGUAGE.md'),
        os.path.join('docs', 'ARCHITECTURE.md'), os.path.join('docs', 'README.md')]

FENCE = re.compile(r'```text\n(.*?)```', re.DOTALL)

# Snippets that are output transcripts or deliberate fragments, not programs.
SKIP_MARKERS = ('shell :>', 'Traceback (most recent call last):', 'File ',
                'statements ->', '# everything:', 'source text')


def snippets():
    for name in DOCS:
        path = os.path.join(REPO, name)
        text = io.open(path, encoding='utf-8').read()
        for i, block in enumerate(FENCE.findall(text)):
            if any(marker in block for marker in SKIP_MARKERS):
                continue
            if not block.strip():
                continue
            yield name, i, block


def test_there_are_snippets_to_check():
    assert len(list(snippets())) >= 8


def test_every_doc_snippet_runs():
    failures = []

    for name, index, block in snippets():
        table = shit.new_symbol_table()
        # snippets often reference names a nearby paragraph set up
        for helper in ('stash x = 7', 'stash n = 3', 'stash name = "ana"',
                       'stash scores = {"ana": 3}', 'stash xs = [1, 2, 3]',
                       'chore lastchar(s) ong yeet s[-1] bet',
                       'chore bounds() ong yeet [1, 9] bet',
                       'stash grid = [[1, 2], [3, 4]]', 'stash i = 0',
                       'stash b = {"x": 1}'):
            shit.run('<setup>', helper, table)

        _, error = shit.run(f'{name}#{index}', block, table)
        if error:
            failures.append(f'{name} snippet {index}: {error.details}\n{block.strip()[:200]}')

    assert not failures, '\n\n'.join(failures)
