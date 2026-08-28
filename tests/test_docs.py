"""Every aura snippet in the docs has to actually run.

Docs drift silently; this makes them fail loudly instead.

The convention: a ```text fence holds runnable aura, so it gets executed here.
Notation - grammars, pipeline diagrams, word listings - uses a bare fence.
"""

import io
import os
import re

import aura

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# every markdown file in the repo root and docs/, so a new one is covered by default
DOCS = ['README.md', 'CONTRIBUTING.md'] + sorted(
    os.path.join('docs', name)
    for name in os.listdir(os.path.join(REPO, 'docs'))
    if name.endswith('.md')
)

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
        table = aura.new_symbol_table()
        # snippets often reference names a nearby paragraph set up
        for helper in ('stash x = 7', 'stash n = 3', 'stash name = "ana"',
                       'stash scores = {"ana": 3}', 'stash xs = [1, 2, 3]',
                       'chore lastchar(s) ong yeet s[-1] bet',
                       'chore bounds() ong yeet [1, 9] bet',
                       'stash grid = [[1, 2], [3, 4]]', 'stash i = 0',
                       'stash b = {"x": 1}',
                       'stash path = "no-such-file.txt"',
                       'stash player = {"name": "ana", "score": 0}',
                       'stash score = 7', 'stash n = 3', 'stash count = 0',
                       'stash scores = {"ana": 3}'):
            aura.run('<setup>', helper, table)

        _, error = aura.run(f'{name}#{index}', block, table)
        if isinstance(error, aura.BounceError):
            continue  # a snippet showing bounce() is behaving correctly
        if error:
            failures.append(f'{name} snippet {index}: {error.details}\n{block.strip()[:200]}')

    assert not failures, '\n\n'.join(failures)
