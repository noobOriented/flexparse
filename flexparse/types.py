import ast
import math
import os
import re
import termcolor
from itertools import takewhile, dropwhile, starmap
from typing import Dict

from .formatters import format_choices
from .utils import (
    format_id, dict_of_unique, format_list, join_arg_string, get_args, extract_wrapped,
    match_abbrev,
)


class IntRange:

    def __init__(self, minval=-math.inf, maxval=math.inf):
        self.minval = minval
        self.maxval = maxval

    def __call__(self, x):
        return _validate_in_range(int(x), self.minval, self.maxval, inclusive=True)

    def __repr__(self):
        if (self.minval, self.maxval) == (1, math.inf):
            return 'positive-int'
        elif (self.minval, self.maxval) == (0, math.inf):
            return 'non-negative-int'
        else:
            return f'int∈{_repr_inteval(self.minval, self.maxval, inclusive=True)}'


class FloatRange:

    def __init__(self, minval=-math.inf, maxval=math.inf, inclusive=True):
        self.minval = minval
        self.maxval = maxval
        self.inclusive = inclusive

    def __call__(self, x):
        return _validate_in_range(float(x), self.minval, self.maxval, inclusive=self.inclusive)

    def __repr__(self):
        if (self.minval, self.maxval) == (0., math.inf):
            return 'non-negative-float' if self.inclusive else 'positive-float'
        else:
            return f'float∈{_repr_inteval(self.minval, self.maxval, inclusive=self.inclusive)}'


def _validate_in_range(x, minval, maxval, inclusive):
    if math.isinf(x):
        raise ValueError
    if inclusive:
        if not (minval <= x <= maxval):
            raise ValueError
    elif not (minval < x < maxval):
        raise ValueError
    return x


def _repr_inteval(minval, maxval, inclusive):

    def _math_repr(x):
        if x == -math.inf:
            return '-∞'
        if x == math.inf:
            return '∞'
        return repr(x)

    left_bracket = '[' if (inclusive and not math.isinf(minval)) else '('
    right_bracket = ']' if (inclusive and not math.isinf(maxval)) else ')'
    return f"{left_bracket}{_math_repr(minval)}, {_math_repr(maxval)}{right_bracket}"


def path(x):
    return os.path.normpath(x)


def filepath(x):
    """Check if file exists.
    """
    x = path(x)
    if not os.path.isfile(x):
        raise ValueError
    return x


def dirpath(x):
    """Check if directory exists.
    """
    x = path(x)
    if not os.path.isdir(x):
        raise ValueError
    return x


class LookUp:

    def __init__(self, choices: dict):
        self.choices = choices

    def __call__(self, arg_string):
        return self.choices[arg_string]

    def __repr__(self):
        return format_choices(self.choices.keys())


class FactoryMethod:

    COMMA = ','  # TODO configurable color?

    def __init__(
            self,
            registry: Dict[str, callable],
            return_info: bool = False,
            default_as_string: bool = True,
            use_match_abbrev: bool = True,
        ):
        if all(map(callable, registry.values())):
            self.registry = registry
        else:
            raise ValueError

        self.return_info = return_info
        self.default_as_string = default_as_string
        self.use_match_abbrev = use_match_abbrev

    def __call__(self, arg_string):
        # clean color
        ANSI_CLEANER = re.compile(r"(\x9B|\x1B\[)[0-?]*[ -/]*[@-~]")
        arg_string = ANSI_CLEANER.sub("", arg_string)
        if arg_string[-1] == ')':
            try:
                m = re.match(r'(.*)\((.*)\)', arg_string)
                func_name, arg_string = m.group(1), m.group(2)
            except (AttributeError, IndexError):
                raise ValueError(f"invalid arguments: {arg_string!r}")
        else:
            func_name, arg_string = arg_string, ''

        try:
            func = self.registry[func_name]
        except KeyError:
            raise ValueError(
                f"invalid choice: '{func_name}' (choose from {format_list(self.registry.keys())})",
            )
        try:
            pos_args, kwargs = self._parse_arg_string(arg_string)
        except ValueError:
            raise ValueError(f"invalid kwargs: {arg_string!r}")
        except NameError:
            raise ValueError("value should be built-in types.")

        if self.use_match_abbrev:
            result = match_abbrev(func)(*pos_args, **kwargs)
        else:
            result = func(*pos_args, **kwargs)

        if self.return_info:
            return result, CallInfo(func, func_name, *pos_args, **kwargs)
        else:
            return result

    def _parse_arg_string(self, arg_string):
        if not arg_string:
            return (), {}

        arg_list = arg_string.split(',')
        pos_args = tuple(
            self._literal_eval(s)
            for s in takewhile(lambda s: '=' not in s, arg_list)
        )
        kwargs = dict_of_unique(
            self._parse_kwarg(s)
            for s in dropwhile(lambda s: '=' not in s, arg_list)
        )
        return pos_args, kwargs

    def _parse_kwarg(self, item_string):
        try:
            key, val = item_string.split('=')
        except ValueError:
            raise
        return key, self._literal_eval(val)

    def _literal_eval(self, val):
        try:
            val = ast.literal_eval(val)
        except (SyntaxError, ValueError):
            if not self.default_as_string:
                raise ValueError
            # default as string if can't eval
        return val

    @staticmethod
    def format_call(func, *args, **kwargs):
        return CallInfo.format_call(func, *args, **kwargs)

    def get_registry_help(self):

        def format_item(key, val):
            func = extract_wrapped(val)
            arg_string = self.COMMA.join(get_args(func))
            return f"{format_id(key, bracket=False)}({arg_string})"

        help_string = "\n".join(starmap(format_item, self.registry.items()))
        return f"registry & custom options: \n{help_string}\n"

    def __repr__(self):
        return f"{format_choices(self.registry.keys())}(*args{self.COMMA}**kwargs)"


class CallInfo:

    COMMA = termcolor.colored(',', attrs=['dark'])

    def __init__(self, func, func_name, *args, **kwargs):
        self.func = func
        self.func_name = func_name
        self.args = args
        self.kwargs = kwargs

    @property
    def arg_string(self):
        return self.format_call(self.func_name, *self.args, **self.kwargs)

    @classmethod
    def format_call(cls, func, *args, **kwargs):
        func_name = func if isinstance(func, str) else func.__name__
        func_name = format_id(func_name, bracket=False)
        return f"{func_name}({join_arg_string(*args, **kwargs, sep=cls.COMMA)})"
