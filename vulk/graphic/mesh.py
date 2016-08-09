class Mesh():
    def __init__(self, driver, num_vertices, num_indices, attributes):
        self.driver = driver
        self._data = driver.mesh_data(num_vertices, num_indices, attributes)

    @property
    def vertices(self):
        return self._data.vertices

    @vertices.setter
    def vertices(self, values):
        self.update_vertices(values, 0)

    def update_vertices(self, values, offset=0):
        self._data.update_vertices(values, offset)

    @property
    def indices(self):
        return self._data.indices

    @indices.setter
    def indices(self, values):
        self.update_indices(values, 0)

    def update_indices(self, values, offset=0):
        self._data.update_indices(values, offset)

    def bind_shader(self, shader_program):
        self._data.bind_shader(shader_program)

    def render(self, primitive_type, offset, count):
        with self._data:
            self.driver.render(primitive_type, offset, count)
