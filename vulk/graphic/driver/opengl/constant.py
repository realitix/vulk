import OpenGL.GL as gl

from vulk.graphic.constant import Constant as c


def gl_constant(constant):
    return mapping['constant']

mapping = {
    c.TRIANGLES: gl.GL_TRIANGLES
}
