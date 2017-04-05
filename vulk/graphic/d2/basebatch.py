'''BaseBatch module

BaseBatch is used by SpriteBatch and BlockBatch.
'''
from vulk import vulkanconstant as vc
from vulk import vulkanobject as vo
from vulk import vulkanutil as vu
from vulk.graphic import uniform
from vulk.math.matrix import ProjectionMatrix, TransformationMatrix, Matrix4


class BaseBatch():
    def __init__(self, context, size=1000, shaderprogram=None,
                 out_view=None):
        '''Initialize BaseBatch

        *Parameters:*

        - `context`: `VulkContext`
        - `size`: Max number of block in one batch
        - `shaderprogram`: Custom `ShaderProgram`
        - `clear`: `list` of 4 `float` (r,g,b,a) or `None`
        - `out_view`: Out `ImageView` to render into

        **Note: By default, `BaseBatch` doesn't clear `out_image`, you have
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
