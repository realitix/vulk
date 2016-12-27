"""Module to create Window and Vulkan context

This module contains class to create the SDL2 window and the Vulkan
logical device and queues.
The context will be then passed to the Application to use it.

Vulk uses a specific way to interact with Vulkan that allow a good
abstraction. Instead of performing the final drawing operation
directly on the swapchain's images, Vulk performs all operations on
custom images and framebuffer and finally just copy the result in the
swapchain's image.
"""
import ctypes
import logging
import sdl2
import sdl2.ext
import vulkan as vk  # pylint: disable=import-error

from vulk.exception import VulkError
from vulk.vulkanobject import CommandPool, Image, ImageView, \
        ImageSubresourceRange, Semaphore, immediate_buffer

logger = logging.getLogger()
ENGINE_NAME = "Vulk 3D Engine"


class SDL2Error(VulkError):
    pass


class VulkWindow():
    def __init__(self):
        self.window = None
        self.info = None

    def open(self, configuration):
        '''Open the SDL2 Window

        *Parameters:*

        - `configuration`: Configurations parameters from Application
        '''
        if sdl2.SDL_Init(sdl2.SDL_INIT_VIDEO) != 0:
            msg = "Can't open window: %s" % sdl2.SDL_GetError()
            logger.critical(msg)
            raise SDL2Error(msg)

        flags = 0
        if configuration.fullscreen and \
           configuration.width and configuration.height:
            flags |= sdl2.SDL_WINDOW_FULLSCREEN
        elif configuration.fullscreen:
            flags |= sdl2.SDL_WINDOW_FULLSCREEN_DESKTOP
        if not configuration.decorated:
            flags |= sdl2.SDL_WINDOW_BORDERLESS
        if configuration.resizable:
            flags |= sdl2.SDL_WINDOW_RESIZABLE
        if configuration.highdpi:
            flags |= sdl2.SDL_WINDOW_ALLOW_HIGHDPI

        self.window = sdl2.SDL_CreateWindow(
            configuration.name.encode('ascii'), configuration.x,
            configuration.y, configuration.width, configuration.height, 0)

        if not self.window:
            msg = "Can't open window: %s" % sdl2.SDL_GetError()
            logger.critical(msg)
            raise SDL2Error(msg)

        logger.debug("SDL2 window opened with configuration: %s",
                     (configuration,))

        self.info = sdl2.SDL_SysWMinfo()
        sdl2.SDL_VERSION(self.info.version)
        sdl2.SDL_GetWindowWMInfo(self.window, ctypes.byref(self.info))

    def close(self):
        logger.debug("SDL2 window closed")
        sdl2.SDL_DestroyWindow(self.window)
        sdl2.SDL_Quit()


