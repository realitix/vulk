class Mesh():
    def __init__(self, driver, num_vertices, num_indices, attributes):
        self._vertices = driver.vertices(num_vertices, num_indices, attributes)

    def __enter__(self):
        self._vertices.__enter__()
        return self

    def __exit__(self, *args):
        self._vertices.__exit__(*args)

    @property
    def vertices(self):
        return self._vertices.vertices

    @vertices.setter
    def vertices(self, values):
        self.update_vertices(values, 0)

    def update_vertices(self, values, offset=0):
        self._vertices.update_vertices(values, offset)

    @property
    def indices(self):
        return self._vertices.indices

    @indices.setter
    def indices(self, values):
        self.update_indices(values, 0)

    def update_indices(self, values, offset=0):
        self._vertices.update_indices(values, offset)

    def bind_shader(self, shader_program):
        self._vertices.bind_shader(shader_program)
