import os

import aura

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_example_program_runs_end_to_end(capsys):
    exit_code = aura.main([os.path.join(REPO, 'example.aura')])
    out = capsys.readouterr().out.splitlines()

    assert exit_code == 0
    assert out[:6] == ['1', '2', 'fizz', '4', 'buzz', 'fizz']
    assert 'fizzbuzz' in out
    assert '10! = 3628800' in out
    assert 'counted til 3' in out
    assert '["this", "is", "a", "language"]' in out
    assert 'aura is a language ' in out
    assert '[2, 4, 6, 8, 10]' in out
    assert '2 ^ 16 = 65536' in out
    assert '{"the": 3, "quick": 1, "lazy": 1, "end": 1}' in out
    assert 'distinct words: 4' in out
    assert 'aura still works' in out
    assert 'dodged: Division by zero' in out
    assert '10 / 0 = 0' in out


def test_missing_file_is_reported(capsys):
    exit_code = aura.main([os.path.join(REPO, 'no-such-file.aura')])
    assert exit_code == 1
    assert 'cannot read' in capsys.readouterr().out


def test_program_error_exits_nonzero(tmp_path, capsys):
    program = tmp_path / 'bad.aura'
    program.write_text('stash x = 1 / 0\n', encoding='utf-8')

    exit_code = aura.main([str(program)])
    assert exit_code == 1
    assert 'Division by zero' in capsys.readouterr().out


def test_file_mode_does_not_echo_statement_values(capsys):
    program = os.path.join(REPO, 'tests', '_echo_check.aura')
    with open(program, 'w', encoding='utf-8') as handle:
        handle.write('stash x = 99\nx\ncook("only this")\n')
    try:
        exit_code = aura.main([program])
    finally:
        os.remove(program)

    assert exit_code == 0
    assert capsys.readouterr().out == 'only this\n'