class VulkContext():
    def __init__(self):
        # Vulkan instance
        self.instance = None
        # Extension functions in a dict
        self.pfn = {}
        # Instance to the debug callback
        self.debug_callback = None
        # Surface to the window
        self.surface = None
        # Physical device
        self.physical_device = None
        # Properties of physical device
        self.physical_device_properties = None
        # Features of physical device
        self.physical_device_features = None
        # Logical device
        self.device = None
        # Graphic queue
        self.graphic_queue = None
        # Presentation queue
        self.present_queue = None
        # Indices of queue families
        self.queue_family_indices = None
        # Swapchain
        self.swapchain = None
        # Swapchain images (vulkanobject.Image type)
        self.swapchain_images = None
        # Swapchain format
        self.swapchain_format = None
        # Width of the window
        self.width = 0
        # Height of the window
        self.height = 0
        # Final image which is copied into swapchain image
        self.final_image = None
        # Image view of the final image
        self.final_image_view = None
        # Internal semaphores
        self._semaphore_available = None
        self._semaphore_copied = None
        # Command buffers
        self.commandbuffers = None

    @staticmethod
    def _get_instance_extensions(window, configuration):
        '''Get extensions which depend on the window and configuration

        *Parameters:*

        - `window`: The `VulkWindow`
        - `configuration`: Configuration from App

        *Returns:*

        Extension list
        '''

        # Get available extensions
        available_extensions = [
            e.extensionName
            for e in vk.vkEnumerateInstanceExtensionProperties(None)]
        logger.debug("Available instance extensions: %s",
                     available_extensions)

        # Compute needed extensions
        extension_mapping = {
            sdl2.SDL_SYSWM_X11: vk.VK_KHR_XLIB_SURFACE_EXTENSION_NAME,
            sdl2.SDL_SYSWM_WINDOWS: vk.VK_KHR_WIN32_SURFACE_EXTENSION_NAME,
            sdl2.SDL_SYSWM_WAYLAND: vk.VK_KHR_WAYLAND_SURFACE_EXTENSION_NAME,
            sdl2.SDL_SYSWM_MIR: vk.VK_KHR_MIR_SURFACE_EXTENSION_NAME
        }
        sdl_subsystem = window.info.subsystem

        if sdl_subsystem not in extension_mapping:
            msg = "Vulkan not supported on this plateform: %s" % sdl_subsystem
            logger.critical(msg)
            raise VulkError(msg)

        # Select extension
        enabled_extensions = []
        enabled_extensions.append(vk.VK_KHR_SURFACE_EXTENSION_NAME)
        enabled_extensions.append(extension_mapping[sdl_subsystem])

        if configuration.debug:
            if vk.VK_EXT_DEBUG_REPORT_EXTENSION_NAME in available_extensions:
                enabled_extensions.append(
                    vk.VK_EXT_DEBUG_REPORT_EXTENSION_NAME)
            else:
                configuration.debug = False
                logger.warning("Vulkan debug extension not present and debug"
                               "mode asked, disabling debug mode")

        # Check extensions availability
        if not all(e in available_extensions for e in enabled_extensions):
            msg = "Vulkan extensions are not all available"
            logger.critical(msg)
            raise VulkError(msg)

        return enabled_extensions

    @staticmethod
    def _get_device_extensions(physical_device):
        '''Get device extensions

        *Parameters:*

        - `physical_device`: The VkPhysicalDevice to check

        *Returns:*

        Extension list
        '''

        # Get available extensions
        available_extensions = [
            e.extensionName for e in vk.vkEnumerateDeviceExtensionProperties(
                physical_device, None)]
        logger.debug("Available device extensions: %s", available_extensions)

        # Select extensions
        enabled_extensions = []
        enabled_extensions.append(vk.VK_KHR_SWAPCHAIN_EXTENSION_NAME)

        # Check extensions availability
        if not all(e in available_extensions for e in enabled_extensions):
            msg = "Vulkan extensions are not all available"
            logger.critical(msg)
            raise VulkError(msg)

        return enabled_extensions

    @staticmethod
    def _get_layers(configuration):
        '''Get all enabled layers

        Simple algorythm: return everything in debug mode else nothing

        *Parameters:*

        - configuration: configuration from App

        *Returns:*

        List of all enabled layers
        '''

        if not configuration.debug:
            return []

        layers = [l.layerName for l in
                  vk.vkEnumerateInstanceLayerProperties(None)]
        logger.debug("Available layers: %s", layers)

        # Standard validation is a meta layer containing the others
        standard = 'VK_LAYER_LUNARG_standard_validation'
        if standard in layers:
            logger.debug("Selecting only %s", standard)
            layers = [standard]

        return layers

    @staticmethod
    def _get_queue_families(physical_device, surface, pfn):
        '''Get graphic and present queue families

        Check for graphic and presentation queue families.

        *Parameters:*

        - `physical_device`: The `VkPhysicalDevice` to check for
        - `surface`: The `VkSurfaceKHR` to present
        - `pfn`: Function `vkGetPhysicalDeviceSurfaceSupportKHR` callable

        *Returns:*

        A tuple with graphic index and present index or None
        '''
        queue_families = vk.vkGetPhysicalDeviceQueueFamilyProperties(physical_device) # noqa

        graphic_index = -1
        present_index = -1

        for i, queue_family in enumerate(queue_families):
            # Queue family needs queues
            if queue_family.queueCount <= 0:
                continue

            # Check that queue family support present queue
            present_available = pfn(physical_device, i, surface)

            if queue_family.queueFlags & vk.VK_QUEUE_GRAPHICS_BIT:
                graphic_index = i
            if present_available:
                present_index = i

        if graphic_index == -1 or present_index == -1:
            return None

        return graphic_index, present_index

    def _get_pfn(self, configuration):
        '''Get extension function pointers

        Get only functions used in `VulkContext`, vulkan instance must exist

        *Parameters:*

        - `configuration`: Configuration from Application
        '''

        if not self.instance:
            msg = "_create_instance must be called before _get_pfn"
            logger.critical(msg)
            raise VulkError(msg)

        def add_pfn(name):
            try:
                self.pfn[name] = vk.vkGetInstanceProcAddr(self.instance, name)
            except ImportError:
                msg = "Can't get address of %s extension function" % name
                logger.critical(msg)
                raise VulkError(msg)

        extension_functions = {
            'vkDestroySurfaceKHR',
            'vkGetPhysicalDeviceSurfaceSupportKHR',
            'vkGetPhysicalDeviceSurfaceCapabilitiesKHR',
            'vkGetPhysicalDeviceSurfaceFormatsKHR',
            'vkGetPhysicalDeviceSurfacePresentModesKHR',
            'vkCreateSwapchainKHR',
            'vkGetSwapchainImagesKHR',
            'vkAcquireNextImageKHR',
            'vkQueuePresentKHR'
        }

        debug_extension_functions = {
            'vkCreateDebugReportCallbackEXT',
            'vkDestroyDebugReportCallbackEXT',
        }

        if configuration.debug:
            extension_functions.update(debug_extension_functions)

        for name in extension_functions:
            add_pfn(name)

    def _create_instance(self, window, configuration):
        '''Create Vulkan instance

        *Parameters:*

        - `window`: The window for Vulkan
        - `configuration`: Configuration from Application
        '''

        extensions = VulkContext._get_instance_extensions(window,
                                                          configuration)
        layers = VulkContext._get_layers(configuration)

        app_info = vk.VkApplicationInfo(
            sType=vk.VK_STRUCTURE_TYPE_APPLICATION_INFO,
            pApplicationName=configuration.name,
            applicationVersion=vk.VK_MAKE_VERSION(1, 0, 0),
            pEngineName=ENGINE_NAME,
            engineVersion=vk.VK_MAKE_VERSION(1, 0, 0),
            apiVersion=vk.VK_API_VERSION_1_0)

        instance_create_info = vk.VkInstanceCreateInfo(
            sType=vk.VK_STRUCTURE_TYPE_INSTANCE_CREATE_INFO,
            flags=0,
            pApplicationInfo=app_info,
            enabledExtensionCount=len(extensions),
            ppEnabledExtensionNames=extensions,
            enabledLayerCount=len(layers),
            ppEnabledLayerNames=layers)

        self.instance = vk.vkCreateInstance(pCreateInfo=instance_create_info)

    def _create_debug_callback(self, configuration):
        '''Create debug callback

        It works only on debug mode

        *Parameters:*

        - `configuration`: Configuration from Application
        '''
        if not configuration.debug:
            return

        vulkan_debug_mapping = {
            vk.VK_DEBUG_REPORT_DEBUG_BIT_EXT: logging.DEBUG,
            vk.VK_DEBUG_REPORT_WARNING_BIT_EXT: logging.WARNING,
            vk.VK_DEBUG_REPORT_ERROR_BIT_EXT: logging.ERROR,
            vk.VK_DEBUG_REPORT_INFORMATION_BIT_EXT: logging.INFO,
            vk.VK_DEBUG_REPORT_PERFORMANCE_WARNING_BIT_EXT: logging.WARNING
        }

        def debug_function(*args):
            logger.log(vulkan_debug_mapping[args[0]], "VULKAN: %s", args[6])

        flags = (vk.VK_DEBUG_REPORT_ERROR_BIT_EXT |
                 vk.VK_DEBUG_REPORT_WARNING_BIT_EXT |
                 # vk.VK_DEBUG_REPORT_INFORMATION_BIT_EXT |
                 # vk.VK_DEBUG_REPORT_DEBUG_BIT_EXT |
                 vk.VK_DEBUG_REPORT_PERFORMANCE_WARNING_BIT_EXT)

        debug_create_info = vk.VkDebugReportCallbackCreateInfoEXT(
            sType=vk.VK_STRUCTURE_TYPE_DEBUG_REPORT_CALLBACK_CREATE_INFO_EXT,
            flags=flags,
            pfnCallback=debug_function)

        self.debug_callback = self.pfn['vkCreateDebugReportCallbackEXT'](
            instance=self.instance,
            pCreateInfo=debug_create_info)

    def _create_surface(self, info):
        '''Create Vulkan surface

        *Parameters:*

        - `info`: The window information for Vulkan
        '''
        def call_platform(name, surface_create):
            f = vk.vkGetInstanceProcAddr(self.instance, name)
            return f(instance=self.instance, pCreateInfo=surface_create)

        def xlib():
            logger.info("Create XLIB surface")
            # pylint: disable=no-member
            surface_create = vk.VkXlibSurfaceCreateInfoKHR(
                sType=vk.VK_STRUCTURE_TYPE_XLIB_SURFACE_CREATE_INFO_KHR,
                dpy=info.info.x11.display,
                window=info.info.x11.window,
                flags=0)
            return call_platform('vkCreateXlibSurfaceKHR', surface_create)

        def mir():
            logger.info("Create MIR surface")
            # pylint: disable=no-member
            surface_create = vk.VkMirSurfaceCreateInfoKHR(
                sType=vk.VK_STRUCTURE_TYPE_MIR_SURFACE_CREATE_INFO_KHR,
                connection=info.info.mir.connection,
                mirSurface=info.info.mir.surface,
                flags=0)
            return call_platform('vkCreateMirSurfaceKHR', surface_create)

        def wayland():
            logger.info("Create WAYLAND surface")
            # pylint: disable=no-member
            surface_create = vk.VkWaylandSurfaceCreateInfoKHR(
                sType=vk.VK_STRUCTURE_TYPE_WAYLAND_SURFACE_CREATE_INFO_KHR,
                display=info.info.wl.display,
                surface=info.info.surface,
                flags=0)
            return call_platform('vkCreateWaylandSurfaceKHR', surface_create)

        def windows():
            logger.info("Create WINDOWS surface")
            # pylint: disable=no-member
            surface_create = vk.VkWin32SurfaceCreateInfoKHR(
                sType=vk.VK_STRUCTURE_TYPE_WAYLAND_SURFACE_CREATE_INFO_KHR,
                hinstance=info.info.win.hinstance,
                hwdn=info.info.win.window,
                flags=0)
            return call_platform('vkCreateWin32SurfaceKHR', surface_create)

        def android():
            # TODO
            raise VulkError("Android not supported for now")

        surface_mapping = {
            sdl2.SDL_SYSWM_X11: xlib,
            sdl2.SDL_SYSWM_MIR: mir,
            sdl2.SDL_SYSWM_WAYLAND: wayland,
            sdl2.SDL_SYSWM_WINDOWS: windows,
            sdl2.SDL_SYSWM_ANDROID: android
        }

        self.surface = surface_mapping[info.subsystem]()

    def _create_physical_device(self):
        '''Create Vulkan physical device

        The best physical device is selected through criteria.
        '''

        physical_devices = vk.vkEnumeratePhysicalDevices(self.instance)

        if not physical_devices:
            msg = "No physical device found"
            logger.critical(msg)
            raise VulkError(msg)

        features = [vk.vkGetPhysicalDeviceFeatures(p)
                    for p in physical_devices]
        properties = [vk.vkGetPhysicalDeviceProperties(p)
                      for p in physical_devices]

        logger.debug("Available physical devices: %s",
                     [p.deviceName for p in properties])

        # Select best physical device based on properties ans features
        selected_index = 0
        best_score = 0
        for i, d in enumerate(physical_devices):
            score = 0

            # Discrete GPU is better
            if properties[i].deviceType == \
               vk.VK_PHYSICAL_DEVICE_TYPE_DISCRETE_GPU:
                score += 1000

            score += properties[i].limits.maxImageDimension2D

            # Device must contain graphic and present queue family
            if not VulkContext._get_queue_families(
                d, self.surface,
                self.pfn['vkGetPhysicalDeviceSurfaceSupportKHR']
            ):
                score = 0

            if score > best_score:
                best_score = score
                selected_index = i

        # No available physical device
        if best_score == 0:
            msg = "No available physical device"
            logger.critical(msg)
            raise VulkError(msg)

        # The best device is now selected_index
        self.physical_device = physical_devices[selected_index]
        self.physical_device_properties = properties[selected_index]
        self.physical_device_features = features[selected_index]

        logger.debug("%s device selected",
                     self.physical_device_properties.deviceName)

    def _create_device(self, configuration):
        '''Create Vulkan logical device

        *Parameters:*

        - `configuration`: Configuration from Application
        '''
        extensions = VulkContext._get_device_extensions(self.physical_device)
        layers = VulkContext._get_layers(configuration)

        graphic_index, present_index = VulkContext._get_queue_families(
            self.physical_device, self.surface,
            self.pfn['vkGetPhysicalDeviceSurfaceSupportKHR'])

        queues_create = [
            vk.VkDeviceQueueCreateInfo(
                vk.VK_STRUCTURE_TYPE_DEVICE_QUEUE_CREATE_INFO, 0, i, 1, [1]
            )
            for i in {graphic_index, present_index}]

        device_create = vk.VkDeviceCreateInfo(
            vk.VK_STRUCTURE_TYPE_DEVICE_CREATE_INFO, 0, len(queues_create),
            queues_create, len(layers), layers, len(extensions), extensions,
            self.physical_device_features)

        self.device = vk.vkCreateDevice(self.physical_device, device_create)
        self.graphic_queue = vk.vkGetDeviceQueue(self.device, graphic_index, 0)
        self.present_queue = vk.vkGetDeviceQueue(self.device, present_index, 0)
        self.queue_family_indices = {'graphic': graphic_index,
                                     'present': present_index}

    def _create_swapchain(self, configuration):
        '''Create Vulkan swapchain

        *Parameters:*

        - `configuration`: Configuration from Application
        '''
        surface_capabilities = self.pfn['vkGetPhysicalDeviceSurfaceCapabilitiesKHR'](self.physical_device, self.surface) # noqa
        surface_formats = self.pfn['vkGetPhysicalDeviceSurfaceFormatsKHR'](self.physical_device, self.surface) # noqa
        surface_present_modes = self.pfn['vkGetPhysicalDeviceSurfacePresentModesKHR'](self.physical_device, self.surface) # noqa

        if not surface_formats or not surface_present_modes:
            msg = "No available swapchain"
            logger.critical(msg)
            raise VulkError(msg)

        def get_format(formats):
            for f in formats:
                if f.format == vk.VK_FORMAT_UNDEFINED:
                    return f
                if f.format == vk.VK_FORMAT_B8G8R8A8_UNORM and \
                   f.colorSpace == vk.VK_COLOR_SPACE_SRGB_NONLINEAR_KHR:
                    return f
            return formats[0]

        def get_present_mode(present_modes):
            for p in present_modes:
                if p == vk.VK_PRESENT_MODE_MAILBOX_KHR:
                    return p
            return vk.VK_PRESENT_MODE_FIFO_KHR

        def get_swap_extent(capabilities):
            uint32_max = 4294967295

            if capabilities.currentExtent.width != uint32_max:
                return capabilities.currentExtent

            width = max(
                capabilities.minImageExtent.width,
                min(capabilities.maxImageExtent.width, configuration.width))

            height = max(
                capabilities.minImageExtent.height,
                min(capabilities.maxImageExtent.height, configuration.height))

            return vk.VkExtent2D(width=width, height=height)

        surface_format = get_format(surface_formats)
        present_mode = get_present_mode(surface_present_modes)
        extent = get_swap_extent(surface_capabilities)

        # Try to create triple buffering
        image_count = surface_capabilities.minImageCount + 1
        if surface_capabilities.maxImageCount > 0 and \
           image_count > surface_capabilities.maxImageCount:
            image_count = surface_capabilities.maxImageCount

        sharing_mode = vk.VK_SHARING_MODE_EXCLUSIVE
        queue_family_indices = []
        if self.queue_family_indices['graphic'] != \
           self.queue_family_indices['present']:
            sharing_mode = vk.VK_SHARING_MODE_CONCURRENT
            queue_family_indices = [v for v in
                                    self.queue_family_indices.values()]

        # Finally create swapchain
        swapchain_create = vk.VkSwapchainCreateInfoKHR(
            sType=vk.VK_STRUCTURE_TYPE_SWAPCHAIN_CREATE_INFO_KHR,
            flags=0,
            surface=self.surface,
            minImageCount=image_count,
            imageFormat=surface_format.format,
            imageColorSpace=surface_format.colorSpace,
            imageExtent=extent,
            imageArrayLayers=1,
            imageUsage=vk.VK_IMAGE_USAGE_TRANSFER_DST_BIT,
            imageSharingMode=sharing_mode,
            queueFamilyIndexCount=len(queue_family_indices),
            pQueueFamilyIndices=queue_family_indices,
            compositeAlpha=vk.VK_COMPOSITE_ALPHA_OPAQUE_BIT_KHR,
            presentMode=present_mode,
            clipped=vk.VK_TRUE,
            oldSwapchain=None,
            preTransform=surface_capabilities.currentTransform)

        self.swapchain = self.pfn['vkCreateSwapchainKHR'](
            self.device, swapchain_create)
        self.width = extent.width
        self.height = extent.height
        self.swapchain_format = surface_format.format

        swapchain_raw_images = self.pfn['vkGetSwapchainImagesKHR'](
            self.device, self.swapchain)

        self.swapchain_images = []
        for raw_image in swapchain_raw_images:
            # Put swapchain image in Image
            # It's a bad practice but for this specific use case, it's good
            img = Image.__new__(Image)
            img.image = raw_image
            img.format = surface_format.format
            img.width = self.width
            img.height = self.height
            img.depth = 1
            self.swapchain_images.append(img)

        # Update layout of all swapchain images to present khr
        for image in self.swapchain_images:
            with immediate_buffer(self) as cmd:
                image.update_layout(
                    cmd, 'VK_IMAGE_LAYOUT_UNDEFINED',
                    'VK_IMAGE_LAYOUT_PRESENT_SRC_KHR',
                    'VK_PIPELINE_STAGE_TOP_OF_PIPE_BIT',
                    'VK_PIPELINE_STAGE_TOP_OF_PIPE_BIT',
                    0, 'VK_ACCESS_MEMORY_READ_BIT'
                )

        logger.debug("Swapchain created with %s images",
                     len(self.swapchain_images))

    def _create_final_image(self):
        usage = 'VK_IMAGE_USAGE_TRANSFER_SRC_BIT | VK_IMAGE_USAGE_COLOR_ATTACHMENT_BIT' # noqa
        self.final_image = Image(
            self, 'VK_IMAGE_TYPE_2D', self.swapchain_format,
            self.width, self.height, 1, 1,
            1, 'VK_SAMPLE_COUNT_1_BIT', 'VK_SHARING_MODE_EXCLUSIVE', [],
            'VK_IMAGE_LAYOUT_UNDEFINED', 'VK_IMAGE_TILING_OPTIMAL', usage,
            'VK_MEMORY_PROPERTY_DEVICE_LOCAL_BIT'
        )

        subresource_range = ImageSubresourceRange(
            aspect='VK_IMAGE_ASPECT_COLOR_BIT',
            base_miplevel=0,
            level_count=1,
            base_layer=0,
            layer_count=1
        )

        self.final_image_view = ImageView(
            self, self.final_image, 'VK_IMAGE_VIEW_TYPE_2D',
            self.swapchain_format, subresource_range)

    def _create_commandbuffers(self):
        '''Create the command buffers used to copy image'''
        commandpool = CommandPool(self, self.queue_family_indices['graphic'])
        self.commandbuffers = commandpool.allocate_buffers(
            self, 'VK_COMMAND_BUFFER_LEVEL_PRIMARY',
            len(self.swapchain_images))

        for i, commandbuffer in enumerate(self.commandbuffers):
            with commandbuffer.bind() as cmd:
                self.swapchain_images[i].update_layout(
                    cmd, 'VK_IMAGE_LAYOUT_PRESENT_SRC_KHR',
                    'VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL',
                    'VK_PIPELINE_STAGE_TOP_OF_PIPE_BIT',
                    'VK_PIPELINE_STAGE_TOP_OF_PIPE_BIT',
                    'VK_ACCESS_MEMORY_READ_BIT',
                    'VK_ACCESS_TRANSFER_WRITE_BIT'
                )
                self.final_image.copy_to(cmd, self.swapchain_images[i])
                self.swapchain_images[i].update_layout(
                    cmd, 'VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL',
                    'VK_IMAGE_LAYOUT_PRESENT_SRC_KHR',
                    'VK_PIPELINE_STAGE_BOTTOM_OF_PIPE_BIT',
                    'VK_PIPELINE_STAGE_BOTTOM_OF_PIPE_BIT',
                    'VK_ACCESS_TRANSFER_WRITE_BIT',
                    'VK_ACCESS_MEMORY_READ_BIT'
                )

    def _create_semaphores(self):
        '''Create semaphores used during image swaping'''
        self._semaphore_available = Semaphore(self)
        self._semaphore_copied = Semaphore(self)

    def create(self, window, configuration):
        '''Create Vulkan context

        *Parameters:*

        - `window`: The `VulkWindow`
        - `configuration`: Configuration from Application
        '''
        self._create_instance(window, configuration)

        # Next functions need extension pointers
        self._get_pfn(configuration)
        self._create_debug_callback(configuration)
        self._create_surface(window.info)
        self._create_physical_device()
        self._create_device(configuration)
        self._create_swapchain(configuration)
        self._create_final_image()
        self._create_commandbuffers()
        self._create_semaphores()

    def swap(self, semaphores=None):
        '''Display final image on screen.

        This function makes all the rendering work. To proceed, it copies the
        `final_image` into the current swapchain image previously acquired.
        You can pass custom semaphores (and you should) to synchronize the
        command.

        *Parameters:*

        - `semaphore`: A `list` of `Semaphore` to wait on

        **Note: The `final_image` layout must be set to
                VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL before calling `swap`.
                `VulkContext` never update the `final_image` layout**
        '''
        # Acquire image
        index = self.pfn['vkAcquireNextImageKHR'](
            self.device, self.swapchain, vk.UINT64_MAX,
            self._semaphore_available.semaphore, None)

        wait_semaphores = [self._semaphore_available]
        if semaphores:
            wait_semaphores.extend(semaphores)

        wait_masks = [vk.VK_PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT]
        wait_masks *= len(wait_semaphores)

        copied_semaphores = [self._semaphore_copied.semaphore]

        # Transfer final image to swapchain image
        submit = vk.VkSubmitInfo(
            sType=vk.VK_STRUCTURE_TYPE_SUBMIT_INFO,
            waitSemaphoreCount=len(wait_semaphores),
            pWaitSemaphores=[s.semaphore for s in wait_semaphores],
            pWaitDstStageMask=wait_masks,
            commandBufferCount=1,
            pCommandBuffers=[self.commandbuffers[index].commandbuffer],
            signalSemaphoreCount=len(copied_semaphores),
            pSignalSemaphores=copied_semaphores
        )
        vk.vkQueueSubmit(self.graphic_queue, 1, [submit], None)

        # Present swapchain image on screen
        present = vk.VkPresentInfoKHR(
            sType=vk.VK_STRUCTURE_TYPE_PRESENT_INFO_KHR,
            waitSemaphoreCount=len(copied_semaphores),
            pWaitSemaphores=copied_semaphores,
            swapchainCount=1,
            pSwapchains=[self.swapchain],
            pImageIndices=[index],
            pResults=None
        )
        self.pfn['vkQueuePresentKHR'](self.present_queue, present)

        vk.vkDeviceWaitIdle(self.device)
