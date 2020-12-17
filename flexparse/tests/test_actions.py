from argparse import Namespace

from ..actions import create_action


def test_create_action():
    action = create_action(
        '-f', '--very-long-argument', '--foo',
        action='append',
    )
    namespace = Namespace()

    for x in range(5):
        action(parser=None, namespace=namespace, values=x)

    assert namespace.very_long_argument == list(range(5))
