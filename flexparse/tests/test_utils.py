import pytest

from ..utils import match_abbrev


def test_match_abbrev():

    @match_abbrev
    def format_fruit(apple=1, banana=2, cherry=3, bamboo=None):
        return f"A={apple}, B={banana}, C={cherry}"

    assert format_fruit(che=3) == "A=1, B=2, C=3"
    assert format_fruit(cher=4, bana=5) == "A=1, B=5, C=4"

    with pytest.raises(TypeError):
        format_fruit(1, app=1)  # raise by original function
    with pytest.raises(TypeError):
        format_fruit(appleeee=1)  # doesn't match
    with pytest.raises(TypeError):
        format_fruit(ba=1)  # 1 abbrev -> 2 keywords
    with pytest.raises(TypeError):
        format_fruit(app=1, appl=2)  # 2 abbrevs -> 1 keyword
