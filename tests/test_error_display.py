"""Errors should show the offending line, not just describe it."""

import aura

Q = '"'


def error_text(source, filename='prog.aura'):
    _, error = aura.run(filename, source, aura.new_symbol_table())
    assert error is not None, source
    return error.as_string()


def lines_of(source, **kwargs):
    return error_text(source, **kwargs).splitlines()


def test_the_offending_line_is_shown():
    out = lines_of('stash x = 1\nstash y = x + $ + 2')
    assert 'Illegal Character' in out[0]
    assert 'line 2, col 15' in out[1]
    assert out[2] == '  stash y = x + $ + 2'


def test_a_caret_points_at_the_column():
    out = lines_of('stash x = 1\nstash y = x + $ + 2')
    caret = out[3]
    assert set(caret.strip()) == {'^'}
    # the caret must sit under the offending character
    assert out[2][len(caret.rstrip('^'))] == '$'


def test_the_caret_spans_a_whole_name():
    out = lines_of('stash t = 0\nt += nope')
    assert out[2] == '  t += nope'
    assert out[3].strip() == '^' * len('nope')


def test_tabs_do_not_shift_the_caret():
    source = 'grind i = 0 til 2 ong\n' + chr(9) + 'nope\nbet'
    out = lines_of(source)
    # the tab renders as four spaces in both the line and the caret row
    assert out[2] == '      nope'
    assert out[3].index('^') == out[2].index('nope')


def test_an_error_at_the_end_of_a_line_still_shows_it():
    out = lines_of('fr 1 ong\ncook(1)')
    assert "Expected 'bet'" in out[0]
    assert out[2] == '  cook(1)'


def test_an_error_past_the_last_line_shows_no_excerpt():
    # the trailing newline puts EOF on a line that does not exist
    out = lines_of('fr 1 ong\ncook(1)\n')
    assert "Expected 'bet'" in out[0]
    assert len(out) == 2


def test_a_traceback_still_leads_the_message():
    source = ('chore inner(n) ong\nyeet n / 0\nbet\n'
              'chore outer() ong\nyeet inner(5)\nbet\nouter()')
    out = lines_of(source)

    assert out[0] == 'Traceback (most recent call last):'
    assert 'in outer' in out[1]
    assert 'in inner' in out[2]
    assert 'Division by zero' in out[3]
    assert out[5] == '  yeet n / 0'
    assert '^' in out[6]


def test_runtime_errors_show_the_line_too():
    out = lines_of('stash xs = [1]\nxs[9]')
    assert 'out of range' in out[0]
    assert out[2] == '  xs[9]'


def test_the_excerpt_survives_a_source_with_no_trailing_newline():
    out = lines_of('nope')
    assert out[2] == '  nope'
    assert out[3].strip() == '^' * len('nope')


def test_an_error_in_a_summoned_file_shows_that_files_line(tmp_path):
    (tmp_path / 'lib.aura').write_text('stash bad = 1 / 0\n', encoding='utf-8')
    main = tmp_path / 'main.aura'
    main.write_text('summon(' + Q + 'lib.aura' + Q + ')\n', encoding='utf-8')

    text = error_text(main.read_text(encoding='utf-8'), filename=str(main))
    assert 'Division by zero' in text
    assert 'stash bad = 1 / 0' in text


def test_excerpt_is_empty_when_there_is_no_source():
    error = aura.RTError(None, None, 'nowhere', kind='runtime')
    assert error.excerpt() == ''
