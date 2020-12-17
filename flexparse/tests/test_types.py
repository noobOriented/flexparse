import os

import pytest

from ..types import (
    int_in_range,
    float_in_range,
    path,
    filepath,
    dirpath,
    LookUp,
    FactoryMethod,
)


@pytest.mark.parametrize('func, x, valid', [
    (int_in_range(0), '2', True),
    (int_in_range(0), '0', True),
    (int_in_range(2, 5), '6', False),
    (int_in_range(), 'a', False),
    (int_in_range(), '2.', False),
])
def test_int_in_range(func, x, valid):
    if valid:
        assert func(x) == int(x)
    else:
        with pytest.raises(ValueError):
            func(x)


@pytest.mark.parametrize('func, x, valid', [
    (float_in_range(0), '2', True),
    (float_in_range(0), '0', True),
    (float_in_range(0, inclusive=False), '0', False),
    (float_in_range(), 'a', False),
    (float_in_range(), 'inf', False),
])
def test_float_in_range(func, x, valid):
    if valid:
        assert func(x) == float(x)
    else:
        with pytest.raises(ValueError):
            func(x)


def test_path():
    assert path("A//B") == path("A/B/") == path("A/./B") == path("A/foo/../B") == "A/B"


def test_filepath(tmpdir):
    filename = os.path.join(tmpdir, 'new_file')
    with pytest.raises(ValueError):
        filepath(filename)

    with open(filename, 'w'):
        pass
    assert filepath(filename) == filename


def test_dirpath(tmpdir):
    assert dirpath(tmpdir) == tmpdir
    with pytest.raises(ValueError):
        dirpath(os.path.join(tmpdir, 'dir_not_existed'))


@pytest.mark.parametrize('func, expected_name', [
    (int_in_range(0), 'nonnegative_int'),
    (int_in_range(1), 'positive_int'),
    (int_in_range(2), 'int∈[2, ∞)'),
    (int_in_range(2, 5), 'int∈[2, 5]'),
    (float_in_range(0.), 'nonnegative_float'),
    (float_in_range(0., inclusive=False), 'positive_float'),
    (float_in_range(1.), 'float∈[1.0, ∞)'),
    (float_in_range(1., inclusive=False), 'float∈(1.0, ∞)'),
])
def test_name(func, expected_name):
    assert func.__name__ == expected_name


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
            'foo(1,F1=1.,F2=1e-4,F3=-1e-4)',
            foo(1, F1=1., F2=1e-4, F3=-1e-4),
            id='int float',
        ),
        pytest.param(
            'foo(False,B2=True,N=None)',
            foo(False, B2=True, N=None),
            id='bool None',
        ),
        pytest.param(
            'goo(s,S2="s",S3=\'s\')',
            goo('s', S2='s', S3='s'),
            id='string quotation',
        ),
        pytest.param(
            'goo(S1=open,S2=exit,S3=exec,S4=import,S5=OSError)',
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
        with pytest.raises(ValueError):
            type_(invalid_arg)
