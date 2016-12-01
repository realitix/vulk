'''Vulkan objects modules

This module contains the "High" level Vulkan object. It's not that "high"
level, you need to understand fully Vulkan to use theses objects.
This module must be use by Vulkan expert and is very complicated to work with.
You will see a lot of namedtuple here, they are used to better document the
object arguments. Instead of passing a dict whith unknow keys, you pass a
documented namedtuple, I think it's better.
If you want to understand internal Vulkan functions, you can hack around this
module.
'''

from collections import namedtuple
import logging
import vulkan as vk

from vulk.exception import VulkError

logger = logging.getLogger()

STAGE_MAPPING = {
    'vertex': vk.VK_SHADER_STAGE_VERTEX_BIT,
    'tessellation_control': vk.VK_SHADER_STAGE_TESSELLATION_CONTROL_BIT, # noqa
    'tessellation_evaluation': vk.VK_SHADER_STAGE_TESSELLATION_EVALUATION_BIT, # noqa
    'geometry': vk.VK_SHADER_STAGE_GEOMETRY_BIT,
    'fragment': vk.VK_SHADER_STAGE_FRAGMENT_BIT,
    'compute': vk.VK_SHADER_STAGE_COMPUTE_BIT
}


def vk_const(v):
    '''Get constant

    if v is str, we get the constant in vulkan
    else we return it as is
    '''

    if isinstance(v, str):
        if '|' in v:
            result = 0
            for attr in v.split('|'):
                result |= vk_const(attr)
            return result
        return getattr(vk, v)
    return v


def btov(b):
    '''Convert boolean to Vulkan boolean'''
    return vk.VK_TRUE if b else vk.VK_FALSE


class ShaderModule():
    '''ShaderModule Vulkan object

    A shader module is a Spir-V shader loaded into Vulkan.
    After being created, it must be inserted in a pipeline stage.
    The real Vulkan module can be accessed by the 'module' property.
    '''

    def __init__(self, context, code):
        '''Initialize the module

        :param context: The Vulkan context
        :param code: Binary Spir-V loaded file
        :type context: VulkContext
        :type code: bytes
        :return The shader module
        :rtype ShaderModule
        '''
        if not isinstance(code, bytes):
            logger.info("Type of code is not 'bytes', it may be an error")

        self.code = code

        # Create the shader module
        shader_create = vk.VkShaderModuleCreateInfo(
            sType=vk.VK_STRUCTURE_TYPE_SHADER_MODULE_CREATE_INFO,
            flags=0, codeSize=len(code), pCode=code)
        self.module = vk.vkCreateShaderModule(context.device, shader_create)


#  Objects used in Renderpass
AttachmentDescription = namedtuple('AttachmentDescription',
                                   ['format', 'samples', 'load', 'store',
                                    'stencil_load', 'stencil_store',
                                    'initial_layout', 'final_layout'])
AttachmentDescription.__doc__ = '''AttachmentDescription object

    AttachmentDescription describe the attachment.

    :param format: VkFormat vulkan constant
    :param samples: VkSampleCountFlagBits vulkan constant
    :param load: VkAttachmentLoadOp vulkan constant
    :param store: VkAttachmentStoreOp vulkan constant
    :param stencil_load: VkAttachmentLoadOp vulkan constant
    :param stencil_store: VkAttachmentStoreOp vulkan constant
    :param initial_layout: VkImageLayout vulkan constant
    :param final_layout: VkImageLayout vulkan constant
    :type format: VkFormat
    :type samples: VkSampleCountFlagBits
    :type load: VkAttachmentLoadOp
    :type store: VkAttachmentStoreOp
    :type stencil_load: VkAttachmentLoadOp
    :type stencil_store: VkAttachmentStoreOp
    :type initial_layout: VkImageLayout
    :type final_layout: VkImageLayout
    '''


AttachmentReference = namedtuple('AttachmentReference', ['index', 'layout'])
AttachmentReference.__doc__ = '''AttachmentReference object

    AttachmentReference links an attachment index with a layout.

    :param index: Index of attachment description
    :param layout: VkImageLayout vulkan constant
    :type index: int
    :type layout: VkImageLayout
    '''


SubpassDescription = namedtuple('SubpassDescription',
                                ['colors', 'inputs', 'resolves',
                                 'preserves', 'depth_stencil'])
SubpassDescription.__new__.__defaults__ = \
        ([],) * len(SubpassDescription._fields)
