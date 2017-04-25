'''Vulkan objects modules

This module contains the *High* level Vulkan object. It's not that *high*
level, you need to understand fully Vulkan to use theses objects.
This module must be use by Vulkan expert and is very complicated to work with.
You will see a lot of namedtuple here, they are used to better document the
object arguments. Instead of passing a dict whith unknow keys, you pass a
documented namedtuple, I think it's better.
If you want to understand internal Vulkan functions, you can hack around this
module.


**Note: All classes, functions, tuples of this module are sorted
        alphabetically.**

**Note: In this module, when it's needed, the parameter type is indicated. If
        the type begins with Vk..., it means a real Vulkan object and not an
        object in this module.**
'''

from collections import namedtuple
from contextlib import contextmanager
import logging
import pyshaderc
import vulkan as vk  # pylint: disable=import-error

from vulk.exception import VulkError
from vulk import vulkanconstant as vc

logger = logging.getLogger()


# ----------
# FUNCTIONS
# ----------
def btov(b):
    '''Convert boolean to Vulkan boolean'''
    return vk.VK_TRUE if b else vk.VK_FALSE


def find_memory_type(context, type_filter, properties):
    '''
    Graphics cards can offer different types of memory to allocate from.
    Each type of memory varies in terms of allowed operations and performance
    characteristics. We need to combine the requirements of the memory and our
    own application requirements to find the right type of memory to use.

    *Parameters:*

    - `context`: The `VulkContext`
    - `type_filter`: Bit field of the memory types that are suitable
                     for the memory (int)
    - `properties`: `MemoryProperty` Vulkan constant, type of
                    memory we want

    **Todo: I made a bitwise comparaison with `type_filter`, I have to test
            it to be sure it's working**
    '''
    cache_properties = vk.vkGetPhysicalDeviceMemoryProperties(
        context.physical_device)

    for i, memory_type in enumerate(cache_properties.memoryTypes):
        # TODO: Test type_filter
        if (type_filter & (1 << i)) and \
           (memory_type.propertyFlags & properties) == properties:
            return i

    msg = "Can't find suitable memory type"
    logger.critical(msg)
    raise VulkError(msg)


@contextmanager
def immediate_buffer(context, commandpool=None):
    '''
    Manage creation and destruction of commandbuffer for one time submit.
    If commandpool is not given, it is created here.

    *Parameters:*

    - `context`: `VulkContext`
    - `commandpool`: `CommandPool` (optional)
    '''
    own_commandpool = False
    if not commandpool:
        commandpool = CommandPool(
            context, context.queue_family_indices['graphic'],
            vc.CommandPoolCreate.TRANSIENT)
        own_commandpool = True

    try:
        commandbuffers = commandpool.allocate_buffers(
            context, vc.CommandBufferLevel.PRIMARY, 1)
        flags = vc.CommandBufferUsage.ONE_TIME_SUBMIT
        with commandbuffers[0].bind(flags) as cmd:
            yield cmd
    finally:
        submit = vk.VkSubmitInfo(
            sType=vk.VK_STRUCTURE_TYPE_SUBMIT_INFO,
            waitSemaphoreCount=0,
            pWaitSemaphores=None,
            pWaitDstStageMask=None,
            commandBufferCount=1,
            pCommandBuffers=[c.commandbuffer for c in commandbuffers],
            signalSemaphoreCount=0,
            pSignalSemaphores=None
        )

        vk.vkQueueSubmit(context.graphic_queue, 1, [submit], None)
        vk.vkQueueWaitIdle(context.graphic_queue)
        commandpool.free_buffers(context, commandbuffers)

        if own_commandpool:
            commandpool.free(context)


def submit_to_graphic_queue(context, submits):
    '''
    Convenient function to submit commands to graphic queue

    *Parameters:*

    - `context`: `VulkContext`
    - `submits`: `list` of `SubmitInfo`
    '''
    submit_to_queue(context.graphic_queue, submits)


def submit_to_queue(queue, submits):
    '''
    Submit commands to queue

    *Parameters:*

    - `queue`: `VkQueue`
    - `submits`: `list` of `SubmitInfo`
    '''
    vk_submits = []
    for s in submits:
        wait_stages = None
        if s.wait_stages:
            wait_stages = [st.value for st in s.wait_stages]

        wait_semaphores = None
        if s.wait_semaphores:
            wait_semaphores = [sem.semaphore for sem in s.wait_semaphores]

        signal_semaphores = None
        if s.signal_semaphores:
            signal_semaphores = [sem.semaphore for sem in s.signal_semaphores]

        vk_submits.append(vk.VkSubmitInfo(
            sType=vk.VK_STRUCTURE_TYPE_SUBMIT_INFO,
            waitSemaphoreCount=len(s.wait_semaphores),
            pWaitSemaphores=wait_semaphores,
            pWaitDstStageMask=wait_stages,
            commandBufferCount=len(s.commandbuffers),
            pCommandBuffers=[c.commandbuffer for c in s.commandbuffers],
            signalSemaphoreCount=len(s.signal_semaphores),
            pSignalSemaphores=signal_semaphores
        ))

    vk.vkQueueSubmit(queue, len(vk_submits), vk_submits, None)


def update_descriptorsets(context, writes, copies):
    '''
    Update the contents of a descriptor set object

    *Parameters:*

    - `context`: `VulkContext`
    - `writes`: `list` of `WriteDescriptorSet`
    - `copies`: `list` of `CopyDescriptorSet`

    **Todo: `copies` is unusable currently**
    **Todo: Only `DescriptorBufferInfo` supported**
    '''
    def get_type(t, descriptors):
        result = {'pImageInfo': None, 'pBufferInfo': None,
                  'pTexelBufferView': None}
        vk_descriptors = []

        if t in (vk.VK_DESCRIPTOR_TYPE_SAMPLER,
                 vk.VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER,
                 vk.VK_DESCRIPTOR_TYPE_SAMPLED_IMAGE,
                 vk.VK_DESCRIPTOR_TYPE_STORAGE_IMAGE,
                 vk.VK_DESCRIPTOR_TYPE_INPUT_ATTACHMENT):
            for d in descriptors:
                vk_descriptors.append(vk.VkDescriptorImageInfo(
                    sampler=d.sampler.sampler,
                    imageView=d.view.imageview,
                    imageLayout=d.layout.value
                ))
            result['pImageInfo'] = vk_descriptors

        elif t in (vk.VK_DESCRIPTOR_TYPE_UNIFORM_TEXEL_BUFFER,
                   vk.VK_DESCRIPTOR_TYPE_STORAGE_TEXEL_BUFFER):
            result['pTexelBufferView'] = [d.view for d in descriptors]

        elif t in (vk.VK_DESCRIPTOR_TYPE_UNIFORM_BUFFER,
                   vk.VK_DESCRIPTOR_TYPE_STORAGE_BUFFER,
                   vk.VK_DESCRIPTOR_TYPE_UNIFORM_BUFFER_DYNAMIC,
                   vk.VK_DESCRIPTOR_TYPE_STORAGE_BUFFER_DYNAMIC):
            for d in descriptors:
                vk_descriptors.append(vk.VkDescriptorBufferInfo(
                    buffer=d.buffer.buffer,
                    offset=d.offset,
                    range=d.range
                ))
            result['pBufferInfo'] = vk_descriptors

        return result

    vk_writes = []
    for w in writes:
        vk_writes.append(vk.VkWriteDescriptorSet(
            sType=vk.VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET,
            dstSet=w.set.descriptorset,
            dstBinding=w.binding,
            dstArrayElement=w.set_offset,
            descriptorCount=len(w.descriptors),
            descriptorType=w.type.value,
            **get_type(w.type.value, w.descriptors)
        ))

    # TODO: copies must be implemented
    vk.vkUpdateDescriptorSets(context.device, len(vk_writes),
                              vk_writes, len(copies), None)


# ----------
# NAMED TUPLES
# ----------
AttachmentDescription = namedtuple('AttachmentDescription',
                                   ['format', 'samples', 'load', 'store',
                                    'stencil_load', 'stencil_store',
                                    'initial_layout', 'final_layout'])
AttachmentDescription.__doc__ = '''
    AttachmentDescription describes the attachment.

    *Parameters:*

    - `format`: `Format` vulk constant
    - `samples`: `SampleCount` vulk constant
    - `load`: `AttachmentLoadOp` vulk constant
    - `store`: `AttachmentStoreOp` vulk constant
    - `stencil_load`: `AttachmentLoadOp` vulk constant
    - `stencil_store`: `AttachmentStoreOp` vulk constant
    - `initial_layout`: `ImageLayout` vulk constant
    - `final_layout`: `ImageLayout` vulk constant
    '''


AttachmentReference = namedtuple('AttachmentReference', ['index', 'layout'])
AttachmentReference.__doc__ = '''
    AttachmentReference links an attachment index with a layout.

    *Parameters:*

    - `index`: Index of attachment description
    - `layout`: `ImageLayout` vulk constant
    '''


DescriptorBufferInfo = namedtuple('DescriptorBufferInfo',
                                  ['buffer', 'offset', 'range'])
DescriptorBufferInfo.__doc__ = '''
    Structure specifying descriptor buffer info

    *Parameters:*

    - `buffer`: `Buffer` ressource
    - `offset`: Offset in bytes from the start of buffer
    - `range`: Size in bytes that is used for this descriptor update
    '''


DescriptorImageInfo = namedtuple('DescriptorImageInfo',
                                 ['sampler', 'view', 'layout'])
DescriptorImageInfo.__doc__ = '''
    Structure specifying descriptor image info

    *Parameters:*

    - `sampler`: `Sampler` ressource
    - `view`: `ImageView`
    - `layout`: `ImageLayout` vulk constant
    '''


DescriptorPoolSize = namedtuple('DescriptorPoolSize', ['type', 'count'])
DescriptorPoolSize.__doc__ = '''
    Structure specifying descriptor pool size.

    *Parameters:*

    - `type`: `DescriptorType` vulk constant
    - `count`: Number of descriptors of that type to allocate
    '''


