import os

import shit

Q = '"'


def ev(source, filename='<stdin>'):
    result, error = shit.run(filename, source, shit.new_symbol_table())
    if isinstance(result, list):
        result = result[-1] if result else None
    return result, error


def yap(text):
    return Q + str(text).replace(chr(92), chr(92) * 2) + Q


# --- reading and writing ---

def test_spill_then_slurp_round_trips(tmp_path):
    target = tmp_path / 'note.txt'
    source = ('spill(' + yap(target) + ', ' + Q + 'hello' + Q + ')\n'
              'slurp(' + yap(target) + ')')
    result, error = ev(source)

    assert error is None
    assert result.value == 'hello'
    assert target.read_text(encoding='utf-8') == 'hello'


def test_spill_reports_how_much_it_wrote(tmp_path):
    target = tmp_path / 'note.txt'
    result, error = ev('spill(' + yap(target) + ', ' + Q + 'abcde' + Q + ')')
    assert error is None
    assert repr(result) == '5'


def test_spill_overwrites_and_dribble_appends(tmp_path):
    target = tmp_path / 'log.txt'
    source = ('spill(' + yap(target) + ', ' + Q + 'a' + Q + ')\n'
              'spill(' + yap(target) + ', ' + Q + 'b' + Q + ')\n'
              'dribble(' + yap(target) + ', ' + Q + 'c' + Q + ')\n'
              'slurp(' + yap(target) + ')')
    result, error = ev(source)

    assert error is None
    assert result.value == 'bc'


def test_slurping_a_missing_file_is_a_runtime_error(tmp_path):
    result, error = ev('slurp(' + yap(tmp_path / 'nope.txt') + ')')
    assert result is None
    assert 'Cannot slurp' in error.details


def test_slurp_error_is_catchable(tmp_path):
    source = ('risky ong\nslurp(' + yap(tmp_path / 'nope.txt') + ')\n'
              'whoops e ong\n' + Q + 'handled' + Q + '\nbet')
    result, error = ev(source)
    assert error is None
    assert result.value == 'handled'


def test_isthere_checks_a_path(tmp_path):
    target = tmp_path / 'here.txt'
    target.write_text('x', encoding='utf-8')

    result, error = ev('isthere(' + yap(target) + ')')
    assert error is None
    assert repr(result) == '1'

    result, error = ev('isthere(' + yap(tmp_path / 'gone.txt') + ')')
    assert error is None
    assert repr(result) == '0'


def test_paths_must_be_yaps():
    for source in ('slurp(5)', 'isthere(5)', 'spill(5, ' + Q + 'x' + Q + ')'):
        result, error = ev(source)
        assert result is None, source
        assert 'needs a yap' in error.details, source


def test_spilled_text_must_be_a_yap(tmp_path):
    result, error = ev('spill(' + yap(tmp_path / 'x.txt') + ', 5)')
    assert result is None
    assert 'needs a yap' in error.details


def test_a_program_can_read_its_own_source(tmp_path, capsys):
    program = tmp_path / 'self.shit'
    program.write_text('yap(howmany(slurp(handed()[0])) > 0)\n', encoding='utf-8')

    assert shit.main([str(program), str(program)]) == 0
    assert capsys.readouterr().out == '1\n'


# --- bounce ---

def test_bounce_sets_the_exit_code(tmp_path, capsys):
    program = tmp_path / 'p.shit'
    program.write_text('yap("before")\nbounce(3)\nyap("after")\n', encoding='utf-8')

    assert shit.main([str(program)]) == 3
    assert capsys.readouterr().out == 'before\n'


def test_bounce_defaults_to_zero(tmp_path):
    program = tmp_path / 'p.shit'
    program.write_text('bounce()\n', encoding='utf-8')
    assert shit.main([str(program)]) == 0


def test_bounce_is_not_catchable():
    result, error = ev('risky ong\nbounce(2)\nwhoops e ong\n' + Q + 'caught' + Q + '\nbet')
    assert result is None
    assert isinstance(error, shit.BounceError)
    assert error.code == 2


def test_bounce_code_must_be_a_math():
    result, error = ev('bounce(' + Q + 'x' + Q + ')')
    assert result is None
    assert "'bounce' needs a math" in error.details


def test_bounce_stops_a_loop_and_the_program():
    result, error = ev('stash n = 0\ngrind i = 0 til 10 ong\nn += 1\nbounce(1)\nbet\nn')
    assert result is None
    assert isinstance(error, shit.BounceError)


# --- handed ---

def test_handed_is_empty_when_run_directly():
    shit.SCRIPT_ARGS = []
    result, error = ev('handed()')
    assert error is None
    assert repr(result) == '[]'