SubpassDescription.__doc__ = '''SubpassDescription object
SubpassDescription describes all attachments in the subpass.
    All parameters are of type AttachmentReference. The order of
    If you don't want an attachment, don't set it, its default
    value is an empty list.

    :param colors: colors attachments
    :param inputs: inputs attachments
    :param resolves: resolves attachments (must be the same size as inputs)
    :param preserves: preserves attachments
    :param depth_stencil: list containing only one attachment
    :type colors: list
    :type inputs: list
    :type resolves: list
    :type preserves: list
    :type depth_stencil: list
    '''


SubpassDependency = namedtuple('SubpassDependency',
                               ['src_subpass', 'src_stage', 'src_access',
                                'dst_subpass', 'dst_stage', 'dst_access'])
SubpassDependency.__doc__ = '''SubpassDependency object

    SubpassDependency describes all dependencies of the subpass.

    :param src_subpass: Source subpass
    :param src_stage: Source stage
    :param src_access: Source access
    :param dst_subpass: Destination subpass
    :param dst_stage: Destination stage
    :param dst_access: Destination access
    :type src_subpass: int
    :type src_stage: VkPipelineStageFlagBits
    :type src_access: VkAccessFlagBits
    :type dst_subpass: int
    :type dst_stage: VkPipelineStageFlagBits
    :type dst_access: VkAccessFlagBits
    '''


class Renderpass():
    '''Renderpass object

    When creating the pipeline, we need to tell Vulkan about the
    framebuffer attachments that will be used while rendering. We need to
    specify how many color and depth buffers there will be, how many samples
    to use for each of them and how their contents should be handled
    throughout the rendering operations. All of this information is wrapped
    in a RenderPass object
    '''

    def __init__(self, context, attachments, subpasses, dependencies):
        '''Renderpass constructor

        :param context: The Vulkan context
        :param attachments: List of AttachmentDescription
        :param subpasses: List of SubpassDescription
        :param dependencies: List of SubpassDependency
        :type context: VulkContext
        :type attachments: list
        :type subpasses: list
        :type dependencies: list
        :return A renderpass object
        :rtype RenderPass

        .. warning:: Arguments ar not checked, you must kwnow what you  are
                     doing.
        '''

        vk_attachments = []
        for a in attachments:
            vk_attachments.append(vk.VkAttachmentDescription(
                flags=0,
                format=vk_const(a.format),
                samples=vk_const(a.samples),
                loadOp=vk_const(a.load),
                storeOp=vk_const(a.store),
                stencilLoadOp=vk_const(a.stencil_load),
                stencilStoreOp=vk_const(a.stencil_store),
                initialLayout=vk_const(a.initial_layout),
                finalLayout=vk_const(a.final_layout)
            ))

        # Loop through the list of subpasses to create the reference
        # reference key is index_layout
        vk_references = {}
        for s in subpasses:
            all_list = [s.setdefault(k, []) for k in ('colors', 'inputs',
                        'resolves', 'preserves', 'depth_stencil')]
            all_list = [item for sublist in all_list for item in sublist]

            for r in (s.colors + s.inputs + s.resolves +
                      s.preserves + s.depth_stencil):
                key = (r.index, r.layout)
                if key not in vk_references:
                    vk_references[key] = vk.VkAttachmentReference(
                        attachment=r.index,
                        layout=vk_const(r.layout)
                    )

        # Create the subpasses using references
        vk_subpasses = []
        for s in subpasses:
            leninputs = len(s.inputs)
            lenpreserves = len(s.preserves)
            lencolors = len(s.colors)
            lenresolves = len(s.resolves)
            inputs = s.inputs or None
            preserves = s.preserves or None
            colors = s.colors or None
            resolves = s.resolves or None
            depth_stencil = next(iter(s.depth_stencil), None)

            if resolves and inputs and lenresolves != lencolors:
                msg = "resolves and inputs list must be of the same size"
                logger.error(msg)
                raise VulkError(msg)

            vk_subpasses.append(vk.VkSubpassDescription(
                flags=0,
                pipelineBindPoint=vk.VK_PIPELINE_BIND_POINT_GRAPHICS,
                inputAttachmentCount=leninputs,
                pInputAttachments=inputs,
                colorAttachmentCount=lencolors,
                pColorAttachments=colors,
                pResolveAttachments=resolves,
                preserveAttachmentCount=lenpreserves,
                pPreserveAttachments=preserves,
                pDepthStencilAttachment=depth_stencil
            ))

        # Create the dependancies
        vk_dependencies = []
        for d in dependencies:
            vk_dependencies.append(vk.VkSubpassDependency(
                dependencyFlags=0,
                srcSubpass=vk_const(d.src_subpass),
                dstSubpass=vk_const(d.dst_subpass),
                srcStageMask=vk_const(d.src_stage),
                dstStageMask=vk_const(d.dst_stage),
                srcAccessMask=vk_const(d.src_access),
                dstAccessMask=vk_const(d.dst_access)
            ))

        # Create the render pass
        renderpass_create = vk.VkRenderPassCreateInfo(
            flags=0,
            sType=vk.VK_STRUCTURE_TYPE_RENDER_PASS_CREATE_INFO,
            attachmentCount=len(vk_attachments),
            pAttachments=vk_attachments,
            subpassCount=len(vk_subpasses),
            pSubpasses=vk_subpasses,
            dependencyCount=len(vk_dependencies),
            pDependencies=vk_dependencies
        )

        self.renderpass = vk.vkCreateRenderPass(
            context.device, renderpass_create)


