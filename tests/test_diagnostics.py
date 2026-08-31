# Copyright (c) 2026 iam-kira (Vijay Biradar)
# Licensed under the MIT License. See LICENSE for the full text.

import aura


def ev(source, filename='<stdin>'):
    result, error = aura.run(filename, source, aura.new_symbol_table())
    if isinstance(result, list):
        result = result[-1] if result else None
    return result, error


def test_runtime_error_records_call_frames():
    source = (
        'chore inner(n) ong\nyeet n / 0\nbet\n'
        'chore outer(n) ong\nyeet inner(n)\nbet\n'
        'outer(5)'
    )
    result, error = ev(source, 'prog.aura')
    assert result is None
    assert [name for name, _ in error.frames] == ['inner', 'outer']

    text = error.as_string()
    assert 'Traceback (most recent call last):' in text
    assert 'in outer' in text and 'in inner' in text
    assert 'Division by zero' in text


def test_error_without_a_call_has_no_traceback():
    result, error = ev('1 / 0')
    assert result is None
    assert error.frames == []
    assert 'Traceback' not in error.as_string()


def test_runaway_recursion_reports_a_language_error():
    result, error = ev('chore boom(n) ong\nyeet boom(n + 1)\nbet\nboom(0)')
    assert result is None
    assert 'Maximum call depth' in error.details


def test_traceback_is_capped_and_says_how_many_it_dropped():
    result, error = ev('chore boom(n) ong\nyeet boom(n + 1)\nbet\nboom(0)')
    assert len(error.frames) == aura.RTError.MAX_FRAMES
    assert error.frames_omitted > 0
    assert 'more frame(s)' in error.as_string()


def test_deeply_nested_expression_does_not_crash():
    result, error = ev('(' * 400 + '1' + ')' * 400)
    assert error is None
    assert repr(result) == '1'


def test_malformed_number_literals():
    for source in ('1.5.5', '1.', '1..2'):
        result, error = ev(source)
        assert result is None, source
        assert 'malformed number' in error.details, source


def test_valid_numbers_still_lex():
    for source, expected in (('42', '42'), ('3.14', '3.14'), ('0.5', '0.5')):
        result, error = ev(source)
        assert error is None, source
        assert repr(result) == expected, source


def test_error_reports_file_line_and_column():
    result, error = ev('stash x = 1\nx + $', 'prog.aura')
    assert result is None
    text = error.as_string()
    assert 'File prog.aura' in text
    assert 'line 2' in text
    assert 'col 5' in text
