import os

import shit

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def run_example(name, capsys):
    exit_code = shit.main([os.path.join(REPO, name)])
    return exit_code, capsys.readouterr().out.splitlines()


def test_calculator_example(capsys):
    """A calculator written in shit - the language exercising itself."""
    exit_code, out = run_example(os.path.join('examples', 'calc.shit'), capsys)

    assert exit_code == 0
    assert out == [
        '1 + 2 * 3 = 7',
        '(1 + 2) * 3 = 9',
        '2 ^ 3 ^ 2 = 512',
        '-4 + 10 = 6',
        '7 % 4 = 3',
        '10 / 4 = 2.5',
        '2 * (3 + 4) - 5 = 9',
        '1.5 * 4 = 6',
        '((2)) = 2',
        '1 / 0 -> nope: Division by zero',
        '2 + -> nope: expected a number, got end',
        "4 $ 2 -> nope: I do not know what '$' is",
        '(1 + 2 -> nope: missing )',
    ]
