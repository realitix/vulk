'''
This module allows to load texture and to sample from it
'''
import numpy as np
from vulkbare import load_image

from vulk import vulkanobject as vo
from vulk import vulkanconstant as vc


class Texture():
    '''This class represent a texture.

    It handles a Vulkan buffer and a bitmap array (numpy array)
    '''

    def __init__(self, context, path_file):
        '''
        *Parameter:*

        - `context`: `VulkContext`
        - `path_file`: Path to the image to load
        '''
        # Load bitmap
        self.bitmap, self.width, self.height, self.components = load_image(
            open(path_file, 'rb').read())

        # Create vulkan images
        self.format = vc.Format.R8G8B8_UNORM
        self.texture = vo.HighPerformanceImage(
            context, vc.ImageType.TYPE_2D, self.format, self.width,
            self.height, 1, 1, 1, vc.SampleCount.COUNT_1)

        # Upload image into vulkan memory
        with self.texture.bind(context) as t:
            np.copyto(np.array(t, copy=False),
                      np.array(self.bitmap, copy=False),
                      casting='no')
