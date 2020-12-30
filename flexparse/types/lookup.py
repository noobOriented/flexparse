import ast
import builtins
import inspect
import re
from argparse import ArgumentTypeError
from collections import namedtuple
from typing import Dict

from flexparse.formatters import format_choices, format_id, format_list


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


class LookUpCall:

    ArgumentInfo = namedtuple('ArgumentInfo', ['arg_string', 'func_name', 'func', 'args', 'kwargs'])

    def __init__(self, choices: Dict[str, callable], set_info: bool = False):
        if all(map(callable, choices.values())):
            self.choices = choices
        else:
            raise ValueError

        self.set_info = set_info

    def __call__(self, arg_string):
        # clean color
        ANSI_CLEANER = re.compile(r"(\x9B|\x1B\[)[0-?]*[ -/]*[@-~]")
        arg_string = ANSI_CLEANER.sub("", arg_string)
        try:
            func_name, pos_args, kwargs = get_func_name_and_args(arg_string)
        except Exception as e:
            raise ArgumentTypeError(f"invalid value: {arg_string!r} ({getattr(e, 'msg', e)})")

        try:
            func = self.choices[func_name]
        except KeyError:
            raise ArgumentTypeError(
                f"invalid function name: {func_name!r} "
                f"(choose from {format_list(self.choices.keys())})",
            )

        try:
            result = func(*pos_args, **kwargs)
        except TypeError as e:
            raise ArgumentTypeError(str(e))

        if self.set_info:
            result.argument_info = self.ArgumentInfo(arg_string, func_name, func, pos_args, kwargs)
        return result

    def get_helps(self):
        for key, func in self.choices.items():
            yield f"{format_id(key, bracket=False)}{inspect.signature(func)}"

    def __repr__(self):
        return f"{format_choices(self.choices.keys())}(*args, **kwargs)"


def get_func_name_and_args(string: str):
    node = ast.parse(string, mode='eval').body
    if isinstance(node, ast.Name):
        return node.id, (), {}
    if not isinstance(node, ast.Call):
        raise ValueError("can't be parsed as a call.")

    def _convert(node):
        if isinstance(node, (ast.Str, ast.Bytes)):
            return node.s
        elif isinstance(node, ast.Num):
            return node.n
        elif isinstance(node, ast.Tuple):
            return tuple(map(_convert, node.elts))
        elif isinstance(node, ast.List):
            return list(map(_convert, node.elts))
        elif isinstance(node, ast.Set):
            return set(map(_convert, node.elts))
        elif isinstance(node, ast.Dict):
            return {_convert(k): _convert(v) for k, v in zip(node.keys, node.values)}
        elif isinstance(node, ast.NameConstant):  # True, False, None
            return node.value
        elif (
            isinstance(node, ast.UnaryOp)
            and isinstance(node.op, ast.USub)
            and isinstance(node.operand, ast.Num)
        ):
            return -_convert(node.operand)
        elif isinstance(node, ast.Call):
            raise ValueError("inner function call is not allowed")
        elif isinstance(node, ast.Name):
            builtin = getattr(builtins, node.id, None)
            if builtin:
                raise NameError(f"{builtin} is not allowed")
            else:
                raise NameError(f"name {node.id!r} is not defined")
        elif isinstance(node, ast.BinOp):
            raise ValueError("operation is not allowed")

        raise ValueError("forbidden expression")

    return (
        node.func.id,
        [_convert(arg) for arg in node.args],
        {kw.arg: _convert(kw.value) for kw in node.keywords},
    )
