'''SpriteBatch module

SpriteBatch is the pillar of 2D rendering. It has to be very performant
and reliable.
'''
from os import path

from vulk import PATH_VULK_SHADER
from vulk import vulkanconstant as vc
from vulk import vulkanobject as vo
from vulk.graphic import mesh as me
from vulk.graphic import uniform
from vulk.math.matrix import Matrix4


class SpriteBatch():
    '''
    SpriteBatch allows to batch lot of sprites (small quad) into minimum
    of draw calls.
    '''

    def __init__(self, context, size=1000, shaderprogram=None,
                 clear=None, out_view=None):
        '''Initialize SpriteBatch

        *Parameters:*

        - `context`: `VulkContext`
        - `size`: Max number of sprite in one batch
        - `shaderprogram`: Custom `ShaderProgram`
        - `clear`: `list` of 4 `float` (r,g,b,a) or `None`
        - `out_view`: Out `ImageView` to render into

        **Note: By default, `SpriteBatch` doesn't clear `out_image`, you have
                to fill `clear_color` to clear `out_image`**

        **Note: By default, out image is the context `final_image`, you can
                override this behavior with the `out_view` parameter**
        '''
        # ShaderProgram
        if not shaderprogram:
            self.shaderprogram = self.get_default_shaderprogram(context)

        # Stored parameters
        self.clear = clear
        self.out_view = out_view if out_view else context.final_image_view

        # Init rendering attributes
        self.mesh = self.init_mesh(context, size)
        self.init_indices(size)
        self.uniformblock = self.init_uniform(context)
        self.renderpass = self.init_renderpass(context)
        self.descriptorlayout = self.init_descriptorlayout(context)
        self.descriptorpool = self.init_descriptorpool(context)
        self.descriptorset = self.init_descriptorset(context)
        self.pipelinelayout = self.init_pipelinelayout(context)
        self.pipeline = self.init_pipeline(context)
        self.commandpool = self.init_commandpool(context)
        self.commandbuffer = self.init_commandbuffer(context)
        self.framebuffer = self.init_framebuffer(context)

        # Others attributes
        self.semaphores_in = []
        self.semaphore_out = vo.Semaphore(context)
        self.drawing = False
        self.drawing_context = None
        self.projection_matrix = Matrix4()
        self.projection_matrix.to_orthographic_2d(
            0, 0, context.width, context.height)
        self.transform_matrix = Matrix4()
        self.combined_matrix = Matrix4()
        self.idx = 0
        self.last_texture = None
        self.matrices_dirty = True

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

    def init_indices(self, size):
        '''Initialize mesh's indices.
        It's done only at initialization for better performance.

        *Parameters:*

        - `size`: Number of sprite to handle
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
        '''Initialize `SpriteBatch` uniforms.
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

    def init_renderpass(self, context):
        '''Initialize `SpriteBatch` renderpass

        *Parameters:*

        - `context`: `VulkContext`
        '''
        vk_load = vc.AttachmentLoadOp.CLEAR if self.clear else vc.AttachmentLoadOp.LOAD # noqa
        attachment = vo.AttachmentDescription(
            self.out_view.image.format, vc.SampleCount.COUNT_1,
            vk_load, vc.AttachmentStoreOp.STORE,
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

    def init_descriptorpool(self, context):
        '''Create the `SpriteBatch` descriptor pool

        *Parameters:*

        - `context`: `VulkContext`
        '''
        pool_sizes = [
            vo.DescriptorPoolSize(vc.DescriptorType.UNIFORM_BUFFER, 1),
            vo.DescriptorPoolSize(vc.DescriptorType.COMBINED_IMAGE_SAMPLER, 1)
        ]
        return vo.DescriptorPool(context, pool_sizes, 1)

    def init_descriptorset(self, context):
        '''Initialize descriptor set for uniform and texture

        *Parameters:*

        - `context`: `VulkContext`
        '''
        descriptorset = self.descriptorpool.allocate_descriptorsets(
            context, 1, [self.descriptorlayout])[0]

        descriptorub_info = vo.DescriptorBufferInfo(
            self.uniformblock.uniform_buffer.final_buffer, 0,
            self.uniformblock.size)
        descriptorub_write = vo.WriteDescriptorSet(
            descriptorset, 0, 0, vc.DescriptorType.UNIFORM_BUFFER,
            [descriptorub_info])

        vo.update_descriptorsets(context, [descriptorub_write], [])

        return descriptorset

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

    def init_commandpool(self, context):
        '''
        Initialize command pool as `TRANSIENT` because we reset it each frame

        *Parameters:*

        - `context`: `VulkContext`
        '''
        flags = vc.CommandPoolCreate.TRANSIENT | vc.CommandPoolCreate.RESET_COMMAND_BUFFER # noqa
        return vo.CommandPool(
            context, context.queue_family_indices['graphic'], flags)

    def init_commandbuffer(self, context):
        '''Create the command buffer

        *Parameters:*

        - `context`: `VulkContext`
        '''
        return self.commandpool.allocate_buffers(
            context, vc.CommandBufferLevel.PRIMARY, 1)[0]

    def init_framebuffer(self, context):
        '''Create the framebuffer with the final_image (from context)

        *Parameters:*

        - `context`: `VulkContext`
        '''
        return vo.Framebuffer(
            context, self.renderpass, [self.out_view],
            context.width, context.height, 1)

    def get_default_shaderprogram(self, context):
        '''Generate a basic shader program if nono given

        *Parameters:*

        - `context`: `VulkContext`
        '''
        vs = path.join(PATH_VULK_SHADER, "spritebatch.vs.spv")
        fs = path.join(PATH_VULK_SHADER, "spritebatch.fs.spv")

        with open(vs, 'rb') as f:
            spirv_v = f.read()
        with open(fs, 'rb') as f:
            spirv_f = f.read()

        shaders_mapping = {
            vc.ShaderStage.VERTEX: spirv_v,
            vc.ShaderStage.FRAGMENT: spirv_f
        }

        return vo.ShaderProgram(context, shaders_mapping)

    def update_texture(self, context, texture):
        '''Update descriptor set containing texture

        *Parameters:*

        - `context`: `VulkContext`
        - `texture`: `RawTexture` to update
        '''
        descriptorimage_info = vo.DescriptorImageInfo(
            texture.sampler, texture.view,
            vc.ImageLayout.SHADER_READ_ONLY_OPTIMAL)
        descriptorimage_write = vo.WriteDescriptorSet(
            self.descriptorset, 1, 0, vc.DescriptorType.COMBINED_IMAGE_SAMPLER,
            [descriptorimage_info])

        vo.update_descriptorsets(context, [descriptorimage_write], [])

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
        self.semaphores_in = semaphores if semaphores else []

        # Keep the context only during rendering and release it at `end` call
        self.drawing_context = context

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
        self.semaphores_in = []
        self.drawing = False
        self.drawing_context = None

        return self.semaphore_out

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
        self.mesh.upload(self.drawing_context)

        # Bind texture
        self.update_texture(self.drawing_context, self.last_texture)

        # Compute indices count
        sprites_in_batch = self.idx / 4  # 4 idx per vertex
        indices_count = int(sprites_in_batch) * 6

        # Explicitly reset command buffer
        self.commandbuffer.reset()

        # Register command
        flags = vc.CommandBufferUsage.ONE_TIME_SUBMIT
        with self.commandbuffer.bind(flags) as cmd:
            vk_clear = []
            if self.clear:
                vk_clear.append(vo.ClearColorValue(float32=self.clear))

            width = self.drawing_context.width
            height = self.drawing_context.height
            cmd.begin_renderpass(
                self.renderpass,
                self.framebuffer,
                vo.Rect2D(vo.Offset2D(0, 0),
                          vo.Extent2D(width, height)),
                vk_clear
            )
            cmd.bind_pipeline(self.pipeline)
            self.mesh.bind(cmd)
            cmd.bind_descriptor_sets(self.pipelinelayout, 0,
                                     [self.descriptorset], [])
            self.mesh.draw(cmd, 0, indices_count)
            cmd.end_renderpass()

        # Submit command
        submit = vo.SubmitInfo(
            [s for s in self.semaphores_in if s],
            [vc.PipelineStage.VERTEX_INPUT], [self.semaphore_out],
            [self.commandbuffer])
        vo.submit_to_graphic_queue(self.drawing_context, [submit])

        self.idx = 0

    def upload_matrices(self, context):
        '''
        Compute combined matrix from transform and projection matrix.
        Then upload combined matrix.

        *Parameters:*

        - `context`: `VulkContext`
        '''
        self.combined_matrix.to_matrix(self.projection_matrix)
        self.combined_matrix.mul(self.transform_matrix)
        self.uniformblock.set_uniform(0, self.combined_matrix.values)
        self.uniformblock.set_uniform(0, self.projection_matrix.values)
        self.uniformblock.upload(context)
        self.matrices_dirty = False

    def update_transform(self, matrix):
        '''Update the transfrom matrix with `matrix`

        *Parameters:*

        - `matrix`: `Matrix4`

        **Note: This function doesn't keep a reference to the matrix,
                it only copies data**
        '''
        self.transform_matrix.to_matrix(matrix)
        self.matrices_dirty = True

    def update_projection(self, matrix):
        '''Update the projection matrix with `matrix`

        *Parameters:*

        - `matrix`: `Matrix4`

        **Note: This function doesn't keep a reference to the matrix,
                it only copies data**
        '''
        self.projection_matrix.to_matrix(matrix)
        self.matrices_dirty = True

    def draw(self, texture, x, y, width, height):
        '''
        Draw `texture` at position x, y of size `width`, `height`

        *Parameters:*

        - `texture`: `RawTexture`
        - `x`: X position
        - `y`: Y position
        - `width`: Width
        - `heigth`: Height
        '''
        if not self.drawing:
            raise Exception("Not currently drawing")

        if self.last_texture is not texture:
            self.flush()

        self.last_texture = texture

        x2 = x + width
        y2 = y + height
        u = 0
        v = 0
        u2 = 1
        v2 = 1
        r = 1
        g = 1
        b = 1
        a = 1

        for val in [([x, y], [u, v], [r, g, b, a]),
                    ([x, y2], [u, v2], [r, g, b, a]),
                    ([x2, y2], [u2, v2], [r, g, b, a]),
                    ([x2, y], [u2, v], [r, g, b, a])]:
            self.mesh.set_vertex(self.idx, val)
            self.idx += 1
