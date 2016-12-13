import array
import math

from vulk.math.vector import Vector3


class Matrix():

    def __init__(self, values):
        self._values = array.array('f', values)
        self._tmpv = []

    def get_tmp_vec(self, count):
        current = len(self._tmpv)
        if current < count:
            self._tmpv.extend([Vector3]*(count-current))

        return self._tmpv[:count]

    @property
    def values(self):
        return self._values


class Matrix3(Matrix):
    M00 = 0
    M01 = 3
    M02 = 6
    M10 = 1
    M11 = 4
    M12 = 7
    M20 = 2
    M21 = 5
    M22 = 8

    def __init__(self, *args):
        if not args:
            super().__init__([1, 0, 0,
                              0, 1, 0,
                              0, 0, 1])
        elif len(args) == 9:
            super().__init__(args)
        else:
            raise ValueError("Matrix3 needs 9 components")


class Matrix4(Matrix):
    """Matrix4 class

    The matrix is not represented as a multidimensional array but as a simple
    array. To access directly to components, you must use matrix.values
    property and the Mxx keys.
    Mxy: x represents the row and y the colums so M10 is the row 2
    and column 1.
    """
    M = {0:  0,  1: 4,  2: 8,   3: 12,
         10: 1, 11: 5, 12: 9,  13: 13,
         20: 2, 21: 6, 22: 10, 23: 14,
         30: 3, 31: 7, 32: 11, 33: 15}

    def __init__(self, *args):
        if not args:
            super().__init__([1, 0, 0, 0,
                              0, 1, 0, 0,
                              0, 0, 1, 0,
                              0, 0, 0, 1])
        elif len(args) == 16:
            super().__init__(args)
        else:
            raise ValueError("Matrix4 needs 16 components")

    def idt(self):
        v = self.values
        for i in range(len(v)):
            if not i % 5:
                v[i] = 1
            else:
                v[i] = 0
        return self

    def set(self, matrix):
        for i in range(len(self.values)):
            self.values[i] = matrix.values[i]

        return self

    def to_projection(self, near, far, fov, aspect):
        fd = 1 / math.tan((fov * (math.pi / 180)) / 2.0)
        a1 = (far + near) / (near - far)
        a2 = (2 * far * near) / (near - far)
        self.idt()

        v = self.values
        m = Matrix4.M
        v[m[0]] = fd / aspect
        v[m[11]] = fd
        v[m[22]] = a1
        v[m[32]] = -1
        v[m[23]] = a2
        v[m[33]] = 0

        return self

    def to_look_at(self, direction, up):
        tmp0, tmp1, tmp2 = self.get_tmp_vec(3)
        tmp0.set(direction).nor()
        tmp1.set(tmp0).crs(up).nor()
        tmp2.set(tmp1).crs(tmp0).nor()
        self.idt()

        v = self.values
        m = Matrix4.M
        v[m[0]] = tmp1.x
        v[m[1]] = tmp1.y
        v[m[2]] = tmp1.z
        v[m[10]] = tmp2.x
        v[m[11]] = tmp2.y
        v[m[12]] = tmp2.z
        v[m[20]] = -tmp0.x
        v[m[21]] = -tmp0.y
        v[m[22]] = -tmp0.z

        return self

    def to_look_at2(self, position, target, up):
        tmp_v = Vector3()
        tmp_v.set(target).sub(position)
        self.to_look_at(tmp_v, up)

        tmp_m = Matrix4()
        tmp_m.to_translation(Vector3(-position.x, -position.y, -position.z))
        return self.mul(tmp_m)

    def to_translation(self, vector):
        self.idt()

        self.values[Matrix4.M[3]] = vector.x
        self.values[Matrix4.M[13]] = vector.y
        self.values[Matrix4.M[23]] = vector.z

        return self

    def mul(self, matrix):
        tmp = Matrix4()
        ma = self.values
        mb = matrix.values
        m = Matrix4.M

        for key in Matrix4.M.keys():
            k0 = key // 10
            k1 = key % 10
            tmp.values[key] = (ma[m[k0]] * mb[m[k1]] +
                               ma[m[k0 + 1]] * mb[m[k1 + 10]] +
                               ma[m[k0 + 2]] * mb[m[k1 + 20]] +
                               ma[m[k0 + 3]] * mb[m[k1 + 30]])
        return self.set(tmp)
