import functools
import inspect
import termcolor
from inspect import Parameter


def match_abbrev(func):
    signature = inspect.signature(func)
    target_args = [
        key
        for key, param in signature.parameters.items()
        if param.kind in (Parameter.POSITIONAL_OR_KEYWORD, Parameter.KEYWORD_ONLY)
    ]
    bypass_unmatched = any(
        param.kind == Parameter.VAR_KEYWORD
        for param in signature.parameters.values()
    )

    def match_in_func_args(abbrev):
        matches = [kw for kw in target_args if kw.startswith(abbrev)]
        if len(matches) > 1:
            raise TypeError(
                f"{abbrev!r} matches multiple keywords: {format_list(matches)}",
            )
        if len(matches) == 1:
            return matches[0]
        elif bypass_unmatched:  # too short
            return abbrev

        raise TypeError(
            f"{func.__qualname__}() got an unexpected keyword argument {abbrev!r}, "
            f"allowed arguments: {format_list(target_args)}",
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


def format_id(id_str: str, bracket: bool = True) -> str:
    return termcolor.colored(f"[{id_str}]" if bracket else id_str, 'cyan')


def format_list(lst):
    return ', '.join(map(repr, lst))


def dict_of_unique(items):
    output = {}
    for key, val in items:
        if key in output:
            raise ValueError(repr(key))
        output[key] = val
    return output
