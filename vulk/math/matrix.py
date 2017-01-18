'''Matrix module

This module contains all class relative to Matrix
'''
import numpy as np


class Matrix():
    '''Base class for Matrix'''
    def __init__(self, values):
        self._values = np.array(values, dtype=np.float32)

    @property
    def values(self):
        return self._values

    def set(self, values, offset=0):
        self._values[offset:] = values

    def to_matrix(self, matrix):
        self.set(matrix.values)


class Matrix3(Matrix):
    '''Matrix3 class'''

    def __init__(self, *args):
        if not args:
            super().__init__([1, 0, 0,
                              0, 1, 0,
                              0, 0, 1])
        elif np.shape(args) == (9,):
            super().__init__(args)
        else:
            raise ValueError("Matrix3 needs 9 components")


class Matrix4(Matrix):
    '''Matrix4 class'''

    def __init__(self, *args):
        if not args:
            super().__init__([1, 0, 0, 0,
                              0, 1, 0, 0,
                              0, 0, 1, 0,
                              0, 0, 0, 1])
        elif np.shape(args) == (16,):
            super().__init__(args)
        else:
            raise ValueError("Matrix4 needs 16 components")

    def mul(self, matrix):
        # Make a matrix4 shape to matmul function
        view1 = self._values.view()
        view2 = matrix.values.view()
        view1.shape = (4, 4)
        view2.shape = (4, 4)

        result = np.matmul(view1, view2)
        self._values = result.reshape((16,))

    def to_identity(self):
        self.values[:] = 0
        self.values[::4] = 1

    def to_orthographic_2d(self, x, y, width, height, near=0, far=5):
        self.to_orthographic(x, x + width, y, y + height, near, far)

    def to_orthographic(self, left, right, bottom, top, near, far):
        '''
        Set this matrix to an orthographic projection matrix

        **Note: Vulkan coordinate system is not the same as OpenGL,
                thus the matrix is adapted to Vulkan**
        '''
        x_orth = 2 / (right - left)
        y_orth = 2 / (top - bottom)
        z_orth = 1 / (far - near)

        tx = -(right + left) / (right - left)
        ty = -(top + bottom) / (top - bottom)
        tz = 0

        self.values[:] = 0
        self.values[0] = x_orth
        self.values[5] = y_orth
        self.values[10] = z_orth
        self.values[12] = tx
        self.values[13] = ty
        self.values[14] = tz
        self.values[15] = 1
