'''Matrix module

This module contains all class relative to Matrices.
In graphic computing, matrices is a key to manipulate object in
space. I recommand you to read this article to understand what is
the main goal of matrices:
http://www.codinglabs.net/article_world_view_projection_matrix.aspx
'''
import numpy as np


class Matrix():
    '''Base class for Matrix'''
    def __init__(self, values):
        '''
        *Parameters:*

        - `values`: `list` of float

        **Note: In Vulk, Matrix is in column-major order**
        '''
        self._values = np.array(values, dtype=np.float32)

    @property
    def values(self):
        return self._values

    def set(self, values, offset=0):
        '''Set this matrix to `values` from `offset`

        *Parameters:*

        - `values`: `list` of `float`
        - `offset`: Start of the update
        '''
        self._values[offset:] = values

    def to_matrix(self, matrix):
        '''Set this matrix's values to the `matrix` values.

        *Parameters:*

        - `matrix`: Other matrix of the same size
        '''
        self.set(matrix.values)


class Matrix3(Matrix):
    '''Matrix3 class'''

    def __init__(self, values=None):
        '''
        *Parameters:*

        - `values`: `list` of 9 `float`
        '''
        if not values:
            super().__init__([1, 0, 0,
                              0, 1, 0,
                              0, 0, 1])
        elif np.shape(values) == (9,):
            super().__init__(values)
        else:
            raise ValueError("Matrix3 needs 9 components")


class Matrix4(Matrix):
    '''Matrix4 class'''

    def __init__(self, values=None):
        '''
        *Parameters:*

        - `values`: `list` of 16 `float`
        '''
        if not values:
            super().__init__([1, 0, 0, 0,
                              0, 1, 0, 0,
                              0, 0, 1, 0,
                              0, 0, 0, 1])
        elif np.shape(values) == (16,):
            super().__init__(values)
        else:
            raise ValueError("Matrix4 needs 16 components")

        # Tmp property used during computation
        self.tmp = np.zeros(16, dtype=np.float32)

    def mul(self, matrix):
        '''Multiply this matrix by `matrix`
        The order of operation is: `this @ matrix`.

        *Parameters:*

        - `matrix`: `Matrix4`
        '''
        # Make a matrix4 shape to matmul function
        view1 = self._values.view()
        view2 = matrix.values.view()
        view1.shape = (4, 4)
        view2.shape = (4, 4)
        self.tmp.shape = (4, 4)

        np.matmul(view1, view2, out=self.tmp)

        self.tmp.shape = (16,)
        self._values[:] = self.tmp

    def to_identity(self):
        '''Set this matrix to identity matrix'''
        self.values[:] = 0
        self.values[::4] = 1

    def to_orthographic_2d(self, x, y, width, height, near=0, far=1):
        '''Set this matrix to an orthographic matrix used in 2D rendering

        *Parameters:*

        - `x`: X coordinate of the origin
        - `y`: Y coordinate of the origin
        - `width`: Width
        - `hight`: Height
        - `near`: Near plane
        - `Far`: Far plane
        '''
        self.to_orthographic(x, x + width, y, y + height, near, far)

    def to_orthographic(self, left, right, bottom, top, near, far):
        '''
        Set this matrix to an orthographic projection matrix

        *Parameters:*

        - `left`: Left clipping plane
        - `right`: Right clipping plane
        - `bottom`: Bottom clipping plane
        - `top`: Top clipping plane
        - `near`: Near clipping plane
        - `far`: Far clipping plane

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
