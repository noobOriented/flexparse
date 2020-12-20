import argparse

from .formatters import ArgumentDefaultsHelpFormatter
from .namespace import Namespace


class ArgumentParser(argparse.ArgumentParser):

    def __init__(
            self,
            prog=None,
            usage=None,
            description=None,
            epilog=None,
            parents=(),
            formatter_class=ArgumentDefaultsHelpFormatter,
            prefix_chars='-',
            fromfile_prefix_chars=None,
            argument_default=None,
            conflict_handler='error',
            add_help=True,
            allow_abbrev=True,
        ):
        super().__init__(
            prog=prog,
            usage=usage,
            description=description,
            epilog=epilog,
            parents=parents,
            formatter_class=formatter_class,
            prefix_chars=prefix_chars,
            fromfile_prefix_chars=fromfile_prefix_chars,
            argument_default=argument_default,
            conflict_handler=conflict_handler,
            add_help=add_help,
            allow_abbrev=allow_abbrev,
        )

    def parse_known_args(self, args=None, namespace=None):
        if namespace is None:
            namespace = Namespace()

        return super().parse_known_args(args, namespace)

    def add_argument_group(self, title=None, description=None, actions=(), **kwargs):
        group = super().add_argument_group(title, description=description, **kwargs)
        for action in actions:
            group._add_action(action)
        return group
