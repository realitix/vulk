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

        **Note: You can use *args and **kwargs to pass data in `init_bitmap`
                but you must subclass `RawTexture`**
        '''

        self.width = width
        self.height = height
        self.format = texture_format
        self.texture = vo.HighPerformanceImage(
            context, vc.ImageType.TYPE_2D, self.format, self.width,
            self.height, 1, 1, 1, vc.SampleCount.COUNT_1)

        # Init bitmap
        self.bitmap = self.init_bitmap(*args, **kwargs)

        # Init view and sampler
        self.view = None
        self.sampler = None
        self.set_view(context)
        self.set_sampler(context)

    def init_bitmap(self):
        '''Return the numpy array containing bitmap'''
        _, _, pixel_size = vc.format_info(self.format)
        return np.zeros(self.width*self.height*pixel_size, dtype=np.uint8)

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
                    address_mode_v=vc.SamplerAddressMode.REPEAT,
                    anisotropy_enable=True, max_anisotropy=16):
        '''
        Allow to customize the texture sampler

        *Parameters:*

        - `context`: `VulkContext`
        - `mag_filter`: `Filter` vulk constant
        - `min_filter`: `Filter` vulk constant
        - `address_mode_u`: `SamplerAddressMode` vulk constant
        - `address_mode_v`: `SamplerAddressMode` vulk constant
        '''
        if self.sampler:
            self.sampler.destroy(context)

        self.sampler = vo.Sampler(
            context, mag_filter, min_filter, vc.SamplerMipmapMode.LINEAR,
            address_mode_u, address_mode_v, vc.SamplerAddressMode.REPEAT,
            0, anisotropy_enable, max_anisotropy, False, vc.CompareOp.ALWAYS,
            0, 0, vc.BorderColor.INT_OPAQUE_BLACK, False)

    def upload(self, context):
        '''Upload bitmap into Vulkan memory

        *Parameters:*

        - `context`: `VulkContext`
        '''
        with self.texture.bind(context) as t:
            np.copyto(np.array(t, copy=False),
                      self.bitmap,
                      casting='no')


class BinaryTexture(RawTexture):
    '''
    RawTexture with provided bitmap buffer.

    **Warning: You are responsible of the bitmap buffer**
    '''

    def __init__(self, context, width, height, texture_format, raw_bitmap,
                 *args, **kwargs):
        '''
        *Parameter:*

        - `context`: `VulkContext`
        - `width`: Width of the texture
        - `height`: Height of the texture
        - `texture_format`: `Format` of the vulkan texture
        - `raw_bitmap`: Buffer to a bitmap
        '''
        # Create all the components by calling parent init
        super().__init__(context, width, height, texture_format,
                         raw_bitmap=raw_bitmap, *args, **kwargs)

        # Upload data
        self.upload(context)

    def init_bitmap(self, **kwargs):
        '''Initialize bitmap array with `raw_bitmap`'''
        return np.array(kwargs['raw_bitmap'], dtype=np.uint8, copy=False)


class Texture(BinaryTexture):
    '''
    BinaryTexture with file managing.
    '''

    def __init__(self, context, path_file, *args, **kwargs):
        '''
        *Parameter:*

        - `context`: `VulkContext`
        - `path_file`: Path to the image to load
        '''
        # Load bitmap
        with open(path_file, 'rb') as f:
            raw_bitmap, width, height, components = load_image(f.read())
        texture_format = Texture.components_to_format(components)

        # Create all the components by calling parent init
        super().__init__(context, width, height, texture_format, raw_bitmap,
                         *args, **kwargs)

    @staticmethod
    def components_to_format(components):
        '''Convert number of channel components in image to Vulkan format

        *Parameters:*

        - `components`: Number of components
        '''
        if components < 1 or components > 4:
            raise ValueError("components must be between 0 and 4")

        return [vc.Format.NONE, vc.Format.R8_UNORM, vc.Format.R8G8_UNORM,
                vc.Format.R8G8B8_UNORM, vc.Format.R8G8B8A8_UNORM][components]


class TextureRegion():
    '''
    Defines a rectangular area of a texture. The coordinate system used has
    its origin in the upper left corner with the x-axis pointing to the
    right and the y axis pointing downwards.
    '''

    def __init__(self, texture, u=0, v=0, u2=1, v2=1):
        '''Initialize texture region

        *Parameters:*

        - `texture`: `RawTexture`
        - `u`, `u2`: X coordinate relative to texture size
        - `v`, `v2`: Y coordinate relative to texture size
        '''
        self.texture = texture
        self.u = u
        self.u2 = u2
        self.v = v
        self.v2 = v2

    @staticmethod
    def from_pixels(texture, x, y, width, height):
        """Create a TextureRegion with pixel coordinates

        Args:
            texture (Texture): Base texture of region
            x (int): X offset (left to right)
            y (int): Y offset (top to bottom)
            width (int): Region width
            height (int): Region height

        Returns:
            The new TextureRegion
        """
        u = x / texture.width
        u2 = u + width / texture.width
        v = y / texture.height
        v2 = v + height / texture.height
        return TextureRegion(texture, u, v, u2, v2)

    def set_texture(self, texture):
        '''Set texture of `TextureRegion`

        *Parameters:*

        - `texture`: `RawTexture`
        '''
        self.texture = texture

    def set_region(self, u, u2, v, v2):
        '''Set coordinate relatively to texture size

        *Parameters:*

        - `u`, `u2`: X coordinate relative to texture size
        - `v`, `v2`: Y coordinate relative to texture size
        '''
        self.u = u
        self.u2 = u2
        self.v = v
        self.v2 = v2

    def set_region_pixel(self, x, y, width, height):
        '''Set coordinate relatively to pixel size

        *Parameters:*

        - `x`: X coordinate of the texture
        - `y`: Y coordinate of the texture
        - `width`: Width of the region
        - `height`: Height of the region
        '''
        inv_width = 1. / self.texture.width
        inv_height = 1. / self.texture.height
        self.set_region(
            x * inv_width, y * inv_height,
            (x + width) * inv_width, (y + height) * inv_height
        )
