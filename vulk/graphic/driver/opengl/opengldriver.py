import OpenGL.GL as gl

from vulk.graphic.driver.opengl import vao, shaderprogram


class OpenGLDriver():
    def __init__(self):
        self.vertices = vao.Vao
        self.shader_program = shaderprogram.ShaderProgram
        self.clear = clear


def clear(color=None, depth=None):
    bit = 0

    if color:
        gl.glClearColor(*color)
        bit |= gl.GL_COLOR_BUFFER_BIT

    if depth:
        gl.glClearDepth(depth)
        bit |= gl.GL_DEPTH_BUFFER_BIT

    gl.glClear(bit)
