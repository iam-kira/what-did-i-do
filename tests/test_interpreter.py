import shit


def reset_symbols():
    shit.global_symbol_table.symbols.clear()


def test_interpreter_arithmetic_evaluation():
    reset_symbols()
    result, error = shit.run('<stdin>', '1 + 2 * 3')

    assert error is None
    assert repr(result) == '7'


def test_interpreter_var_declare_assign_and_access():
    reset_symbols()
    result, error = shit.run('<stdin>', 'var x = 10\nx = x + 5\nx')

    assert error is None
    assert isinstance(result, list)
    assert [repr(value) for value in result] == ['10', '15', '15']


def test_interpreter_comparison_result():
    reset_symbols()
    result, error = shit.run('<stdin>', '5 + 1 >= 3')

    assert error is None
    assert repr(result) == '1'


def test_interpreter_undefined_variable_error():
    reset_symbols()
    result, error = shit.run('<stdin>', 'y')

    assert result is None
    assert isinstance(error, shit.RTError)
    assert 'not defined' in error.as_string()


def test_interpreter_division_by_zero_error():
    reset_symbols()
    result, error = shit.run('<stdin>', '1 / 0')

    assert result is None
    assert isinstance(error, shit.RTError)
    assert 'Division by zero' in error.as_string()
