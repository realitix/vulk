'''BlockBatch module

BlockBatch is similar to SpriteBatch but it doesn't display sprite.
Instead, it displays block with is a concept similar to a HTML block
stylized with CSS. It allows to create UI easily.
'''
from os import path
import math

from vulk import PATH_VULK_SHADER
from vulk import vulkanconstant as vc
from vulk import vulkanobject as vo
from vulk.graphic import mesh as me
from vulk.graphic.d2.basebatch import BaseBatch


class BlockProperty():
    """Allow to set properties for a draw call"""
    def __init__(self):
        """
        x, y: position
        width, height: size
        colors: color of each point (top-left, top-right, bot-right, bot-left)
        scale: x and y scale
        rotation: rotation in clockwise
        """
        self.x = 0
        self.y = 0
        self.width = 0
        self.height = 0
        self.colors = [[1] * 4] * 4
        self.scale = [1] * 2
        self.rotation = 0
        self.border_widths = [0] * 4
        self.border_radius = [0] * 4
        self.border_colors = [[1] * 4] * 4


class BlockBatch(BaseBatch):
    """
    BlockBatch allows to batch lot of block (small and stylized quad) into
    minimum of draw calls.
    """

    def __init__(self, context, size=1000, shaderprogram=None,
                 out_view=None):
        super().__init__(context, size, shaderprogram, out_view)

        # Init rendering attributes
        self.descriptorsets = self.init_descriptorsets(context)

    def init_mesh(self, context, size):
        '''Initialize the Mesh handling blocks

        *Parameters:*

        - `context`: `VulkContext`
        - `size`: Number of blocks to handle
        '''
        vertex_attributes = me.VertexAttributes([
            # Position
            me.VertexAttribute(0, vc.Format.R32G32_SFLOAT),
            # Texture UV
            me.VertexAttribute(1, vc.Format.R32G32_SFLOAT),
            # Color
            me.VertexAttribute(2, vc.Format.R32G32B32A32_SFLOAT),
            # Border widths
            me.VertexAttribute(3, vc.Format.R32G32B32A32_SFLOAT),
            # Border color (top)
            me.VertexAttribute(4, vc.Format.R32G32B32A32_SFLOAT),
            # Border color (right)
            me.VertexAttribute(5, vc.Format.R32G32B32A32_SFLOAT),
            # Border color (bottom)
            me.VertexAttribute(6, vc.Format.R32G32B32A32_SFLOAT),
            # Border color (left)
            me.VertexAttribute(7, vc.Format.R32G32B32A32_SFLOAT),
            # Border radius
            me.VertexAttribute(8, vc.Format.R32G32B32A32_SFLOAT)
        ])

        return me.Mesh(context, size * 4, size * 6, vertex_attributes)

    def init_descriptorpool(self, context):
        # Only 1 uniform buffer
        size = 1
        pool_sizes = [vo.DescriptorPoolSize(
            vc.DescriptorType.UNIFORM_BUFFER, size)]
        return vo.DescriptorPool(context, pool_sizes, size)

    def init_descriptorlayout(self, context):
        ubo_descriptor = vo.DescriptorSetLayoutBinding(
            0, vc.DescriptorType.UNIFORM_BUFFER, 1,
            vc.ShaderStage.VERTEX, None)
        bindings = [ubo_descriptor]
        return vo.DescriptorSetLayout(context, bindings)

    def init_descriptorsets(self, context):
        """Create the descriptor set (for mat4)"""
        descriptorsets = self.descriptorpool.allocate_descriptorsets(
            context, 1, [self.descriptorlayout])

        descriptorub_info = vo.DescriptorBufferInfo(
            self.uniformblock.uniform_buffer.final_buffer, 0,
            self.uniformblock.size)
        descriptorub_write = vo.WriteDescriptorSet(
            descriptorsets[0], 0, 0, vc.DescriptorType.UNIFORM_BUFFER,
            [descriptorub_info])

        vo.update_descriptorsets(context, [descriptorub_write], [])

        return descriptorsets

    def get_default_shaderprogram(self, context):
        '''Generate a basic shader program if none given

        *Parameters:*

        - `context`: `VulkContext`
        '''
        vs = path.join(PATH_VULK_SHADER, "block.vs.glsl")
        fs = path.join(PATH_VULK_SHADER, "block.fs.glsl")

        shaders_mapping = {
            vc.ShaderStage.VERTEX: vs,
            vc.ShaderStage.FRAGMENT: fs
        }

        return vo.ShaderProgramGlslFile(context, shaders_mapping)

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

        # Compute indices count
        blocks_in_batch = self.idx / 4  # 4 idx per vertex
        indices_count = int(blocks_in_batch) * 6

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
                                     self.descriptorsets, [])
            self.mesh.draw(cmd, 0, indices_count)
            cmd.end_renderpass()

        self.idx = 0

    def draw(self, properties):
        '''
        Draw a block with `properties`

        *Parameters:*

        - `properties`: `BlockProperty`
        '''
        if not self.drawing:
            raise Exception("Not currently drawing")

        width = properties.width * properties.scale[0]
        height = properties.height * properties.scale[1]

        x = properties.x
        y = properties.y
        x2 = x + width
        y2 = y + height

        p1x, p2x, p3x, p4x = x, x, x2, x2
        p1y, p2y, p3y, p4y = y, y2, y2, y

        rotation = properties.rotation

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

        c = properties.colors
        bw = properties.border_widths
        bct = properties.border_colors[0]
        bcr = properties.border_colors[1]
        bcb = properties.border_colors[2]
        bcl = properties.border_colors[3]
        br = properties.border_radius

        for val in [([x1, y1], [0, 0], c[0], bw, bct, bcr, bcb, bcl, br),
                    ([x2, y2], [0, 1], c[3], bw, bct, bcr, bcb, bcl, br),
                    ([x3, y3], [1, 1], c[2], bw, bct, bcr, bcb, bcl, br),
                    ([x4, y4], [1, 0], c[1], bw, bct, bcr, bcb, bcl, br)]:
            self.mesh.set_vertex(self.idx, val)
            self.idx += 1
