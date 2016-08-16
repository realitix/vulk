from vulk import exception
from vulk.graphic.driver.webgl.gl import GL


class ShaderProgram():
    def __init__(self, vertex, fragment, **kwargs):
        def get_shader(shader_source, shader_type):
            mapping = {GL.gl.VERTEX_SHADER: 'vertex',
                       GL.gl.FRAGMENT_SHADER: 'fragment'}

            shader = GL.gl.createShader(shader_type)
            GL.gl.shaderSource(shader, shader_source)
            GL.gl.compileShader(shader)

            if not GL.gl.getShaderParameter(shader, GL.gl.COMPILE_STATUS):
                error = "Can't compile {} shader".format(mapping[shader_type])
                log = GL.gl.getShaderInfoLog(shader)
                raise exception.VulkError('\n'.join([error, log]))

            return shader

        vertex_shader = get_shader(vertex, GL.gl.VERTEX_SHADER)
        fragment_shader = get_shader(fragment, GL.gl.FRAGMENT_SHADER)

        program = GL.gl.createProgram()
        GL.gl.attachShader(program, vertex_shader)
        GL.gl.attachShader(program, fragment_shader)
        GL.gl.linkProgram(program)

        if not GL.gl.getProgramParameter(program, GL.gl.LINK_STATUS):
            error = "Can't link program"
            log = GL.gl.getProgramInfoLog(program)
            raise exception.VulkError('\n'.join([error, log]))

        self.handle = program

    def __enter__(self):
        GL.gl.useProgram(self.handle)
        return self

    def __exit__(self, *args):
        GL.gl.useProgram(None)

    def delete(self):
        GL.gl.useProgram(None)

        for shader in self._shaders:
            GL.gl.deleteShader(shader)

        GL.gl.deleteProgram(self.handle)
        self.handle = None
