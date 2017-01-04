'''This module contains mesh'''
import numpy as np

import vulk.vulkanconstant as vc
import vulk.vulkanobject as vo


# Vulk DataType to numpy dtype
datatype_mapping = {
    vc.DataType.UINT8: np.uint8,
    vc.DataType.SINT8: np.int8,
    vc.DataType.UINT16: np.uint16,
    vc.DataType.SINT16: np.int16,
    vc.DataType.UINT32: np.uint32,
    vc.DataType.SINT32: np.int32,
    vc.DataType.UFLOAT16: np.float16,
    vc.DataType.SFLOAT16: np.float16,
    vc.DataType.UFLOAT32: np.float32,
    vc.DataType.SFLOAT32: np.float32,
    vc.DataType.UNORM8: np.uint8,
    vc.DataType.SNORM8: np.int8
}


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
    def __init__(self, context, max_vertices, max_indices, attributes,
                 index_type=vc.IndexType.UINT16):
        '''
        *Parameters:*

        - `max_vertices`: Maximum number of vertices for this mesh
        - `max_indices`: Maximum number of indice for this mesh
        - `attributes`: `VertexAttributes`
        '''
        self.attributes = attributes
        self.index_type = index_type
        self.has_indices = max_indices > 0

        # Create numpy type based of vertex attributes
        numpy_types = []
        for attr in attributes:
            numpy_types.append(('', (datatype_mapping[attr.dtype],
                                     attr.components)))

        # Create vertices array and buffer
        self.vertices_array = np.zeros(max_vertices, dtype=numpy_types)
        self.vertices_buffer = vo.HighPerformanceBuffer(
            context, max_vertices * attributes.size,
            vc.BufferUsage.VERTEX_BUFFER)

        # Create indices array and buffer
        if self.has_indices:
            self.indices_array = np.zeros(max_indices, dtype=np.uint16)
            self.indices_buffer = vo.HighPerformanceBuffer(
                context, max_indices * vc.index_type_size(index_type),
                vc.BufferUsage.INDEX_BUFFER)

    def set_indices(self, indices, offset=0):
        if not self.has_indices:
            raise Exception('No index in this mesh')

        self.indices_array[offset:] = indices

    def set_vertices(self, vertices, offset=0):
        self.vertices_array[offset:] = vertices

    def upload_indices(self, context):
        if not self.has_indices:
            raise Exception('No index in this mesh')

        with self.indices_buffer.bind(context) as b:
            np.copyto(np.array(b, copy=False),
                      self.indices_array.view(dtype=np.uint8),
                      casting='no')

    def upload_vertices(self, context):
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