DescriptorSetLayoutBinding = namedtuple('DescriptorSetLayoutBinding',
                                        ['binding', 'type', 'count',
                                         'stage', 'immutable_samplers'])
DescriptorSetLayoutBinding.__doc__ = '''
    Structure specifying a descriptor set layout binding.

    *Parameters:*

    - `binding`: Binding number of this entry and corresponds to a resource
                 of the same binding number in the shader stages
    - `type`: `DescriptorType` specifying which type of resource descriptors
              are used for this binding
    - `count`:  Number of descriptors contained in the binding,
                accessed in a shader as an array
    - `stage`: `ShaderStage` vulk constant specifying which pipeline shader
                stages can access a resource for this binding
    - `immutable_samplers`: Immutable `Sampler` (can be `None`)
    '''


Extent2D = namedtuple('Extent2D', ['width', 'height'])
Extent2D.__doc__ = '''
    *Parameters:*

    - `width`: Width
    - `height`: Height
    '''


Extent3D = namedtuple('Extent3D', ['width', 'height', 'depth'])
Extent3D.__doc__ = '''
    *Parameters:*

    - `width`: Width
    - `height`: Height
    - `depth`: Depth
    '''


ImageSubresourceRange = namedtuple('ImageSubresourceRange',
                                   ['aspect', 'base_miplevel', 'level_count',
                                    'base_layer', 'layer_count'])
ImageSubresourceRange.__doc__ = '''
    `ImageSubresourceRange` object describes what the image's purpose is and
    which part of the image should be accessed.

    *Parameters:*

    - `aspect`: `ImageAspect` vulk constant indicating which aspect(s) of the
                image are included in the view
    - `base_miplevel`: The first mipmap level accessible to the view
    - `level_count`: Number of mipmap levels (starting from base_miplevel)
                     accessible to the view
    - `base_layer`: First array layer accessible to the view
    - `layer_count`: Number of array layers (starting from base_layer)
                     accessible to the view
    '''


Offset2D = namedtuple('Offset2D', ['x', 'y'])
Offset2D.__doc__ = '''
    *Parameters:*

    - `x`: x offset
    - `y`: y offset
    '''


PipelineColorBlendAttachmentState = namedtuple(
    'PipelineColorBlendAttachmentState',
    ['enable', 'src_color', 'dst_color', 'color_op',
     'src_alpha', 'dst_alpha', 'alpha_op', 'color_mask']
)
PipelineColorBlendAttachmentState.__doc__ = '''
    *Parameters:*

    - `enable`: Enable blending
    - `src_color`: `BlendFactor` vulk constant for source color
    - `dst_color`: `BlendFactor` vulk constant for destination color
    - `color_op`: `BlendOp` vulk constant Operation on color
    - `src_alpha`: `BlendFactor` vulk constant for source alpha
    - `dst_alpha`: `BlendFactor` vulk constant for destination alpha
    - `alpha_op`: `BlendOp` vulk constant operation on alpha
    - `color_mask`: `ColorComponent` vulk constant selecting which of the
                    R, G, B, and A components are enabled for writing
    '''

PipelineColorBlendState = namedtuple('PipelineColorBlendState',
                                     ['op_enable', 'op', 'attachments',
                                      'constants'])
PipelineColorBlendState.__doc__ = '''
    *Parameters:*

    - `op_enable`: Enable bitwise combination
    - `op`: `LogicOp` vulk constant operation to perform
    - `attachments`: List of blend attachments for each framebuffer
    - `constants`: Constants depending on blend factor (`list` of 4 `float`)
    '''


PipelineDepthStencilState = namedtuple(
    'PipelineDepthStencilState',
    ['depth_test_enable', 'depth_write_enable', 'depth_bounds_test_enable',
     'depth_compare', 'stencil_test_enable', 'front', 'back', 'min', 'max']
)
PipelineDepthStencilState.__doc__ = '''
    *Parameters:*

    - `depth_test_enable`: Enable depth test
    - `depth_write_enable`: Enable depth write
    - `depth_bounds_test_enable`: Enable bounds test
    - `depth_compare`: `CompareOp` vulk constant condition to overwrite depth
    - `stencil_test_enable`: Enable stencil test
    - `front`: Control stencil parameter (`StencilOpState`)
    - `back`: Control stencil parameter (`StencilOpState`)
    - `min`: Define the min value in depth bound test (`float`)
    - `max`: Define the max value in depth bound test (`float`)
    '''


PipelineDynamicState = namedtuple('PipelineDynamicState', 'states')
PipelineDynamicState.__doc__ = '''
    - `states`: List of `VkDynamicState`
    '''


PipelineInputAssemblyState = namedtuple('PipelineInputAssemblyState',
                                        'topology')
PipelineInputAssemblyState.__doc__ = '''
    *Parameters:*

    - `topology`: `PrimitiveTopology` vulk constant to use when drawing
    '''


PipelineMultisampleState = namedtuple('PipelineMultisampleState',
                                      ['shading_enable', 'samples',
                                       'min_sample_shading'])
PipelineMultisampleState.__doc__ = '''
    *Parameters:*

    - `shading_enable`: Enable multisampling (`boolean`)
    - `samples`: Number of samples, `SampleCount` vulk constant
    - `min_sample_shading`: Minimum of sample (`float`)
    '''


PipelineRasterizationState = namedtuple(
    'PipelineRasterizationState',
    ['depth_clamp_enable', 'polygon_mode', 'line_width', 'cull_mode',
     'front_face', 'depth_bias_constant', 'depth_bias_clamp',
     'depth_bias_slope']
)
PipelineRasterizationState.__doc__ = '''
    *Parameters:*

    - `depth_clamp_enable`: Whether to enable depth clamping (`boolean`)
    - `polygon_mode`: Which `PolygonMode` vulk constant to use
    - `line_width`: Width of line (`float`)
    - `cull_mode`: The way of culling, `CullMode` vulk constant
    - `front_face`: `FrontFace` vulk constant
    - `depth_bias_constant`: Constant to add to depth (`float`)
    - `depth_bias_clamp`: Max depth bias (`float`)
    - `depth_bias_slope`: Factor to slope (`float`)
    '''


PipelineShaderStage = namedtuple('PipelineShaderStage', ['module', 'stage'])
PipelineShaderStage.__doc__ = '''
    *Parameters:*

    - `module`: The `ShaderModule` to bind
    - `stage`: `ShaderStage` vulk constant
    '''

PipelineVertexInputState = namedtuple('PipelineVertexInputState',
                                      ['bindings', 'attributes'])
PipelineVertexInputState.__doc__ = '''
    *Parameters:*

    - `bindings`: List of `VertexInputBindingDescription`
    - `attributes`: List of `VertexInputAttributeDescription`

    **Note: `bindings` and `attributes` can be empty `list`**
    '''


PipelineViewportState = namedtuple('PipelineViewportState',
                                   ['viewports', 'scissors'])
PipelineViewportState.__doc__ = '''
    The PipelineViewportState object contains viewports and scissors.

    *Parameters:*

    - `viewports`: `list` of `Viewport`
    - `scissors`: `list` of `Rect2D`
    '''


Rect2D = namedtuple('Rect2d', ['offset', 'extent'])
Rect2D.__doc__ = '''
    2D surface with offset.

    *Parameters:*

    - `offset`: `Offset2D` object
    - `extent`: `Extent2D` object
    '''


SubmitInfo = namedtuple('SubmitInfo', ['wait_semaphores', 'wait_stages',
                                       'signal_semaphores', 'commandbuffers'])
SubmitInfo.__doc__ = '''
    Submit information when submitting to queue

    *Parameters:*

    - `wait_semaphores`: `list` of `Semaphore` to wait on
    - `wait_stages`: `list` of `PipelineStage` vulk constant at which each
                     corresponding semaphore wait will occur. Must be the
                     same size as `wait_semaphores`
    - `signal_semaphores`: `list` of `Semaphore` to signal when commands
                           are finished
    - `commandbuffers`: `list` of `CommandBuffer` to execute
    '''


SubpassDependency = namedtuple('SubpassDependency',
                               ['src_subpass', 'src_stage', 'src_access',
                                'dst_subpass', 'dst_stage', 'dst_access'])
SubpassDependency.__doc__ = '''
    SubpassDependency describes all dependencies of the subpass.

    *Parameters:*

    - `src_subpass`: Source subpass `int` or `SUBPASS_EXTERNAL` vulk constant
    - `src_stage`: Source stage `PipelineStage` vulk constant
    - `src_access`: Source `Access` vulk constant
    - `dst_subpass`: Destination subpass `int` or
                     `SUBPASS_EXTERNAL` vulk constant
    - `dst_stage`: Destination stage `PipelineStage` vulk constant
    - `dst_access`: Destination `Access` vulk constant
    '''


SubpassDescription = namedtuple('SubpassDescription',
                                ['colors', 'inputs', 'resolves',
                                 'preserves', 'depth_stencil'])
SubpassDescription.__doc__ = '''
    `SubpassDescription` describes all attachments in the subpass.
    All parameters are of type `AttachmentReference`. If you don't want
    an attachment, set it to an empty list.

    *Parameters:*

    - `colors`: `list` of colors attachments
    - `inputs`: `list` of inputs attachments
    - `resolves`: `list` of resolves attachments (must be the same
                  size as inputs)
    - `preserves`: `list` of preserves attachments
    - `depth_stencil`: `list` containing only one attachment
    '''


VertexInputAttributeDescription = namedtuple('VertexInputAttributeDescription',
                                             ['location', 'binding', 'format',
                                              'offset'])
VertexInputAttributeDescription.__doc__ = '''
     Structure specifying vertex input attribute description

    *Parameters:*

    - `location`: Shader binding location number for this attribute (`int`)
    - `binding`: Binding number which this attribute takes its data from
    - `format`: `Format` vulk constant of the vertex attribute data
    - `offset`: Byte offset of this attribute relative to the start of an
                element in the vertex input binding (`int`)
    '''


