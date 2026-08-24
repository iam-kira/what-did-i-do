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


def test_run_uses_supplied_symbol_table_and_leaves_global_alone():
    reset_symbols()
    table = shit.SymbolTable()
    result, error = shit.run('<stdin>', 'var z = 99', table)

    assert error is None
    assert repr(result) == '99'
    assert table.exists('z')
    assert not shit.global_symbol_table.exists('z')


def test_interpreter_if_takes_true_branch():
    reset_symbols()
    result, error = shit.run('<stdin>', 'var x = 0\nif 1 < 2 then\n  x = 10\nend\nx')

    assert error is None
    assert [repr(value) for value in result] == ['0', '10', '10']


def test_interpreter_if_elif_else_chain():
    reset_symbols()
    src = 'var x = 5\nif x > 10 then\n  1\nelif x > 3 then\n  2\nelse\n  3\nend'
    result, error = shit.run('<stdin>', src)

    assert error is None
    assert [repr(value) for value in result] == ['5', '2']


def test_interpreter_if_without_else_yields_zero():
    reset_symbols()
    result, error = shit.run('<stdin>', 'if 0 then\n  1\nend')

    assert error is None
    assert repr(result) == '0'
