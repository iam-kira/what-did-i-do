import os

import shit

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_example_program_runs_end_to_end(capsys):
    exit_code = shit.main([os.path.join(REPO, 'example.shit')])
    out = capsys.readouterr().out.splitlines()

    assert exit_code == 0
    assert out[:6] == ['1', '2', 'fizz', '4', 'buzz', 'fizz']
    assert 'fizzbuzz' in out
    assert '10! = 3628800' in out
    assert 'shit is a language' in out
    assert '[2, 4, 6, 8, 10]' in out
    assert '2 ^ 16 = 65536' in out


def test_missing_file_is_reported(capsys):
    exit_code = shit.main([os.path.join(REPO, 'no-such-file.shit')])
    assert exit_code == 1
    assert 'cannot read' in capsys.readouterr().out


def test_program_error_exits_nonzero(tmp_path, capsys):
    program = tmp_path / 'bad.shit'
    program.write_text('var x = 1 / 0\n', encoding='utf-8')

    exit_code = shit.main([str(program)])
    assert exit_code == 1
    assert 'Division by zero' in capsys.readouterr().out


def test_file_mode_does_not_echo_statement_values(capsys):
    program = os.path.join(REPO, 'tests', '_echo_check.shit')
    with open(program, 'w', encoding='utf-8') as handle:
        handle.write('var x = 99\nx\nprint("only this")\n')
    try:
        exit_code = shit.main([program])
    finally:
        os.remove(program)

    assert exit_code == 0
    assert capsys.readouterr().out == 'only this\n'
