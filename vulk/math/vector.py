'''Vector module

This module contains all Vector classes definition.
Vector are a key of graphic computing.
'''
import numpy as np
from numpy import linalg


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
        '''
        *Parameters:*

        - `values`: `list` of `float`
        '''
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

    def __str__(self):
        return str(self._values)

    def __eq__(self, other):
        return all(self._values == other.values)

    def __copy__(self):
        return self.__class__(self._values)

    @property
    def values(self):
        return self._values

    @values.setter
    def values(self, value):
        self._values = value

    @property
    def size(self):
        '''
        Return the size of vector
        '''
        return linalg.norm(self._values)

    def nor(self):
        '''Normalize the vector and return it for chaining'''
        return self * (1 / self.size)

    def crs(self, value):
        '''Return the croos product between the two vectors

        *Parameters:*

        - `value`: `Vector` of the same size
        '''
        return np.cross(self._values, value)


class XMixin():
    '''Mixin adding `x` property to class'''
    @property
    def x(self):
        return self._values[0]

    @x.setter
    def x(self, value):
        self._values[0] = value


class YMixin():
    '''Mixin adding `y` property to class'''
    @property
    def y(self):
        return self._values[1]

    @y.setter
    def y(self, value):
        self._values[1] = value


class ZMixin():
    '''Mixin adding `z` property to class'''
    @property
    def z(self):
        return self._values[2]

    @z.setter
    def z(self, value):
        self._values[2] = value


class Vector2(Vector, XMixin, YMixin):
    '''Vector2 class represents a Vector in 2D space.
    It has two components `x` and `y`.
    '''
    def __init__(self, values=None):
        '''
        *Parameters:*

        - `values`: `list` of 2 `float`
        '''
        if not values:
            super().__init__([0, 0])
        elif len(values) == 2:
            super().__init__(values)
        else:
            raise ValueError("Vector2 needs 2 components")


class Vector3(Vector, XMixin, YMixin, ZMixin):
    '''Vector2 class represents a Vector in 2D space.
    It has two components `x`, `y` and `z`.
    '''
    def __init__(self, values = None):
        '''
        *Parameters:*

        - `values`: `list` of 3 `float`
        '''
        if not values:
            super().__init__([0, 0, 0])
        elif len(values) == 3:
            super().__init__(values)
        else:
            raise ValueError("Vector3 needs 3 components")

        # tmp properties used during computation
        self.tmp = np.zeros(4, dtype=np.float32)
        self.tmp1 = np.zeros(4, dtype=np.float32)

    def mul_matrix4(self, matrix):
        '''Multiply this vector by a `Matrix4`

        *Parameters:*

        - `matrix`: `Matrix4`
        '''
        # prepare tmp
        self.tmp[0:3] = self._values
        self.tmp[3] = 1.

        # load matrix in column order (default is row order)
        # reshape returns a view (I hope!)
        mv = np.reshape(matrix.values, (4, 4), order='F')
        np.dot(mv, self.tmp, out=self.tmp1)
        self._values[:] = self.tmp1[0:3]


# Vector2 constants
Vector2.X = Vector2([1, 0])
Vector2.Y = Vector2([0, 1])
Vector2.Zero = Vector2([0, 0])

# Vector3 constants
Vector3.X = Vector3([1, 0, 0])
Vector3.Y = Vector3([0, 1, 0])
Vector3.Z = Vector3([0, 0, 1])
Vector3.Zero = Vector3([0, 0, 0])
