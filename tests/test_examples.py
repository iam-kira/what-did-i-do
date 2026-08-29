import os

import aura

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def run_example(name, capsys):
    exit_code = aura.main([os.path.join(REPO, name)])
    return exit_code, capsys.readouterr().out.splitlines()


def test_calculator_example(capsys):
    """A calculator written in aura - the language exercising itself."""
    exit_code, out = run_example(os.path.join('examples', 'calc.aura'), capsys)

    assert exit_code == 0
    assert out == [
        '1 + 2 * 3 = 7',
        '(1 + 2) * 3 = 9',
        '2 ^ 3 ^ 2 = 512',
        '-4 + 10 = 6',
        '7 % 4 = 3',
        '10 / 4 = 2.5',
        '2 * (3 + 4) - 5 = 9',
        '1.5 * 4 = 6',
        '((2)) = 2',
        '1 / 0 -> nope: Division by zero',
        '2 + -> nope: expected a number, got end',
        "4 $ 2 -> nope: I do not know what '$' is",
        '(1 + 2 -> nope: missing )',
    ]


def test_word_count_example_reads_a_file(tmp_path, capsys):
    sample = tmp_path / 'sample.txt'
    sample.write_text('one two three\nfour five\n', encoding='utf-8')

    exit_code = aura.main([os.path.join(REPO, 'examples', 'wc.aura'), str(sample)])
    out = capsys.readouterr().out.strip()

    assert exit_code == 0
    assert '5 words' in out
    assert '24 chars' in out


def test_word_count_example_walks_a_folder(tmp_path, capsys):
    (tmp_path / 'a.txt').write_text('one two\n', encoding='utf-8')
    (tmp_path / 'b.txt').write_text('three\n', encoding='utf-8')
    (tmp_path / 'sub').mkdir()

    exit_code = aura.main([os.path.join(REPO, 'examples', 'wc.aura'), str(tmp_path)])
    out = capsys.readouterr().out.strip().splitlines()

    assert exit_code == 0
    assert len(out) == 2, out
    assert any('a.txt' in line and '2 words' in line for line in out)
    assert any('b.txt' in line and '1 words' in line for line in out)


def test_word_count_example_complains_with_no_file(capsys):
    exit_code = aura.main([os.path.join(REPO, 'examples', 'wc.aura')])

    assert exit_code == 2
    assert 'give me a file' in capsys.readouterr().out


def test_word_count_example_survives_a_missing_file(tmp_path, capsys):
    exit_code = aura.main([os.path.join(REPO, 'examples', 'wc.aura'), str(tmp_path / 'gone.txt')])

    assert exit_code == 0
    assert 'not there' in capsys.readouterr().out


# --- the JSON parser ---

def test_json_example_parses_a_document(tmp_path, capsys):
    doc = tmp_path / 'doc.json'
    doc.write_text('{"name": "ana", "score": 42, "tags": ["a", "b"], '
                   '"ok": true, "nil": null}', encoding='utf-8')

    exit_code = aura.main([os.path.join(REPO, 'examples', 'json.aura'), str(doc)])
    out = capsys.readouterr().out

    assert exit_code == 0
    assert '"name": "ana"' in out
    assert '"nil": ghosted' in out      # JSON null survives as ghosted
    assert 'score: math = 42' in out
    assert 'tags: pile of 2' in out
    assert 'nil: null' in out


def test_json_example_handles_nesting(tmp_path, capsys):
    doc = tmp_path / 'nested.json'
    doc.write_text('{"a": [1, [2, {"b": 3}]]}', encoding='utf-8')

    assert aura.main([os.path.join(REPO, 'examples', 'json.aura'), str(doc)]) == 0
    assert '[1, [2, {"b": 3}]]' in capsys.readouterr().out


def test_json_example_reports_bad_input(tmp_path, capsys):
    doc = tmp_path / 'bad.json'
    doc.write_text('{"a": }', encoding='utf-8')

    exit_code = aura.main([os.path.join(REPO, 'examples', 'json.aura'), str(doc)])
    assert exit_code == 1
    assert 'unexpected' in capsys.readouterr().out


def test_json_example_wants_a_file(capsys):
    exit_code = aura.main([os.path.join(REPO, 'examples', 'json.aura')])
    assert exit_code == 2
    assert 'give me a .json file' in capsys.readouterr().out


def test_json_example_reports_a_missing_file(tmp_path, capsys):
    exit_code = aura.main([os.path.join(REPO, 'examples', 'json.aura'),
                           str(tmp_path / 'gone.json')])
    assert exit_code == 1
    assert 'Cannot slurp' in capsys.readouterr().out
