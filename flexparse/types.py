import ast
import math
import re
import termcolor
from argparse import ArgumentTypeError
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
        try:
            int_x = int(x)
        except ValueError:
            raise ArgumentTypeError(f"invalid int value: {x!r}")
        if self.minval <= int_x <= self.maxval:
            return int_x
        else:
            raise ArgumentTypeError(f"{int_x} not in {self._interval}")

    def __repr__(self):
        if (self.minval, self.maxval) == (1, math.inf):
            return 'positive-int'
        elif (self.minval, self.maxval) == (0, math.inf):
            return 'non-negative-int'
        else:
            return f'int∈{self._interval}'

    @property
    def _interval(self):
        return _repr_inteval(self.minval, self.maxval, inclusive=True)


class FloatRange:

    def __init__(self, minval=-math.inf, maxval=math.inf, inclusive=True):
        self.minval = float(minval)
        self.maxval = float(maxval)
        self.inclusive = inclusive

    def __call__(self, x):
        try:
            float_x = int(x)
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
        if (self.minval, self.maxval) == (0., math.inf):
            return 'non-negative-float' if self.inclusive else 'positive-float'
        else:
            return f'float∈{self._interval}'

    @property
    def _interval(self):
        return _repr_inteval(self.minval, self.maxval, inclusive=self.inclusive)


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


class LookUp:

    def __init__(self, choices: dict):
        self.choices = choices

    def __call__(self, arg_string):
        try:
            return self.choices[arg_string]
        except KeyError:
            raise ArgumentTypeError(
                f"invalid choice: {arg_string!r} (choose from {format_list(self.choices.keys())})",
            )

    def __repr__(self):
        return format_choices(self.choices.keys())


class FactoryMethod:

    COMMA = ','  # TODO configurable color?

    class InvalidLiteralError(Exception):
        pass

    def __init__(
            self,
            registry: Dict[str, callable],
            return_info: bool = False,
            default_as_string: bool = True,
            match_abbrev: bool = True,
        ):
        if all(map(callable, registry.values())):
            self.registry = registry
        else:
            raise ValueError

        self.return_info = return_info
        self.default_as_string = default_as_string
        self.match_abbrev = match_abbrev

    def __call__(self, arg_string):
        # clean color
        ANSI_CLEANER = re.compile(r"(\x9B|\x1B\[)[0-?]*[ -/]*[@-~]")
        arg_string = ANSI_CLEANER.sub("", arg_string)
        if arg_string[-1] == ')':
            try:
                m = re.match(r'(.*)\((.*)\)', arg_string)
                func_name, arg_string = m.group(1), m.group(2)
            except (AttributeError, IndexError):
                raise ArgumentTypeError(f"{arg_string!r} can't be parsed as a call")
        else:
            func_name, arg_string = arg_string, ''

        try:
            func = self.registry[func_name]
        except KeyError:
            raise ArgumentTypeError(
                f"invalid function name: '{func_name}' "
                f"(choose from {format_list(self.registry.keys())})",
            )
        try:
            pos_args, kwargs = self._parse_arg_string(arg_string)
        except self.InvalidLiteralError as e:
            raise ArgumentTypeError(str(e))
        except Exception:
            raise ArgumentTypeError(f"invalid syntax: {arg_string!r}")

        try:
            if self.match_abbrev:
                result = match_abbrev(func)(*pos_args, **kwargs)
            else:
                result = func(*pos_args, **kwargs)
        except TypeError as e:
            raise ArgumentTypeError(str(e))

        if self.return_info:
            return result, CallInfo(func, func_name, *pos_args, **kwargs)
        else:
            return result

    def _parse_arg_string(self, arg_string):
        if not arg_string:
            return (), {}

        arg_list = [arg.strip(' ') for arg in arg_string.split(',')]
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
        key, val = item_string.split('=')
        return key, self._literal_eval(val)

    def _literal_eval(self, val):
        try:
            val = ast.literal_eval(val)
        except Exception:
            if not self.default_as_string:
                raise self.InvalidLiteralError(
                    f"{val!r} can't be evaled to built-in types",
                )
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