VertexInputBindingDescription = namedtuple('VertexInputBindingDescription',
                                           ['binding', 'stride', 'rate'])
VertexInputBindingDescription.__doc__ = '''
    Structure specifying vertex input binding description

    *Parameters:*

    - `binding`: Binding number (`int`)
    - `stride`: Distance in bytes between two consecutive elements within
                the buffer (`int`)
    - `rate`: `VertexInputRate` vulk constant
    '''

Viewport = namedtuple('Viewport', ['x', 'y', 'width', 'height',
                                   'min_depth', 'max_depth'])
Viewport.__doc__ = '''
    Structure specifying a viewport

    *Parameters:*

    - `x`: X upper left corner
    - `y`: Y upper left corner
    - `width`: Viewport width
    - `height`: Viewport height
    - `min_depth`: Depth range for the viewport
    - `max_depth`: Depth range for the viewport

    **Note: `min_depth` and `max_depth` must be between 0.0 and 1.0**
    '''


WriteDescriptorSet = namedtuple('WriteDescriptorSet',
                                ['set', 'binding', 'set_offset',
                                 'type', 'descriptors'])
WriteDescriptorSet.__doc__ = '''
    Structure specifying the parameters of a descriptor set write operation

    *Parameters:*

    - `set`: Destination `DescriptorSet` set to update
    - `binding`: Descriptor binding within that set
    - `set_offset`: Offset to start with in the descriptor
    - `type`: Type of descriptor `DescriptorType` vulk constant
    - `descriptors`: `list` of `DescriptorBufferInfo` or `DescriptorImageInfo`
                    or `BufferView` depending on `type`

    **Note: The descriptor type must correspond to the `type` parameter**
    '''


# ----------
# CLASSES
# ----------
class Buffer():
    '''
    `Buffer` wrap a `VkBuffer` and a `VkMemory`
    '''

    def __init__(self, context, flags, size, usage, sharing_mode,
                 queue_families, memory_properties):
        '''Create a new buffer

        Creating a buffer is made of several steps:

        - Create the buffer
        - Allocate the memory
        - Bind the memory to the buffer

        *Parameters:*

        - `context`: `VulkContext`
        - `flags`: `BufferCreate` vulk constant
        - `size`: Buffer size in bytes
        - `usage`: `BufferUsage` vulk constant
        - `sharing_mode`: `SharingMode` vulk constant
        - `queue_families`: List of queue families accessing this image
                            (ignored if sharingMode is not
                            `CONCURRENT`) (can be [])
        - `memory_properties`: `MemoryProperty` vulk constant
        '''
        self.memory_properties = memory_properties.value
        self.size = size

        # Create VkBuffer
        buffer_create = vk.VkBufferCreateInfo(
            sType=vk.VK_STRUCTURE_TYPE_BUFFER_CREATE_INFO,
            flags=flags.value,
            size=self.size,
            usage=usage.value,
            sharingMode=sharing_mode.value,
            queueFamilyIndexCount=len(queue_families),
            pQueueFamilyIndices=queue_families if queue_families else None
        )

        self.buffer = vk.vkCreateBuffer(context.device, buffer_create, None)

        # Get memory requirements
        requirements = vk.vkGetBufferMemoryRequirements(context.device,
                                                        self.buffer)

        alloc_info = vk.VkMemoryAllocateInfo(
            sType=vk.VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO,
            allocationSize=requirements.size,
            memoryTypeIndex=find_memory_type(
                context,
                requirements.memoryTypeBits,
                self.memory_properties
            )
        )

        # Create memory
        self.memory = vk.vkAllocateMemory(context.device, alloc_info, None)

        # Bind device memory to the buffer
        vk.vkBindBufferMemory(context.device, self.buffer, self.memory, 0)

    def copy_to(self, cmd, dst_buffer):
        '''
        Copy this buffer to the destination buffer.
        Commands to copy are registered in the commandbuffer but it's up to
        you to start and submit the command buffer to the execution queue.

        *Parameters:*

        - `cmd`: `CommandBufferRegister` used to register commands
        - `dst_buffer`: Destination `Buffer`

        **Note: Buffers must have the same size**
        '''
        if self.size != dst_buffer.size:
            msg = "Buffers must have the same size"
            logger.error(msg)
            raise VulkError(msg)

        region = vk.VkBufferCopy(
            srcOffset=0,
            dstOffset=0,
            size=self.size
        )

        cmd.copy_buffer(self, dst_buffer, [region])

    @contextmanager
    def bind(self, context):
        '''
        Map this buffer to upload data in it.
        This function is a context manager and must be called with `with`.
        It return a python buffer and let you do what you want with it,
        be careful!

        *Parameters:*

        - `context`: The `VulkContext`

        **Warning: Buffer memory must be host visible**
        '''
        compatible_memories = {vk.VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT,
                               vk.VK_MEMORY_PROPERTY_HOST_COHERENT_BIT,
                               vk.VK_MEMORY_PROPERTY_HOST_CACHED_BIT}
        if not any([self.memory_properties & m for m in compatible_memories]):
            msg = "Can't map this buffer, memory must be host visible"
            logger.error(msg)
            raise VulkError(msg)

        try:
            data = vk.vkMapMemory(context.device, self.memory, 0,
                                  self.size, 0)
            yield data
        finally:
            vk.vkUnmapMemory(context.device, self.memory)


class ClearColorValue():
    '''ClearValue for color clearing'''

    def __init__(self, float32=None, uint32=None, int32=None):
        '''
        Take only one value depending on the type you want.
        `list` must be of size 4.

        *Parameters:*

        - `float32`: Type `float`
        - `uint32`: Type `uint`
        - `int32`: Type `int`
        '''
        t = (float32, uint32, int32)

        # Set to list
        for v in t:
            v = [] if v is None else v

        # Check that only one value is set
        if sum(1 for i in t if i) != 1:
            msg = "Only one value in [float32, uint32, int32] must be given"
            logger.error(msg)
            raise VulkError(msg)

        # Check size of value (must be 4)
        if len(next(iter([v for v in t if t]))) != 4:
            msg = "Value must be a list of 4 elements"
            logger.error(msg)
            raise VulkError(msg)

        if float32:
            clear = vk.VkClearColorValue(float32=float32)
        if uint32:
            clear = vk.VkClearColorValue(uint32=uint32)
        if int32:
            clear = vk.VkClearColorValue(int32=int32)

        self.clear = clear


class ClearDepthStencilValue():
    '''ClearValue for depth and stencil clearing'''

    def __init__(self, depth, stencil):
        '''
        *Parameters:*

        - `depth`: Value in [0.0, 1.0]
        - `stencil`; `int` value
        '''
        self.clear = vk.VkClearDepthStencilValue(depth=depth, stencil=stencil)


class CommandBuffer():
    '''
    Commands in Vulkan, like drawing operations and memory transfers, are not
    executed directly using function calls. You have to record all of the
    operations you want to perform in command buffer objects. The advantage of
    this is that all of the hard work of setting up the drawing commands can
    be done in advance and in multiple threads. After that, you just have to
    tell Vulkan to execute the commands in the main loop.

    Commands are executed directly from the `CommandBufferRegister` subclass.
    The naming convention is simple:
    `vkCmd[CommandName]` becomes `command_name`
    '''

    def __init__(self, commandbuffer):
        '''
        This object must be initialized with an existing `VkCommandBuffer`
        because it is generated from `CommandPool`.

        *Parameters:*

        - `commandbuffer`: `VkCommandBuffer`
        '''
        self.commandbuffer = commandbuffer

    def reset(self, flags=vc.CommandBufferReset.NONE):
        '''
        Reset the command buffer

        *Parameters:*

        - `flags`: `CommandBufferReset` vulk constant, default to 0
        '''
        vk.vkResetCommandBuffer(self.commandbuffer, flags)

    @contextmanager
    def bind(self, flags=vc.CommandBufferUsage.NONE):
        '''
        Bind this buffer to register command.

        *Parameters:*

        - `flags`: `CommandBufferUsage` vulk constant, default to 0

        *Returns:*

        `CommandBufferRegister` object

        **Todo: `pInheritanceInfo` must be implemented**
        '''
        commandbuffer_begin_create = vk.VkCommandBufferBeginInfo(
            sType=vk.VK_STRUCTURE_TYPE_COMMAND_BUFFER_BEGIN_INFO,
            flags=flags.value,
            pInheritanceInfo=None
        )
        try:
            vk.vkBeginCommandBuffer(
                self.commandbuffer,
                commandbuffer_begin_create)
            yield CommandBufferRegister(self.commandbuffer)
        finally:
            vk.vkEndCommandBuffer(self.commandbuffer)


