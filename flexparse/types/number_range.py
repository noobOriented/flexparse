import math
from argparse import ArgumentTypeError


class IntRange:

    def __init__(self, minval=float('-inf'), maxval=float('inf')):  # noqa
        self.minval = minval
        self.maxval = maxval

    def __call__(self, x):
        try:
            int_x = int(x)
        except ValueError:
            raise ArgumentTypeError(f"invalid int value: {x!r}")
        if self.minval <= int_x <= self.maxval:
            return int_x
        else:
            raise ArgumentTypeError(f"{int_x} not in {self._interval}")

    def __repr__(self):
        if (self.minval, self.maxval) == (1, float('inf')):
            return 'positive-int'
        elif (self.minval, self.maxval) == (0, float('inf')):
            return 'non-negative-int'
        else:
            return f'int∈{self._interval}'

    @property
    def _interval(self):
        return _repr_inteval(self.minval, self.maxval, inclusive=True)


class FloatRange:

    def __init__(self, minval=float('-inf'), maxval=float('inf'), inclusive=True):  # noqa
        self.minval = float(minval)
        self.maxval = float(maxval)
        self.inclusive = inclusive

    def __call__(self, x):
        try:
            float_x = float(x)
        except ValueError:
            raise ArgumentTypeError(f"invalid float value: {x!r}")
        if (
            self.minval <= float_x <= self.maxval
            and (self.inclusive or float_x not in (self.minval, self.maxval))
        ):
            return float_x
        else:
            raise ArgumentTypeError(f"{float_x} not in {self._interval}")

    def __repr__(self):
        if (self.minval, self.maxval) == (0., float('inf')):
            return 'non-negative-float' if self.inclusive else 'positive-float'
        else:
            return f'float∈{self._interval}'

    @property
    def _interval(self):
        return _repr_inteval(self.minval, self.maxval, inclusive=self.inclusive)


def _repr_inteval(minval, maxval, inclusive):

    def _math_repr(x):
        if x == float('-inf'):
            return '-∞'
        if x == float('inf'):
            return '∞'
        return repr(x)

    left_bracket = '[' if (inclusive and not math.isinf(minval)) else '('
    right_bracket = ']' if (inclusive and not math.isinf(maxval)) else ')'
    return f"{left_bracket}{_math_repr(minval)}, {_math_repr(maxval)}{right_bracket}"
