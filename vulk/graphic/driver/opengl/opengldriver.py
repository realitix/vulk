from vulk.graphic.driver.opengl import vao, shaderprogram


class OpenGLDriver():
    def __init__(self):
        self.vertices = vao.Vao
        self.shader_program = shaderprogram.ShaderProgram
