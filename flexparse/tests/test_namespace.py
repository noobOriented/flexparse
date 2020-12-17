from ..namespace import Namespace


class MockAction:

    def __init__(self, dest):
        self.dest = dest


def test_getitem():
    namespace = Namespace()
    apple_arg = MockAction(dest='apple')
    banana_arg = MockAction(dest='banana')

    namespace.apple = 'Apple'
    namespace.banana = 'Banana'

    assert namespace[apple_arg] == 'Apple'
    assert namespace[[banana_arg, apple_arg]] == ['Banana', 'Apple']
