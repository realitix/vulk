from vulk.math.vector import Vector2
from vulk.math.vector import Vector3


def test_init():
    assert len(Vector2(0, 0)) == 2
    assert len(Vector3(0, 0, 0)) == 3


def test_equals():
    assert Vector3(1, 2, 3) == Vector3(1, 2, 3)
    assert Vector2(4, 5) == Vector2(4, 5)


def test_iter():
    vector = Vector3(1, 2, 3)
    for t in zip(vector, [1, 2, 3]):
        assert t[0] == t[1]

    vector = Vector2(1, 2)
    for t in zip(vector, [1, 2]):
        assert t[0] == t[1]


def test_operations_vector3():
    # Add
    assert Vector3(1, 2, 3) + 2 == Vector3(3, 4, 5)
    assert Vector3(1, 2, 3) + (3, 2, 1) == Vector3(4, 4, 4)
    assert Vector3(1, 2, 3) + Vector3(3, 2, 1) == Vector3(4, 4, 4)

    # Sub
    assert Vector3(1, 2, 3) - 2 == Vector3(-1, 0, 1)
    assert Vector3(1, 2, 3) - (3, 2, 1) == Vector3(-2, 0, 2)
    assert Vector3(1, 2, 3) - Vector3(3, 2, 1) == Vector3(-2, 0, 2)

    # Mul
    assert Vector3(1, 2, 3) * 2 == Vector3(2, 4, 6)
    assert Vector3(1, 2, 3) * (3, 2, 1) == Vector3(3, 4, 3)
    assert Vector3(1, 2, 3) * Vector3(3, 2, 1) == Vector3(3, 4, 3)

    # Div
    assert Vector3(0, 2, 4) / 2 == Vector3(0, 1, 2)
    assert Vector3(0, 2, 4) / (3, 2, 1) == Vector3(0, 1, 4)
    assert Vector3(0, 2, 4) / Vector3(3, 2, 1) == Vector3(0, 1, 4)


def test_operations_vector2():
    # Add
    assert Vector2(1, 2) + 2 == Vector2(3, 4)
    assert Vector2(1, 2) + (3, 2) == Vector2(4, 4)
    assert Vector2(1, 2) + Vector2(3, 2) == Vector2(4, 4)

    # Sub
    assert Vector2(1, 2) - 2 == Vector2(-1, 0)
    assert Vector2(1, 2) - (3, 2) == Vector2(-2, 0)
    assert Vector2(1, 2) - Vector2(3, 2) == Vector2(-2, 0)

    # Mul
    assert Vector2(1, 2) * 2 == Vector2(2, 4)
    assert Vector2(1, 2) * (3, 2) == Vector2(3, 4)
    assert Vector2(1, 2) * Vector2(3, 2) == Vector2(3, 4)

    # Div
    assert Vector2(0, 2) / 2 == Vector2(0, 1)
    assert Vector2(0, 2) / (3, 2) == Vector2(0, 1)
    assert Vector2(0, 2) / Vector2(3, 2) == Vector2(0, 1)
