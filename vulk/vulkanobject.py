import logging
import vulkan as vk

from vulk.exception import VulkError

logger = logging.getLogger()


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


class PipelineShaderStage():
    '''PipelineShaderStage Vulkan object

    A shader stage allows a shader to take place in pipeline
    '''

    def __init__(self, context, module, stage, constants={}, main='main'):
        '''Init a shader stage

        :param context: The Vulkan context
        :param module: The shader module to bind
        :param stage: The stage to bind
        :param constants: A dict of constants to modify in shader
        :param main: Name of the main function in shader(default=main)
        :type context: VulkContext
        :type module: ShaderModule
        :type stage: str
        :type constants: dict
        :type main: str
        :return The shader stage
        :rtype PipelineShaderStage

        .. note:: The stage constant must be one of theses values:
                  vertex, fragment, geometry, tessellation_control,
                  tessellation_evluation, compute
        .. todo:: constants value has no effect for now
        '''
        stage_mapping = {
            'vertex': vk.VK_SHADER_STAGE_VERTEX_BIT,
            'tessellation_control': vk.VK_SHADER_STAGE_TESSELLATION_CONTROL_BIT, # noqa
            'tessellation_evluation': vk.VK_SHADER_STAGE_TESSELLATION_EVALUATION_BIT, # noqa
            'geometry': vk.VK_SHADER_STAGE_GEOMETRY_BIT,
            'fragment': vk.VK_SHADER_STAGE_FRAGMENT_BIT,
            'compute': vk.VK_SHADER_STAGE_COMPUTE_BIT
        }

        try:
            vulkan_stage = stage_mapping[stage]
        except KeyError:
            msg = "Stage %s doesn't exist"
            logger.error(msg)
            raise TypeError(msg)

        self.stage = vk.VkPipelineShaderStageCreateInfo(
            sType=vk.VK_STRUCTURE_TYPE_PIPELINE_SHADER_STAGE_CREATE_INFO,
            flags=0, stage=vulkan_stage, module=module.module,
            pSpecializationInfo=None, pName=main)


class RenderPass():
    '''RenderPass object

    When creating the pipeline, we need to tell Vulkan about the about the
    framebuffer attachments that will be used while rendering. We need to
    specify how many color and depth buffers there will be, how many samples
    to use for each of them and how their contents should be handled
    throughout the rendering operations. All of this information is wrapped
    in a RenderPass object
    '''

    def __init__(self, context, attachments, subpasses, dependencies):
        '''RenderPass constructor

        :param context: The Vulkan context
        :param attachments: List of attachments
        :param subpasses: List of subpasses
        :param dependencies: List of dependencies
        :type context: VulkContext
        :type attachments: list
        :type subpasses: list
        :type dependencies: list
        :return A renderpass object
        :rtype RenderPass

        :Example:

        Arguments are hard to fill. But if you understand Vulkan, this
        exemple for each argument will help you to understand how to fill
        them. All the pure Vulkan parameters can be passed as Vulkan constant
        or just as string (they will be fetched from vulkan wrapper).
        Ex: Just pass the string 'VK_FORMAT_R8_SNORM' for format.

        attachments is a list of dict:
        [{
            'format': a VkFormat vulkan constant
            'samples': a VkSampleCountFlagBits vulkan constant,
            'load': a VkAttachmentLoadOp vulkan constant,
            'store': a VkAttachmentStoreOp vulkan constant,
            'stencil_load': same as load,
            'stencil_store': same as store,
            'initial_layout': a VkImageLayout vulkan constant,
            'final_layout': a VkImageLayout vulkan constant
        }, {...}]

        subpasses is a list of dict too:
        [{
            'colors': [{
                'index': id of attachments in attachments list
                'layout': a VkImageLayout vulkan constant
            }],
            'inputs': same as colors,
            'resolves': same as colors,
            'preserves': same as colors,
            'depth_stencil': same as color, it shouldn't be an array but it's
                             more convenient
        }, {...}]
        Each property in subpass is a list of attachments reference.
        The order of the attachments list is very important here.
        If you don't want an attachment type, just don't put it in the dict.

        dependencies is again a list of dict:
        [{
            'src_subpass': index of source subpass in subpasses list,
            'dst_subpass': index of destination subpass in subpasses list,
            'src_stage': a VkPipelineStageFlagBits constant,
            'dst_stage': like src_stage,
            'src_access': the way src stage is accessed, a VkAccessFlagBits
            'dst_access': like src_access
        }, {...}]

        .. warning:: Arguments ar not checked, you must kwnow what you do
        '''
        def vk_const(v):
            '''Get constant

            if v is str, we get the cosntant in vulkan
            else we return it as is
            '''

            if isinstance(v, str):
                return getattr(vk, v)
            return v

        vk_attachments = []
        for a in attachments:
            vk_attachments.append(vk.VkAttachmentDescription(
                flags=0,
                format=vk_const(a['format']),
                samples=vk_const(a['samples']),
                loadOp=vk_const(a['load']),
                storeOp=vk_const(a['store']),
                stencilLoadOp=vk_const(a['stencil_load']),
                stencilStoreOp=vk_const(a['stencil_store']),
                initialLayout=vk_const(a['initial_layout']),
                finalLayout=vk_const(a['final_layout'])
            ))

        # Loop through the list of subpasses to create the reference
        # reference key is index_layout
        vk_references = {}
        for s in subpasses:
            all_list = [s.setdefault(k, []) for k in ('colors', 'inputs',
                        'resolves', 'preserves', 'depth_stencil')]
            all_list = [item for sublist in all_list for item in sublist]

            for r in all_list:
                key = (r['id'], r['layout'])
                if key not in vk_references:
                    vk_references[key] = vk.VkAttachmentReference(
                        attachment=r['id'],
                        layout=vk_const(r['layout'])
                    )

        # Create the subpasses using references
        def info_attachments(a):
            return (len(a) if a else 0, a if a else None)

        vk_subpasses = []
        for s in subpasses:
            leninputs, inputs = info_attachments(s['inputs'])
            lenpreserves, preserves = info_attachments(s['preserves'])
            lencolors, colors = info_attachments(s['colors'])
            lenresolves, resolves = info_attachments(s['resolves'])
            depth_stencil = (s['depth_stencil'].pop()
                             if s.get['depth_stencil'] else None)

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
                srcSubpass=vk_const(d['src_subpass']),
                dstSubpass=vk_const(d['dst_subpass']),
                srcStageMask=vk_const(d['src_stage']),
                dstStageMask=vk_const(d['dst_stage']),
                srcAccessMask=vk_const(d['src_access']),
                dstAccessMask=vk_const(d['dst_access'])
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
