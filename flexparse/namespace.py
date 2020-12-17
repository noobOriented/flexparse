import argparse
from typing import List, Union


class Namespace(argparse.Namespace):

    # NOTE syntax sugar
    def __getitem__(self, key: Union[argparse.Action, List[argparse.Action]]):
        if isinstance(key, list):
            return [getattr(self, action.dest) for action in key]
        else:
            return getattr(self, key.dest)
