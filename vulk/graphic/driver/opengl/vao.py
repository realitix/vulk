import ctypes
import struct

import OpenGL.GL as gl


class Vao():
    """OpenGL Vertex Array Object

    Specify attributes:
    {'position': {
        'size': 4,
        'type': GL_FLOAT,
        'normalized': False
    }}
    default type is GL_FLOAT
    Warning: attributes must be an OrderedDict
    """

    def __init__(self, num_vertices, attributes, usage=gl.GL_STATIC_DRAW):
        """Create new VAO

        :param num_vertices: number of vertices
        :type num_vertices: int
        :param attributes: shader attributes
        :type attributes: dict(dict())
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

    @property
    def vertices(self):
        return self.vertices_buffer

    @vertices.setter
    def vertices(self, values, offset=0):
        self.dirty = True
        start = offset * self.vertex_size * 4
        fmt = '=%df' % len(values)
        struct.pack_into(fmt, self.vertices_buffer, start, *values)

    def bind(self, shader):
        if self.dirty:
            self.reload(shader)

        gl.glBindVertexArray(self.vao)

    def unbind(self):
        gl.glBindVertexArray(0)

    def reload(self, shader):
        # Bind vao and vbo
        gl.glBindVertexArray(self.vao)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self.vbo)

        # Bind attributes
        offset = 0
        for attribute_name, params in self.attributes:
            index = gl.glGetAttribLocation(shader, attribute_name)
            size = params.get('size', 4)
            data_type = params.get('type', gl.GL_FLOAT)
            normalized = params.get('normalized', False)
            stride = self.vertex_size * 4

            gl.glEnableVertexAttribArray(index)
            gl.glVertexAttribPointer(index, size, data_type, normalized,
                                     stride, ctypes.c_void_p(offset))
            offset += size * 4  # float = 4 bytes

        # Bind data
        gl.glBufferData(gl.GL_ARRAY_BUFFER, len(self.vertices_buffer),
                        self._vertices, self.usage)

        # Unbind vao and vbo
        gl.glBindVertexArray(0)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, 0)
