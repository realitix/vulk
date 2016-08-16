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
    M00 = 0
    M01 = 4
    M02 = 8
    M03 = 12
    M10 = 1
    M11 = 5
    M12 = 9
    M13 = 13
    M20 = 2
    M21 = 6
    M22 = 10
    M23 = 14
    M30 = 3
    M31 = 7
    M32 = 11
    M33 = 15

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

    def to_projection(self, near, far, fov, aspect):
        fd = 1 / math.tan((fov * (math.pi / 180)) / 2.0)
        a1 = (far + near) / (near - far)
        a2 = (2 * far * near) / (near - far)
        self.idt()

        v = self.values
        v[Matrix4.M00] = fd / aspect
        v[Matrix4.M11] = fd
        v[Matrix4.M22] = a1
        v[Matrix4.M32] = -1
        v[Matrix4.M23] = a2
        v[Matrix4.M33] = 0

        return self

    def to_look_at(self, direction, up):
        tmp0, tmp1, tmp2 = self.get_tmp_vec(3)
        tmp0.set(direction).nor()
        tmp1.set(tmp0).crs(up).nor()
        tmp2.set(tmp1).crs(tmp0).nor()
        self.idt()

        v = self.values
        v[Matrix4.M00] = tmp1.x
        v[Matrix4.M01] = tmp1.y
        v[Matrix4.M02] = tmp1.z
        v[Matrix4.M10] = tmp2.x
        v[Matrix4.M11] = tmp2.y
        v[Matrix4.M12] = tmp2.z
        v[Matrix4.M20] = -tmp0.x
        v[Matrix4.M21] = -tmp0.y
        v[Matrix4.M22] = -tmp0.z

        return self
