'''
This module allows to load texture and to sample from it
'''
import numpy as np
from vulkbare import load_image, resize_image

from vulk import vulkanobject as vo
from vulk import vulkanconstant as vc
from vulk.util import mipmap_size, mipmap_levels


class RawTexture():
    """A Raw texture is not initialized with an image file but can be filled
    manually"""

    def __init__(self, context, width, height, texture_format, mip_levels=1):
        """
        Args:
            context (VulkContext)
            width (int): Width of the texture
            height (int): Height of the texture
            texture_format (Format): Format of vulkan texture
            mip_levels (int): Number of mipmaps
        """
        self.width = width
        self.height = height
        self.format = texture_format
        self.mip_levels = mip_levels or mipmap_levels(width, height)
        self.texture = self.init_texture(context, self.mip_levels)

        # Init bitmap
        self.bitmap = self.init_bitmap()

        # Init view and sampler
        self.view = None
        self.init_view(context)

        self.sampler = None
        self.init_sampler(context)

    def init_texture(self, context, mip_levels):
        return vo.HighPerformanceImage(
            context, vc.ImageType.TYPE_2D, self.format, self.width,
            self.height, 1, mip_levels, 1, vc.SampleCount.COUNT_1)

    def init_view(self, context):
        self.set_view(context)

    def init_sampler(self, context):
        self.set_sampler(context)

    def init_bitmap(self):
        # pylint: disable=unused-argument
        '''Return the numpy array containing bitmap'''
        _, _, pixel_size = vc.format_info(self.format)
        return np.zeros(self.width*self.height*pixel_size, dtype=np.uint8)

    def set_view(self, context):
        """Set texture view

        Args:
            context (VulkContext)
        """
        texture_range = vo.ImageSubresourceRange(
            vc.ImageAspect.COLOR, 0, 1, 0, 1)
        self.view = vo.ImageView(
            context, self.texture.final_image,
            vc.ImageViewType.TYPE_2D, self.format, texture_range)

    def set_sampler(self, context, mag_filter=vc.Filter.NEAREST,
                    min_filter=vc.Filter.NEAREST,
                    mipmap_mode=vc.SamplerMipmapMode.NEAREST,
                    address_mode_u=vc.SamplerAddressMode.REPEAT,
                    address_mode_v=vc.SamplerAddressMode.REPEAT,
                    address_mode_w=vc.SamplerAddressMode.REPEAT,
                    anisotropy_enable=False, max_anisotropy=16):
        """Set the texture sampler

        By default, sampler is configured for the best performance.
        If you want better quality, you must enable manually bilinear,
        trilinear or anisotropic filtering.

        Args:
            context (VulkContext): Context
            mag_filter (Filter): Magnification filter to apply to lookups
            min_filter (Filter): Minification filter to apply to lookups
            mipmap_mode (SamplerMipmapMode): Mipmap filter to apply to lookups
            address_mode_u (SamplerAddressMode):
            address_mode_v (SamplerAddressMode):
            address_mode_w (SamplerAddressMode):
            anisotropy_enable (bool): Whether to enable anisotropy
            max_anisotropy (int): Anisotropy value clamp
        """
        if self.sampler:
            self.sampler.destroy(context)

        self.sampler = vo.Sampler(
            context, mag_filter, min_filter, mipmap_mode,
            address_mode_u, address_mode_v, address_mode_w, 0,
            anisotropy_enable, max_anisotropy, False, vc.CompareOp.ALWAYS,
            0, 0, vc.BorderColor.INT_OPAQUE_BLACK, False)

    def upload(self, context):
        """Make texture accessible for shader

        If this function is not called, the texture can't be used.
        When all your buffers are uploaded, call this function
        """
        self.texture.finalize(context)


class BinaryTexture(RawTexture):
    """RawTexture with provided bitmap buffer.

    **Warning: You are responsible of the bitmap buffer**
    """

    def __init__(self, context, width, height, texture_format, raw_bitmap,
                 mip_levels=1):
        """
        Args:
            context (VulkContext)
            width (int): Texture width
            height (int): Texture height
            texture_format (Format): Texture format
            raw_bitmap (buffer): Bitmap buffer (can be None)
            mip_levels (int): Number of mipmaps to generate (0 = until 1x1)
        """
        self.raw_bitmap = raw_bitmap

        # Create all the components by calling parent init
        super().__init__(context, width, height, texture_format,
                         mip_levels=mip_levels)

        # Upload data
        if self.raw_bitmap:
            self.generate_mipmaps(context)
            self.upload(context)

    def init_bitmap(self):
        '''Initialize bitmap array with `raw_bitmap`'''
        if not self.raw_bitmap:
            return
        return np.array(self.raw_bitmap, dtype=np.uint8, copy=False)

    def upload_buffer(self, context, mip_level):
        """Upload bitmap into Vulkan memory

        Args:
            context (VulkContext)
            mip_level (int): Level of mip
        """
        base_width = self.width
        base_height = self.height
        components = vc.format_info(self.format)[1]
        width, height = mipmap_size(base_width, base_height, mip_level)

        if width == base_width and height == base_height:
            upload_bitmap = self.bitmap
        else:
            upload_raw_bitmap = resize_image(
                self.raw_bitmap, base_width, base_height, components,
                width, height
            )
            upload_bitmap = np.array(upload_raw_bitmap, dtype=np.uint8,
                                     copy=False)

        with self.texture.bind_buffer(context, mip_level) as buf:
            np.copyto(np.array(buf, copy=False),
                      upload_bitmap,
                      casting='no')

    def generate_mipmaps(self, context):
        """Generate mipmap automatically

        This method generates mipmap on processor and then upload it on GPU.
        This method is heavy, use it with care. You shouldn't need to call it
        several times unless raw_bitmap is modified.

        You must call `upload` to update the texture in Graphic Card.

        Args:
            context (VulkContext)
        """
        for i in range(self.mip_levels):
            self.upload_buffer(context, i)


class Texture(BinaryTexture):
    """BinaryTexture with file managing"""

    def __init__(self, context, path_file, mip_levels=1):
        """
        Args:
            context (VulkContext)
            path_file (str): Path to the image to load
            mip_levels (int): Number of mip level (0=max)
        """
        # Load bitmap
        with open(path_file, 'rb') as f:
            raw_bitmap, width, height, components = load_image(f.read())
        texture_format = Texture.components_to_format(components)

        # Create all the components by calling parent init
        super().__init__(context, width, height, texture_format, raw_bitmap,
                         mip_levels=mip_levels)

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


class HighQualityTexture(Texture):
    """Texture with best quality

    To get best quality, we generate automatically all mipmaps and
    set filter to trilinear or anisotropy filtering.
    It's really just a helper class.
    """

    def __init__(self, context, path_file, anisotropy=0):
        self.anisotropy = anisotropy
        # Set mipmap_levels to 0 to generate all mipmaps
        super().__init__(context, path_file, 0)

    def init_sampler(self, context):
        anisotropy_enable = self.anisotropy > 0
        self.set_sampler(context, mag_filter=vc.Filter.LINEAR,
                         min_filter=vc.Filter.LINEAR,
                         mipmap_mode=vc.SamplerMipmapMode.LINEAR,
                         anisotropy_enable=anisotropy_enable,
                         max_anisotropy=self.anisotropy)


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
