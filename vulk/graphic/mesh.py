class Mesh():
    def __init__(self, driver, num_vertices, num_indices, attributes):
        self.driver = driver
        self._data = driver.mesh_data(num_vertices, num_indices, attributes)
        self.bound_attributes = False

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

    def prepare(self, shader_program):
        self._data.prepare(shader_program)
        self.bound_attributes = True

    def render(self, primitive_type, offset, count):
        if not self.bound_attributes:
            raise Exception("Attributes not bounded, "
                            "you must call bind_attributes")

        with self._data:
            self.driver.render(primitive_type, offset, count)
