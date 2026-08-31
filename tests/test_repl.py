"""The REPL as a person actually meets it."""

CREDIT = 'aura by Vijay Biradar'


import aura
import shell


def drive(typed, monkeypatch, capsys):
    """Feed lines to the REPL and return everything it printed."""
    lines = iter(typed)

    def fake_input(prompt=''):
        try:
            return next(lines)
        except StopIteration:
            raise EOFError

    monkeypatch.setattr('builtins.input', fake_input)
    aura.global_symbol_table.symbols.clear()
    shell.main()
    return capsys.readouterr().out


# --- the commands a newcomer reaches for ---

def test_help_lists_the_vocabulary(monkeypatch, capsys):
    out = drive(['help'], monkeypatch, capsys)
    for expected in ('stash', 'chore', 'cook(v)', 'sus ong', 'bet', 'docs/BOOK.md'):
        assert expected in out, expected


def test_help_explains_the_prompt_itself(monkeypatch, capsys):
    out = drive(['help'], monkeypatch, capsys)
    assert '...  >' in out
    assert 'ctrl-c' in out


def test_builtins_lists_every_builtin(monkeypatch, capsys):
    out = drive(['builtins'], monkeypatch, capsys)
    assert '%d built-in chores' % len(aura.BUILTINS) in out
    for name in ('cook', 'howmany', 'is_ghosted', 'swap', 'pair'):
        assert name in out, name


def test_a_defined_name_beats_the_shell_command(monkeypatch, capsys):
    out = drive(['stash help = 5', 'help'], monkeypatch, capsys)
    assert out.count('5') == 2
    assert 'regrettable keywords' not in out


def test_quit_words_all_leave(monkeypatch, capsys):
    for word in ('exit', 'quit', ':q'):
        out = drive([word, 'cook("never")'], monkeypatch, capsys)
        assert 'aight imma head out' in out
        assert 'never' not in out


# --- editing behaviour ---

def test_a_block_keeps_prompting_until_it_closes(monkeypatch, capsys):
    out = drive(['chore sq(n) ong', 'yeet n * n', 'bet', 'sq(9)'], monkeypatch, capsys)
    assert '<chore sq>' in out
    assert '81' in out


def test_a_blank_line_ends_a_stuck_block(monkeypatch, capsys):
    out = drive(['fr 1 ong', '', '2'], monkeypatch, capsys)
    assert "Expected 'bet'" in out
    assert '2' in out


def test_values_echo_with_repr_so_types_are_visible(monkeypatch, capsys):
    out = drive(['1', '"1"', 'ghosted', '[1]'], monkeypatch, capsys)
    assert '1\n' in out
    assert '"1"' in out
    assert 'ghosted' in out
    assert '[1]' in out


def test_state_persists_between_lines(monkeypatch, capsys):
    out = drive(['stash n = 1', 'n += 1', 'n'], monkeypatch, capsys)
    printed = [line for line in out.splitlines()
               if line and line not in ('aight imma head out', CREDIT)
               and not line.startswith(('aura ', "type 'help'"))]
    assert printed == ['1', '2', '2']


# --- the author is credited where people actually look ---

def test_the_repl_greets_you_with_version_and_author(monkeypatch, capsys):
    out = drive([], monkeypatch, capsys)
    assert aura.BANNER in out
    assert aura.__version__ in out
    assert 'Vijay Biradar' in out
    assert "type 'help'" in out


def test_the_farewell_credits_the_author(monkeypatch, capsys):
    out = drive(['exit'], monkeypatch, capsys)
    lines = out.strip().splitlines()

    assert lines[-2] == 'aight imma head out'
    assert lines[-1] == 'aura by Vijay Biradar'


def test_every_way_out_credits_the_author(monkeypatch, capsys):
    for typed in (['exit'], ['quit'], [':q'], []):
        out = drive(typed, monkeypatch, capsys)
        assert 'aight imma head out' in out, typed
        assert 'Vijay Biradar' in out, typed


def test_an_error_does_not_end_the_session(monkeypatch, capsys):
    out = drive(['1 / 0', 'cook("still here")'], monkeypatch, capsys)
    assert 'Division by zero' in out
    assert 'still here' in out


def test_errors_show_the_offending_line(monkeypatch, capsys):
    out = drive(['stash x = 1 + $'], monkeypatch, capsys)
    assert 'Illegal Character' in out
    assert 'stash x = 1 + $' in out
    assert '^' in out


def test_a_missing_bracket_call_is_explained(monkeypatch, capsys):
    out = drive(['cook "hi"'], monkeypatch, capsys)
    assert 'put the arguments in brackets' in out


def test_blank_lines_are_ignored(monkeypatch, capsys):
    out = drive(['', '   ', '7'], monkeypatch, capsys)
    assert '7' in out


def test_ctrl_c_drops_the_buffer_without_quitting(monkeypatch, capsys):
    """KeyboardInterrupt mid-block throws the block away, not the session."""
    lines = iter(['chore f() ong', KeyboardInterrupt, '42'])

    def fake_input(prompt=''):
        try:
            item = next(lines)
        except StopIteration:
            raise EOFError
        if item is KeyboardInterrupt:
            raise KeyboardInterrupt
        return item

    monkeypatch.setattr('builtins.input', fake_input)
    aura.global_symbol_table.symbols.clear()
    shell.main()
    out = capsys.readouterr().out

    assert 'Dropped that' in out
    assert '42' in out
    assert 'aight imma head out' in out


def test_eof_says_goodbye(monkeypatch, capsys):
    out = drive([], monkeypatch, capsys)
    assert 'aight imma head out' in out
