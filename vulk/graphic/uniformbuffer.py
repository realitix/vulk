import numpy as np

from vulk import vulkanconstant as vc
from vulk import vulkanobject as vo


class UniformBuffer():
    def __init__(self, context, dtype, size=1):
        self.uniform_array = np.zeros(size, dtype=dtype)
        self.uniform_buffer = vo.HighPerformanceBuffer(
            context, self.uniform_array.nbytes, vc.BufferUsage.UNIFORM_BUFFER)

    def set_uniforms(self, uniforms, offset=0):
        self.uniform_array[offset:] = uniforms

    def upload(self, context):
        with self.uniform_buffer.bind(context) as b:
            np.copyto(np.array(b, copy=False),
                      self.uniform_array.view(dtype=np.unit8),
                      casting='no')
