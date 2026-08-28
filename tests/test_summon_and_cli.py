import os

import aura

Q = '"'


def write(tmp_path, name, source):
    target = tmp_path / name
    target.write_text(source, encoding='utf-8')
    return str(target)


# --- summon ---

def test_summon_brings_in_chores_and_stashes(tmp_path):
    write(tmp_path, 'lib.aura', 'chore double(n) ong\nyeet n * 2\nbet\nstash NAME = "lib"\n')
    main = write(tmp_path, 'main.aura', 'summon("lib.aura")\ncook(NAME)\ncook(double(21))\n')

    result, error = aura.run(main, open(main, encoding='utf-8').read(), aura.new_symbol_table())
    assert error is None


def test_summon_resolves_relative_to_the_summoning_file(tmp_path, capsys):
    sub = tmp_path / 'pkg'
    sub.mkdir()
    (sub / 'lib.aura').write_text('stash FROM_SUB = 1\n', encoding='utf-8')
    main = write(tmp_path, 'main.aura', 'summon("pkg/lib.aura")\ncook(FROM_SUB)\n')

    assert aura.main([main]) == 0
    assert capsys.readouterr().out == '1\n'


def test_summon_of_a_missing_file_is_a_runtime_error(tmp_path):
    main = write(tmp_path, 'main.aura', 'summon("nope.aura")\n')
    result, error = aura.run(main, open(main, encoding='utf-8').read(), aura.new_symbol_table())

    assert result is None
    assert 'Cannot summon' in error.details


def test_summon_reports_a_cycle_instead_of_recursing(tmp_path):
    main = write(tmp_path, 'loop.aura', 'summon("loop.aura")\n')
    result, error = aura.run(main, open(main, encoding='utf-8').read(), aura.new_symbol_table())

    assert result is None
    assert 'summoning itself' in error.details


def test_an_error_inside_a_summoned_file_points_at_that_file(tmp_path):
    write(tmp_path, 'bad.aura', 'stash x = 1 / 0\n')
    main = write(tmp_path, 'main.aura', 'summon("bad.aura")\n')
    result, error = aura.run(main, open(main, encoding='utf-8').read(), aura.new_symbol_table())

    assert result is None
    assert 'Division by zero' in error.details
    assert 'bad.aura' in error.as_string()


def test_summon_needs_a_yap(tmp_path):
    main = write(tmp_path, 'main.aura', 'summon(5)\n')
    result, error = aura.run(main, open(main, encoding='utf-8').read(), aura.new_symbol_table())

    assert result is None
    assert "'summon' needs a yap" in error.details


# --- CLI ---

def test_help_flag(capsys):
    assert aura.main(['--help']) == 0
    assert 'usage:' in capsys.readouterr().out


def test_tokens_flag_prints_the_stream(tmp_path, capsys):
    program = write(tmp_path, 'p.aura', 'stash x = 1\n')
    assert aura.main(['--tokens', program]) == 0

    out = capsys.readouterr().out.split()
    assert out[:4] == ['KEYWORD:stash', 'IDENTIFIER:x', 'EQ', 'INT:1']
    assert out[-1] == 'EOF'


def test_ast_flag_prints_one_line_per_statement(tmp_path, capsys):
    program = write(tmp_path, 'p.aura', 'stash x = 1\nx + 2\n')
    assert aura.main(['--ast', program]) == 0

    lines = capsys.readouterr().out.strip().splitlines()
    assert len(lines) == 2
    assert lines[0] == '(stash IDENTIFIER:x = INT:1)'


def test_dump_flags_report_errors_without_running(tmp_path, capsys):
    program = write(tmp_path, 'p.aura', 'stash x = $\n')
    assert aura.main(['--tokens', program]) == 1
    assert 'Illegal Character' in capsys.readouterr().out


def test_ast_flag_reports_a_syntax_error(tmp_path, capsys):
    program = write(tmp_path, 'p.aura', 'fr 1\n2\nbet\n')
    assert aura.main(['--ast', program]) == 1
    assert 'Invalid Syntax' in capsys.readouterr().out


def test_unknown_flag_exits_two(capsys):
    assert aura.main(['--nope', 'x.aura']) == 2
    assert 'unknown option' in capsys.readouterr().out


def test_no_file_is_an_error(capsys):
    assert aura.main(['--ast']) == 2
    assert 'expected a file' in capsys.readouterr().out


def test_extra_arguments_are_handed_to_the_program(tmp_path, capsys):
    program = write(tmp_path, 'p.aura', 'cook(handed())\n')
    assert aura.main([program, 'one', 'two']) == 0
    assert capsys.readouterr().out == '["one", "two"]\n'


def test_a_program_with_no_extra_arguments_gets_an_empty_pile(tmp_path, capsys):
    program = write(tmp_path, 'p.aura', 'cook(howmany(handed()))\n')
    assert aura.main([program]) == 0
    assert capsys.readouterr().out == '0\n'


# --- token positions ---

def test_token_without_positions_still_has_the_attributes():
    token = aura.Token(aura.TT_EOF)
    assert token.pos_start is None
    assert token.pos_end is None


# --- REPL continuation ---

def test_wants_more_on_an_unfinished_block():
    for source in ('chore f() ong', 'fr 1 ong', 'keep 1 ong', 'grind i = 0 til 2 ong'):
        assert aura.wants_more('<stdin>', source), source


def test_wants_more_on_an_unfinished_expression():
    for source in ('1 +', '[1,', '{' + Q + 'a' + Q + ': 1', '(1 + 2'):
        assert aura.wants_more('<stdin>', source), source


def test_wants_more_on_an_unterminated_yap():
    assert aura.wants_more('<stdin>', Q + 'oops')


def test_complete_input_does_not_want_more():
    for source in ('1 + 2', 'chore f() ong yeet 1 bet', 'stash x = [1, 2]'):
        assert not aura.wants_more('<stdin>', source), source


def test_a_real_error_does_not_want_more():
    for source in ('1 $ 2', 'stash 1 = 2'):
        assert not aura.wants_more('<stdin>', source), source
