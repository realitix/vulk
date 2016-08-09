class Model():
    def __init__(self, mesh, material):
        self.mesh = mesh
        self.material = material
        mesh.bind_shader(material.shader_program)