class CommandBufferRegister():
    '''
    Allow to call command on command buffer.
    `CommandBufferRegister` is not in charge of begin and end the command
    buffer. You should not use it directly but with `bind` method of
    `CommandBuffer`.
    '''
    def __init__(self, commandbuffer):
        '''
        *Parameters:*

        - `commandbuffer`: The `VkCommandBuffer`
        '''
        self.commandbuffer = commandbuffer

    def begin_renderpass(self, renderpass, framebuffer, renderarea,
                         clears, contents=vc.SubpassContents.INLINE):
        '''
        Begin a new renderpass

        *Parameters:*

        - `renderpass`: The `RenderPass` to begin an instance of
        - `framebuffer`: The `Framebuffer` containing the attachments that
                         are used with the render pass
        - `renderarea`: `Rect2D` size to render
        - `clears`:  `list` of `ClearValue` for each `Framebuffer`
        - `contents`: `SubpassContents` vulk constant (default: `INLINE`)
        '''
        vk_renderarea = vk.VkRect2D(
            offset=vk.VkOffset2D(
                x=renderarea.offset.x,
                y=renderarea.offset.y),
            extent=vk.VkExtent2D(
                width=renderarea.extent.width,
                height=renderarea.extent.height)
        )

        vk_clearvalues = []
        for c in clears:
            if isinstance(c, ClearColorValue):
                vk_clearvalues.append(vk.VkClearValue(color=c.clear))
            elif isinstance(c, ClearDepthStencilValue):
                vk_clearvalues.append(vk.VkClearValue(depthStencil=c.clear))
            else:
                msg = "Unknown clear value"
                logger.error(msg)
                raise VulkError(msg)

        renderpass_begin = vk.VkRenderPassBeginInfo(
            sType=vk.VK_STRUCTURE_TYPE_RENDER_PASS_BEGIN_INFO,
            renderPass=renderpass.renderpass,
            framebuffer=framebuffer.framebuffer,
            renderArea=vk_renderarea,
            clearValueCount=len(vk_clearvalues),
            pClearValues=vk_clearvalues
        )

        vk.vkCmdBeginRenderPass(self.commandbuffer, renderpass_begin,
                                contents)

    def bind_descriptor_sets(self, layout, first, descriptors, offsets,
                             bind_point=vc.PipelineBindPoint.GRAPHICS):
        '''
        Binds descriptor sets to this `CommandBuffer`

        *Parameters:*

        - `layout`: `PipelineLayout`
        - `first`: Number of the first descriptor set to be bound
        - `descriptors`: `list` of `DescriptorSet`
        - `offsets`: `list` of dynamic offsets
        - `bind_point`: `PipelineBindPoint` vulk constant (default: GRAPHICS)
        '''
        vk_descriptors = [d.descriptorset for d in descriptors]
        vk.vkCmdBindDescriptorSets(
            self.commandbuffer, bind_point, layout.layout, first,
            len(vk_descriptors), vk_descriptors, len(offsets),
            offsets if offsets else None)

    def bind_pipeline(self, pipeline,
                      bind_point=vc.PipelineBindPoint.GRAPHICS):
        '''
        Bind the pipeline to this `CommandBuffer`.

        *Parameters:*

        - `pipeline`: The `Pipeline` to bind
        - `bind_point`: `PipelineBindPoint` vulk constant (default: GRAPHICS)
        '''
        vk.vkCmdBindPipeline(self.commandbuffer, bind_point, pipeline.pipeline)

    def bind_vertex_buffers(self, first, count, buffers, offsets):
        '''
        Bind vertex buffers to a command buffer

        *Parameters:*

        - `first`: Index of the first vertex input binding
        - `count`: Number of vertex input bindings
        - `buffers`: `list` of `Buffer`
        - `offsets`: `list` of offset (`int`)

        **Note: I don't understand what is the point with offset but you
                must pass an array of the same size as `buffers`.**

        **Note: Generally, `count = len(buffers)` and `first = 0`**
        '''
        vk.vkCmdBindVertexBuffers(self.commandbuffer, first, count,
                                  [b.buffer for b in buffers], offsets)

    def bind_index_buffer(self, buffer, offset, index_type):
        '''
        Bind an index buffer to a command buffer

        *Parameters:*

        - `buffer`: Index `Buffer`
        - `offset`: Offset (`int`)
        - `index_type`: `IndexType` vulk constant
        '''
        vk.vkCmdBindIndexBuffer(self.commandbuffer, buffer.buffer, offset,
                                index_type)

    def clear_color_image(self, image, layout, clear_color, ranges):
        '''
        Clear image with color values

        *Parameters:*

        - `image`: `Image` to clear
        - `layout`: `ImageLayout` of `image`
        - `clear_color`: `ClearColorValue`
        - `ranges`: `list` of `ImageSubresourceRange`
        '''
        vk_ranges = []
        for r in ranges:
            vk_ranges.append(vk.VkImageSubresourceRange(
                aspectMask=r.aspect.value,
                baseMipLevel=r.base_miplevel,
                levelCount=r.level_count,
                baseArrayLayer=r.base_layer,
                layerCount=r.layer_count
            ))

        vk.vkCmdClearColorImage(self.commandbuffer, image.image, layout,
                                clear_color.clear, len(vk_ranges), vk_ranges)

    def draw(self, vertex_count, first_vertex,
             instance_count=1, first_instance=0):
        '''
        Draw the vertice buffer.

        When the command is executed, primitives are assembled using the
        current primitive topology and vertexCount consecutive vertex
        indices with the first vertexIndex value equal to firstVertex.
        The primitives are drawn instanceCount times with instanceIndex
        starting with firstInstance and increasing sequentially for each
        instance. The assembled primitives execute the currently bound
        graphics pipeline.

        *Parameters:*

        - `vertex_count`: Number of vertices to draw
        - `first_vertex`: Index of the first vertex to draw
        - `instance_count`: Number of instance to draw (default: 1)
        - `first_instance`: First instance to draw (default: 0)
        '''
        vk.vkCmdDraw(self.commandbuffer, vertex_count, instance_count,
                     first_vertex, first_instance)

    def draw_indexed(self, index_count, first_index, vertex_offset=0,
                     instance_count=1, first_instance=0):
        '''
        Draw the index buffer.

        When the command is executed, primitives are assembled using the
        current primitive topology and indexCount vertices whose indices are
        retrieved from the index buffer. The index buffer is treated as an
        array of tightly packed unsigned integers of size defined by the
        vkCmdBindIndexBuffer::indexType parameter with which the buffer
        was bound.

        The first vertex index is at an offset of
        firstIndex * indexSize + offset within the currently bound index
        buffer, where offset is the offset specified by vkCmdBindIndexBuffer
        and indexSize is the byte size of the type specified by indexType.
        Subsequent index values are retrieved from consecutive locations in
        the index buffer. Indices are first compared to the primitive restart
        value, then zero extended to 32 bits
        (if the indexType is VK_INDEX_TYPE_UINT16) and have vertexOffset added
        to them, before being supplied as the vertexIndex value.

        The primitives are drawn instanceCount times with instanceIndex
        starting with firstInstance and increasing sequentially for each
        instance. The assembled primitives execute the currently bound
        graphics pipeline.

        *Parameters:*

        - `index_count`: Number of vertices to draw
        - `first_index`: Base index within the index buffer
        - `vertex_offset`: Value added to the vertex index before indexing
                           into the vertex buffer (default: 0)
        - `instance_count`: Number of instance to draw (default: 1)
        - `first_instance`: First instance to draw (default: 0)
        '''
        vk.vkCmdDrawIndexed(self.commandbuffer, index_count, instance_count,
                            first_index, vertex_offset, first_instance)

    def pipeline_barrier(self, src_stage, dst_stage, dependency, memories,
                         buffers, images):
        '''
        Insert a memory dependency

        *Parameters:*

        - `src_stage`: `PipelineStage` vulk constant
        - `dst_stage`: `PipelineStage` vulk constant
        - `dependency`: `Dependency` vulk constant
        - `memories`: `list` of `VkMemoryBarrier` Vulkan objects
        - `buffers`: `list` of `VkBufferMemoryBarrier` Vulkan objects
        - `images`: `list` of `VkImageMemoryBarrier` Vulkan objects
        '''
        vk_memories = memories if memories else None
        vk_buffers = buffers if buffers else None
        vk_images = images if images else None
        vk.vkCmdPipelineBarrier(
            self.commandbuffer, src_stage.value, dst_stage.value,
            dependency.value, len(memories), vk_memories, len(buffers),
            vk_buffers, len(images), vk_images
        )

    def copy_image(self, src_image, src_layout, dst_image,
                   dst_layout, regions):
        '''
        Copy data between images

        *Parameters:*

        - `src_image`: `Image`
        - `src_layout`: `ImageLayout` vulk constant
        - `dst_image`: `Image`
        - `dst_layout`: `ImageLayout` vulk constant
        - `regions`: `list` of `VkImageCopy`

        '''
        vk.vkCmdCopyImage(
            self.commandbuffer, src_image.image, src_layout.value,
            dst_image.image, dst_layout.value, len(regions), regions
        )

    def copy_buffer(self, src_buffer, dst_buffer, regions):
        '''
        Copy data between buffers

        *Parameters:*

        - `src_buffer`: `Buffer`
        - `dst_buffer`: `Buffer`
        - `regions`: `list` of `VkBufferCopy`
        '''
        vk.vkCmdCopyBuffer(self.commandbuffer, src_buffer.buffer,
                           dst_buffer.buffer, len(regions), regions)

    def end_renderpass(self):
        '''End the current render pass'''
        vk.vkCmdEndRenderPass(self.commandbuffer)


class CommandPool():
    '''
    Command pools manage the memory that is used to store the buffers and
    command buffers are allocated from them.
    '''

    def __init__(self, context, queue_family_index,
                 flags=vc.CommandPoolCreate.NONE):
        '''
        *Parameters:*

        - `context`: The `VulkContext`
        - `queue_family_index`: Index of the queue family to use
        - `flags`: `CommandPoolCreate` vulk constant, default to 0
        '''
        commandpool_create = vk.VkCommandPoolCreateInfo(
            sType=vk.VK_STRUCTURE_TYPE_COMMAND_POOL_CREATE_INFO,
            queueFamilyIndex=queue_family_index,
            flags=flags.value
        )

        # The Vulkan command pool
        self.commandpool = vk.vkCreateCommandPool(
            context.device, commandpool_create, None)
        # Command buffers allocated from this pool
        self.commandbuffers = []

    def allocate_buffers(self, context, level, count):
        '''
        Allocate `list` of `CommandBuffer` from pool.

        *Parameters:*

        - `context`: The `VulkContext`
        - `level`: `CommandBufferLevel` vulk constant
        - `count`: Number of `CommandBuffer` to create

        *Returns:*

        `list` of `CommandBuffer`
        '''
        commandbuffers_create = vk.VkCommandBufferAllocateInfo(
            sType=vk.VK_STRUCTURE_TYPE_COMMAND_BUFFER_ALLOCATE_INFO,
            commandPool=self.commandpool,
            level=level.value,
            commandBufferCount=count
        )

        vk_commandbuffers = vk.vkAllocateCommandBuffers(
            context.device,
            commandbuffers_create)

        commandbuffers = [CommandBuffer(cb) for cb in vk_commandbuffers]
        self.commandbuffers.extend(commandbuffers)

        return commandbuffers

    def free_buffers(self, context, buffers):
        '''
        Free list of `CommandBuffer` allocated from this pool.

        *Parameters:*

        - `context`: The `VulkContext`
        - `buffers`: `list` of `CommandBuffer` to free
        '''
        if any([b not in self.commandbuffers for b in buffers]):
            msg = "Can't free a commandbuffer not allocated by this pool"
            logger.error(msg)
            raise VulkError(msg)

        vk.vkFreeCommandBuffers(
            context.device, self.commandpool, len(buffers),
            [b.commandbuffer for b in buffers]
        )

    def free(self, context):
        '''
        Free this command pool

        *Parameters:*

        - `context`: `VulkContext`
        '''
        vk.vkDestroyCommandPool(context.device, self.commandpool, None)


