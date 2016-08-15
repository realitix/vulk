from vulk import exception
from vulk.graphic.driver.webgl.constant import gl_constant
from vulk.graphic.driver.webgl.gl import GL
from vulk.graphic.driver.webgl.meshdata import MeshData
from vulk.graphic.driver.webgl.shaderprogram import ShaderProgram


class WebGLDriver():
    def __init__(self, config):
        get_context = config['canvas'].getContext
        GL.gl = get_context('webgl') or get_context('experimental-webgl')

        if not GL.gl:
            raise exception.VulkError("Can't create webgl context")

        self.mesh_data = MeshData
        self.shader_program = ShaderProgram
        self.clear = clear
        self.render = render


def clear(color=None, depth=None):
    bit = 0

    if color:
        GL.gl.clearColor(*color)
        bit |= GL.gl.COLOR_BUFFER_BIT

    if depth:
        GL.gl.clearDepth(depth)
        bit |= GL.gl.DEPTH_BUFFER_BIT

    GL.gl.clear(bit)


def render(primitive_type, offset, count):
    GL.gl.drawElements(gl_constant(primitive_type), count,
                       GL.gl.UNSIGNED_SHORT, offset * 2)
