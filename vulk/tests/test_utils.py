from vulk import utils

import numbers


def test_returns_number():
    assert isinstance(utils.millis(), numbers.Number)
