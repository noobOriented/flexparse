import pytest

from ..types import (
    ArgumentTypeError,
    IntRange,
    FloatRange,
    LookUp,
    FactoryMethod,
)


class TestIntRange:

    @pytest.mark.parametrize('func, x', [
        (IntRange(0), '2'),
        (IntRange(0), '0'),
    ])
    def test_call(self, func, x):
        assert func(x) == int(x)

    @pytest.mark.parametrize('func, x', [
        (IntRange(2, 5), '6'),
        (IntRange(), 'a'),
        (IntRange(), '2.'),
    ])
    def test_raise(self, func, x):
        with pytest.raises(ArgumentTypeError):
            func(x)

    @pytest.mark.parametrize('func, expected_repr', [
        (IntRange(0), 'non-negative-int'),
        (IntRange(1), 'positive-int'),
        (IntRange(2), 'int∈[2, ∞)'),
        (IntRange(2, 5), 'int∈[2, 5]'),
    ])
    def test_repr(self, func, expected_repr):
        assert repr(func) == expected_repr


class TestFloatRange:

    @pytest.mark.parametrize('func, x', [
        (FloatRange(0), '2'),
        (FloatRange(0), '0'),
    ])
    def test_call(self, func, x):
        assert func(x) == float(x)

    @pytest.mark.parametrize('func, x', [
        (FloatRange(0, inclusive=False), '0'),
        (FloatRange(), 'a'),
        (FloatRange(), 'inf'),
    ])
    def test_raise(self, func, x):
        with pytest.raises(ArgumentTypeError):
            func(x)

    @pytest.mark.parametrize('func, expected_repr', [
        (FloatRange(0.), 'non-negative-float'),
        (FloatRange(0., inclusive=False), 'positive-float'),
        (FloatRange(1.), 'float∈[1.0, ∞)'),
        (FloatRange(1., inclusive=False), 'float∈(1.0, ∞)'),
    ])
    def test_repr(self, func, expected_repr):
        assert repr(func) == expected_repr


def test_lookup():
    type_ = LookUp({'a': 1, 'b': 2, 'c': 3})
    assert type_('a') == 1
    assert type_('b') == 2
    assert type_('c') == 3


def foo(*args, **kwargs):
    return 'foo', args, kwargs


def goo(*args, **kwargs):
    return 'goo', args, kwargs


class TestFactoryMethod:

    @pytest.fixture
    def type_(self):
        return FactoryMethod(registry={'foo': foo, 'goo': goo})

    @pytest.mark.parametrize('arg_string, expected_output', [
        pytest.param(
            'foo',
            foo(),
            id='empty',
        ),
        pytest.param(
            'foo(1, F1=1.,  F2=1e-4, F3=-1e-4)',
            foo(1, F1=1., F2=1e-4, F3=-1e-4),
            id='int float',
        ),
        pytest.param(
            'foo(False,   B2=True, N=None)',
            foo(False, B2=True, N=None),
            id='bool None',
        ),
        pytest.param(
            'goo(s, S2="s", S3=\'s\')',
            goo('s', S2='s', S3='s'),
            id='string quotation',
        ),
        pytest.param(
            'goo(S1=open, S2=exit,  S3=exec, S4=import, S5=OSError)',
            goo(S1='open', S2='exit', S3='exec', S4='import', S5='OSError'),
            id='no builtins',
        ),
    ])
    def test_store(self, type_, arg_string, expected_output):
        assert type_(arg_string) == expected_output

    @pytest.mark.parametrize('invalid_arg', [
        pytest.param('zoo(1)', id='invalid_choice'),
        pytest.param('foo(x=1=y)', id='invalid_format_='),
        pytest.param('foo(x=1+y=y)', id='invalid_format_split'),
        pytest.param('foo(x=1,x=2)', id='duplicated_key'),
    ])
    def test_raise_invalid_arg(self, type_, invalid_arg):
        with pytest.raises(ArgumentTypeError):
            type_(invalid_arg)
