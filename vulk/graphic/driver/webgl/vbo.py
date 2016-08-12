from vulk.graphic.driver.webgl.gl import GL


class Vbo():
    """WebGL Vertex Buffer Object

    Specify attributes:
        {'position': 4, 'normal': 3}
    default type is FLOAT
    Warning: attributes must be an OrderedDict
    """

    def __init__(self, num_vertices, num_indices, attributes,
                 usage=GL.gl.STATIC_DRAW):
        """Create new VBO

        :param num_vertices: number of vertices
        :type num_vertices: int
        :param num_indices: number of indices
        :type num_indices: int
        :param attributes: shader attributes
        :type attributes: dict()
        :returns: Vao
        """

        self.vertex_size = sum([x for x in attributes.values()])
        self.attributes = attributes
        self.num_vertices = num_vertices
        self.usage = usage

        # create array of float (4 bytes)
        self._vertices = bytearray(num_vertices * self.vertex_size * 4)
        self.vertices_buffer = memoryview(self._vertices)

        # create array of short (2 bytes)
        self._indices = bytearray(num_indices * 2)
        self.indices_buffer = memoryview(self._indices)

        self.vao_handle = gl.glGenVertexArrays(1)
        self.vbo_handle = gl.glGenBuffers(1)
        self.ibo_handle = gl.glGenBuffers(1)
        self.dirty = True
        self.bound = False

    def __enter__(self):
        if self.dirty:
            self.bind_data()

        gl.glBindVertexArray(self.vao_handle)
        self.bound = True

    def __exit__(self, *args):
        self.bound = False
        gl.glBindVertexArray(0)

    def delete(self):
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, 0)
        gl.glDeleteBuffers(2, [self.ibo_handle, self.vbo_handle])
        gl.glDeleteVertexArrays(1, [self.vao_handle])

        self.vbo_handle = None
        self.vao_handle = None
        self.ibo_handle = None
        self.vertices_buffer = None
        self._vertices = None
        self.indices_buffer = None
        self._indices = None

    @property
    def vertices(self):
        return self.vertices_buffer

    @vertices.setter
    def vertices(self, values):
        self.update_vertices(values, 0)

    def update_vertices(self, values, offset=0):
        self.dirty = True
        start = offset * self.vertex_size * 4
        fmt = '=%df' % len(values)
        struct.pack_into(fmt, self.vertices_buffer, start, *values)

    @property
    def indices(self):
        return self.indices_buffer

    @indices.setter
    def indices(self, values):
        self.update_indices(values, 0)

    def update_indices(self, values, offset=0):
        self.dirty = True
        start = offset * 2
        fmt = '=%dH' % len(values)
        struct.pack_into(fmt, self.indices_buffer, start, *values)

    def bind_attributes(self, shader_program):
        # Bind vao then vbo
        gl.glBindVertexArray(self.vao_handle)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self.vbo_handle)

        # Bind attributes
        offset = 0
        for attribute_name, size in self.attributes.items():
            index = gl.glGetAttribLocation(shader_program.handle,
                                           attribute_name)
            if index == -1:
                raise Exception()

            data_type = gl.GL_FLOAT
            normalized = False
            stride = self.vertex_size * 4

            gl.glEnableVertexAttribArray(index)
            gl.glVertexAttribPointer(index, size, data_type, normalized,
                                     stride, ctypes.c_void_p(offset))
            offset += size * 4  # float = 4 bytes

        # Unbind vao then vbo
        gl.glBindVertexArray(0)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, 0)

    def bind_data(self):
        gl.glBindVertexArray(self.vao_handle)

        data = [
            (gl.GL_ELEMENT_ARRAY_BUFFER, self.ibo_handle, self.indices_buffer),
            (gl.GL_ARRAY_BUFFER, self.vbo_handle, self.vertices_buffer)]

        for target, handle, buffer in data:
            gl.glBindBuffer(target, handle)
            gl.glBufferData(target, len(buffer), buffer.tobytes(), self.usage)

        gl.glBindVertexArray(0)
        gl.glBindBuffer(gl.GL_ELEMENT_ARRAY_BUFFER, 0)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, 0)

        self.dirty = False
