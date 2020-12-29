from functools import partial

import pytest

from ..lookup import ArgumentTypeError, LookUp, LookUpCall, LookUpPartial


class TestLookUp:

    def test_call(self):
        type_ = LookUp({'a': 1, 'b': 2, 'c': 3})
        assert type_('a') == 1
        assert type_('b') == 2
        assert type_('c') == 3

    def test_raise(self):
        type_ = LookUp({'a': 1, 'b': 2, 'c': 3})
        with pytest.raises(ArgumentTypeError):
            type_('d')


def foo(*args, **kwargs):
    return 'foo', args, kwargs


def goo(*args, **kwargs):
    return 'goo', args, kwargs


class TestLookUpCall:

    @pytest.fixture(scope='class')
    def type_(self):
        return LookUpCall(choices={'foo': foo, 'goo': goo})

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
    def test_call(self, type_, arg_string, expected_output):
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


def hoo(a, *, b, c):
    return a, b, c


class TestLookPartial:

    @pytest.fixture(scope='class')
    def type_(self):
        return LookUpPartial(choices={'hoo': hoo}, target_signature=['a'])

    @pytest.mark.parametrize('arg_string, expected_output', [
        pytest.param(
            'hoo(b=2,c=3)',
            partial(hoo, b=2, c=3),
            id='empty',
        ),
    ])
    def test_call(self, type_, arg_string, expected_output):
        assert type_(arg_string)(a=1) == expected_output(a=1)

    @pytest.mark.parametrize('invalid_arg', [
        pytest.param('hoo(d=4)', id='unexpected_argument'),
    ])
    def test_raise_invalid_arg(self, type_, invalid_arg):
        with pytest.raises(ArgumentTypeError):
            type_(invalid_arg)
