"""The REPL is what most people meet first, so it gets tested like everything else."""

import pytest

import shell
import aura


@pytest.fixture
def repl(monkeypatch, capsys):
    """Feed the REPL a script of lines; return (exit code, printed lines)."""

    def run(*lines, interrupt_at=None):
        script = iter(lines)
        seen = {'count': 0}

        def fake_input(prompt=''):
            seen['count'] += 1
            if interrupt_at is not None and seen['count'] == interrupt_at:
                raise KeyboardInterrupt
            try:
                return next(script)
            except StopIteration:
                raise EOFError

        monkeypatch.setattr('builtins.input', fake_input)
        code = shell.main(aura.new_symbol_table())
        return code, capsys.readouterr().out.splitlines()

    return run


def test_a_value_is_echoed(repl):
    code, out = repl('1 + 2')
    assert code == 0
    assert '3' in out


def test_yaps_echo_with_their_quotes(repl):
    _, out = repl('"hi"')
    assert '"hi"' in out


def test_state_persists_between_lines(repl):
    _, out = repl('stash x = 2', 'x * 21')
    assert '42' in out


def test_a_multi_line_block_is_buffered_until_complete(repl):
    _, out = repl('chore f(n) ong', 'yeet n + 1', 'bet', 'f(41)')
    assert '42' in out


def test_a_blank_line_force_ends_an_unfinished_block(repl):
    _, out = repl('fr 1 ong', '', '2')
    assert any("Expected 'bet'" in line for line in out)
    assert '2' in out


def test_errors_print_and_the_session_continues(repl):
    _, out = repl('1 / 0', '7')
    assert any('Division by zero' in line for line in out)
    assert '7' in out


def test_blank_lines_are_ignored(repl):
    _, out = repl('', '   ', '5')
    assert out.count('5') == 1


@pytest.mark.parametrize('word', ['exit', 'quit', ':q', 'EXIT'])
def test_quit_words_leave(repl, word):
    code, out = repl(word, '999')
    assert code == 0
    assert 'bye!' in out
    assert '999' not in out


def test_end_of_input_leaves(repl):
    code, out = repl()
    assert code == 0
    assert any('bye!' in line for line in out)


def test_ctrl_c_does_not_quit(repl):
    code, out = repl('5', interrupt_at=1)
    assert code == 0
    assert any('Type' in line for line in out)


def test_ctrl_c_drops_a_half_typed_block(repl):
    code, out = repl('chore f() ong', '5', interrupt_at=2)
    assert code == 0
    assert any('Dropped that' in line for line in out)
    # the buffer is gone, so the next line is read fresh rather than continuing
    assert '5' in out


def test_bounce_sets_the_exit_code(repl):
    code, _ = repl('bounce(3)')
    assert code == 3


def test_several_statements_on_one_line_each_echo(repl):
    _, out = repl('1; 2')
    assert '1' in out and '2' in out


def test_builtins_are_available(repl):
    _, out = repl('howmany([1, 2])')
    assert '2' in out


def test_yap_prints_raw_while_the_echo_is_repr(repl):
    _, out = repl('cook("hi")')
    assert 'hi' in out
    assert '0' in out
