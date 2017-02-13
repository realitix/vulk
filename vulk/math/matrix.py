'''Matrix module

This module contains all class relative to Matrices.
In graphic computing, matrices is a key to manipulate object in
space. I recommand you to read this article to understand what is
the main goal of matrices:
http://www.codinglabs.net/article_world_view_projection_matrix.aspx
'''
import numpy as np

from vulk.math.vector import Vector3


class Matrix():
    '''Base class for Matrix'''
    def __init__(self, values):
        '''
        *Parameters:*

        - `values`: `list` of float

        **Note: In Vulk, Matrix is in column-major order**
        '''
        self._values = np.array(values, dtype=np.float32)

    def __len__(self):
        '''Return the matrix size'''
        return len(self._values)

    @property
    def values(self):
        return self._values

    def set(self, matrix):
        '''Set this matrix to `matrix`

        *Parameters:*

        - `matrix`: `Matrix` to set
        '''
        return self.set2(matrix.values)

    def set2(self, values, offset=0):
        '''Set this matrix to `values` from `offset`

        *Parameters:*

        - `values`: `list` of `float`
        - `offset`: Start of the update
        '''
        self._values[offset:] = values
        return self


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

    def __str__(self):
        '''Return a beautiful readable matrix'''
        v = self._values
        return ('{} {} {} {}\n'
                '{} {} {} {}\n'
                '{} {} {} {}\n'
                '{} {} {} {}\n'.format(
                   v[0], v[4], v[8], v[12],
                   v[1], v[5], v[9], v[13],
                   v[2], v[6], v[10], v[14],
                   v[3], v[7], v[11], v[15]))

    def mul(self, matrix):
        '''Multiply this matrix by `matrix`
        The order of operation is: `this @ matrix`.

        *Parameters:*

        - `matrix`: `Matrix4`
        '''
        # Make a matrix4 shape to matmul function
        view1 = np.reshape(self._values, (4, 4))
        view2 = np.reshape(matrix.values, (4, 4))
        self.tmp.shape = (4, 4)

        # np.matmul(view2, view1, out=out)
        np.matmul(view2, view1, out=self.tmp)

        self.tmp.shape = (16,)
        self._values[:] = self.tmp

        return self

    def inv(self):
        '''Inverse this matrix'''
        view = self._values.view()
        view.shape = (4, 4)
        tmp_mat = np.matrix(view, copy=False)
        self._values[:] = tmp_mat.I.flatten()

    def to_identity(self):
        '''Set this matrix to identity matrix'''
        self._values[:] = 0.
        self._values[0] = 1.
        self._values[5] = 1.
        self._values[10] = 1.
        self._values[15] = 1.

        return self


class ViewMatrix(Matrix4):
    '''This class represents a view Matrix.

    View Matrix convert vertex from World space to View space.
    '''
    def to_look_at_direction(self, direction, up):
        '''
        Set this matrix to a *look at* matrix with a `direction` and a `up`
        vector.

        *Parameters:*

        - `direction`: Direction `Vector3`
        - `up`: Up `Vector3`
        '''
        vec_z = Vector3(direction).nor()
        vec_x = Vector3(direction).nor()
        vec_x.crs(up.nor()).nor()
        vec_y = Vector3(vec_x).crs(vec_z).nor()

        self.to_identity()
        self.values[0] = vec_x.x
        self.values[4] = vec_x.y
        self.values[8] = vec_x.z
        self.values[1] = vec_y.x
        self.values[5] = vec_y.y
        self.values[9] = vec_y.z
        self.values[2] = -vec_z.x
        self.values[6] = -vec_z.y
        self.values[10] = -vec_z.z

        return self

    def to_look_at(self, position, target, up):
        '''
        Set this matrix to a *look at* matrix with a `position`, `target` and
        `up` vector.

        *Parameters:*

        - `position`: Position `Vector3`
        - `direction`: Direction `Vector3`
        - `up`: Up `Vector3`
        '''
        # http://www.cs.virginia.edu/~gfx/Courses/1999/intro.fall99.html/lookat.html
        vec = Vector3(target).sub(position)
        self.to_look_at_direction(vec, up)
        translation = TransformationMatrix().to_translation(
            -position.x, -position.y, -position.z)
        self.mul(translation)

        return self


class ProjectionMatrix(Matrix4):
    '''This class represents a projection Matrix.

    Projection is the last step to compute Vertex position.
    It must be applied after the view matrix.
    '''
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
        return self.to_orthographic(x, x + width, y, y + height, near, far)

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
        # https://matthewwellings.com/blog/the-new-vulkan-coordinate-system/

        # OpenGL Orthographic matrix
        # x_orth = 2 / (right - left)
        # y_orth = 2 / (top - bottom)
        # z_orth = -2 / (far - near)

        # tx = -(right + left) / (right - left)
        # ty = -(top + bottom) / (top - bottom)
        # tz = -(far + near) / (far - near)

        # Vulkan Orthographic matrix
        x_orth = 2 / (right - left)
        y_orth = -2 / (top - bottom)
        z_orth = -1 / (far - near)

        tx = -(right + left) / (right - left)
        ty = (top + bottom) / (top - bottom)
        tz = -0.5 * (far + near) / (far - near) + 0.5

        self.to_identity()
        self.values[0] = x_orth
        self.values[5] = y_orth
        self.values[10] = z_orth
        self.values[12] = tx
        self.values[13] = ty
        self.values[14] = tz

        return self


class TransformationMatrix(Matrix4):
    '''This class represents a transformation Matrix.

    It's a Matrix4 with added capabilities used to transform model space
    to world space.
    '''
    def to_translation(self, x, y, z):
        '''
        Set this matrix to a translation matrix.
        First set it to identity and then set the 4th column to the
        translation vector.

        *Parameters:*

        - `x`: x-component of translation vector
        - `y`: y-component of translation vector
        - `z`: z-component of translation vector
        '''
        self.to_identity()
        self._values[12] = x
        self._values[13] = y
        self._values[14] = z

        return self
