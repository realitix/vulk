import OpenGL.GL as gl

from vulk.graphic import constant as c


def gl_constant(constant):
    return mapping[constant]

mapping = {
    c.TRIANGLES: gl.GL_TRIANGLES
}