#  Objects used in Pipeline
PipelineShaderStage = namedtuple('PipelineShaderStage', ['module', 'stage'])
PipelineShaderStage.__doc__ = '''PipelineShaderStage object
    :param module: The shader module to bind
    :param stage: Stage in ['vertex', 'fragment', 'geometry',
                  'tesselation_control', 'tesselation_evaluation',
                  'compute']
    :type module: ShaderModule
    :type stage: str
    '''

PipelineVertexInputState = namedtuple('PipelineVertexInputState',
                                      ['bindings', 'attributes'])
PipelineVertexInputState.__new__.__defaults__ = \
        ([],) * len(PipelineVertexInputState._fields)
PipelineVertexInputState.__doc__ = '''PipelineVertexInputState object
    :param bindings: The vertice bindings
    :param attributes: The vertice attributes
    :type bindings: list
    :type attributes: list
    '''

PipelineInputAssemblyState = namedtuple('PipelineInputAssemblyState',
                                        'topology')
PipelineInputAssemblyState.__doc__ = '''PipelineInputAssemblyState object
    :param topology: The topology to use when drawing
    :type topoloy: str or VkPrimitiveTopology
    '''

PipelineViewportState = namedtuple('PipelineViewportState',
                                   ['viewports', 'scissors'])
PipelineViewportState.__doc__ = '''PipelineViewportState object
    Contains viewports and scissors.

    .. warning:: The viewports and scissors are real Vulkan objects
                 (vk.VkRect2D) and not Vulk objects.

    :param viewports: List of viewport
    :param scissors: List of scissor
    :type viewports: list
    :type scissors: list
    '''

PipelineRasterizationState = namedtuple(
    'PipelineRasterizationState',
    ['depth_clamp_enable', 'polygon_mode', 'line_width', 'cull_mode',
     'front_face', 'depth_bias_constant', 'depth_bias_clamp',
     'depth_bias_slope']
)
PipelineRasterizationState.__doc__ = '''PipelineRasterizationState object
    :param depth_clamp_enable: Whether to enable depth clamping
    :param polygon_mode: Which polygon mode to use
    :param line_width: Width of line
    :param cull_mode: The way of culling
    :param front_face: Front face
    :param depth_bias_constant: Constant to add to depth
    :param depth_bias_clamp: Max depth bias
    :param depth_bias_slope: Factor to slope
    :type depth_clamp_enable: boolean
    :type polygon_mode: VkPolygonMode
    :type line_width: float
    :type cull_mode: VkCullModeFlagBits
    :type front_face: VkFrontFace
    :type depth_bias_constant: float
    :type depth_bias_clamp: float
    :type depth_bias_slope: float
    '''

PipelineMultisampleState = namedtuple('PipelineMultisampleState',
                                      ['shading_enable', 'samples',
                                       'min_sample_shading'])
PipelineMultisampleState.__doc__ = '''PipelineMultisampleState
    :param shading_enable: Enable multisampling
    :param samples: Number of samples
    :param min_sample_shading: Minimum of sample
    :type shading_enable: boolean
    :type samples: VkSampleCountFlagBits
    :type min_sample_shading: float
    '''

