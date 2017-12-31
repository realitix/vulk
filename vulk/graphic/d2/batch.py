'''BaseBatch module

BaseBatch is used by SpriteBatch and BlockBatch.
'''
from abc import ABC, abstractmethod
from os import path
import math

from vulk import PATH_VULK_SHADER
from vulk import vulkanconstant as vc
from vulk import vulkanobject as vo
from vulk import vulkanutil as vu
from vulk.graphic import mesh as me
from vulk.graphic import uniform
from vulk.math.matrix import ProjectionMatrix, TransformationMatrix, Matrix4


class BaseBatch(ABC):
    def __init__(self, context, size=1000, shaderprogram=None,
                 out_view=None):
        """Initialize BaseBatch

        Args:
            context (VulkContext)
            size (int): Max number of blocks in one batch
            shaderprogram (ShaderProgram): Custom shader program
            clear (list[float]): 4 `float` (r,g,b,a) or `None`
            out_view (ImageView): Out image view to render into

        **Note: By default, `BaseBatch` doesn't clear `out_image`, you have
                to fill `clear` to clear `out_image`**

        **Note: By default, out image is the context `final_image`, you can
                override this behavior with the `out_view` parameter**
        """
        # ShaderProgram
        if not shaderprogram:
            shaderprogram = self.get_default_shaderprogram(context)
        self.shaderprogram = shaderprogram

        # Stored parameters
        self.custom_out_view = out_view is not None
        self.out_view = out_view if out_view else context.final_image_view

        # Init rendering attributes
        self.mesh = self.init_mesh(context, size)
        self.init_indices(size)
        self.uniformblock = self.init_uniform(context)
        self.cbpool = self.init_commandpool(context)
        self.descriptorpool = self.init_descriptorpool(context)
        self.descriptorlayout = self.init_descriptorlayout(context)
        self.pipelinelayout = self.init_pipelinelayout(context)

        self.renderpass = self.init_renderpass(context)
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
        self.reload_count = context.reload_count

    @abstractmethod
    def init_descriptorlayout(self, context):
        """Initialize and return descriptor layout

        Args:
            context (VulkContext)

        Returns:
            DescriptorSetLayout
        """
        pass

    def reload(self, context):
        """Reload the spritebatch

        Args:
            context (VulkContext)
        """
        # Reload projection matrix
        self.projection_matrix.to_orthographic_2d(
            0, 0, context.width, context.height)
        self.matrices_dirty = True

        # Reload out view
        if not self.custom_out_view:
            self.out_view = context.final_image_view

        # Reload renderpass, pipeline and framebuffer
        self.renderpass.destroy(context)
        self.renderpass = self.init_renderpass(context)

        self.pipeline.destroy(context)
        self.pipeline = self.init_pipeline(context)

        self.framebuffer.destroy(context)
        self.framebuffer = self.init_framebuffer(context)

        # Update reload count
        self.reload_count = context.reload_count

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

        if self.reload_count != context.reload_count:
            raise Exception("Batch not reloaded, can't draw")

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


class SpriteBatchDescriptorPool():
    '''
    Manage pool of descriptor sets dedicated to spritebatch textures.
    Theses sets contain uniform buffer and texture.
    '''

    def __init__(self, descriptorpool, descriptorlayout):
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

        self.dspool = self.init_dspool()
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

    def init_dspool(self):
        return SpriteBatchDescriptorPool(self.descriptorpool,
                                         self.descriptorlayout)

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
        """Flush all draws to graphic card

        Currently, flush register and submit command.

        Args:
            context (VulkContext)
        """
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

            x4 = cos * w2 - sin * h1
            y4 = sin * w2 + cos * h1

            x_abs = p1x + width / 2
            y_abs = p1y + height / 2

            x1 += x_abs
            x2 += x_abs
            x3 += x_abs
            x4 += x_abs
            y1 += y_abs
            y2 += y_abs
            y3 += y_abs
            y4 += y_abs
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
        self.draw(region.texture, x, y, width, height, u, v, u2, v2,
                  r, g, b, a, scale_x, scale_y, rotation)


class CharBatch(SpriteBatch):
    """CharBatch allows to batch chars into minimum of draw calls."""
    def __init__(self, context, size=1000, shaderprogram=None,
                 out_view=None):
        super().__init__(context, size, shaderprogram, out_view)

        self.dspool = self.init_dspool()
        self.last_texture = None

    def get_default_shaderprogram(self, context):
        '''Generate a basic shader program if nono given

        *Parameters:*

        - `context`: `VulkContext`
        '''
        vs = path.join(PATH_VULK_SHADER, "distancefieldfont.vs.glsl")
        fs = path.join(PATH_VULK_SHADER, "distancefieldfont.fs.glsl")

        shaders_mapping = {
            vc.ShaderStage.VERTEX: vs,
            vc.ShaderStage.FRAGMENT: fs
        }

        return vo.ShaderProgramGlslFile(context, shaders_mapping)

    def draw_char(self, fontdata, char, x, y, r=1., g=1., b=1., a=1.,
                  scale_x=1., scale_y=1., rotation=0.):
        """Draw a char

        Args:
            fontdata (FontData): Data on font
            char (str): One character to draw
            size (float): Size
            x (int): X position
            y (int): Y position
            r (float): Red channel
            g (float): Green channel
            b (float): Blue channel
            a (float): Alpha channel
            scale_x (float): Scaling on x axis
            scale_y (float): Scaling on y axis
            rotation (float): Rotation in radian (clockwise)
        """
        region = fontdata.get_region(char)
        width, height = fontdata.get_sizes(char)
        super().draw_region(region, x, y, width, height, r, g,
                            b, a, scale_x, scale_y, rotation)
