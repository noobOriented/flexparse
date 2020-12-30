import pytest

from ..lookup import ArgumentTypeError, LookUp, LookUpCall


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
            'foo(1, I2=0xF, I3=0b101, F1=1., F2=1e-4, F3=-1E-4)',
            foo(1, I2=15, I3=5, F1=1., F2=1e-4, F3=-1e-4),
            id='numbers',
        ),
        pytest.param(
            'foo(B=True, N=None)',
            foo(B=True, N=None),
            id='bool None',
        ),
        pytest.param(
            'foo(S1="s", S2=\'s\', B=b"123")',
            foo(S1="s", S2="s", B=b'123'),
            id='str bytes',
        ),
        pytest.param(
            'foo(L=[1, 2, 3], T=(1, 2, 3), D={1: (2, 3)}, S={1, 2})',
            foo(L=[1, 2, 3], T=(1, 2, 3), D={1: (2, 3)}, S={1, 2}),
            id='collections',
        ),
    ])
    def test_call(self, type_, arg_string, expected_output):
        assert type_(arg_string) == expected_output

    @pytest.mark.parametrize('invalid_arg', [
        pytest.param('zoo(1)', id='invalid_choice'),
        pytest.param('foo(x=1=y)', id='invalid_format_='),
        pytest.param('foo(x=1,x=2)', id='duplicated_key'),
        pytest.param('foo(x=open)', id='no_builtins'),
        pytest.param('foo(x=os.system)', id='unknown_name'),
    ])
    def test_raise_invalid_arg(self, type_, invalid_arg):
        with pytest.raises(ArgumentTypeError):
            type_(invalid_arg)
