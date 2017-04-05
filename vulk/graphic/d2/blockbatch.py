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
from vulk import vulkanutil as vu
from vulk.graphic import mesh as me
from vulk.graphic import uniform
from vulk.math.matrix import ProjectionMatrix, TransformationMatrix, Matrix4


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


class BlockBatch():
    """
    BlockBatch allows to batch lot of block (small and stylized quad) into
    minimum of draw calls.
    """

    def __init__(self, context, size=1000, shaderprogram=None,
                 out_view=None):
        '''Initialize BlockBatch

        *Parameters:*

        - `context`: `VulkContext`
        - `size`: Max number of block in one batch
        - `shaderprogram`: Custom `ShaderProgram`
        - `clear`: `list` of 4 `float` (r,g,b,a) or `None`
        - `out_view`: Out `ImageView` to render into

        **Note: By default, `BlockBatch` doesn't clear `out_image`, you have
                to fill `clear` to clear `out_image`**

        **Note: By default, out image is the context `final_image`, you can
                override this behavior with the `out_view` parameter**
        '''
        # ShaderProgram
        if not shaderprogram:
            self.shaderprogram = self.get_default_shaderprogram(context)

        # Stored parameters
        self.out_view = out_view if out_view else context.final_image_view

        # Init rendering attributes
        self.mesh = self.init_mesh(context, size)
        self.init_indices(size)
        self.uniformblock = self.init_uniform(context)
        self.cbpool = self.init_commandpool(context)
        self.renderpass = self.init_renderpass(context)
        self.descriptorpool = self.init_descriptorpool(context)
        self.descriptorlayout = self.init_descriptorlayout(context)
        self.descriptorsets = self.init_descriptorsets(context)
        self.pipelinelayout = self.init_pipelinelayout(context)
        self.pipeline = self.init_pipeline(context)
        self.framebuffer = self.init_framebuffer(context)

        # Others attributes
        self.drawing = False
        self.context = None
        self.projection_matrix = ProjectionMatrix()
        self.projection_matrix.to_orthographic_2d(
            0, 0, context.width, context.height)
        self.transform_matrix = TransformationMatrix()
        self.combined_matrix = Matrix4()
        self.idx = 0
        self.matrices_dirty = True

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

    def init_indices(self, size):
        '''Initialize mesh's indices.
        It's done only at initialization for better performance.

        *Parameters:*

        - `size`: Number of blocks to handle
        '''
        j = 0
        indices = self.mesh.indices_array
        for i in range(0, size * 6, 6):
            indices[i] = j
            indices[i + 1] = j + 1
            indices[i + 2] = j + 2
            indices[i + 3] = j + 2
            indices[i + 4] = j + 3
            indices[i + 5] = j
            j += 4

    def init_uniform(self, context):
        '''Initialize `BlockBatch` uniforms.
        It contains only the `combined_matrix` but you can extend it to add
        uniforms.

        *Parameters:*

        - `context`: `VulkContext`
        '''
        matrix_attribute = uniform.UniformAttribute(
            uniform.UniformShapeType.MATRIX4,
            vc.DataType.SFLOAT32)
        uniform_attributes = uniform.UniformAttributes([matrix_attribute])

        return uniform.UniformBlock(context, uniform_attributes)

    def init_commandpool(self, context):
        return vu.CommandBufferSynchronizedPool(context)

    def init_renderpass(self, context):
        '''Initialize `BlockBatch` renderpass

        *Parameters:*

        - `context`: `VulkContext`
        '''
        attachment = vo.AttachmentDescription(
            self.out_view.image.format, vc.SampleCount.COUNT_1,
            vc.AttachmentLoadOp.LOAD, vc.AttachmentStoreOp.STORE,
            vc.AttachmentLoadOp.DONT_CARE,
            vc.AttachmentStoreOp.DONT_CARE,
            vc.ImageLayout.COLOR_ATTACHMENT_OPTIMAL,
            vc.ImageLayout.COLOR_ATTACHMENT_OPTIMAL)
        subpass = vo.SubpassDescription([vo.AttachmentReference(
            0, vc.ImageLayout.COLOR_ATTACHMENT_OPTIMAL)],
            [], [], [], [])
        dependency = vo.SubpassDependency(
            vc.SUBPASS_EXTERNAL,
            vc.PipelineStage.COLOR_ATTACHMENT_OUTPUT, vc.Access.NONE, 0,
            vc.PipelineStage.COLOR_ATTACHMENT_OUTPUT,
            vc.Access.COLOR_ATTACHMENT_READ | vc.Access.COLOR_ATTACHMENT_WRITE
        )
        return vo.Renderpass(context, [attachment], [subpass], [dependency])

    def init_pipelinelayout(self, context):
        '''Initialize pipeline layout

        *Parameters:*

        - `context`: `VulkContext`
        '''
        return vo.PipelineLayout(context, [self.descriptorlayout])

    def init_pipeline(self, context):
        '''Initialize pipeline

        Here we are to set the Vulkan pipeline.

        *Parameters:*

        - `context`: `VulkContext`
        '''
        # Vertex attribute
        vertex_description = vo.VertexInputBindingDescription(
            0, self.mesh.attributes.size, vc.VertexInputRate.VERTEX)

        vk_attrs = []
        for attr in self.mesh.attributes:
            vk_attrs.append(vo.VertexInputAttributeDescription(
                attr.location, 0, attr.format, attr.offset))

        vertex_input = vo.PipelineVertexInputState(
            [vertex_description], vk_attrs)
        input_assembly = vo.PipelineInputAssemblyState(
            vc.PrimitiveTopology.TRIANGLE_LIST)

        # Viewport and Scissor
        viewport = vo.Viewport(0, 0, context.width, context.height, 0, 1)
        scissor = vo.Rect2D(vo.Offset2D(0, 0),
                            vo.Extent2D(context.width, context.height))
        viewport_state = vo.PipelineViewportState([viewport], [scissor])

        # Rasterization
        rasterization = vo.PipelineRasterizationState(
            False, vc.PolygonMode.FILL, 1, vc.CullMode.BACK,
            vc.FrontFace.COUNTER_CLOCKWISE, 0, 0, 0)

        # Disable multisampling
        multisample = vo.PipelineMultisampleState(
            False, vc.SampleCount.COUNT_1, 0)

        # Disable depth
        depth = None

        # Enable blending
        blend_attachment = vo.PipelineColorBlendAttachmentState(
            True, vc.BlendFactor.SRC_ALPHA,
            vc.BlendFactor.ONE_MINUS_SRC_ALPHA, vc.BlendOp.ADD,
            vc.BlendFactor.SRC_ALPHA, vc.BlendFactor.ONE_MINUS_SRC_ALPHA,
            vc.BlendOp.ADD, vc.ColorComponent.R | vc.ColorComponent.G | vc.ColorComponent.B | vc.ColorComponent.A # noqa
        )
        blend = vo.PipelineColorBlendState(
            False, vc.LogicOp.COPY, [blend_attachment], [0, 0, 0, 0])
        dynamic = None

        return vo.Pipeline(
            context, self.shaderprogram.stages, vertex_input, input_assembly,
            viewport_state, rasterization, multisample, depth,
            blend, dynamic, self.pipelinelayout, self.renderpass)

    def init_framebuffer(self, context):
        '''Create the framebuffer with the final_image (from context)

        *Parameters:*

        - `context`: `VulkContext`
        '''
        return vo.Framebuffer(
            context, self.renderpass, [self.out_view],
            context.width, context.height, 1)

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

    def begin(self, context, semaphores=None):
        '''Begin drawing sprites

        *Parameters:*

        - `context`: `VulkContext`
        - `semaphore`: `list` of `Semaphore` to wait on before
                       starting all drawing operations

        **Note: `context` is borrowed until `end` call**
        '''
        if self.drawing:
            raise Exception("Currently drawing")

        if self.matrices_dirty:
            self.upload_matrices(context)

        self.drawing = True

        # Keep the context only during rendering and release it at `end` call
        self.context = context
        self.cbpool.begin(context, semaphores)

    def end(self):
        '''End drawing of sprite

        *Parameters:*

        - `context`: `VulkContext`

        *Returns:*

        `Semaphore` signaled when all drawing operations in
        `SpriteBatch` are finished
        '''
        if not self.drawing:
            raise Exception("Not currently drawing")

        self.flush()
        self.drawing = False
        self.context = None

        return self.cbpool.end()

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

    def upload_matrices(self, context):
        '''
        Compute combined matrix from transform and projection matrix.
        Then upload combined matrix.

        *Parameters:*

        - `context`: `VulkContext`
        '''
        self.combined_matrix.set(self.projection_matrix)
        self.combined_matrix.mul(self.transform_matrix)
        self.uniformblock.set_uniform(0, self.combined_matrix.values)
        self.uniformblock.upload(context)
        self.matrices_dirty = False

    def update_transform(self, matrix):
        '''Update the transfrom matrix with `matrix`

        *Parameters:*

        - `matrix`: `Matrix4`

        **Note: This function doesn't keep a reference to the matrix,
                it only copies data**
        '''
        self.transform_matrix.set(matrix)
        self.matrices_dirty = True

    def update_projection(self, matrix):
        '''Update the projection matrix with `matrix`

        *Parameters:*

        - `matrix`: `Matrix4`

        **Note: This function doesn't keep a reference to the matrix,
                it only copies data**
        '''
        self.projection_matrix.set(matrix)
        self.matrices_dirty = True

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
