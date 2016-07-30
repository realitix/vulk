import abc

from vulk.graphic import exception


class BaseRenderer(abc.ABC):
    def __init__(self, width=None, height=None):
        if not width or not height:
            raise exception.VulkError("Renderer size unspecicified")

        self.initialized = False
        self.width = width
        self.height = height

    @abc.abstractmethod
    def init_renderer(self):
        if self.initialized:
            raise exception.VulkError("Renderer already initialized")

    @abc.abstractmethod
    def render(self):
        if not self.initialized:
            self.initRenderer()
