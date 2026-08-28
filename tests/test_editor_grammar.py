"""The VS Code grammar lists keywords and builtins by hand, so it drifts.

These tests fail the moment the language grows a word the grammar has not
heard of, or the grammar keeps one the language dropped.
"""

import json
import os
import re

import shit

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GRAMMAR = os.path.join(REPO, 'editors', 'vscode', 'syntaxes', 'shit.tmLanguage.json')


def load():
    with open(GRAMMAR, encoding='utf-8') as handle:
        return json.load(handle)


def words_in(pattern):
    """Pull the alternatives out of a \\b(a|b|c)\\b style match."""
    inner = re.search(r'\(([^)]*)\)', pattern)
    assert inner, pattern
    return set(inner.group(1).split('|'))


def collect(node, found):
    if isinstance(node, dict):
        for key, value in node.items():
            if key in ('match', 'begin', 'end') and isinstance(value, str):
                found.append(value)
            else:
                collect(value, found)
    elif isinstance(node, list):
        for item in node:
            collect(item, found)
    return found


def test_grammar_is_valid_json_with_compilable_patterns():
    for pattern in collect(load(), []):
        re.compile(pattern)


def test_grammar_knows_every_keyword():
    patterns = collect(load()['repository']['keyword'], [])
    highlighted = set()
    for pattern in patterns:
        highlighted |= words_in(pattern)

    missing = set(shit.KEYWORDS) - highlighted
    extra = highlighted - set(shit.KEYWORDS)

    assert not missing, f'grammar does not highlight: {sorted(missing)}'
    assert not extra, f'grammar highlights words the language dropped: {sorted(extra)}'


def test_grammar_knows_every_builtin():
    highlighted = words_in(load()['repository']['builtin']['match'])

    missing = set(shit.BUILTINS) - highlighted
    extra = highlighted - set(shit.BUILTINS)

    assert not missing, f'grammar does not highlight: {sorted(missing)}'
    assert not extra, f'grammar highlights builtins that do not exist: {sorted(extra)}'


def test_extension_declares_the_shit_extension():
    with open(os.path.join(REPO, 'editors', 'vscode', 'package.json'), encoding='utf-8') as handle:
        package = json.load(handle)

    language = package['contributes']['languages'][0]
    assert language['extensions'] == ['.shit']
    assert package['contributes']['grammars'][0]['scopeName'] == load()['scopeName']


def test_language_configuration_matches_the_block_words():
    path = os.path.join(REPO, 'editors', 'vscode', 'language-configuration.json')
    with open(path, encoding='utf-8') as handle:
        config = json.load(handle)

    rules = config['indentationRules']
    assert 'ong' in rules['increaseIndentPattern']
    for word in ('bet', 'whatever', 'orfr', 'whoops'):
        assert word in rules['decreaseIndentPattern'], word
        assert word in shit.KEYWORDS, word
