import ast
import os

import shit

Q = '"'
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def ev(source):
    result, error = shit.run('<stdin>', source, shit.new_symbol_table())
    if isinstance(result, list):
        result = result[-1] if result else None
    return result, error


def kind_of(source):
    _, error = ev(source)
    assert error is not None, source
    return error.kind


CASES = {
    'math': ['1 / 0', '1 % 0', '0 ^ -1', 'grind i = 1 til 2 by 0 ong\n1\nbet'],
    'name': ['nope', 'nope = 1', 'chore f() ong\nnope = 1\nbet\nf()'],
    'index': ['[1][9]', '[1][' + Q + 'a' + Q + ']', 'stash n = 5\nn[0]',
              'stash s = ' + Q + 'a' + Q + '\ns[0] = ' + Q + 'b' + Q],
    'label': ['{}[' + Q + 'z' + Q + ']', '{}[[]]'],
    'type': [Q + 'a' + Q + ' + 1', 'stash n = 5\nn()', 'chunk(5)', 'smol(' + Q + 'a' + Q + ')',
             'grind x among 5 ong\n1\nbet'],
    'arity': ['yap(1, 2)', 'chore f(a) ong\n1\nbet\nf()'],
    'flow': ['bail', 'skip', 'yeet 1'],
    'unpack': ['stash a, b = [1]', 'stash a, b = 5'],
    'depth': ['chore f() ong\nyeet f()\nbet\nf()'],
    'custom': ['oops ' + Q + 'boom' + Q],
    'file': ['slurp(' + Q + 'definitely-not-here.txt' + Q + ')',
             'summon(' + Q + 'definitely-not-here.shit' + Q + ')'],
}


def test_every_case_reports_its_kind():
    wrong = []
    for expected, sources in CASES.items():
        for source in sources:
            actual = kind_of(source)
            if actual != expected:
                wrong.append(f'{source!r}: expected {expected}, got {actual}')
    assert not wrong, '\n'.join(wrong)


def test_kinds_are_from_the_known_set():
    for sources in CASES.values():
        for source in sources:
            assert kind_of(source) in shit.RTError.KINDS, source


def test_the_whoops_bag_carries_the_kind():
    source = ('risky ong\n1 / 0\nwhoops e ong\ne.kind\nbet')
    result, error = ev(source)
    assert error is None
    assert result.value == 'math'


def test_shit_code_can_branch_on_the_kind():
    source = (
        'chore describe(thunk) ong\n'
        'risky ong\n'
        'thunk()\n'
        'yeet ' + Q + 'fine' + Q + '\n'
        'whoops e ong\n'
        'fr e.kind == ' + Q + 'math' + Q + ' ong\n'
        'yeet ' + Q + 'bad sums' + Q + '\n'
        'orfr e.kind == ' + Q + 'file' + Q + ' ong\n'
        'yeet ' + Q + 'bad file' + Q + '\n'
        'bet\n'
        'yeet ' + Q + 'something else' + Q + '\n'
        'bet\n'
        'bet\n'
        'chore divzero() ong\nyeet 1 / 0\nbet\n'
        'chore missing() ong\nyeet slurp(' + Q + 'nope.txt' + Q + ')\nbet\n'
        'chore fine() ong\nyeet 1\nbet\n'
        '[describe(divzero), describe(missing), describe(fine)]'
    )
    result, error = ev(source)
    assert error is None
    assert repr(result) == '["bad sums", "bad file", "fine"]'


def test_the_whoops_bag_still_carries_why_file_and_line():
    result, error = ev('risky ong\n\n1 / 0\nwhoops e ong\ne\nbet')
    assert error is None
    assert repr(result) == (
        '{"why": "Division by zero", "kind": "math", "file": "<stdin>", "line": 3}'
    )


def test_every_error_site_in_the_source_declares_a_kind():
    """A new RTError with no kind would silently report as 'runtime'."""
    with open(os.path.join(REPO, 'shit.py'), encoding='utf-8') as handle:
        tree = ast.parse(handle.read())

    untagged = [
        node.lineno
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == 'RTError'
        and not any(keyword.arg == 'kind' for keyword in node.keywords)
    ]

    assert not untagged, f'RTError without a kind at lines: {untagged}'
