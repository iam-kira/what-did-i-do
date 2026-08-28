import aura

Q = '"'


def ev(source):
    result, error = aura.run('<stdin>', source, aura.new_symbol_table())
    if isinstance(result, list):
        result = result[-1] if result else None
    return result, error


def check(cases):
    for source, expected in cases.items():
        result, error = ev(source)
        assert error is None, (source, error.details if error else None)
        assert repr(result) == expected, source


def test_bag_literals():
    check({
        '{}': '{}',
        '{' + Q + 'a' + Q + ': 1}': '{"a": 1}',
        '{1: ' + Q + 'one' + Q + '}': '{1: "one"}',
    })


def test_bag_literal_may_span_lines_with_a_trailing_comma():
    result, error = ev('{\n' + Q + 'a' + Q + ': 1,\n' + Q + 'b' + Q + ': 2,\n}')
    assert error is None
    assert repr(result) == '{"a": 1, "b": 2}'


def test_lookup_by_label():
    check({'{' + Q + 'a' + Q + ': 1, ' + Q + 'b' + Q + ': 2}[' + Q + 'b' + Q + ']': '2'})


def test_missing_label_is_an_error():
    result, error = ev('{' + Q + 'a' + Q + ': 1}[' + Q + 'z' + Q + ']')
    assert result is None
    assert 'No label' in error.details


def test_only_maths_and_yaps_may_be_labels():
    result, error = ev('{' + Q + 'a' + Q + ': 1}[[1]]')
    assert result is None
    assert 'label must be a math or a yap' in error.details


def test_assigning_a_new_label():
    result, error = ev('stash d = {' + Q + 'a' + Q + ': 1}\nd[' + Q + 'b' + Q + '] = 2\nd')
    assert error is None
    assert repr(result) == '{"a": 1, "b": 2}'


def test_compound_assignment_into_a_bag():
    result, error = ev('stash d = {' + Q + 'a' + Q + ': 1}\nd[' + Q + 'a' + Q + '] += 10\nd')
    assert error is None
    assert repr(result) == '{"a": 11}'


def test_nested_bags_and_piles():
    check({'{' + Q + 'a' + Q + ': {' + Q + 'b' + Q + ': 1}}[' + Q + 'a' + Q + '][' + Q + 'b' + Q + ']': '1'})

    result, error = ev('stash d = {' + Q + 'a' + Q + ': [1, 2]}\nd[' + Q + 'a' + Q + '][0] = 9\nd')
    assert error is None
    assert repr(result) == '{"a": [9, 2]}'


def test_bags_keep_value_semantics():
    source = ('stash a = {' + Q + 'x' + Q + ': 1}\nstash b = a\n'
              'b[' + Q + 'x' + Q + '] = 9\na')
    result, error = ev(source)
    assert error is None
    assert repr(result) == '{"x": 1}'


def test_merging_with_plus_lets_the_right_win():
    check({
        '{' + Q + 'a' + Q + ': 1} + {' + Q + 'b' + Q + ': 2}': '{"a": 1, "b": 2}',
        '{' + Q + 'a' + Q + ': 1} + {' + Q + 'a' + Q + ': 9}': '{"a": 9}',
    })


def test_equality_is_by_value():
    check({
        '{' + Q + 'a' + Q + ': 1} == {' + Q + 'a' + Q + ': 1}': '1',
        '{' + Q + 'a' + Q + ': 1} == {' + Q + 'a' + Q + ': 2}': '0',
        '{} == {}': '1',
        '{} == []': '0',
    })


def test_empty_bag_is_falsy():
    check({'nah {}': '1', 'nah {' + Q + 'a' + Q + ': 1}': '0'})


def test_howmany_labels_and_goods():
    bag = '{' + Q + 'a' + Q + ': 1, ' + Q + 'b' + Q + ': 2}'
    check({
        'howmany(' + bag + ')': '2',
        'labels(' + bag + ')': '["a", "b"]',
        'goods(' + bag + ')': '[1, 2]',
        'whatis(' + bag + ')': '"bag"',
    })


def test_labels_needs_a_bag():
    result, error = ev('labels([1])')
    assert result is None
    assert "'labels' needs a bag, got pile" in error.details


def test_gotit_checks_labels():
    bag = '{' + Q + 'a' + Q + ': 1}'
    check({'gotit(' + bag + ', ' + Q + 'a' + Q + ')': '1',
           'gotit(' + bag + ', ' + Q + 'z' + Q + ')': '0'})


def test_yoink_drops_a_label():
    result, error = ev('yoink({' + Q + 'a' + Q + ': 1, ' + Q + 'b' + Q + ': 2}, ' + Q + 'a' + Q + ')')
    assert error is None
    assert repr(result) == '{"b": 2}'


def test_yoink_of_a_missing_label_is_an_error():
    result, error = ev('yoink({' + Q + 'a' + Q + ': 1}, ' + Q + 'z' + Q + ')')
    assert result is None
    assert 'No label' in error.details


def test_among_walks_the_labels():
    source = ('stash d = {' + Q + 'a' + Q + ': 1, ' + Q + 'b' + Q + ': 2}\n'
              'stash t = 0\ngrind k among d ong\nt += d[k]\nbet\nt')
    result, error = ev(source)
    assert error is None
    assert repr(result) == '3'


def test_missing_colon_is_a_syntax_error():
    result, error = ev('{' + Q + 'a' + Q + ' 1}')
    assert result is None
    assert "Expected ':'" in error.details


def test_unclosed_bag_is_a_syntax_error():
    result, error = ev('{' + Q + 'a' + Q + ': 1')
    assert result is None
    assert "Expected ',' or '}'" in error.details