class DescriptorPool():
    '''
    A descriptor pool maintains a pool of descriptors, from which descriptor
    sets are allocated. Descriptor pools are externally synchronized, meaning
    that the application must not allocate and/or free descriptor sets from
    the same pool in multiple threads simultaneously.
    '''

    def __init__(self, context, poolsizes, max_sets,
                 flags=vc.DescriptorPoolCreate.NONE):
        '''
        *Parameters:*

        - `context`: `VulkContext`
        - `poolsizes`: `list` of `PoolSize`
        - `max_sets`: Maximum number of descriptor sets that can be
                      allocated from the pool
        - `flags`: `DescriptorPoolCreate`  vulk constant (default=0)
        '''
        vk_poolsizes = []
        for p in poolsizes:
            vk_poolsizes.append(vk.VkDescriptorPoolSize(
                type=p.type.value,
                descriptorCount=p.count
            ))

        descriptorpool_create = vk.VkDescriptorPoolCreateInfo(
            sType=vk.VK_STRUCTURE_TYPE_DESCRIPTOR_POOL_CREATE_INFO,
            flags=flags.value,
            maxSets=max_sets,
            poolSizeCount=len(vk_poolsizes),
            pPoolSizes=vk_poolsizes
        )

        self.descriptorpool = vk.vkCreateDescriptorPool(
            context.device, descriptorpool_create, None)

    def allocate_descriptorsets(self, context, count, layouts):
        '''
        Allocate `list` of `DescriptorSet` from pool.

        *Parameters:*

        - `context`: `VulkContext`
        - `count`: Number of `DescriptorSet` to create
        - `layouts`: `list` of `DescriptorSetLayout`

        *Returns:*

        `list` of `DescriptorSet`

        **Note: Size of `layouts` list must be equals to `count`**
        '''
        descriptorsets_create = vk.VkDescriptorSetAllocateInfo(
            sType=vk.VK_STRUCTURE_TYPE_DESCRIPTOR_SET_ALLOCATE_INFO,
            descriptorPool=self.descriptorpool,
            descriptorSetCount=count,
            pSetLayouts=[d.descriptorsetlayout for d in layouts]
        )

        vk_descriptorsets = vk.vkAllocateDescriptorSets(
            context.device, descriptorsets_create)

        descriptorsets = [DescriptorSet(ds) for ds in vk_descriptorsets]
        return descriptorsets


class DescriptorSet():
    '''
    A *descriptor set* specifies the actual buffer or image resources that
    will be bound to the descriptors, just like a framebuffer specifies the
    actual image views to bind to render pass attachments. The descriptor set
    is then bound for the drawing commands just like the vertex buffers
    and framebuffer.
    '''

    def __init__(self, descriptorset):
        '''
        This object must be initialized with an existing `VkDescriptorSet`
        because it is generated from `DescriptorPool`.

        *Parameters:*

        - `descriptorset`: `VkDescriptorSet`
        '''
        self.descriptorset = descriptorset


class DescriptorSetLayout():
    '''
    A descriptor set layout object is defined by an array of zero or more
    descriptor bindings. Each individual descriptor binding is specified by
    a descriptor type, a count (array size) of the number of descriptors in
    the binding, a set of shader stages that can access the binding,
    and (if using immutable samplers) an array of sampler descriptors.
    '''

    def __init__(self, context, bindings):
        '''
        *Parameters:*

        - `context`: `VulkContext`
        - `bindings`: `list` of `DescriptorSetLayoutBinding`
        '''
        vk_bindings = []
        for b in bindings:
            vk_bindings.append(vk.VkDescriptorSetLayoutBinding(
                binding=b.binding,
                descriptorType=b.type.value,
                descriptorCount=b.count,
                stageFlags=b.stage.value,
                pImmutableSamplers=b.immutable_samplers
            ))

        layout_create = vk.VkDescriptorSetLayoutCreateInfo(
            sType=vk.VK_STRUCTURE_TYPE_DESCRIPTOR_SET_LAYOUT_CREATE_INFO,
            flags=0,
            bindingCount=len(vk_bindings),
            pBindings=vk_bindings
        )

        self.descriptorsetlayout = vk.vkCreateDescriptorSetLayout(
            context.device, layout_create, None)


