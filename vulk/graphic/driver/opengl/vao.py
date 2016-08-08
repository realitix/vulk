import ctypes
import struct

import OpenGL.GL as gl


class Vao():
    """OpenGL Vertex Array Object

    Specify attributes:
        {'position': 4, 'normal': 3}
    default type is GL_FLOAT
    Warning: attributes must be an OrderedDict
    """

    def __init__(self, num_vertices, num_indices, attributes,
                 usage=gl.GL_STATIC_DRAW):
        """Create new VAO

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

        self.vao = gl.glGenVertexArrays(1)
        self.vbo = gl.glGenBuffers(1)
        self.ibo = gl.glGenBuffers(1)
        self.dirty = True
        self.is_bound = False

    def __enter__(self):
        self.is_bound = True
        if self.dirty:
            self.bind_vbo()
            self.bind_ibo()

        gl.glBindVertexArray(self.vao)

    def __exit__(self, *args):
        self.is_bound = False
        gl.glBindVertexArray(0)

    def delete(self):
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, 0)
        gl.glDeleteBuffers(2, [self.ibo, self.vbo])
        gl.glDeleteVertexArrays(1, [self.vao])

        self.vbo = None
        self.vao = None
        self.ibo = None
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
        fmt = '=%dh' % len(values)
        struct.pack_into(fmt, self.indices_buffer, start, *values)

    def bind_shader(self, shader):
        # Bind vao
        gl.glBindVertexArray(self.vao)

        # Bind attributes
        offset = 0
        for attribute_name, size in self.attributes:
            index = gl.glGetAttribLocation(shader, attribute_name)
            data_type = gl.GL_FLOAT
            normalized = False
            stride = self.vertex_size * 4

            gl.glEnableVertexAttribArray(index)
            gl.glVertexAttribPointer(index, size, data_type, normalized,
                                     stride, ctypes.c_void_p(offset))
            offset += size * 4  # float = 4 bytes

        # Unbind vao
        gl.glBindVertexArray(0)

    def bind_ibo(self):
        # Bind vao and ibo
        gl.glBindVertexArray(self.vao)
        gl.glBindBuffer(gl.GL_ELEMENT_ARRAY_BUFFER, self.ibo)

        # Bind data
        gl.glBufferData(gl.GL_ELEMENT_ARRAY_BUFFER, len(self.indices_buffer),
                        self._indices, self.usage)

        # Unbind vao and ibo
        gl.glBindBuffer(gl.GL_ELEMENT_ARRAY_BUFFER, 0)
        gl.glBindVertexArray(0)