PipelineDepthStencilState = namedtuple(
    'PipelineDepthStencilState',
    ['depth_test_enable', 'depth_write_enable', 'depth_bounds_test_enable',
     'depth_compare', 'stencil_test_enable', 'front', 'back', 'min', 'max']
)
PipelineDepthStencilState.__doc__ = '''PipelineDepthStencilState
    :param depth_test_enable: Enable depth test
    :param depth_write_enable: Enable depth write
    :param depth_bounds_test_enable: Enable bounds test
    :param depth_compare: Condition to overwrite depth
    :param stencil_test_enable: Enable stencil test
    :param front: Control stencil parameter (the real vulkan object)
    :param back: Control stencil parameter (the real vulkan object)
    :param min: Define the min value in depth bound test
    :param max: Define the max value in depth bound test
    :type depth_test_enable: boolean
    :type depth_write_enable: boolean
    :type depth_bounds_test_enable: boolean
    :type depth_compare: VkCompareOp
    :type stencil_test_enable: boolean
    :type front: VkStencilOpState
    :type back: VkStencilOpState
    :type min: float
    :type max: float
    '''

PipelineColorBlendAttachmentState = namedtuple(
    'PipelineColorBlendAttachmentState',
    ['enable', 'src_color', 'dst_color', 'color_op',
     'src_alpha', 'dst_alpha', 'alpha_op', 'color_mask']
)
PipelineColorBlendAttachmentState.__doc__ = '''PipelineColorBlendAttachmentState
    :param enable: Enable blending
    :param src_color: Blending factor for source color
    :param dst_color: Blending factor for destination color
    :param color_op: Operation on color
    :param src_alpha: Blending factor for source alpha
    :param dst_alpha: Blending factor for destination alpha
    :param alpha_op: Operation on alpha
    :param color_mask: Bitmask selecting which of the R, G, B, and/or A
                       components are enabled for writing
    :type enable: boolean
    :type src_color: VkBlendFactor
    :type dst_color: VkBlendFactor
    :type color_op: VkBlendOp
    :type src_alpha: VkBlendFactor
    :type dst_alpha: VkBlendFactor
    :type alpha_op: VkBlendOp
    :type color_mask: VkColorComponentFlags
    '''

PipelineColorBlendState = namedtuple('PipelineColorBlendState',
                                     ['op_enable', 'op', 'attachments',
                                      'constants'])
PipelineColorBlendState.__doc__ = '''PipelineColorBlendState
    :param op_enable: Enable bitwise combination
    :param op: Operation to perform
    :param attachments: List of blend attachments for each framebuffer
    :param constants: Constants depending on blend factor (list of 4 float)
    :type op_enable: boolean
    :type op: VkLogicOp
    :type attachments: list
    :type constants: list
    '''

PipelineDynamicState = namedtuple('PipelineDynamicState', 'states')
PipelineDynamicState.__doc__ = '''PipelineDynamicState
    :param states: Array of VkDynamicState
    :type states: list
    '''


