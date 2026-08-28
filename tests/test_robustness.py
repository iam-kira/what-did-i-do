"""Nothing should ever escape as a Python exception.

Every failure mode in aura is a returned error with a position. If a Python
traceback reaches the user, that is a bug in the interpreter, not their program.
"""

import itertools
import random

import pytest

import aura

AWKWARD = [
    '', ' ', '\n\n', '#', '#only comment', ';;;', '()', '(', ')', '[', ']', '{', '}',
    '{}', '{,}', '[,]', '{:}', '{1:}', '{:1}', '"', '""', '"\\"', '"{"', '"}"', '"{{"',
    '1..', '.1', '1.2.3', '- ', '+', '*', '/', '%', '^', '**', '=', '==', '===',
    'stash', 'stash =', 'stash x', 'stash x =', 'x =', '= 1',
    'fr', 'fr ong', 'fr ong bet', 'fr 1 ong bet', 'whatever', 'orfr', 'bet',
    'keep', 'keep ong bet', 'grind', 'grind ong', 'grind x', 'grind x =',
    'grind x among', 'grind x among [] ong bet', 'chore', 'chore f', 'chore f(',
    'chore f() ong', 'chore f() ong bet', 'chore f(,) ong bet',
    'yeet', 'bail', 'skip', 'oops', 'sus', 'sus ong bet', 'whoops',
    'summon', 'summon()', 'summon("")',
    'yap', 'cook(', 'cook()', 'cook(,)', 'cook(1,)',
    '[][0]', '""[0]', '{}["a"]', '[1][1.5]', '[1]["a"]', '{}[[]]', '{}[{}]',
    '1[0]', '1()', 'based', 'cringe', 'ghosted', 'nah', 'also', 'orelse',
    'based also', 'nah nah nah 1',
    '1 / 0', '1 % 0', '0 ^ -1', '2 ^ 10000', '(0-8) ^ (1/3)',
    'howmany()', 'howmany(1,2)', 'smol()', 'chunk()', 'chunk([1], "a")',
    'sortof()', 'sortof([1], 1)', 'eachof()', 'eachof([1])', 'smoosh([])',
    'mathify("")', 'mathify(" ")', 'mathify("nan")',
    'yapify()', 'stuff([])', 'yoink([])', 'yoink([], 0)', 'glue(1)', 'shred(1)',
    'stash a, b = []', 'stash a, = [1]', 'a, b = 1', ', = 1',
    'grind a, b among {} ong bet', 'grind a, b among "ab" ong bet',
    '"{}"', '"{;}"', '"{1;2}"', '"{[}"',
    'x' * 500, '(' * 300 + '1' + ')' * 300, '[' * 100 + ']' * 100,
    '1 ' + '+ 1 ' * 500,
    'chore f() ong\nyeet f()\nbet\nf()',
    'keep based ong\nbail\nbet',
    'grind i = 0 til 1000000 ong\nbail\nbet',
]

PIECES = ['stash', 'x', '=', '1', '+', '(', ')', '[', ']', '{', '}', ':', ',',
          'fr', 'ong', 'bet', 'chore', 'yeet', 'grind', 'among', 'keep',
          '"a"', '"{x}"', 'yap', 'sus', 'whoops', 'oops', 'nah', 'also', '.', '$']


def run_quietly(source):
    """Run and return nothing; the point is that it must not raise."""
    aura.run('<robustness>', source, aura.new_symbol_table())


@pytest.mark.parametrize('source', AWKWARD, ids=range(len(AWKWARD)))
def test_awkward_input_returns_an_error_instead_of_raising(source):
    run_quietly(source)


def test_random_token_soup_never_raises():
    random.seed(1234)
    for _ in range(2000):
        pieces = [random.choice(PIECES) for _ in range(random.randint(1, 7))]
        run_quietly(' '.join(pieces))


def test_every_ordered_pair_of_tokens_never_raises():
    for first, second in itertools.product(PIECES, repeat=2):
        run_quietly(first + ' ' + second)


def test_runaway_recursion_reports_rather_than_blowing_the_python_stack():
    _, error = aura.run('<robustness>', 'chore f() ong\nyeet f()\nbet\nf()', aura.new_symbol_table())
    assert error is not None
    assert 'Maximum call depth' in error.details


def test_deeply_nested_expressions_survive():
    source = '(' * 400 + '1' + ')' * 400
    result, error = aura.run('<robustness>', source, aura.new_symbol_table())
    assert error is None
    assert repr(result) == '1'
