'''This module contains mesh'''
import numpy as np

import vulk.vulkanconstant as vc
import vulk.vulkanobject as vo


class VertexAttribute():
    def __init__(self, location, attribute_format):
        '''
        *Parameters:*

        - `location`: Attribute location in shader
        - `attribute_format`: `Format` constant from `vulkanconstant`
        '''
        dtype, num_components, size = vc.format_info(attribute_format)

        self.location = location
        self.format = attribute_format
        self.dtype = dtype
        self.components = num_components
        self.size = size
        self.offset = 0


class VertexAttributes():
    def __init__(self, attributes):
        '''
        *Parameters:*

        - `attributes`: `list` of `VertexAttribute`
        '''
        self.attributes = attributes

        offset = 0
        for attr in attributes:
            attr.offset = offset
            offset += attr.size

    @property
    def size(self):
        return sum([a.size for a in self.attributes])

    def __iter__(self):
        return iter(self.attributes)


class Mesh():
    def __init__(self, context, max_vertices, max_indices, attributes):
        '''
        *Parameters:*

        - `context`: `VulkContext`
        - `max_vertices`: Maximum number of vertices for this mesh
        - `max_indices`: Maximum number of indice for this mesh
        - `attributes`: `VertexAttributes`
        '''
        self.index_type = vc.IndexType.UINT16
        if max_vertices > 65535:
            self.index_type = vc.IndexType.UINT32

        self.attributes = attributes
        self.has_indices = max_indices > 0

        # Create numpy type based on vertex attributes
        numpy_dtype = []
        for attr in attributes:
            numpy_dtype.append(
                ('', vc.DataTypeNumpy[attr.dtype],  attr.components))

        # Create vertices array and buffer
        self.vertices_array = np.zeros(max_vertices, dtype=numpy_dtype)
        self.vertices_buffer = vo.HighPerformanceBuffer(
            context, self.vertices_array.nbytes,
            vc.BufferUsage.VERTEX_BUFFER)

        # Create indices array and buffer
        if self.has_indices:
            self.indices_array = np.zeros(max_indices, dtype=np.uint16)
            self.indices_buffer = vo.HighPerformanceBuffer(
                context, max_indices * vc.index_type_size(self.index_type),
                vc.BufferUsage.INDEX_BUFFER)

        # Create othens attributes
        self.dirty_indices = True
        self.dirty_vertices = True

    def set_indices(self, indices, offset=0):
        if not self.has_indices:
            raise Exception('No index in this mesh')

        self.indices_array[offset:] = indices
        self.dirty_indices = True

    def set_vertices(self, vertices, offset=0):
        self.vertices_array[offset:] = vertices
        self.dirty_vertices = True

    def upload_indices(self, context):
        if not self.has_indices:
            raise Exception('No index in this mesh')

        if not self.dirty_indices:
            return
        self.dirty_indices = False

        with self.indices_buffer.bind(context) as b:
            np.copyto(np.array(b, copy=False),
                      self.indices_array.view(dtype=np.uint8),
                      casting='no')

    def upload_vertices(self, context):
        if not self.dirty_vertices:
            return
        self.dirty_vertices = False

        with self.vertices_buffer.bind(context) as b:
            np.copyto(np.array(b, copy=False),
                      self.vertices_array.view(dtype=np.uint8),
                      casting='no')

    def upload(self, context):
        self.upload_vertices(context)

        if self.has_indices:
            self.upload_indices(context)

    def bind(self, cmd):
        '''Bind the buffers during command buffer registering

        *Parameters:*

        - `command`: `CommandBufferRegister`
        '''
        cmd.bind_vertex_buffers(
            0, 1, [self.vertices_buffer.final_buffer], [0])

        if self.has_indices:
            cmd.bind_index_buffer(
                self.indices_buffer.final_buffer, 0, self.index_type)

    def draw(self, cmd, offset=0, count=0):
        '''Draw the mesh during command buffer registration

        *Parameters:*

        - `cmd`: `CommandBufferRegister`
        - `offset`: Start drawing at `offset` vertices
        - `count`: Draw `count` vertices

        **Note: `offset` and `count` target indices if mesh is indexed**
        '''
        if self.has_indices:
            if not count:
                count = len(self.indices_array) - offset
            cmd.draw_indexed(count, offset)
        else:
            if not count:
                count = len(self.vertices_array) - offset
            cmd.draw(count, offset)
