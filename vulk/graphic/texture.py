'''
This module allows to load texture and to sample from it
'''
import numpy as np
from vulkbare import load_image

from vulk import vulkanobject as vo
from vulk import vulkanconstant as vc


class RawTexture():
    '''A Raw texture is not initialized with an image file but can be filled
    manually'''

    def __init__(self, context, width, height, texture_format,
                 *args, **kwargs):
        '''
        *Parameters:*

        - `context`: `VulkContext`
        - `width`: Width of the texture
        - `height`: Height of the texture
        - `texture_format`: `Format` of the vulkan texture
        '''

        self.width = width
        self.height = height
        self.format = texture_format
        self.texture = vo.HighPerformanceImage(
            context, vc.ImageType.TYPE_2D, self.format, self.width,
            self.height, 1, 1, 1, vc.SampleCount.COUNT_1)
        self.bitmap = self.init_bitmap(*args, **kwargs)

        # Init view and
        self.view = None
        self.sampler = None
        self.init_view_sampler(context)

    def init_bitmap(self, *args, **kwargs):
        _, _, pixel_size = vc.format_info(self.format)
        return np.zeros(self.width*self.height*pixel_size, dtype=np.uint8)

    def init_view_sampler(self, context):
        self.set_view(context)
        self.set_sampler(context)

    def set_view(self, context):
        '''
        Allow to customize the texture view

        *Parameters:*

        - `context`: `VulkContext`
        '''
        texture_range = vo.ImageSubresourceRange(
            vc.ImageAspect.COLOR, 0, 1, 0, 1)
        self.view = vo.ImageView(
            context, self.texture.final_image,
            vc.ImageViewType.TYPE_2D, self.format, texture_range)

    def set_sampler(self, context, mag_filter=vc.Filter.LINEAR,
                    min_filter=vc.Filter.LINEAR,
                    address_mode_u=vc.SamplerAddressMode.REPEAT,
                    address_mode_v=vc.SamplerAddressMode.REPEAT):
        self.sampler = vo.Sampler(
            context, mag_filter, min_filter, vc.SamplerMipmapMode.LINEAR,
            address_mode_u, address_mode_v, vc.SamplerAddressMode.REPEAT,
            0, True, 16, False, vc.CompareOp.ALWAYS, 0, 0,
            vc.BorderColor.INT_OPAQUE_BLACK, False)

    def upload(self, context):
        '''Upload bitmap into Vulkan memory'''
        with self.texture.bind(context) as t:
            np.copyto(np.array(t, copy=False),
                      self.bitmap,
                      casting='no')


class Texture(RawTexture):
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
        raw_bitmap, width, height, components = load_image(
            open(path_file, 'rb').read())
        texture_format = Texture.components_to_format(components)

        # Create all the components by calling parent init
        super().__init__(context, width, height, texture_format,
                         raw_bitmap=raw_bitmap)

        # Upload data
        self.upload(context)

    def init_bitmap(self, *args, **kwargs):
        return np.array(kwargs['raw_bitmap'], copy=False)

    @staticmethod
    def components_to_format(components):
        if components < 1 or components > 4:
            raise ValueError("components must be between 0 and 4")

        return [vc.Format.NONE, vc.Format.R8_UNORM, vc.Format.R8G8_UNORM,
                vc.Format.R8G8B8_UNORM, vc.Format.R8G8B8A8_UNORM][components]
