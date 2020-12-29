import abc
import ast
import inspect
import re
from argparse import ArgumentTypeError
from collections import namedtuple
from functools import partial
from itertools import takewhile, dropwhile
from typing import Dict, List

from flexparse.formatters import format_choices
from flexparse.utils import format_id, dict_of_unique, format_list, match_abbrev


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


class _LookUpCallBase(abc.ABC):

    ArgumentInfo = namedtuple('ArgumentInfo', ['arg', 'func_name', 'param_string'])

    def __init__(
            self,
            choices: Dict[str, callable],
            set_info: bool = False,
            default_as_str: bool = True,
            match_abbrev: bool = True,
        ):
        if all(map(callable, choices.values())):
            self.choices = choices
        else:
            raise ValueError

        self.set_info = set_info
        self.default_as_str = default_as_str
        self.match_abbrev = match_abbrev

    def __call__(self, arg_string):
        try:
            func_name, param_string = split_func_name_and_param_string(arg_string)
        except (AttributeError, IndexError):
            raise ArgumentTypeError(f"{arg_string!r} can't be parsed as a call")

        try:
            func = self.choices[func_name]
        except KeyError:
            raise ArgumentTypeError(
                f"invalid function name: {func_name!r} "
                f"(choose from {format_list(self.choices.keys())})",
            )
        try:
            pos_args, kwargs = get_pos_keyword_args(param_string, self.default_as_str)
        except InvalidLiteralError as e:
            raise ArgumentTypeError(str(e))
        except Exception:
            raise ArgumentTypeError(f"invalid syntax: {param_string!r}")

        result = self.make_result(func, *pos_args, **kwargs)
        if self.set_info:
            result.argument_info = self.ArgumentInfo(arg_string, func_name, param_string)
        return result

    @abc.abstractmethod
    def make_result(self, func, *args, **kwargs):
        pass

    def get_helps(self):
        for key, func in self.choices.items():
            yield f"{format_id(key, bracket=False)}{inspect.signature(func)}"

    def __repr__(self):
        return f"{format_choices(self.choices.keys())}(*args, **kwargs)"


class LookUpCall(_LookUpCallBase):

    def make_result(self, func, *args, **kwargs):
        try:
            if self.match_abbrev:
                return match_abbrev(func)(*args, **kwargs)
            else:
                return func(*args, **kwargs)
        except TypeError as e:
            raise ArgumentTypeError(str(e))


class LookUpPartial(_LookUpCallBase):

    def __init__(
            self,
            choices: Dict[str, callable],
            target_signature: List[str] = None,
            default_as_str: bool = True,
            match_abbrev: bool = True,
        ):
        super().__init__(choices, default_as_str, match_abbrev)
        self.target_signature = target_signature

    def make_result(self, func, *args, **kwargs):
        try:
            signature = inspect.signature(func)
            kwargs = signature.bind_partial(*args, **kwargs).arguments
        except TypeError as e:
            raise ArgumentTypeError(str(e))

        return partial(func, **kwargs)

    def get_helps(self):
        for key, func in self.choices.items():
            if self.target_signature is not None:
                original_signature = inspect.signature(func)
                signature = inspect.Signature(
                    p
                    for p in original_signature.parameters.values()
                    if p.name not in self.target_signature
                )
            else:
                signature = inspect.signature(func)

            yield f"{format_id(key, bracket=False)}{signature}"


def split_func_name_and_param_string(arg_string):
    # clean color
    ANSI_CLEANER = re.compile(r"(\x9B|\x1B\[)[0-?]*[ -/]*[@-~]")
    arg_string = ANSI_CLEANER.sub("", arg_string)
    if arg_string[-1] == ')':
        m = re.match(r'(.*)\((.*)\)', arg_string)
        return m.group(1), m.group(2)
    else:
        return arg_string, ''


def get_pos_keyword_args(arg_string, default_as_str: bool = True):
    if not arg_string:
        return (), {}

    def literal_eval(val):
        try:
            val = ast.literal_eval(val)
        except Exception:
            if not default_as_str:
                raise InvalidLiteralError(f"{val!r} can't be evaled to built-in types")
            # default as string if can't eval
        return val

    def parse_item(item_string):
        key, val = item_string.split('=')
        return key, literal_eval(val)

    arg_list = [arg.strip(' ') for arg in arg_string.split(',')]
    pos_args = tuple(
        literal_eval(s)
        for s in takewhile(lambda s: '=' not in s, arg_list)
    )
    kwargs = dict_of_unique(
        parse_item(s)
        for s in dropwhile(lambda s: '=' not in s, arg_list)
    )
    return pos_args, kwargs


class InvalidLiteralError(Exception):

    pass