class Pipeline():
    '''Pipeline (graphic) object

    The graphics pipeline is the sequence of operations that take the
    vertices and textures of your meshes all the way to the pixels in
    the render targets. The pipeline combines the following elements:
        * Shader stages: the shader modules that define the functionality of
            the programmable stages of the graphics pipeline
        * Fixed-function state: all of the structures that define the
            fixed-function stages of the pipeline, like input assembly,
            rasterizer, viewport and color blending
        * Pipeline layout: the uniform and push values referenced by the
            shader that can be updated at draw time
        * Render pass: the attachments referenced by the pipeline stages
                       and their usage
    '''

    def __init__(self, context, stages, vertex_input, input_assembly,
                 viewport, rasterization, multisample, depth, blend, dynamic,
                 renderpass):
        '''RenderPass constructor

        :param context: The Vulkan context
        :param stages: List of PipelineShaderStage
        :param vertex_input: Define how to handle vertice
        :param input_assembly: Define how to draw vertice
        :param viewport: The pipeline viewport
        :param rasterization: The pipeline rasterization
        :param multisample: The pipeline multisample configuration
        :param depth: The pipeline depth configuration (may be None)
        :param blend: The pipeline blending configuration
        :param dynamic: Set some pipeline parts dynamic (may be None)
        :param renderpass: The renderpass of this pipeline
        :type context: VulkContext
        :type stages: list
        :type vertex_input: PipelineVertexInputState
        :type input_assembly: PipelineInputAssemblyState
        :type viewport: PipelineViewportState
        :type rasterization: PipelineRasterizationState
        :type multisample: PipelineMultisampleState
        :type depth: PipelineDepthStencilState
        :type blend: PipelineColorBlendState
        :type dynamic: PipelineDynamicState
        :type renderpass: Renderpass
        :return A Pipeline object
        :rtype Pipeline
        '''

        vk_stages = []
        for s in stages:
            try:
                vulkan_stage = STAGE_MAPPING[s.stage]
            except KeyError:
                msg = "Stage %s doesn't exist"
                logger.error(msg)
                raise TypeError(msg)

            vk.VkPipelineShaderStageCreateInfo(
                sType=vk.VK_STRUCTURE_TYPE_PIPELINE_SHADER_STAGE_CREATE_INFO,
                flags=0,
                stage=vulkan_stage,
                module=s.module,
                pSpecializationInfo=None,
                pName='main'
            )

        vk_vertex_input = vk.VkPipelineVertexInputStateCreateInfo(
            sType=vk.VK_STRUCTURE_TYPE_PIPELINE_VERTEX_INPUT_STATE_CREATE_INFO,
            flags=0,
            vertexBindingDescriptionCount=len(vertex_input.bindings),
            pVertexBindingDescriptions=vertex_input.bindings or None,
            vertexAttributeDescriptionCount=len(vertex_input.attributes),
            pVertexAttributeDescriptions=vertex_input.attributes or None
        )

        vk_input_assembly = vk.VkPipelineInputAssemblyStateCreateInfo(
            sType=vk.VK_STRUCTURE_TYPE_PIPELINE_INPUT_ASSEMBLY_STATE_CREATE_INFO, # noqa
            flags=0,
            topology=vk_const(input_assembly.topology),
            primitiveRestartEnable=vk.VK_FALSE
        )

        vk_viewport = vk.VkPipelineViewportStateCreateInfo(
            sType=vk.VK_STRUCTURE_TYPE_PIPELINE_VIEWPORT_STATE_CREATE_INFO,
            flags=0,
            viewportCount=len(viewport.viewports),
            pViewports=viewport.viewports,
            scissorCount=len(viewport.scissors),
            pScissors=viewport.scissors
        )

        dbe = vk.VK_FALSE
        if (rasterization.depth_bias_constant or
           rasterization.depth_bias_clamp or
           rasterization.depth_bias_slope):
            dbe = vk.VK_TRUE

        vk_rasterization = vk.VkPipelineRasterizationStateCreateInfo(
            sType=vk.VK_STRUCTURE_TYPE_PIPELINE_RASTERIZATION_STATE_CREATE_INFO, # noqa
            flags=0,
            depthClampEnable=btov(rasterization.depth_clamp_enable),
            rasterizerDiscardEnable=vk.VK_FALSE,
            polygonMode=vk_const(rasterization.polygon_mode),
            lineWidth=rasterization.line_width,
            cullMode=vk_const(rasterization.cull_mode),
            frontFace=vk_const(rasterization.front_face),
            depthBiasEnable=dbe,
            depthBiasConstantFactor=rasterization.depth_bias_constant,
            depthBiasClamp=rasterization.depth_bias_clamp,
            depthBiasSlopeFactor=rasterization.depth_bias_slope
        )

        vk_multisample = vk.VkPipelineMultisampleStateCreateInfo(
            sType=vk.VK_STRUCTURE_TYPE_PIPELINE_MULTISAMPLE_STATE_CREATE_INFO,
            flags=0,
            sampleShadingEnable=btov(multisample.shading_enable),
            rasterizationSamples=vk_const(multisample.samples),
            minSampleShading=multisample.min_sample_shading,
            pSampleMask=None,
            alphaToCoverageEnable=vk.VK_FALSE,
            alphaToOneEnable=vk.VK_FALSE
        )

        vk_depth = None
        if depth:
            vk_depth = vk.VkPipelineDepthStencilStateCreateInfo(
                sType=vk.VK_STRUCTURE_TYPE_PIPELINE_DEPTH_STENCIL_STATE_CREATE_INFO, # noqa
                flags=0,
                depthTestEnable=btov(depth.depth_test_enable),
                depthWriteEnable=btov(depth.depth_write_enable),
                depthCompareOp=vk_const(depth.depth_compare),
                depthBoundsTestEnable=btov(depth.depth_bounds_test_enable),
                stencilTestEnable=btov(depth.stencil_test_enable),
                front=depth.front,
                back=depth.back,
                minDepthBounds=depth.min,
                maxDepthBounds=depth.max
            )

        vk_blend_attachments = []
        for a in blend.attachments:
            vk_a = vk.VkPipelineColorBlendAttachmentState(
                colorWriteMask=vk_const(a.color_mask),
                blendEnable=btov(a.enable),
                srcColorBlendFactor=vk_const(a.src_color),
                dstColorBlendFactor=vk_const(a.dst_color),
                colorBlendOp=vk_const(a.color_op),
                srcAlphaBlendFactor=vk_const(a.src_alpha),
                dstAlphaBlendFactor=vk_const(a.dst_alpha),
                alphaBlendOp=vk_const(a.alpha_op)
            )
            vk_blend_attachments.append(vk_a)

        vk_blend = vk.VkPipelineColorBlendStateCreateInfo(
            sType=vk.VK_STRUCTURE_TYPE_PIPELINE_COLOR_BLEND_STATE_CREATE_INFO,
            flags=0,
            logicOpEnable=btov(blend.op_enable),
            logicOp=vk_const(blend.op),
            attachmentCount=len(vk_blend_attachments),
            pAttachments=vk_blend_attachments,
            blendConstants=blend.constants
        )

        vk_dynamic = None
        if dynamic:
            vk_dynamic = vk.VkPipelineDynamicStateCreateInfo(
                sType=vk.VK_STRUCTURE_TYPE_PIPELINE_DYNAMIC_STATE_CREATE_INFO,
                flags=0,
                dynamicStateCount=len(dynamic.states),
                pDynamicStates=dynamic.states
            )

        # Currently layout is unusable, I have to try it
        vk_layout_create = vk.VkPipelineLayoutCreateInfo(
            sType=vk.VK_STRUCTURE_TYPE_PIPELINE_LAYOUT_CREATE_INFO,
            flags=0,
            setLayoutCount=0,
            pSetLayouts=None,
            pushConstantRangeCount=0,
            pPushConstantRanges=None
        )
        vk_layout = vk.vkCreatePipelineLayout(context.device, vk_layout_create)

        pipeline_create = vk.VkGraphicsPipelineCreateInfo(
            sType=vk.VK_STRUCTURE_TYPE_GRAPHICS_PIPELINE_CREATE_INFO,
            flags=0,
            stageCount=len(vk_stages),
            pStages=vk_stages,
            pVertexInputState=vk_vertex_input,
            pInputAssemblyState=vk_input_assembly,
            pTessellationState=None,
            pViewportState=vk_viewport,
            pRasterizationState=vk_rasterization,
            pMultisampleState=vk_multisample,
            pDepthStencilState=vk_depth,
            pColorBlendState=vk_blend,
            pDynamicState=vk_dynamic,
            layout=vk_layout,
            renderPass=renderpass,
            subpass=0,
            basePipelineHandle=None,
            basePipelineIndex=-1
        )

        self.pipeline = vk.vkCreateGraphicsPipelines(context.device, None,
                                                     1, pipeline_create)


