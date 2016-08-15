from browser import window
from javascript import JSConstructor

from vulk.graphic.driver.webgl.gl import GL


class MeshData():
    """WebGL Vertex Buffer Object

    Specify attributes:
        {'position': 4, 'normal': 3}
    default type is FLOAT
    Warning: attributes must be an OrderedDict
    """

    def __init__(self, num_vertices, num_indices, attributes,
                 usage=None):
        """Create new VBO

        :param num_vertices: number of vertices
        :type num_vertices: int
        :param num_indices: number of indices
        :type num_indices: int
        :param attributes: shader attributes
        :type attributes: dict()
        :returns: Vao
        """

        if usage is None:
            usage = GL.gl.STATIC_DRAW

        self.vertex_size = sum([x for x in attributes.values()])
        self.attributes = attributes
        self.num_vertices = num_vertices
        self.usage = usage

        # Create new js types
        ArrayBuffer = JSConstructor(window.ArrayBuffer)
        Float32Array = JSConstructor(window.Float32Array)
        Uint16Array = JSConstructor(window.Uint16Array)

        # Create array of float (4 bytes)
        self._vertices = ArrayBuffer(num_vertices * self.vertex_size * 4)
        self.vertices_buffer = Float32Array(self._vertices)

        # Create array of unsigned short (2 bytes)
        self._indices = ArrayBuffer(num_indices * 2)
        self.indices_buffer = Uint16Array(self._indices)

        self.vbo_handle = GL.gl.createBuffer()
        self.ibo_handle = GL.gl.createBuffer()
        self.dirty = True
        self.bound = False
        self.cached_locations = None

    def __enter__(self):
        GL.gl.BindBuffer(GL.gl.ARRAY_BUFFER, self.vbo_handle)
        GL.gl.BindBuffer(GL.gl.ELEMENT_ARRAY_BUFFER, self.ibo_handle)

        for l in self.cached_locations:
            GL.gl.enableVertexAttribArray(l[0])
            GL.gl.vertexAttribPointer(l[0], l[1], l[2], l[3], l[4], l[5])

        self.bound = True

        if self.dirty:
            self.upload_data()

    def __exit__(self, *args):
        GL.gl.BindBuffer(GL.gl.ARRAY_BUFFER, 0)
        GL.gl.BindBuffer(GL.gl.ELEMENT_ARRAY_BUFFER, 0)
        self.bound = False

    def delete(self):
        GL.gl.deleteBuffers(2, [self.ibo_handle, self.vbo_handle])

        self.vbo_handle = None
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
        self.vertices_buffer.set(values, offset * self.vertex_size)

    @property
    def indices(self):
        return self.indices_buffer

    @indices.setter
    def indices(self, values):
        self.update_indices(values, 0)

    def update_indices(self, values, offset=0):
        self.dirty = True
        self.indices_buffer.set(values, offset)

    def prepare(self, shader_program):
        cached_locations = []
        offset = 0

        for attribute_name, size in self.attributes.items():
            index = GL.gl.getAttribLocation(shader_program.handle,
                                            attribute_name)
            if index == -1:
                raise Exception()

            data_type = GL.gl.FLOAT
            normalized = False
            stride = self.vertex_size * 4

            cached_locations.append((index, size, data_type, normalized,
                                     stride, offset))

            offset += size * 4  # float = 4 bytes

    def upload_data(self):
        GL.gl.BufferData(
            GL.gl.ARRAY_BUFFER, self.vertices_buffer.byteLength,
            self.vertices_buffer, self.usage)
        GL.gl.BufferData(
            GL.gl.ELEMENT_ARRAY_BUFFER, self.indices_buffer.byteLength,
            self.indices_buffer, self.usage)
        self.dirty = False
