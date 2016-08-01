import array
import collections
import math


class Vector():

    def __init__(self, *args):
        if len(args) < 2 or len(args) > 3:
            raise TypeError("Vector takes only two or three coordinates,"
                            " %s given" % len(args))
        self._coordinates = array.array('f', args)

    def __iter__(self):
        return iter(self._coordinates)

    def __len__(self):
        return len(self._coordinates)

    def __add__(self, value):
        self._update_coordinates(value, "__add__")
        return self

    def __iadd__(self, value):
        return self.__add__(value)

    def __sub__(self, value):
        self._update_coordinates(value, "__sub__")
        return self

    def __isub__(self, value):
        return self.__sub__(value)

    def __mul__(self, value):
        self._update_coordinates(value, "__mul__")
        return self

    def __imul__(self, value):
        return self.__mul__(value)

    def __matmul__(self, value):
        v = self._check_value(value)
        return self._cross2(v) if len(v) == 2 else self._cross3(v)

    def __truediv__(self, value):
        self._update_coordinates(value, "__truediv__")
        return self

    def __itruediv__(self, value):
        return self.__truediv__(value)

    def __getitem__(self, key):
        return self.coordinates[key]

    def __setitem__(self, key, value):
        self._coordinates[key] = value

    def __str__(self):
        return str(self._coordinates)

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

    def _update_coordinates(self, value, operator):
        values = self._check_value(value)

        for i in range(len(self)):
            # Get operator (__add__, __sub__, __mul__) and give it the value
            self._coordinates[i] = getattr(self._coordinates[i],
                                           operator)(values[i])

    def _cross2(self, values):
        return self.x * values[1] - self.y * values[0]

    def _cross3(self, values):
        self.x = self.y * values[2] - self.z * values[1]
        self.y = self.z * values[0] - self.x * values[2]
        self.z = self.x * values[1] - self.y * values[0]
        return self

    @property
    def coordinates(self):
        return self._coordinates

    @coordinates.setter
    def coordinates(self, value):
        values = self._check_value(value)

        for i in range(len(self)):
            self._coordinates[i] = values[i]

    @property
    def x(self):
        return self._coordinates[0]

    @x.setter
    def x(self, value):
        self._coordinates[0] = value

    @property
    def y(self):
        return self._coordinates[1]

    @y.setter
    def y(self, value):
        self._coordinates[1] = value

    @property
    def z(self):
        if len(self) < 3:
            raise ValueError("Dimension of vector is %s so you can't "
                             "access z value")
        return self._coordinates[2]

    @z.setter
    def z(self, value):
        if len(self) < 3:
            raise ValueError("Dimension of vector is %s so you can't "
                             "set z value")
        self._coordinates[2] = value

    @property
    def size(self):
        return math.sqrt(self.x * self.x + self.y * self.y + self.z * self.z)

    @property
    def size2(self):
        return self.x * self.x + self.y * self.y + self.z * self.z

    def normalize(self):
        return self * (1 / self.size)

X = Vector(1, 0, 0)
Y = Vector(0, 1, 0)
Z = Vector(0, 0, 1)
Zero = Vector(0, 0, 0)
