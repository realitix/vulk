'''Vector module

This module contains all Vector class definition
'''
import numpy as np
from numpy import linalg

from vulk.math.matrix import Matrix4


class Vector():
    '''Base class for Vector

    *Exemple:*

    ```
    v1 += 10 # Add 10 to all components
    v1 += [10, 9, 8] # Add a different value to each component
    dot_product = v1 @ v2 # Dot product use the matmul operator
    ```

    **Note: Vector is just a wrapper around a numpy array. You can
            get directly the numpy array if you need more power**
    '''
    def __init__(self, values):
        self._values = np.array(values, dtype=np.float32)

    def __iter__(self):
        return iter(self._values)

    def __len__(self):
        return len(self._values)

    def __add__(self, value):
        self._values += value
        return self

    def __iadd__(self, value):
        return self.__add__(value)

    def __sub__(self, value):
        self._values -= value
        return self

    def __isub__(self, value):
        return self.__sub__(value)

    def __mul__(self, value):
        self._values *= value
        return self

    def __imul__(self, value):
        return self.__mul__(value)

    def __matmul__(self, value):
        return self._values @ value

    def __imatmul__(self, value):
        return self.__matmul__(value)

    def __truediv__(self, value):
        self._values /= value
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
        return all(self._values == other.coordinates)

    def __copy__(self):
        return self.__class__(self._values)

    @property
    def coordinates(self):
        return self._values

    @coordinates.setter
    def coordinates(self, value):
        self._values = value

    @property
    def size(self):
        return linalg.norm(self._values)

    def nor(self):
        return self * (1 / self.size)

    def crs(self, value):
        return np.cross(self._values, value)


class XMixin():
    @property
    def x(self):
        return self._values[0]

    @x.setter
    def x(self, value):
        self._values[0] = value


class YMixin():
    @property
    def y(self):
        return self._values[1]

    @y.setter
    def y(self, value):
        self._values[1] = value


class ZMixin():
    @property
    def z(self):
        return self._values[2]

    @z.setter
    def z(self, value):
        self._values[2] = value


class Vector2(Vector, XMixin, YMixin):
    def __init__(self, *args):
        if not args:
            super().__init__((0, 0))
        elif len(args) == 2:
            super().__init__(args)
        else:
            raise ValueError("Vector2 needs 2 components")


class Vector3(Vector, XMixin, YMixin, ZMixin):
    def __init__(self, *args):
        if not args:
            super().__init__((0, 0, 0))
        elif len(args) == 3:
            super().__init__(args)
        else:
            raise ValueError("Vector3 needs 3 components")


# Vector2 constants
Vector2.X = Vector2(1, 0)
Vector2.Y = Vector2(0, 1)
Vector2.Zero = Vector2(0, 0)

# Vector3 constants
Vector3.X = Vector3(1, 0, 0)
Vector3.Y = Vector3(0, 1, 0)
Vector3.Z = Vector3(0, 0, 1)
Vector3.Zero = Vector3(0, 0, 0)
