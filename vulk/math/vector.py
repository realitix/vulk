import array
import collections
import math


class Vector():
    def __init__(self, values):
        self._values = array.array('f', values)

    def __iter__(self):
        return iter(self._values)

    def __len__(self):
        return len(self._values)

    def __add__(self, value):
        self._update_values(value, "__add__")
        return self

    def __iadd__(self, value):
        return self.__add__(value)

    def __sub__(self, value):
        self._update_values(value, "__sub__")
        return self

    def __isub__(self, value):
        return self.__sub__(value)

    def __mul__(self, value):
        self._update_values(value, "__mul__")
        return self

    def __imul__(self, value):
        return self.__mul__(value)

    def __truediv__(self, value):
        self._update_values(value, "__truediv__")
        return self

    def __itruediv__(self, value):
        return self.__truediv__(value)

    def __getitem__(self, key):
        return self.coordinates[key]

    def __setitem__(self, key, value):
        self._values[key] = value

    def __str__(self):
        return str(self._values)

    def __eq__(self, other):
        return self.coordinates == other.coordinates

    def _check_value(self, value):
        if isinstance(value, collections.Iterable):
            if len(value) != len(self):
                raise ValueError("Dimension of vector is %s but %s "
                                 "coordinates given" %
                                 (len(self), len(value)))
        else:
            value = [value] * len(self)
        return value

    def _update_values(self, value, operator):
        values = self._check_value(value)

        for i in range(len(self)):
            # Get operator (__add__, __sub__, __mul__) and give it the value
            self._values[i] = getattr(self._values[i],
                                      operator)(values[i])

    @property
    def coordinates(self):
        return self._values

    @coordinates.setter
    def coordinates(self, value):
        values = self._check_value(value)

        for i in range(len(self)):
            self._values[i] = values[i]

    @property
    def x(self):
        return self._values[0]

    @x.setter
    def x(self, value):
        self._values[0] = value

    @property
    def y(self):
        return self._values[1]

    @y.setter
    def y(self, value):
        self._values[1] = value

    @property
    def size(self):
        return math.sqrt(self.size2)

    @property
    def size2(self):
        return sum([c ** 2 for c in self._values])

    def normalize(self):
        return self * (1 / self.size)


class Vector2(Vector):
    def __init__(self, x, y):
        super().__init__((x, y))

    def __matmul__(self, value):
        values = self._check_value(value)
        return self.x * values[1] - self.y * values[0]

Vector2.X = Vector2(1, 0)
Vector2.Y = Vector2(0, 1)
Vector2.Zero = Vector2(0, 0)


class Vector3(Vector):

    def __init__(self, x, y, z):
        super().__init__((x, y, z))

    def __matmul__(self, value):
        values = self._check_value(value)
        self.x = self.y * values[2] - self.z * values[1]
        self.y = self.z * values[0] - self.x * values[2]
        self.z = self.x * values[1] - self.y * values[0]
        return self

    @property
    def z(self):
        return self._values[2]

    @z.setter
    def z(self, value):
        self._values[2] = value

Vector3.X = Vector3(1, 0, 0)
Vector3.Y = Vector3(0, 1, 0)
Vector3.Z = Vector3(0, 0, 1)
Vector3.Zero = Vector3(0, 0, 0)
