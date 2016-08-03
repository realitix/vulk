import array


class Matrix():

    def __init__(self, values):
        self._values = array.array('f', values)


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
