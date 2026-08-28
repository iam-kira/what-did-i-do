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


def test_word_count_example_reads_a_file(tmp_path, capsys):
    sample = tmp_path / 'sample.txt'
    sample.write_text('one two three\nfour five\n', encoding='utf-8')

    exit_code = shit.main([os.path.join(REPO, 'examples', 'wc.shit'), str(sample)])
    out = capsys.readouterr().out.strip()

    assert exit_code == 0
    assert '5 words' in out
    assert '24 chars' in out


def test_word_count_example_complains_with_no_file(capsys):
    exit_code = shit.main([os.path.join(REPO, 'examples', 'wc.shit')])

    assert exit_code == 2
    assert 'give me a file' in capsys.readouterr().out


def test_word_count_example_survives_a_missing_file(tmp_path, capsys):
    exit_code = shit.main([os.path.join(REPO, 'examples', 'wc.shit'), str(tmp_path / 'gone.txt')])

    assert exit_code == 0
    assert 'not there' in capsys.readouterr().out
