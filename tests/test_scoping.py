import aura


def ev(source):
    result, error = aura.run('<stdin>', source, aura.new_symbol_table())
    if isinstance(result, list):
        result = result[-1] if result else None
    return result, error


def test_scoping_is_lexical_not_dynamic():
    """A function must not see its caller's locals."""
    source = (
        'chore show() ong\nyeet secret\nbet\n'
        'chore caller() ong\nstash secret = 1\nyeet show()\nbet\n'
        'caller()'
    )
    result, error = ev(source)
    assert result is None
    assert "'secret' is not defined" in error.details


def test_assignment_mutates_the_outer_variable():
    source = 'stash count = 0\nchore bump() ong\ncount = count + 1\nbet\nbump()\nbump()\ncount'
    result, error = ev(source)
    assert error is None
    assert repr(result) == '2'


def test_var_inside_a_function_stays_local():
    source = 'stash x = 1\nchore f() ong\nstash x = 99\nbet\nf()\nx'
    result, error = ev(source)
    assert error is None
    assert repr(result) == '1'


def test_parameters_shadow_outer_names_without_clobbering_them():
    source = 'stash x = 1\nchore f(x) ong\nx = 50\nyeet x\nbet\nf(9)\nx'
    result, error = ev(source)
    assert error is None
    assert repr(result) == '1'


def test_closure_captures_its_defining_scope():
    source = (
        'chore adder(k) ong\nchore add(x) ong\nyeet x + k\nbet\nyeet add\nbet\n'
        'stash add5 = adder(5)\nadd5(3)'
    )
    result, error = ev(source)
    assert error is None
    assert repr(result) == '8'


def test_closures_have_independent_state():
    source = (
        'chore counter() ong\nstash n = 0\nchore tick() ong\nn = n + 1\nyeet n\nbet\nyeet tick\nbet\n'
        'stash a = counter()\nstash b = counter()\na()\na()\nb()'
    )
    result, error = ev(source)
    assert error is None
    assert repr(result) == '1'


def test_closure_keeps_counting_across_calls():
    source = (
        'chore counter() ong\nstash n = 0\nchore tick() ong\nn = n + 1\nyeet n\nbet\nyeet tick\nbet\n'
        'stash a = counter()\na()\na()\na()'
    )
    result, error = ev(source)
    assert error is None
    assert repr(result) == '3'


def test_assigning_an_undeclared_name_is_still_an_error():
    result, error = ev('chore f() ong\nnope = 1\nbet\nf()')
    assert result is None
    assert 'Cannot assign to undefined variable' in error.details


def test_recursion_still_resolves_the_functions_own_name():
    source = 'chore fact(n) ong\nfr n <= 1 ong\nyeet 1\nbet\nyeet n * fact(n - 1)\nbet\nfact(6)'
    result, error = ev(source)
    assert error is None
    assert repr(result) == '720'
