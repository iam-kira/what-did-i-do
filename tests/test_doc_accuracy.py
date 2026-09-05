"""The docs must describe the language that actually exists.

test_docs.py proves the examples run. This proves the prose is not describing
some earlier version of aura - a keyword nobody documented, a builtin that was
renamed, or a count that drifted.

Copyright (c) 2026 iam-kira (Vijay Biradar)
Licensed under the MIT License. See LICENSE for the full text.
"""

import os
import re

import aura

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DOCS = ['README.md', 'CONTRIBUTING.md', os.path.join('editors', 'README.md'),
        os.path.join('docs', 'BOOK.md'), os.path.join('docs', 'LANGUAGE.md'),
        os.path.join('docs', 'ARCHITECTURE.md'), os.path.join('docs', 'README.md')]

# words the language used to use, which must never reappear in the docs
RETIRED = ['risky', 'shit']


def read(name):
    with open(os.path.join(REPO, name), encoding='utf-8') as handle:
        return handle.read()


def reference():
    """The two documents that claim to be complete."""
    return read(os.path.join('docs', 'BOOK.md')) + read(os.path.join('docs', 'LANGUAGE.md'))


def test_every_keyword_is_documented():
    body = reference()
    missing = [kw for kw in aura.KEYWORDS if not re.search(r'\b%s\b' % re.escape(kw), body)]
    assert not missing, 'keywords the reference never mentions: %s' % missing


def test_every_builtin_is_documented():
    body = reference()
    missing = [name for name in aura.BUILTINS if not re.search(r'\b%s\b' % re.escape(name), body)]
    assert not missing, 'builtins the reference never mentions: %s' % missing


def test_no_document_mentions_a_retired_word():
    offenders = []
    for name in DOCS:
        body = read(name)
        for word in RETIRED:
            if re.search(r'\b%s\b' % word, body, re.IGNORECASE):
                offenders.append('%s mentions "%s"' % (name, word))
    assert not offenders, offenders


def test_no_document_calls_yap_as_a_function():
    """yap is the string type; cook is the one that prints."""
    offenders = [name for name in DOCS if re.search(r'\byap\(', read(name))]
    assert not offenders, '%s uses yap( where it means cook(' % offenders


def test_stated_counts_match_reality():
    joined = '\n'.join(read(name) for name in DOCS)
    wrong = []

    for claimed in re.findall(r'(\d+)[- ](?:builtins|function standard library)', joined):
        if int(claimed) != len(aura.BUILTINS):
            wrong.append('claims %s builtins, actual %d' % (claimed, len(aura.BUILTINS)))

    for claimed in re.findall(r'(\d+) keywords', joined):
        if int(claimed) != len(aura.KEYWORDS):
            wrong.append('claims %s keywords, actual %d' % (claimed, len(aura.KEYWORDS)))

    assert not wrong, wrong


def test_every_error_kind_is_documented():
    body = reference()
    # 'runtime' is the fallback and deliberately has no table row
    missing = [k for k in aura.RTError.KINDS - {'runtime'}
               if not re.search(r'`%s`' % k, body)]
    assert not missing, 'error kinds the reference never mentions: %s' % missing


def test_the_docs_point_at_files_that_exist():
    """Ignores illustrative names like prog.aura that are examples, not files."""
    placeholders = {'prog.aura', 'lib.aura', 'f.aura', 'double.aura', 'app.aura',
                    'other.aura', 'notes.txt', 'bad.aura', 'p.aura'}
    missing = []

    for name in DOCS:
        folder = os.path.dirname(name)
        for target in set(re.findall(r'\b[\w./-]+\.(?:aura|py|json|yml)\b', read(name))):
            if target in placeholders or target.startswith(('http', 'source.')):
                continue
            if 'github.com' in target:   # badge URLs, not local paths
                continue
            options = [os.path.join(REPO, target), os.path.join(REPO, folder, target)]
            if not any(os.path.exists(o) for o in options):
                missing.append('%s -> %s' % (name, target))

    assert not missing, missing
