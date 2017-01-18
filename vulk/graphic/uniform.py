from enum import IntEnum
import numpy as np

from vulk import vulkanconstant as vc
from vulk import vulkanobject as vo


class UniformShapeType(IntEnum):
    MATRIX4 = 16


class UniformAttribute():
    def __init__(self, shape_type, data_type):
        '''
        *Parameters:*

        - `shape_type`: `UniformShapeType`
        - `data_type`: `Format` constant from `vulkconstant`
        '''
        self.dtype = data_type
        self.components = shape_type.value
        self.size = vc.DataTypeByte[data_type] * self.components
        self.offset = 0


class UniformAttributes():
    def __init__(self, attributes):
        '''
        *Parameters:*

        - `attributes`: `list` of `UniformAttribute`

        **Note: Order of attributes is important, it must be the same
                as in the shader**
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


class UniformBlock():
    def __init__(self, context, attributes):
        '''
        *Parameters:*

        - `context`: `VulkContext`
        - `attributes`: `UniformAttributes`
        '''
        self.attributes = attributes

        # Create numpy type based on uniform attributes
        numpy_dtype = []
        for attr in attributes:
            numpy_dtype.append(
                ('', vc.DataTypeNumpy[attr.dtype], attr.components))

        self.uniform_array = np.zeros(1, dtype=numpy_dtype)
        self.uniform_buffer = vo.HighPerformanceBuffer(
            context, self.uniform_array.nbytes,
            vc.BufferUsage.UNIFORM_BUFFER)
        self.size = self.uniform_array.nbytes

    def set_uniform(self, index, uniform):
        '''
        Update uniform at `index` position

        *Parameters:*

        - `index`: Position of uniform in `UniformAttributes`
        - `uniform`: Uniform data to pass (flattened)
        '''
        self.uniform_array[index] = uniform

    def upload(self, context):
        with self.uniform_buffer.bind(context) as b:
            np.copyto(np.array(b, copy=False),
                      self.uniform_array.view(dtype=np.uint8),
                      casting='no')
