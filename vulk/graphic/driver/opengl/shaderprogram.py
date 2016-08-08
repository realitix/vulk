import OpenGL as gl


class ShaderProgram():
    def __init__(self, vertex, fragment, geometry=None, compute=None,
                 tesselation_evaluation=None, tesselation_control=None):
        shaders = []

        def add_shader(shader, gl_shader):
            shaders.append(gl.shaders.compileShader(shader, gl_shader))

        add_shader(vertex, gl.GL_VERTEX_SHADER)
        add_shader(fragment, gl.GL_FRAGMENT_SHADER)

        optionals = {
            gl.GL_GEOMETRY_SHADER: geometry,
            gl.GL_COMPUTE_SHADER: compute,
            gl.GL_TESS_CONTROL_SHADER: tesselation_control,
            gl.GL_TESS_EVALUATION_SHADER: tesselation_evaluation}

        for key, value in optionals:
            if value:
                add_shader(value, key)

        self._shaders = shaders
        self._shader_program = gl.shaders.compileProgram(*self._shaders)

    def __enter__(self):
        gl.glUseProgram(self._shader_program)
        return self

    def __exit__(self, *args):
        gl.glUseProgram(0)

    def delete(self):
        gl.glUseProgram(0)

        for shader in self._shaders:
            gl.glDeleteShader(shader)

        gl.glDeleteProgram(self._shader_program)

        self._shaders = None
        self._shader_program = None
