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
        self._values = np.fromiter(values, dtype=np.float32, count=len(values))

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
    def values(self, values):
        self._values[:] = values

    @property
    def size(self):
        '''
        Return the size of vector
        '''
        return linalg.norm(self._values)

    def nor(self):
        '''Normalize the vector and return it for chaining'''
        return self * (1 / self.size)

    def crs(self, vector):
        '''Return the cross product between the two vectors

        *Parameters:*

        - `vector`: `Vector` of the same size
        '''
        return self.crs2(vector.values)

    def crs2(self, values):
        '''Set this vector to the cross product with `values`

        *Parameters:*

        - `values`: `list` of 3 float
        '''
        self._values[:] = np.cross(self._values, values)
        return self

    def sub(self, vector):
        '''
        Substract vector from this vector

        *Parameters:*

        - `vector`: `Vector3`
        '''
        return self.sub2(vector.values)

    def sub2(self, values):
        '''
        Substract values from this vector

        *Parameters:*

        - `values`: `list` of `float`
        '''
        self._values -= values
        return self

    def add(self, vector):
        '''
        Add vector to this vector

        *Parameters:*

        - `vector`: `Vector3`
        '''
        return self.add2(vector.values)

    def add2(self, values):
        '''
        Add values to this vector

        *Parameters:*

        - `values`: `list` of `float`
        '''
        self._values += values
        return self


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


class WMixin():
    '''Mixin adding `w` property to class'''
    @property
    def w(self):
        return self._values[3]

    @w.setter
    def w(self, value):
        self._values[3] = value


class Vector2(Vector, XMixin, YMixin):
    '''Vector2 class represents a Vector in 2D space.
    It has two components `x` and `y`.
    '''
    X = None
    Y = None
    Zero = None

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
    '''Vector3 class represents a Vector in 3D space.
    It has three components `x`, `y` and `z`.
    '''
    X = None
    Y = None
    Z = None
    Zero = None

    def __init__(self, values=None):
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
        self.tmp_v4 = Vector4()

    def mul(self, vector):
        '''Multiply this vector by `vector`.

        *Parameters:*

        - `vector`: `Vector3`
        '''
        # TODO: To test and valid
        self._values *= vector.values

    def mul2(self, matrix):
        '''Multiply this vector by a `Matrix4`

        *Parameters:*

        - `matrix`: `Matrix4`
        '''
        self.tmp_v4.set2(self).mul2(matrix)
        self._values[:] = self.tmp_v4.values[0:3]
        return self

    def prj(self, matrix):
        '''
        Project this vector to the `matrix` parameter.
        It's just a multiplication followed by a division by w.



        *Parameters:*

        - `matrix`: `Matrix4`
        '''
        self.tmp_v4.set2(self).mul2(matrix).norw()
        self._values[:] = self.tmp_v4.values[0:3]

    def set(self, x, y, z):
        '''Set values of this vector

        *Parameters:*

        - `x`, `y`, `z`: `float`
        '''
        self._values[0] = x
        self._values[1] = y
        self._values[2] = z

    def set2(self, vector):
        '''Set values of this vector

        *Parameters:*

        - `vector`: `Vector3`
        '''
        self.set(vector.x, vector.y, vector.z)


class Vector4(Vector, XMixin, YMixin, ZMixin, WMixin):
    '''Vector4 class represents a Vector in 3D space.
    It has four components `x`, `y`, `z`, `w`.
    '''
    def __init__(self, values=None):
        '''
        *Parameters:*

        - `values`: `list` of 4 `float`
        '''
        if not values:
            super().__init__([0, 0, 0, 0])
        elif len(values) == 4:
            super().__init__(values)
        else:
            raise ValueError("Vector4 needs 4 components")

        # tmp properties used during computation
        self.tmp = np.zeros(4, dtype=np.float32)

    def set(self, vector):
        '''Set this `Vector4` to `vector`.

        *Parameters:*

        - `vector`: `Vector4`
        '''
        self._values[:] = vector.values
        return self

    def set2(self, vector):
        '''Set this `Vector4` to `vector` and set `w` to 1.

        *Parameters:*

        - `vector`: `Vector3`
        '''
        self._values[0:3] = vector.values
        self._values[3] = 1.
        return self

    def mul(self, vector):
        '''Multiply this vector by `vector`.

        *Parameters:*

        - `vector`: `Vector4`
        '''
        # TODO: To test and valid
        self._values *= vector.values
        return self

    def mul2(self, matrix):
        '''Multiply this vector by a `Matrix4`

        *Parameters:*

        - `matrix`: `Matrix4`
        '''
        # load matrix in column order (default is row order)
        # reshape returns a view (I hope!)
        mv = np.reshape(matrix.values, (4, 4), order='F')
        np.dot(mv, self._values, out=self.tmp)
        self._values[:] = self.tmp
        return self

    def norw(self):
        '''
        W normalization of this vector.
        All components are divided by w, w must not be 0.
        '''
        self._values[0:3] /= self.w


# Vector2 constants
Vector2.X = Vector2([1, 0])
Vector2.Y = Vector2([0, 1])
Vector2.Zero = Vector2([0, 0])

# Vector3 constants
Vector3.X = Vector3([1, 0, 0])
Vector3.Y = Vector3([0, 1, 0])
Vector3.Z = Vector3([0, 0, 1])
Vector3.Zero = Vector3([0, 0, 0])