class Framebuffer():
    '''
    In Vulkan, a `Framebuffer` references all of the `VkImageView` objects that
    represent the attachments of a `Renderpass`.
    '''

    def __init__(self, context, renderpass, attachments,
                 width, height, layers):
        '''
        *Parameters:*

        - `context`: The `VulkContext`
        - `renderpass`: The compatible `Renderpass` of this `Framebuffer`
        - `attachments`: List of `ImageView`
        - `width`: Width (`int`)
        - `height`: Height (`int`)
        - `layers`: Number of layers (`int`)
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
                                                  framebuffer_create, None)


class HighPerformanceBuffer():
    '''
    `HighPerformanceBuffer` allows to use high performance buffer to be
    accessed in your vertex stage.

    To get the maximum performance, we are going to create two `Buffer`,
    a staging buffer which memory can be updated and a final buffer with
    very fast memory that we will use in pipeline.
    When we create a buffer, we first upload data in the staging buffer
    and then copy the memory in the final buffer. Of course, both of the
    buffer have the same properties.
    '''

    def __init__(self, context, size, usage,
                 sharing_mode=vc.SharingMode.EXCLUSIVE,
                 queue_families=None):
        '''Create a high performance buffer

        *Parameters:*

        - `context`: `VulkContext`
        - `size`: Buffer size in bytes
        - `usage`: `BufferUsage` vulk constant
        - 'buffer_type': `str` in ['index', 'uniform', 'vertex']
        - `sharing_mode`: `SharingMode` vulk constant
        - `queue_families`: List of queue families accessing this image
                            (ignored if sharingMode is not CONCURRENT)
                            (can be [])
        '''
        queue_families = queue_families if queue_families else []

        self.staging_buffer = Buffer(
            context, vc.BufferCreate.NONE, size, vc.BufferUsage.TRANSFER_SRC,
            sharing_mode, queue_families,
            vc.MemoryProperty.HOST_VISIBLE | vc.MemoryProperty.HOST_COHERENT
        )

        self.final_buffer = Buffer(
            context, vc.BufferCreate.NONE, size,
            vc.BufferUsage.TRANSFER_DST | usage,
            sharing_mode, queue_families,
            vc.MemoryProperty.DEVICE_LOCAL
        )

    def _finalize(self, context):
        '''
        Copy the staging buffer to the final buffer.

        *Parameters:*

        - `context`: `VulkContext`
        '''
        with immediate_buffer(context) as cmd:
            self.staging_buffer.copy_to(cmd, self.final_buffer)

    @contextmanager
    def bind(self, context):
        '''Bind buffer for writing

        It calls `bind` method of the staging buffer and copy the buffer
        when the contextmanager is released. Must be used with `with`.

        *Parameters:*

        - `context`: `VulkContext`
        '''
        try:
            with self.staging_buffer.bind(context) as b:
                yield b
        finally:
            self._finalize(context)


class HighPerformanceImage():
    '''
    `HighPerformanceImage` allows to use high performance image to be
    sampled in your shaders.

    To get the maximum performance, we are going to create two `Image`,
    a staging image which memory can be updated (with our texture) and
    a final image with very fast memory that we will use in shaders.
    When we create an image, we first upload the pixels in the staging
    image and then copy the memory in the final image. Of course, both of
    the image have the same properties.

    **Note: MipMap generation is done only on the final image, the staging
            image don't need mipmap.**
    '''

    def __init__(self, context, image_type, image_format, width, height,
                 depth, mip_level, layers, samples,
                 sharing_mode=vc.SharingMode.EXCLUSIVE,
                 queue_families=None):
        '''Create a high performance image

        *Parameters:*

        - `context`: `VulkContext`
        - `image_type`: `ImageType` vulk constant
        - `image_format`: `Format` of the image
        - `width`: Image width
        - `heigth`: Image height
        - `depth`: Image depth
        - `mip_level`: Level of mip (`int`) (only for final_image)
        - `layers`: Number of layers (`int`)
        - `samples`: This `SampleCount` vulk constant is related
                     to multisampling
        - `sharing_mode`: `SharingMode` vulk constant
        - `queue_families`: List of queue families accessing this image
                            (ignored if sharingMode is not `CONCURRENT`)
                            (can be [])
        '''
        if not queue_families:
            queue_families = []

        # Miplevel is applied automatically on final image if > 1
        self.mip_level = mip_level

        self.staging_image = Image(
            context, image_type, image_format, width, height, depth, 1,
            layers, samples, sharing_mode, queue_families,
            vc.ImageLayout.PREINITIALIZED, vc.ImageTiling.LINEAR,
            vc.ImageUsage.TRANSFER_SRC,
            vc.MemoryProperty.HOST_VISIBLE | vc.MemoryProperty.HOST_COHERENT
        )
        self.final_image = Image(
            context, image_type, image_format, width, height, depth, mip_level,
            layers, samples, sharing_mode, queue_families,
            vc.ImageLayout.PREINITIALIZED, vc.ImageTiling.OPTIMAL,
            vc.ImageUsage.TRANSFER_DST | vc.ImageUsage.SAMPLED,
            vc.MemoryProperty.DEVICE_LOCAL
        )

    def _copy_staging_to_final(self, context):
        '''
        Prepare and copy the staging image to the final image.

        *Parameters:*

        - `context`: `VulkContext`
        '''
        commandpool = CommandPool(context,
                                  context.queue_family_indices['graphic'])

        # Transition the staging image to optimal source transfert layout
        with immediate_buffer(context, commandpool) as cmd:
            self.staging_image.update_layout(
                cmd, vc.ImageLayout.PREINITIALIZED,
                vc.ImageLayout.TRANSFER_SRC_OPTIMAL,
                vc.PipelineStage.TOP_OF_PIPE,
                vc.PipelineStage.TOP_OF_PIPE,
                vc.Access.HOST_WRITE,
                vc.Access.TRANSFER_READ
            )

        # Transition the final image to optimal destination transfert layout
        with immediate_buffer(context, commandpool) as cmd:
            self.final_image.update_layout(
                cmd, vc.ImageLayout.PREINITIALIZED,
                vc.ImageLayout.TRANSFER_DST_OPTIMAL,
                vc.PipelineStage.TOP_OF_PIPE,
                vc.PipelineStage.TOP_OF_PIPE,
                vc.Access.HOST_WRITE,
                vc.Access.TRANSFER_WRITE
            )

        # Copy staging image into final image
        with immediate_buffer(context, commandpool) as cmd:
            self.staging_image.copy_to(cmd, self.final_image)

        # Set the best layout for the final image
        with immediate_buffer(context, commandpool) as cmd:
            self.final_image.update_layout(
                cmd, vc.ImageLayout.TRANSFER_DST_OPTIMAL,
                vc.ImageLayout.SHADER_READ_ONLY_OPTIMAL,
                vc.PipelineStage.TOP_OF_PIPE,
                vc.PipelineStage.TOP_OF_PIPE,
                vc.Access.TRANSFER_WRITE,
                vc.Access.SHADER_READ
            )

    def _finalize(self, context):
        '''
        Prepare and copy the staging image to the final image.
        Generate Mipmap if needed.

        *Parameters:*

        - `context`: `VulkContext`
        '''
        self._copy_staging_to_final(context)

    @contextmanager
    def bind(self, context):
        '''Bind image for writing

        It calls `bind` method of the staging image and copy the image
        when the contextmanager is released. Must be used with `with`.

        *Parameters:*

        - `context`: `VulkContext`
        '''
        try:
            with self.staging_image.bind(context) as b:
                yield b
        finally:
            self._finalize(context)


class Image():
    '''
    `Image` is a wrapper around a `VkImage` and a `VkMemory`
    '''

    def __init__(self, context, image_type, image_format, width, height, depth,
                 mip_level, layers, samples, sharing_mode, queue_families,
                 layout, tiling, usage, memory_properties):
        '''Create a new image

        Creating an image is made of several steps:

        - Create the image
        - Allocate the memory
        - Bind the memory to the image

        *Parameters:*

        - `context`: `VulkContext`
        - `image_type`: `ImageType` vulk constant
        - `image_format`: `Format` vulk constant
        - `width`: Image width
        - `heigth`: Image height
        - `depth`: Image depth
        - `mip_level`: Level of mip (`int`)
        - `layers`: Number of layers (`int`)
        - `samples`: This `SampleCount` vulk constant is related
                     to multisampling
        - `sharing_mode`: `SharingMode` vulk constant
        - `queue_families`: List of queue families accessing this image
                            (ignored if sharingMode is not `CONCURRENT`)
                            (can be [])
        - `layout`: `ImageLayout` vulk constant
        - `tiling`: `ImageTiling` vulk constant
        - `usage`: `ImageUsage` vulk constant
        - `memory_properties`: `MemoryProperty` vulk constant
        '''
        self.width = width
        self.height = height
        self.depth = depth
        self.mip_level = mip_level
        self.format = image_format
        self.memory_properties = memory_properties
        image_type = image_type.value
        tiling = tiling.value
        usage = usage.value
        flags = 0

        # Check that image can be created
        try:
            vk.vkGetPhysicalDeviceImageFormatProperties(
                context.physical_device, self.format, image_type, tiling,
                usage, flags)
        except vk.VkErrorFormatNotSupported:
            raise VulkError("Can't create image, format "
                            "%s not supported" % image_format)

        # Create the VkImage
        vk_extent = vk.VkExtent3D(width=width,
                                  height=height,
                                  depth=depth)

        image_create = vk.VkImageCreateInfo(
            sType=vk.VK_STRUCTURE_TYPE_IMAGE_CREATE_INFO,
            flags=0,
            imageType=image_type,
            format=self.format.value,
            extent=vk_extent,
            mipLevels=mip_level,
            arrayLayers=layers,
            samples=samples.value,
            tiling=tiling,
            usage=usage,
            sharingMode=sharing_mode.value,
            queueFamilyIndexCount=len(queue_families),
            pQueueFamilyIndices=queue_families if queue_families else None,
            initialLayout=layout.value
        )

        self.image = vk.vkCreateImage(context.device, image_create, None)

        # Get memory requirements
        requirements = vk.vkGetImageMemoryRequirements(context.device,
                                                       self.image)

        alloc_info = vk.VkMemoryAllocateInfo(
            sType=vk.VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO,
            allocationSize=requirements.size,
            memoryTypeIndex=find_memory_type(
                context,
                requirements.memoryTypeBits,
                self.memory_properties
            )
        )

        self.memory = vk.vkAllocateMemory(context.device, alloc_info, None)

        # Bind device memory to the image
        vk.vkBindImageMemory(context.device, self.image, self.memory, 0)

    def update_layout(self, cmd, old_layout, new_layout, src_stage,
                      dst_stage, src_access, dst_access):
        '''
        Update the image layout.
        Command to update layout are registered in the commandbuffer
        but it's up to you to start and submit the command buffer to
        the execution queue.

        *Parameters:*

        - `cmd`: `CommandBufferRegister` used to register commands
        - `old_layout`: `ImageLayout` vulk constant
        - `new_layout`: `ImageLayout` vulk constant
        - `src_stage`: `PipelineStage` vulk constant
        - `dst_stage`: `PipelineStage` vulk constant
        - `src_access`: `Access` vulk constant
        - `dst_access`: `Access` vulk constant
        '''
        subresource_range = vk.VkImageSubresourceRange(
            aspectMask=vc.ImageAspect.COLOR,
            baseMipLevel=0,
            levelCount=1,
            baseArrayLayer=0,
            layerCount=1
        )

        barrier = vk.VkImageMemoryBarrier(
            sType=vk.VK_STRUCTURE_TYPE_IMAGE_MEMORY_BARRIER,
            srcAccessMask=src_access.value,
            dstAccessMask=dst_access.value,
            oldLayout=old_layout.value,
            newLayout=new_layout.value,
            srcQueueFamilyIndex=vc.QUEUE_FAMILY_IGNORED,
            dstQueueFamilyIndex=vc.QUEUE_FAMILY_IGNORED,
            image=self.image,
            subresourceRange=subresource_range
        )

        cmd.pipeline_barrier(src_stage, dst_stage, vc.Dependency.NONE,
                             [], [], [barrier])

    def generate_mipmap(self, cmd):
        '''
        Generate mipmap of this image based on `self.mip_level`.

        *Parameters:*

        - `cmd`: `CommandBufferRegister` used to register commands

        **Note: TODO about layout**
        '''
        pass

    def copy_to(self, cmd, dst_image):
        '''
        Copy this image to the destination image.
        Commands to copy are registered in the commandbuffer but it's up to
        you to start and submit the command buffer to the execution queue.

        *Parameters:*

        - `cmd`: `CommandBufferRegister` used to register commands
        - `dst_image`: Destination `Image`

        **Note: Layout of source image must be `TRANSFERT_SRC_OPTIMAL` and
                layout of destination image must be `TRANSFERT_DST_OPTIMAL`.
                It's up to you.**

        **Warning: Format of both images must be compatible**
        '''
        # Copy image
        subresource = vk.VkImageSubresourceLayers(
            aspectMask=vc.ImageAspect.COLOR,
            baseArrayLayer=0,
            mipLevel=0,
            layerCount=1
        )
        extent = vk.VkExtent3D(width=self.width, height=self.height,
                               depth=self.depth)
        region = vk.VkImageCopy(
            srcSubresource=subresource,
            dstSubresource=subresource,
            srcOffset=vk.VkOffset3D(x=0, y=0, z=0),
            dstOffset=vk.VkOffset3D(x=0, y=0, z=0),
            extent=extent
        )

        src_layout = vc.ImageLayout.TRANSFER_SRC_OPTIMAL
        dst_layout = vc.ImageLayout.TRANSFER_DST_OPTIMAL

        cmd.copy_image(self, src_layout, dst_image,
                       dst_layout, [region])

    @contextmanager
    def bind(self, context):
        '''
        Map this image to upload data in it.
        This function is a context manager and must be called with `with`.
        It return a python buffer and let you do what you want with it,
        be careful!

        *Parameters:*

        - `context`: The `VulkContext`

        **Warning: Image memory must be host visible**
        '''
        compatible_memories = {vc.MemoryProperty.HOST_VISIBLE,
                               vc.MemoryProperty.HOST_COHERENT,
                               vc.MemoryProperty.HOST_CACHED}
        # TODO: To try, not sure it works
        if not any([self.memory_properties & m for m in compatible_memories]):
            msg = "Can't map this image, memory must be host visible"
            logger.error(msg)
            raise VulkError(msg)

        _, _, format_size = vc.format_info(self.format)
        image_size = (self.width * self.height * self.depth * format_size)

        try:
            data = vk.vkMapMemory(context.device, self.memory, 0,
                                  image_size, 0)
            yield data
        finally:
            vk.vkUnmapMemory(context.device, self.memory)


class ImageView():
    '''
    An image view is quite literally a view into an image.
    It describes how to access the image and which part of the image
    to access, for example if it should be treated as a 2D texture depth
    texture without any mipmapping levels.
    '''

    def __init__(self, context, image, view_type, image_format,
                 subresource_range, swizzle_r=vc.ComponentSwizzle.IDENTITY,
                 swizzle_g=vc.ComponentSwizzle.IDENTITY,
                 swizzle_b=vc.ComponentSwizzle.IDENTITY,
                 swizzle_a=vc.ComponentSwizzle.IDENTITY):
        '''Create ImageView

        *Parameters:*

        - `context`: The `VulkContext`
        - `image`: The `Image` to work on
        - `view_type`: `ImageViewType` vulk constant
        - `image_format`: `Format` vulk constant
        - `subresource_range`: The `ImageSubresourceRange` to use
        - `swizzle_r`: `ComponentSwizzle` of the red color channel
        - `swizzle_g`: `ComponentSwizzle` of the green color channel
        - `swizzle_b`: `ComponentSwizzle` of the blue color channel
        - `swizzle_a`: `ComponentSwizzle` of the alpha color channel
        '''
        components = vk.VkComponentMapping(
            r=swizzle_r.value, g=swizzle_g.value, b=swizzle_b.value,
            a=swizzle_a.value
        )

        vk_subresource_range = vk.VkImageSubresourceRange(
            aspectMask=subresource_range.aspect.value,
            baseMipLevel=subresource_range.base_miplevel,
            levelCount=subresource_range.level_count,
            baseArrayLayer=subresource_range.base_layer,
            layerCount=subresource_range.layer_count
        )

        imageview_create = vk.VkImageViewCreateInfo(
            sType=vk.VK_STRUCTURE_TYPE_IMAGE_VIEW_CREATE_INFO,
            flags=0,
            image=image.image,
            viewType=view_type.value,
            format=image_format.value,
            components=components,
            subresourceRange=vk_subresource_range
        )

        self.image = image
        self.imageview = vk.vkCreateImageView(context.device,
                                              imageview_create, None)


class Pipeline():
    '''Pipeline (graphic) object

    The graphics pipeline is the sequence of operations that take the
    vertices and textures of your meshes all the way to the pixels in
    the render targets. The pipeline combines the following elements:

      - Shader stages: the shader modules that define the functionality of
                       the programmable stages of the graphics pipeline
      - Fixed-function state: all of the structures that define the
                              fixed-function stages of the pipeline, like
                              input assembly, rasterizer, viewport and
                              color blending
      - Pipeline layout: the uniform and push values referenced by the
                         shader that can be updated at draw time
      - Render pass: the attachments referenced by the pipeline stages
                     and their usage
    '''

    def __init__(self, context, stages, vertex_input, input_assembly,
                 viewport_state, rasterization, multisample, depth, blend,
                 dynamic, layout, renderpass):
        '''

        - `context`: The `VulkContext`
        - `stages`: List of `PipelineShaderStage`
        - `vertex_input`: `PipelineVertexInputState`
        - `input_assembly`: `PipelineInputAssemblyState`
        - `viewport_state`: `PipelineViewportState`
        - `rasterization`: `PipelineRasterizationState`
        - `multisample`: `PipelineMultisampleState`
        - `depth`: `PipelineDepthStencilState` (can be `None`)
        - `blend`: `PipelineColorBlendState`
        - `dynamic`: `PipelineDynamicState` (may be `None`)
        - `layout`: `PipelineLayout`
        - `renderpass`: The `Renderpass` of this pipeline
        '''

        vk_stages = []
        for s in stages:
            vk_stages.append(vk.VkPipelineShaderStageCreateInfo(
                sType=vk.VK_STRUCTURE_TYPE_PIPELINE_SHADER_STAGE_CREATE_INFO,
                flags=0,
                stage=s.stage.value,
                module=s.module.module,
                pSpecializationInfo=None,
                pName='main'
            ))

        vk_vertex_bindings = []
        for binding in vertex_input.bindings:
            vk_vertex_bindings.append(vk.VkVertexInputBindingDescription(
                binding=binding.binding,
                stride=binding.stride,
                inputRate=binding.rate.value
            ))

        vk_vertex_attributes = []
        for attribute in vertex_input.attributes:
            vk_vertex_attributes.append(vk.VkVertexInputAttributeDescription(
                location=attribute.location,
                binding=attribute.binding,
                format=attribute.format.value,
                offset=attribute.offset
            ))

        vk_vertex_input = vk.VkPipelineVertexInputStateCreateInfo(
            sType=vk.VK_STRUCTURE_TYPE_PIPELINE_VERTEX_INPUT_STATE_CREATE_INFO,
            flags=0,
            vertexBindingDescriptionCount=len(vk_vertex_bindings),
            pVertexBindingDescriptions=vk_vertex_bindings or None,
            vertexAttributeDescriptionCount=len(vk_vertex_attributes),
            pVertexAttributeDescriptions=vk_vertex_attributes or None
        )

        vk_input_assembly = vk.VkPipelineInputAssemblyStateCreateInfo(
            sType=vk.VK_STRUCTURE_TYPE_PIPELINE_INPUT_ASSEMBLY_STATE_CREATE_INFO, # noqa
            flags=0,
            topology=input_assembly.topology.value,
            primitiveRestartEnable=vk.VK_FALSE
        )

        vk_viewports = []
        for v in viewport_state.viewports:
            vk_viewports.append(vk.VkViewport(
                x=v.x, y=v.y, width=v.width, height=v.height,
                minDepth=v.min_depth, maxDepth=v.max_depth
            ))

        vk_scissors = []
        for s in viewport_state.scissors:
            vk_scissors.append(vk.VkRect2D(
                offset=vk.VkOffset2D(x=s.offset.x, y=s.offset.y),
                extent=vk.VkExtent2D(width=s.extent.width,
                                     height=s.extent.height),
            ))

        vk_viewport_state = vk.VkPipelineViewportStateCreateInfo(
            sType=vk.VK_STRUCTURE_TYPE_PIPELINE_VIEWPORT_STATE_CREATE_INFO,
            flags=0,
            viewportCount=len(vk_viewports),
            pViewports=vk_viewports,
            scissorCount=len(vk_scissors),
            pScissors=vk_scissors
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
            polygonMode=rasterization.polygon_mode.value,
            lineWidth=rasterization.line_width,
            cullMode=rasterization.cull_mode.value,
            frontFace=rasterization.front_face.value,
            depthBiasEnable=dbe,
            depthBiasConstantFactor=rasterization.depth_bias_constant,
            depthBiasClamp=rasterization.depth_bias_clamp,
            depthBiasSlopeFactor=rasterization.depth_bias_slope
        )

        vk_multisample = vk.VkPipelineMultisampleStateCreateInfo(
            sType=vk.VK_STRUCTURE_TYPE_PIPELINE_MULTISAMPLE_STATE_CREATE_INFO,
            flags=0,
            sampleShadingEnable=btov(multisample.shading_enable),
            rasterizationSamples=multisample.samples.value,
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
                depthCompareOp=depth.depth_compare.value,
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
                colorWriteMask=a.color_mask.value,
                blendEnable=btov(a.enable),
                srcColorBlendFactor=a.src_color.value,
                dstColorBlendFactor=a.dst_color.value,
                colorBlendOp=a.color_op.value,
                srcAlphaBlendFactor=a.src_alpha.value,
                dstAlphaBlendFactor=a.dst_alpha.value,
                alphaBlendOp=a.alpha_op.value
            )
            vk_blend_attachments.append(vk_a)

        vk_blend = vk.VkPipelineColorBlendStateCreateInfo(
            sType=vk.VK_STRUCTURE_TYPE_PIPELINE_COLOR_BLEND_STATE_CREATE_INFO,
            flags=0,
            logicOpEnable=btov(blend.op_enable),
            logicOp=blend.op.value,
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

        pipeline_create = vk.VkGraphicsPipelineCreateInfo(
            sType=vk.VK_STRUCTURE_TYPE_GRAPHICS_PIPELINE_CREATE_INFO,
            flags=0,
            stageCount=len(vk_stages),
            pStages=vk_stages,
            pVertexInputState=vk_vertex_input,
            pInputAssemblyState=vk_input_assembly,
            pTessellationState=None,
            pViewportState=vk_viewport_state,
            pRasterizationState=vk_rasterization,
            pMultisampleState=vk_multisample,
            pDepthStencilState=vk_depth,
            pColorBlendState=vk_blend,
            pDynamicState=vk_dynamic,
            layout=layout.layout,
            renderPass=renderpass.renderpass,
            subpass=0,
            basePipelineHandle=None,
            basePipelineIndex=-1
        )

        self.pipeline = vk.vkCreateGraphicsPipelines(
            context.device, None, 1, [pipeline_create], None)


class PipelineLayout():
    '''Pipeline layout object

    Access to descriptor sets from a pipeline is accomplished through a
    pipeline layout. Zero or more descriptor set layouts and zero or more
    push constant ranges are combined to form a pipeline layout object which
    describes the complete set of resources that can be accessed by a
    pipeline. The pipeline layout represents a sequence of descriptor sets
    with each having a specific layout. This sequence of layouts is used to
    determine the interface between shader stages and shader resources.
    Each pipeline is created using a pipeline layout.
    '''

    def __init__(self, context, descriptors):
        '''
        *Parameters:*

        - `context`: `VulkContext`
        - `descriptors`: `list` of `DescriptorSetLayout`

        **Todo: push constants must be implemented**
        '''
        vk_descriptors = []
        for d in descriptors:
            vk_descriptors.append(d.descriptorsetlayout)

        layout_create = vk.VkPipelineLayoutCreateInfo(
            sType=vk.VK_STRUCTURE_TYPE_PIPELINE_LAYOUT_CREATE_INFO,
            flags=0,
            setLayoutCount=len(vk_descriptors),
            pSetLayouts=vk_descriptors if vk_descriptors else None,
            pushConstantRangeCount=0,
            pPushConstantRanges=None
        )
        self.layout = vk.vkCreatePipelineLayout(context.device,
                                                layout_create, None)


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

        *Parameters:*

        - `context`: The `VulkContext`
        - `attachments`: `list` of `AttachmentDescription`
        - `subpasses`: `list` of `SubpassDescription`
        - `dependencies`: `list` of `SubpassDependency`

        **Warning: Arguments ar not checked, you must know
                   what you are doing.**
        '''

        vk_attachments = []
        for a in attachments:
            vk_attachments.append(vk.VkAttachmentDescription(
                flags=0,
                format=a.format.value,
                samples=a.samples.value,
                loadOp=a.load.value,
                storeOp=a.store.value,
                stencilLoadOp=a.stencil_load.value,
                stencilStoreOp=a.stencil_store.value,
                initialLayout=a.initial_layout.value,
                finalLayout=a.final_layout.value
            ))

        # Loop through the list of subpasses to create the reference
        # reference key is index_layout
        vk_references = {}
        for s in subpasses:
            for r in (s.colors + s.inputs + s.resolves +
                      s.preserves + s.depth_stencil):
                key = (r.index, r.layout)
                if key not in vk_references:
                    vk_references[key] = vk.VkAttachmentReference(
                        attachment=r.index,
                        layout=r.layout.value
                    )

        def ref(references):
            '''
            Convert a list of `AttachmentReference` to a list of
            `VkAttachmentReference` by using the cached references in
            `vk_references`
            '''
            if not references:
                return []

            return [vk_references[(r.index, r.layout)] for r in references]

        # Create the subpasses using references
        vk_subpasses = []
        for s in subpasses:
            leninputs = len(s.inputs)
            lenpreserves = len(s.preserves)
            lencolors = len(s.colors)
            lenresolves = len(s.resolves)
            inputs = ref(s.inputs) or None
            preserves = ref(s.preserves) or None
            colors = ref(s.colors) or None
            resolves = ref(s.resolves) or None
            depth_stencil = next(iter(ref(s.depth_stencil)), None)

            if resolves and inputs and lenresolves != lencolors:
                msg = "resolves and inputs list must be of the same size"
                logger.error(msg)
                raise VulkError(msg)

            vk_subpasses.append(vk.VkSubpassDescription(
                flags=0,
                pipelineBindPoint=vc.PipelineBindPoint.GRAPHICS.value,
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
                srcSubpass=d.src_subpass,
                dstSubpass=d.dst_subpass,
                srcStageMask=d.src_stage.value,
                dstStageMask=d.dst_stage.value,
                srcAccessMask=d.src_access.value,
                dstAccessMask=d.dst_access.value
            ))

        # Create the render pass
        renderpass_create = vk.VkRenderPassCreateInfo(
            sType=vk.VK_STRUCTURE_TYPE_RENDER_PASS_CREATE_INFO,
            flags=0,
            attachmentCount=len(vk_attachments),
            pAttachments=vk_attachments,
            subpassCount=len(vk_subpasses),
            pSubpasses=vk_subpasses,
            dependencyCount=len(vk_dependencies),
            pDependencies=vk_dependencies
        )

        self.renderpass = vk.vkCreateRenderPass(
            context.device, renderpass_create, None)


