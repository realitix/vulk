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

    def __init__(self, num_vertices, attributes, usage=gl.GL_STATIC_DRAW):
        """Create new VAO

        :param num_vertices: number of vertices
        :type num_vertices: int
        :param attributes: shader attributes
        :type attributes: dict()
        :returns: Vao
        """

        self.vertex_size = sum([x for x in attributes.values()])
        self.attributes = attributes
        self.num_vertices = num_vertices
        self.usage = usage
        self._vertices = bytearray(num_vertices * self.vertex_size * 4)
        self.vertices_buffer = memoryview(self._vertices)

        self.vao = gl.glGenVertexArrays(1)
        self.vbo = gl.glGenBuffers(1)
        self.dirty = True

    def __enter__(self):
        if self.dirty:
            self.bind_vbo()

        gl.glBindVertexArray(self.vao)

    def __exit__(self, *args):
        gl.glBindVertexArray(0)

    def delete(self):
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, 0)
        gl.glDeleteBuffers(1, [self.vbo])
        gl.glDeleteVertexArrays(1, [self.vao])

        self.vbo = None
        self.vao = None
        self.vertices_buffer = None
        self._vertices = None

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

    def bind_vbo(self):
        # Bind vao and vbo
        gl.glBindVertexArray(self.vao)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self.vbo)

        # Bind data
        gl.glBufferData(gl.GL_ARRAY_BUFFER, len(self.vertices_buffer),
                        self._vertices, self.usage)

        # Unbind vao and vbo
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, 0)
        gl.glBindVertexArray(0)
