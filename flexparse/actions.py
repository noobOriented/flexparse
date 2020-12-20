import inspect
from argparse import (
    Action,
    _StoreAction,
    _StoreConstAction,
    _StoreTrueAction,
    _StoreFalseAction,
    _AppendAction,
    _AppendConstAction,
    _CountAction,
    _HelpAction,
    _VersionAction,
)
from typing import Dict, List, Union, Type

from more_itertools import first_true


def create_action(
        *options,
        action: Union[str, Type[Action]] = 'store',
        dest: str = None,
        **kwargs,  # custom for each action
    ) -> Action:
    # refactor https://github.com/python/cpython/blob/3.9/Lib/argparse.py#L1385-L1434
    # only support options
    _validate_option_strings_prefix(options)
    dest = dest or _find_dest(options)
    if inspect.isclass(action):
        action_cls = action
    else:
        try:
            action_cls = _ACTION_MAP.get(action, action)
        except KeyError:
            raise ValueError(f"invalid action {action}")

    return action_cls(option_strings=options, dest=dest, **kwargs)


def _find_dest(options: List[str]):
    # strings starting with two prefix characters are long options
    # dest is first long_options or first_options
    dest = first_true(options, pred=lambda s: s[1] == PREFIX_CHAR, default=options[0])
    # infer destination, '--foo-bar' -> 'foo_bar' and '-x' -> 'x'
    return dest.lstrip(PREFIX_CHAR).replace('-', '_')


def _validate_option_strings_prefix(options):
    for s in options:
        # error on strings that don't start with an appropriate prefix
        if s[0] != PREFIX_CHAR:
            raise ValueError(
                f"invalid option string {s!r}: must start with a character {PREFIX_CHAR!r}",
            )


_ACTION_MAP: Dict[str, Action] = {
    'store': _StoreAction,
    'store_const': _StoreConstAction,
    'store_true': _StoreTrueAction,
    'store_false': _StoreFalseAction,
    'append': _AppendAction,
    'append_const': _AppendConstAction,
    'count': _CountAction,
    'help': _HelpAction,
    'version': _VersionAction,
}
PREFIX_CHAR = '-'  # hardcoded, not support others
