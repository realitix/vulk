from vulk import util

import numbers


def test_returns_number():
    assert isinstance(util.millis(), numbers.Number)
