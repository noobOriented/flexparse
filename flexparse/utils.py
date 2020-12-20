import inspect
import itertools
import termcolor
import functools
from typing import List


def match_abbrev(func):
    func_args = get_args(func)
    bypass = inspect.getfullargspec(func).varkw is not None

    def match_in_func_args(abbrev):
        matches = [kw for kw in func_args if kw.startswith(abbrev)]
        if len(matches) > 1:
            raise TypeError(
                f"{abbrev!r} matches multiple keywords: {format_list(matches)}",
            )
        if len(matches) == 1:
            return matches[0]
        elif bypass:  # too short
            return abbrev

        raise TypeError(
            f"{func.__qualname__}() got an unexpected keyword argument {abbrev!r}, "
            f"allowed arguments: {format_list(func_args)}",
        )

    @functools.wraps(func)
    def wrapped(*args, **kwargs):
        try:
            new_kwargs = dict_of_unique(
                (match_in_func_args(key), val) for key, val in kwargs.items()
            )
        except ValueError as e:
            raise TypeError(f"more than one abbrev match to the same keyword: {e}")

        return func(*args, **new_kwargs)

    return wrapped


def get_args(func) -> List[str]:
    func_args = inspect.getfullargspec(func).args
    if func_args and func_args[0] in ('self', 'cls'):
        return func_args[1:]
    return func_args


def extract_wrapped(func, attr_name='__wrapped__'):
    if hasattr(func, attr_name):
        return extract_wrapped(getattr(func, attr_name))
    return func


def format_id(id_str: str, bracket: bool = True) -> str:
    return termcolor.colored(f"[{id_str}]" if bracket else id_str, 'cyan')


def format_list(lst):
    return ', '.join(map(repr, lst))


def join_arg_string(*args, sep=', ', **kwargs):
    return sep.join(itertools.chain(
        map(str, args),
        (f"{k}={v}" for k, v in kwargs.items()),
    ))


def dict_of_unique(items):
    output = {}
    for key, val in items:
        if key in output:
            raise ValueError(repr(key))
        output[key] = val
    return output
