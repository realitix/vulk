from vulk.graphic import exception
from vulk.graphic.renderer import baserenderer
from vulk.graphic.renderer.vulkan import base


class VulkanRenderer(baserenderer.BaseRenderer):

    def __init__(self, height=None, width=None):
        super(height=height, width=width)

    def init_renderer(self):
        super.initRenderer()
        window = base.Window(width=width, height=height)
        instance = base.VulkanInstance(window)
        self.swapchain = base.VulkanSwapChain(instance)

    def render(self):
        super.render()
