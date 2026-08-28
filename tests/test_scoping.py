import shit


def ev(source):
    result, error = shit.run('<stdin>', source, shit.new_symbol_table())
    if isinstance(result, list):
        result = result[-1] if result else None
    return result, error


def test_scoping_is_lexical_not_dynamic():
    """A function must not see its caller's locals."""
    source = (
        'fun show() then\nreturn secret\nend\n'
        'fun caller() then\nvar secret = 1\nreturn show()\nend\n'
        'caller()'
    )
    result, error = ev(source)
    assert result is None
    assert "'secret' is not defined" in error.details


def test_assignment_mutates_the_outer_variable():
    source = 'var count = 0\nfun bump() then\ncount = count + 1\nend\nbump()\nbump()\ncount'
    result, error = ev(source)
    assert error is None
    assert repr(result) == '2'


def test_var_inside_a_function_stays_local():
    source = 'var x = 1\nfun f() then\nvar x = 99\nend\nf()\nx'
    result, error = ev(source)
    assert error is None
    assert repr(result) == '1'


def test_parameters_shadow_outer_names_without_clobbering_them():
    source = 'var x = 1\nfun f(x) then\nx = 50\nreturn x\nend\nf(9)\nx'
    result, error = ev(source)
    assert error is None
    assert repr(result) == '1'


def test_closure_captures_its_defining_scope():
    source = (
        'fun adder(k) then\nfun add(x) then\nreturn x + k\nend\nreturn add\nend\n'
        'var add5 = adder(5)\nadd5(3)'
    )
    result, error = ev(source)
    assert error is None
    assert repr(result) == '8'


def test_closures_have_independent_state():
    source = (
        'fun counter() then\nvar n = 0\nfun tick() then\nn = n + 1\nreturn n\nend\nreturn tick\nend\n'
        'var a = counter()\nvar b = counter()\na()\na()\nb()'
    )
    result, error = ev(source)
    assert error is None
    assert repr(result) == '1'


def test_closure_keeps_counting_across_calls():
    source = (
        'fun counter() then\nvar n = 0\nfun tick() then\nn = n + 1\nreturn n\nend\nreturn tick\nend\n'
        'var a = counter()\na()\na()\na()'
    )
    result, error = ev(source)
    assert error is None
    assert repr(result) == '3'


def test_assigning_an_undeclared_name_is_still_an_error():
    result, error = ev('fun f() then\nnope = 1\nend\nf()')
    assert result is None
    assert 'Cannot assign to undefined variable' in error.details


def test_recursion_still_resolves_the_functions_own_name():
    source = 'fun fact(n) then\nif n <= 1 then\nreturn 1\nend\nreturn n * fact(n - 1)\nend\nfact(6)'
    result, error = ev(source)
    assert error is None
    assert repr(result) == '720'
