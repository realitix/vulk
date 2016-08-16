from vulk.graphic import constant as c
from vulk.graphic.driver.webgl.gl import GL

mapping = None


def gl_constant(constant):
    global mapping
    if not mapping:
        set_mapping()
    return mapping[constant]


def set_mapping():
    global mapping
    mapping = {
        c.TRIANGLES: GL.gl.TRIANGLES
    }