class Sampler():
    '''
    `Sampler` objects represent the state of an image sampler which is used
    by the implementation to read image data and apply filtering and other
    transformations for the shader.
    '''

    def __init__(self, context, mag_filter, min_filter, mipmap_mode,
                 address_mode_u, address_mode_v, address_mode_w, mip_lod_bias,
                 anisotropy_enable, max_anisotropy, compare_enable,
                 compare_op, min_lod, max_lod, border_color,
                 unnormalized_coordinates):
        """Construct a new sampler

        Args:
            context (VulkContext): Context containing device
            mag_filter (Filter): Magnification filter to apply to lookups
            min_filter (Filter): Minification filter to apply to lookups
            mipmap_mode (SamplerMipmapMode): mipmap filter to apply to lookups
            address_mode_u (SamplerAddressMode): Repeat X
            address_mode_v (SamplerAddressMode): Repeat Y
            address_mode_w (SamplerAddressMode): Repeat W
            mip_lod_bias (float): Bias to be added to mipmap LOD calculation
            anisotropy_enable (bool): enable anisotropic filtering
            max_anisotropy (int): Anisotropy value clamp
            compare_enable (bool): enable comparison against a reference value
                                   during lookups
            compare_op (CompareOp): comparison function to apply to fetched
                                    data before filtering
            min_lod (float): clamp the computed level-of-detail value
            max_lod (float): clamp the computed level-of-detail value
            border_color (BorderColor): predefined border color to use
            unnormalized_coordinates (bool): True to use unnormalized texel
                                             coordinates
        """
        sampler_create = vk.VkSamplerCreateInfo(
            sType=vk.VK_STRUCTURE_TYPE_SAMPLER_CREATE_INFO,
            flags=0,
            magFilter=mag_filter.value,
            minFilter=min_filter.value,
            mipmapMode=mipmap_mode.value,
            addressModeU=address_mode_u.value,
            addressModeV=address_mode_v.value,
            addressModeW=address_mode_w.value,
            mipLodBias=mip_lod_bias,
            anisotropyEnable=btov(anisotropy_enable),
            maxAnisotropy=max_anisotropy,
            compareEnable=btov(compare_enable),
            compareOp=compare_op.value,
            minLod=min_lod,
            maxLod=max_lod,
            borderColor=border_color.value,
            unnormalizedCoordinates=btov(unnormalized_coordinates)
        )

        self.sampler = vk.vkCreateSampler(context.device, sampler_create,
                                          None)

    def destroy(self, context):
        """Destroy sampler

        Args:
            context (VulkContext): Context containing device
        """
        vk.vkDestroySampler(context.device, self.sampler, None)


