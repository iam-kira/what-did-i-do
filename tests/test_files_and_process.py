import os

import aura

Q = '"'


def ev(source, filename='<stdin>'):
    result, error = aura.run(filename, source, aura.new_symbol_table())
    if isinstance(result, list):
        result = result[-1] if result else None
    return result, error


def cook(text):
    return Q + str(text).replace(chr(92), chr(92) * 2) + Q


# --- reading and writing ---

def test_spill_then_slurp_round_trips(tmp_path):
    target = tmp_path / 'note.txt'
    source = ('spill(' + cook(target) + ', ' + Q + 'hello' + Q + ')\n'
              'slurp(' + cook(target) + ')')
    result, error = ev(source)

    assert error is None
    assert result.value == 'hello'
    assert target.read_text(encoding='utf-8') == 'hello'


def test_spill_reports_how_much_it_wrote(tmp_path):
    target = tmp_path / 'note.txt'
    result, error = ev('spill(' + cook(target) + ', ' + Q + 'abcde' + Q + ')')
    assert error is None
    assert repr(result) == '5'


def test_spill_overwrites_and_dribble_appends(tmp_path):
    target = tmp_path / 'log.txt'
    source = ('spill(' + cook(target) + ', ' + Q + 'a' + Q + ')\n'
              'spill(' + cook(target) + ', ' + Q + 'b' + Q + ')\n'
              'dribble(' + cook(target) + ', ' + Q + 'c' + Q + ')\n'
              'slurp(' + cook(target) + ')')
    result, error = ev(source)

    assert error is None
    assert result.value == 'bc'


def test_slurping_a_missing_file_is_a_runtime_error(tmp_path):
    result, error = ev('slurp(' + cook(tmp_path / 'nope.txt') + ')')
    assert result is None
    assert 'Cannot slurp' in error.details


def test_slurp_error_is_catchable(tmp_path):
    source = ('sus ong\nslurp(' + cook(tmp_path / 'nope.txt') + ')\n'
              'whoops e ong\n' + Q + 'handled' + Q + '\nbet')
    result, error = ev(source)
    assert error is None
    assert result.value == 'handled'


def test_isthere_checks_a_path(tmp_path):
    target = tmp_path / 'here.txt'
    target.write_text('x', encoding='utf-8')

    result, error = ev('isthere(' + cook(target) + ')')
    assert error is None
    assert repr(result) == '1'

    result, error = ev('isthere(' + cook(tmp_path / 'gone.txt') + ')')
    assert error is None
    assert repr(result) == '0'


def test_paths_must_be_yaps():
    for source in ('slurp(5)', 'isthere(5)', 'spill(5, ' + Q + 'x' + Q + ')'):
        result, error = ev(source)
        assert result is None, source
        assert 'needs a yap' in error.details, source


def test_spilled_text_must_be_a_yap(tmp_path):
    result, error = ev('spill(' + cook(tmp_path / 'x.txt') + ', 5)')
    assert result is None
    assert 'needs a yap' in error.details


def test_a_program_can_read_its_own_source(tmp_path, capsys):
    program = tmp_path / 'self.aura'
    program.write_text('cook(howmany(slurp(handed()[0])) > 0)\n', encoding='utf-8')

    assert aura.main([str(program), str(program)]) == 0
    assert capsys.readouterr().out == '1\n'


# --- bounce ---

def test_bounce_sets_the_exit_code(tmp_path, capsys):
    program = tmp_path / 'p.aura'
    program.write_text('cook("before")\nbounce(3)\ncook("after")\n', encoding='utf-8')

    assert aura.main([str(program)]) == 3
    assert capsys.readouterr().out == 'before\n'


def test_bounce_defaults_to_zero(tmp_path):
    program = tmp_path / 'p.aura'
    program.write_text('bounce()\n', encoding='utf-8')
    assert aura.main([str(program)]) == 0


def test_bounce_is_not_catchable():
    result, error = ev('sus ong\nbounce(2)\nwhoops e ong\n' + Q + 'caught' + Q + '\nbet')
    assert result is None
    assert isinstance(error, aura.BounceError)
    assert error.code == 2


def test_bounce_code_must_be_a_math():
    result, error = ev('bounce(' + Q + 'x' + Q + ')')
    assert result is None
    assert "'bounce' needs a math" in error.details


def test_bounce_stops_a_loop_and_the_program():
    result, error = ev('stash n = 0\ngrind i = 0 til 10 ong\nn += 1\nbounce(1)\nbet\nn')
    assert result is None
    assert isinstance(error, aura.BounceError)


# --- handed ---

def test_handed_is_empty_when_run_directly():
    aura.SCRIPT_ARGS = []
    result, error = ev('handed()')
    assert error is None
    assert repr(result) == '[]'


# --- directories ---

def test_rummage_lists_a_folder(tmp_path):
    (tmp_path / 'b.txt').write_text('b', encoding='utf-8')
    (tmp_path / 'a.txt').write_text('a', encoding='utf-8')

    result, error = ev('rummage(' + cook(tmp_path) + ')')
    assert error is None
    assert repr(result) == '["a.txt", "b.txt"]'


def test_rummage_defaults_to_here():
    result, error = ev('gotit(rummage(), ' + Q + 'aura.py' + Q + ')')
    assert error is None
    assert repr(result) == '1'


def test_rummage_of_a_missing_folder_reports_a_file_error(tmp_path):
    result, error = ev('rummage(' + cook(tmp_path / 'gone') + ')')
    assert result is None
    assert error.kind == 'file'
    assert 'Cannot rummage' in error.details


def test_isfolder_tells_folders_from_files(tmp_path):
    (tmp_path / 'f.txt').write_text('x', encoding='utf-8')

    result, error = ev('isfolder(' + cook(tmp_path) + ')')
    assert error is None
    assert repr(result) == '1'

    result, error = ev('isfolder(' + cook(tmp_path / 'f.txt') + ')')
    assert error is None
    assert repr(result) == '0'


def test_stitch_joins_with_forward_slashes():
    result, error = ev('stitch(' + Q + 'a' + Q + ', ' + Q + 'b' + Q + ', ' + Q + 'c.txt' + Q + ')')
    assert error is None
    assert result.value == 'a/b/c.txt'


def test_stitch_takes_one_part_or_many():
    result, error = ev('stitch(' + Q + 'only' + Q + ')')
    assert error is None
    assert result.value == 'only'


def test_stitch_needs_yaps():
    result, error = ev('stitch(1)')
    assert result is None
    assert error.kind == 'type'
    assert "'stitch' needs yaps" in error.details


def test_stitch_output_can_be_slurped(tmp_path):
    folder = tmp_path / 'sub'
    folder.mkdir()
    (folder / 'note.txt').write_text('found me', encoding='utf-8')

    source = ('slurp(stitch(' + cook(folder) + ', ' + Q + 'note.txt' + Q + '))')
    result, error = ev(source)
    assert error is None
    assert result.value == 'found me'
