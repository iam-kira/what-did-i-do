"""The REPL as a person actually meets it."""

CREDIT = 'aura by Vijay Biradar'


def said_goodbye(out):
    """The sign-off is picked at random, so assert the pool, not one phrase."""
    return any(bye in out for bye in aura.FAREWELLS)


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
        assert said_goodbye(out)
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
               and line not in aura.FAREWELLS
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

    assert lines[-2] in aura.FAREWELLS
    assert lines[-1] == 'aura by Vijay Biradar'


def test_every_way_out_credits_the_author(monkeypatch, capsys):
    for typed in (['exit'], ['quit'], [':q'], []):
        out = drive(typed, monkeypatch, capsys)
        assert said_goodbye(out), typed
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
    assert said_goodbye(out)


def test_eof_says_goodbye(monkeypatch, capsys):
    out = drive([], monkeypatch, capsys)
    assert said_goodbye(out)


# --- the send-off animation ---

class FakeTerminal:
    """Stands in for a real terminal, so the animation actually runs."""

    def __init__(self, tty=True):
        self.tty = tty
        self.written = []

    def isatty(self):
        return self.tty

    def write(self, text):
        self.written.append(text)

    def flush(self):
        pass

    def text(self):
        return ''.join(self.written)


def test_the_walk_off_animates_on_a_terminal(monkeypatch):
    monkeypatch.delenv('AURA_NO_MOTION', raising=False)
    monkeypatch.setattr(aura, 'WALK_DELAY', 0)

    screen = FakeTerminal()
    assert aura.walk_off(screen) is True

    drawn = screen.text()
    assert drawn.count(chr(13)) == aura.WALK_FRAMES + 2, 'a redraw per frame, then the wipe'
    assert 'o/' in drawn and chr(92) + 'o' in drawn, 'the arm should alternate'
    assert drawn.endswith(chr(13)), 'it should clear the line on the way out'


def test_the_walk_off_is_ascii_only(monkeypatch):
    """Windows consoles choke on anything else."""
    monkeypatch.delenv('AURA_NO_MOTION', raising=False)
    monkeypatch.setattr(aura, 'WALK_DELAY', 0)

    screen = FakeTerminal()
    aura.walk_off(screen)
    screen.text().encode('ascii')


def test_the_walk_off_is_skipped_when_output_is_not_a_terminal(monkeypatch):
    """Otherwise carriage returns end up in pipes, files and CI logs."""
    monkeypatch.delenv('AURA_NO_MOTION', raising=False)

    screen = FakeTerminal(tty=False)
    assert aura.walk_off(screen) is False
    assert screen.text() == ''


def test_aura_no_motion_switches_it_off(monkeypatch):
    monkeypatch.setenv('AURA_NO_MOTION', '1')

    screen = FakeTerminal()
    assert aura.walk_off(screen) is False
    assert screen.text() == ''


def test_the_farewell_pool_is_all_lowercase_ascii():
    for bye in aura.FAREWELLS:
        bye.encode('ascii')
        assert bye == bye.lower(), bye
        assert bye.strip() == bye


def test_the_pool_includes_auras_own_words():
    """Half the joke is that the shell says goodbye in its own vocabulary."""
    assert 'ghosted' in aura.FAREWELLS
    for word in ('ghosted', 'based', 'bounce', 'yeet'):
        assert any(word in bye for bye in aura.FAREWELLS), word


def test_farewell_always_carries_the_credit():
    for _ in range(30):
        text = aura.farewell()
        first, _, second = text.partition('\n')
        assert first in aura.FAREWELLS
        assert second == CREDIT


def test_the_sign_off_actually_varies():
    seen = {aura.farewell().split('\n')[0] for _ in range(200)}
    assert len(seen) > 1, 'the sign-off should not always be the same'
    assert seen <= set(aura.FAREWELLS)