class Semaphore():
    '''
    Semaphores are a synchronization primitive that can be used to insert a
    dependency between batches submitted to queues. Semaphores have two
    states - signaled and unsignaled. The state of a semaphore can be signaled
    after execution of a batch of commands is completed. A batch can wait for
    a semaphore to become signaled before it begins execution, and the
    semaphore is also unsignaled before the batch begins execution.
    '''

    def __init__(self, context):
        '''
        *Parameters:*

        - `context`: `VulkContext`
        '''
        semaphore_create = vk.VkSemaphoreCreateInfo(
            sType=vk.VK_STRUCTURE_TYPE_SEMAPHORE_CREATE_INFO,
            flags=0
        )

        self.semaphore = vk.vkCreateSemaphore(context.device,
                                              semaphore_create, None)


class ShaderModule():
    '''ShaderModule Vulkan object

    A shader module is a Spir-V shader loaded into Vulkan.
    After being created, it must be inserted in a pipeline stage.
    The real Vulkan module can be accessed by the 'module' property.
    '''

    def __init__(self, context, code):
        '''
        Initialize the module

        *Parameters:*

        - `context`: The `VulkContext` object
        - `code`: Binary Spir-V loaded file (bytes)

        *Returns:*

        The created `ShaderModule`
        '''
        if not isinstance(code, bytes):
            logger.info("Type of code is not 'bytes', it may be an error")

        self.code = code

        # Create the shader module
        shader_create = vk.VkShaderModuleCreateInfo(
            sType=vk.VK_STRUCTURE_TYPE_SHADER_MODULE_CREATE_INFO,
            flags=0, codeSize=len(code), pCode=code)
        self.module = vk.vkCreateShaderModule(context.device, shader_create,
                                              None)


class ShaderProgram():
    '''ShaderProgram

    A `ShaderProgram` embed all `ShaderModule` of a `Pipeline`.
    '''

    def __init__(self, context, modules):
        '''
        *Parameters:*

        - `context`: `VulkContext`
        - `modules`: `dict` containing a mapping between `ShaderStage` and the
                     actual shader. The shader must be a `bytes` object like
                     obtained by open(path, 'rb').read()
        '''
        self.stages = []
        for stage, spirv in modules.items():
            if not isinstance(spirv, bytes):
                raise TypeError("shader must be a bytes object")

            module = ShaderModule(context, spirv)
            self.stages.append(PipelineShaderStage(module, stage))


class ShaderProgramGlsl(ShaderProgram):
    '''ShaderProgramGlsl

    A `ShaderProgramGlsl` is a `ShaderProgram` which compiles glsl to spirv.
    '''
    shaderc_mapping = {
        vc.ShaderStage.VERTEX: 'vert',
        vc.ShaderStage.TESSELLATION_CONTROL: 'tesc',
        vc.ShaderStage.TESSELLATION_EVALUATION: 'tese',
        vc.ShaderStage.GEOMETRY: 'geom',
        vc.ShaderStage.FRAGMENT: 'frag',
        vc.ShaderStage.COMPUTE: 'comp',
    }

    def __init__(self, context, modules):
        '''
        *Parameters:*

        - `context`: `VulkContext`
        - `modules`: `dict` containing a mapping between `ShaderStage` and
                     shader information.
                     modules = {
                         'stage': {
                             'glsl': glsl shader, `bytes` object,
                             'path': path to file, needed if #include "file"
                         }
                     }
        '''
        spirv_modules = {}
        for stage, data in modules.items():
            glsl = data['glsl']
            path = data.get('path', 'nofile')

            if not isinstance(glsl, bytes):
                raise TypeError("shader must be a bytes object")

            stage_shaderc = ShaderProgramGlsl.shaderc_mapping[stage]
            spirv = pyshaderc.compile_into_spirv(glsl, stage_shaderc, path)
            spirv_modules[stage] = spirv

        super().__init__(context, spirv_modules)


class ShaderProgramGlslFile(ShaderProgramGlsl):
    '''ShaderProgramGlslFile

    It's a `ShaderProgramGlsl` which needs only file paths.
    '''

    def __init__(self, context, modules):
        '''
        *Parameters:*

        - `context`: `VulkContext`
        - `modules`: `dict` containing a mapping between `ShaderStage` and
                     shader path (glsl format).
        '''
        glsl_modules = {}
        for stage, path in modules.items():
            with open(path, 'rb') as f:
                glsl_modules[stage] = {'glsl': f.read(), 'path': path}

        super().__init__(context, glsl_modules)
