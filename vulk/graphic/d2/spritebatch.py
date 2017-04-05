'''SpriteBatch module

SpriteBatch is the pillar of 2D rendering. It has to be very performant
and reliable.
'''
from os import path
import math

from vulk import PATH_VULK_SHADER
from vulk import vulkanconstant as vc
from vulk import vulkanobject as vo
from vulk.graphic import mesh as me
from vulk.graphic.d2.basebatch import BaseBatch


class SpriteBatchDescriptorPool():
    '''
    Manage pool of descriptor sets dedicated to spritebatch textures.
    Theses sets contain uniform buffer and texture.
    '''

    def __init__(self, context, descriptorpool, descriptorlayout):
        self.descriptorsets = []
        self.descriptorset_id = -1
        self.descriptorpool = descriptorpool
        self.descriptorlayout = descriptorlayout

    def pull(self, context):
        self.descriptorset_id += 1

        try:
            descriptorset = self.descriptorsets[self.descriptorset_id]
        except IndexError:
            descriptorset = self.descriptorpool.allocate_descriptorsets(
                context, 1, [self.descriptorlayout])[0]
            self.descriptorsets.append(descriptorset)

        return descriptorset

    def reset(self):
        self.descriptorset_id = -1


class SpriteBatch(BaseBatch):
    '''
    SpriteBatch allows to batch lot of sprites (small quad) into minimum
    of draw calls.
    '''

    def __init__(self, context, size=1000, shaderprogram=None,
                 out_view=None):
        super().__init__(context, size, shaderprogram, out_view)

        self.dspool = self.init_dspool(context)
        self.last_texture = None

    def init_mesh(self, context, size):
        '''Initialize the Mesh handling sprites

        *Parameters:*

        - `context`: `VulkContext`
        - `size`: Number of sprites to handle
        '''
        vertex_attributes = me.VertexAttributes([
            # Position
            me.VertexAttribute(0, vc.Format.R32G32_SFLOAT),
            # Texture UV
            me.VertexAttribute(1, vc.Format.R32G32_SFLOAT),
            # Color
            me.VertexAttribute(2, vc.Format.R32G32B32A32_SFLOAT)
        ])

        return me.Mesh(context, size * 4, size * 6, vertex_attributes)

    def init_descriptorpool(self, context):
        '''Create the descriptor pool

        *Parameters:*

        - `context`: `VulkContext`
        '''
        size = 8
        type_uniform = vc.DescriptorType.UNIFORM_BUFFER
        type_sampler = vc.DescriptorType.COMBINED_IMAGE_SAMPLER
        pool_sizes = [
            vo.DescriptorPoolSize(type_uniform, size),
            vo.DescriptorPoolSize(type_sampler, size)
        ]
        return vo.DescriptorPool(context, pool_sizes, size)

    def init_descriptorlayout(self, context):
        '''Initialize descriptor layout for one uniform and one texture

        *Parameters:*

        - `context`: `VulkContext`
        '''
        ubo_descriptor = vo.DescriptorSetLayoutBinding(
            0, vc.DescriptorType.UNIFORM_BUFFER, 1,
            vc.ShaderStage.VERTEX, None)
        texture_descriptor = vo.DescriptorSetLayoutBinding(
            1, vc.DescriptorType.COMBINED_IMAGE_SAMPLER, 1,
            vc.ShaderStage.FRAGMENT, None)
        layout_bindings = [ubo_descriptor, texture_descriptor]
        return vo.DescriptorSetLayout(context, layout_bindings)

    def init_dspool(self, context):
        return SpriteBatchDescriptorPool(
            context, self.descriptorpool, self.descriptorlayout)

    def get_default_shaderprogram(self, context):
        '''Generate a basic shader program if nono given

        *Parameters:*

        - `context`: `VulkContext`
        '''
        vs = path.join(PATH_VULK_SHADER, "spritebatch.vs.glsl")
        fs = path.join(PATH_VULK_SHADER, "spritebatch.fs.glsl")

        shaders_mapping = {
            vc.ShaderStage.VERTEX: vs,
            vc.ShaderStage.FRAGMENT: fs
        }

        return vo.ShaderProgramGlslFile(context, shaders_mapping)

    def get_descriptor(self, context, texture):
        '''Update descriptor set containing texture

        *Parameters:*

        - `context`: `VulkContext`
        - `texture`: `RawTexture` to update
        '''
        descriptorset = self.dspool.pull(context)

        descriptorub_info = vo.DescriptorBufferInfo(
            self.uniformblock.uniform_buffer.final_buffer, 0,
            self.uniformblock.size)
        descriptorub_write = vo.WriteDescriptorSet(
            descriptorset, 0, 0, vc.DescriptorType.UNIFORM_BUFFER,
            [descriptorub_info])

        descriptorimage_info = vo.DescriptorImageInfo(
            texture.sampler, texture.view,
            vc.ImageLayout.SHADER_READ_ONLY_OPTIMAL)
        descriptorimage_write = vo.WriteDescriptorSet(
            descriptorset, 1, 0, vc.DescriptorType.COMBINED_IMAGE_SAMPLER,
            [descriptorimage_info])

        vo.update_descriptorsets(
            context, [descriptorub_write, descriptorimage_write], [])

        return descriptorset

    def end(self):
        semaphore = super().end()
        self.dspool.reset()

        return semaphore

    def flush(self):
        '''Flush all draws to graphic card.
        Currently, `flush` register and submit command.

        *Parameters:*

        - `context`: `VulkContext`
        '''
        if not self.idx:
            return

        if not self.drawing:
            raise Exception("Not currently drawing")

        # Upload mesh data
        self.mesh.upload(self.context)

        # Bind texture
        descriptorset = self.get_descriptor(self.context, self.last_texture)

        # Compute indices count
        sprites_in_batch = self.idx / 4  # 4 idx per vertex
        indices_count = int(sprites_in_batch) * 6

        # Register commands
        with self.cbpool.pull() as cmd:
            width = self.context.width
            height = self.context.height
            cmd.begin_renderpass(
                self.renderpass,
                self.framebuffer,
                vo.Rect2D(vo.Offset2D(0, 0),
                          vo.Extent2D(width, height)),
                []
            )
            cmd.bind_pipeline(self.pipeline)
            self.mesh.bind(cmd)
            cmd.bind_descriptor_sets(self.pipelinelayout, 0,
                                     [descriptorset], [])
            self.mesh.draw(cmd, 0, indices_count)
            cmd.end_renderpass()

        self.idx = 0

    def draw(self, texture, x, y, width=0, height=0, u=0, v=0, u2=1, v2=1,
             r=1, g=1, b=1, a=1, scale_x=1, scale_y=1, rotation=0):
        '''
        Draw `texture` at position x, y of size `width`, `height`

        *Parameters:*

        - `texture`: `RawTexture`
        - `x`: X position
        - `y`: Y position
        - `width`: Width
        - `heigth`: Height
        - `u`: U texture coordinate
        - `v`: V texture coordinate
        - `r`: Red channel
        - `g`: Green channel
        - `b`: Blue channel
        - `a`: Alpha channel
        - `scale_x`: Scaling on x axis
        - `scale_y`: Scaling on y axis
        - `rotation`: Rotation in radian (clockwise)

        **Note: if width and height are set to 0, we take the image size**
        '''
        if not self.drawing:
            raise Exception("Not currently drawing")

        if self.last_texture is not texture:
            self.flush()

        if not width and not height:
            width = texture.width
            height = texture.height

        self.last_texture = texture

        width *= scale_x
        height *= scale_y

        x2 = x + width
        y2 = y + height

        p1x, p2x, p3x, p4x = x, x, x2, x2
        p1y, p2y, p3y, p4y = y, y2, y2, y

        if rotation:
            cos = math.cos(rotation)
            sin = math.sin(rotation)

            # Set coordinates at origin to do a proper rotation
            w1 = -width / 2
            w2 = width / 2
            h1 = -height / 2
            h2 = height / 2

            x1 = cos * w1 - sin * h1
            y1 = sin * w1 + cos * h1

            x2 = cos * w1 - sin * h2
            y2 = sin * w1 + cos * h2

            x3 = cos * w2 - sin * h2
            y3 = sin * w2 + cos * h2

            x4 = x1 + (x3 - x2)
            y4 = y3 - (y2 - y1)

            x1 += p1x
            x2 += p1x
            x3 += p1x
            x4 += p1x
            y1 += p1y
            y2 += p1y
            y3 += p1y
            y4 += p1y
        else:
            x1, x2, x3, x4 = p1x, p2x, p3x, p4x
            y1, y2, y3, y4 = p1y, p2y, p3y, p4y

        for val in [([x1, y1], [u, v], [r, g, b, a]),
                    ([x2, y2], [u, v2], [r, g, b, a]),
                    ([x3, y3], [u2, v2], [r, g, b, a]),
                    ([x4, y4], [u2, v], [r, g, b, a])]:
            self.mesh.set_vertex(self.idx, val)
            self.idx += 1

    def draw_region(self, region, x, y, width, height, r=1, g=1, b=1, a=1,
                    scale_x=1, scale_y=1, rotation=0):
        '''
        Draw `region` at position x, y of size `width`, `height`

        *Parameters:*

        - `region`: `TextureRegion`
        - `x`: X position
        - `y`: Y position
        - `width`: Width
        - `heigth`: Height
        - `r`: Red channel
        - `g`: Green channel
        - `b`: Blue channel
        - `a`: Alpha channel
        - `scale_x`: Scaling on x axis
        - `scale_y`: Scaling on y axis
        - `rotation`: Rotation in radian (clockwise)
        '''
        u = region.u
        v = region.v
        u2 = region.u2
        v2 = region.v2
        self.draw(region.texture, x, y, width, height, u, u2, v, v2,
                  r, g, b, a, scale_x, scale_y, rotation)