class Image():
    '''Image object

    Image can be initialized in two ways:
        - In the classic ways passing all the properties
        - Directly by passing a real vulkan image

    This is useful because image can be created by swapchain and can be
    converted to vulk Image object.
    '''
    def __init__(self, *args, **kwargs):
        '''If only one non-named arg, we create from vkImage,
        else from parameters
        '''
        self.image = args[0] if args else self._create_image(**kwargs)

    def _create_image(image_type, ):
        '''Create a new image

        :param image_type: Type of image (1D, 2D, 3D)
        :type image_type: VkImageType
        '''
        pass


class Framebuffer():
    '''Framebuffer object

    In Vulkan, a Framebuffer references all of the `VkImageView` objects that
    represent the attachments of a Renderpass.
    '''

    def __init__(self, context, renderpass, attachments,
                 width, height, layers):
        '''Initialize the Framebuffer

        :param context: The Vulkan context
        :param renderpass: The renderpass which framebuffer needs
                           to be compatible
        :param attachments: List of ImageView
        :param width: Width of the Framebuffer
        :param height: Height of the Framebuffer
        :param layers: Number of layers in the Framebuffer
        :type context: VulkContext
        :type renderpass: Renderpass
        :type attachments: list
        :type width: int
        :type height: int
        :type layers: int
        '''
        framebuffer_create = vk.VkFramebufferCreateInfo(
            sType=vk.VK_STRUCTURE_TYPE_FRAMEBUFFER_CREATE_INFO,
            flags=0,
            renderPass=renderpass.renderpass,
            attachmentCount=len(attachments),
            pAttachments=[a.imageview for a in attachments],
            width=width,
            height=height,
            layers=layers
        )

        self.framebuffer = vk.vkCreateFramebuffer(context.device,
                                                  framebuffer_create)
