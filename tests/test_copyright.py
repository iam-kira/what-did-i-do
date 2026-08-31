"""Every source file carries a copyright notice.

Copyright (c) 2026 iam-kira (Vijay Biradar)
Licensed under the MIT License. See LICENSE for the full text.

A notice that covers most files is a notice nobody trusts. This keeps the
coverage at all of them, so a new file cannot ship without one.
"""

import glob
import os

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

HOLDER = 'iam-kira (Vijay Biradar)'
YEAR = '2026'


def sources():
    """Every file that ships or is part of the project's source."""
    patterns = ('*.py', '*.aura', 'tests/*.py', 'examples/*.aura')
    for pattern in patterns:
        for path in glob.glob(os.path.join(REPO, pattern)):
            yield path


def head(path, limit=500):
    with open(path, encoding='utf-8') as handle:
        return handle.read(limit)


def test_there_are_sources_to_check():
    assert len(list(sources())) >= 30


def test_every_source_file_carries_a_notice():
    missing = [os.path.relpath(p, REPO) for p in sources() if 'Copyright' not in head(p)]
    assert not missing, 'no copyright notice in: %s' % missing


def test_every_notice_names_the_holder_and_year():
    wrong = []
    for path in sources():
        text = head(path)
        if HOLDER not in text or YEAR not in text:
            wrong.append(os.path.relpath(path, REPO))
    assert not wrong, 'notice does not name %s %s in: %s' % (YEAR, HOLDER, wrong)


def test_every_notice_points_at_the_licence():
    silent = []
    for path in sources():
        if 'LICENSE' not in head(path):
            silent.append(os.path.relpath(path, REPO))
    assert not silent, 'notice does not reference LICENSE in: %s' % silent


def test_the_licence_and_notice_files_exist_and_agree():
    for name in ('LICENSE', 'NOTICE'):
        path = os.path.join(REPO, name)
        assert os.path.exists(path), '%s is missing' % name

        with open(path, encoding='utf-8') as handle:
            text = handle.read()
        assert HOLDER in text, '%s does not name the copyright holder' % name
        assert YEAR in text, '%s does not carry the year' % name


def test_the_notice_records_that_there_are_no_dependencies():
    """A NOTICE that lies about third-party code is worse than none."""
    with open(os.path.join(REPO, 'NOTICE'), encoding='utf-8') as handle:
        notice = handle.read()

    assert 'no runtime dependencies' in notice
    assert 'standard library' in notice
