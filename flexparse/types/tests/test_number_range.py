import pytest

from ..number_range import ArgumentTypeError, IntRange, FloatRange


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
        (IntRange(), '1e-4'),
        (IntRange(), '0b01'),
        (IntRange(), '0xAA'),
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
        (FloatRange(0), 'inf'),
        (FloatRange(0), '1e-4'),
    ])
    def test_call(self, func, x):
        assert func(x) == float(x)

    @pytest.mark.parametrize('func, x', [
        (FloatRange(0, inclusive=False), '0'),
        (FloatRange(inclusive=False), 'inf'),
        (FloatRange(), 'a'),
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
