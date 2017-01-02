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


class Matrix3(Matrix):
    '''Matrix3 class'''
    def __init__(self, *args):
        if not args:
            super().__init__([[1, 0, 0],
                              [0, 1, 0],
                              [0, 0, 1]])
        elif np.shape(args) == (3, 3):
            super().__init__(args)
        else:
            raise ValueError("Matrix3 needs 9 components")


class Matrix4(Matrix):
    '''Matrix4 class'''
    def __init__(self, *args):
        if not args:
            super().__init__([[1, 0, 0, 0],
                              [0, 1, 0, 0],
                              [0, 0, 1, 0],
                              [0, 0, 0, 1]])
        elif np.shape(args) == (4, 4):
            super().__init__(args)
        else:
            raise ValueError("Matrix4 needs 16 components")
