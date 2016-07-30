from vulk.math.vector import Vector


def test_init_vector2():
    assert len(Vector(0, 0)) == 2


def test_init_vector3():
    assert len(Vector(0, 0, 0)) == 3


def test_equals():
    assert Vector(1, 2, 3) == Vector(1, 2, 3)
    assert Vector(4, 5) == Vector(4, 5)


def test_iter_vector3():
    vector = Vector(1, 2, 3)
    for t in zip(vector, [1, 2, 3]):
        assert t[0] == t[1]


def test_iter_vector2():
    vector = Vector(1, 2)
    for t in zip(vector, [1, 2]):
        assert t[0] == t[1]


def test_operations_vector3():
    # Add
    assert Vector(1, 2, 3) + 2 == Vector(3, 4, 5)
    assert Vector(1, 2, 3) + (3, 2, 1) == Vector(4, 4, 4)
    assert Vector(1, 2, 3) + Vector(3, 2, 1) == Vector(4, 4, 4)

    # Sub
    assert Vector(1, 2, 3) - 2 == Vector(-1, 0, 1)
    assert Vector(1, 2, 3) - (3, 2, 1) == Vector(-2, 0, 2)
    assert Vector(1, 2, 3) - Vector(3, 2, 1) == Vector(-2, 0, 2)

    # Mul
    assert Vector(1, 2, 3) * 2 == Vector(2, 4, 6)
    assert Vector(1, 2, 3) * (3, 2, 1) == Vector(3, 4, 3)
    assert Vector(1, 2, 3) * Vector(3, 2, 1) == Vector(3, 4, 3)

    # Div
    assert Vector(0, 2, 4) / 2 == Vector(0, 1, 2)
    assert Vector(0, 2, 4) / (3, 2, 1) == Vector(0, 1, 4)
    assert Vector(0, 2, 4) / Vector(3, 2, 1) == Vector(0, 1, 4)


def test_operations_vector2():
    # Add
    assert Vector(1, 2) + 2 == Vector(3, 4)
    assert Vector(1, 2) + (3, 2) == Vector(4, 4)
    assert Vector(1, 2) + Vector(3, 2) == Vector(4, 4)

    # Sub
    assert Vector(1, 2) - 2 == Vector(-1, 0)
    assert Vector(1, 2) - (3, 2) == Vector(-2, 0)
    assert Vector(1, 2) - Vector(3, 2) == Vector(-2, 0)

    # Mul
    assert Vector(1, 2) * 2 == Vector(2, 4)
    assert Vector(1, 2) * (3, 2) == Vector(3, 4)
    assert Vector(1, 2) * Vector(3, 2) == Vector(3, 4)

    # Div
    assert Vector(0, 2) / 2 == Vector(0, 1)
    assert Vector(0, 2) / (3, 2) == Vector(0, 1)
    assert Vector(0, 2) / Vector(3, 2) == Vector(0, 1)
