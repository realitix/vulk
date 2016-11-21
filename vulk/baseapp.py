from abc import ABC, abstractmethod

from vulk.utils import millis, time_since_millis
from vulk.context import VulkWindow, VulkContext


class BaseApp(ABC):
    """App must inherit this class

    The App is responsible of creating the window and manage the life
    cycle of the program.
    """

    def __init__(self, name='Vulk', x=-1, y=-1, width=640, height=480,
                 fullscreen=False, resizable=True, decorated=True,
                 highdpi=False, debug=False):
        '''Set initial configuration

        :param name: Name of the application
        :param x: X position of the window
        :param y: Y position of the window
        :param width: Width of the window
        :param height: Height of the window
        :param fullscreen: Should the window be in fullscreen mode
        :param resizable: Should the window be resizable
        :param decorated: Should the window be decorated (button close)
        :param highdpi: Enable highdpi mode if supported
        :param debug: Enable debug mode (for development only)
        :type name: string
        :type x: int
        :type y: int
        :type width: int
        :type height: int
        :type fullscreen: boolean
        :type resizable: boolean
        :type decorated: boolean
        :type highdpi: boolean
        :type debug: boolean

        .. note:: When full screen mode is enabled, you can set width and
                  height to 0 to use the native resolution, otherwise the
                  fullscreen resolution will be set to width/height.
        '''
        self.configuration = {k: v for k, v in locals().items() if k != 'self'}
        self.last_time = millis()

    def __enter__(self):
        '''Create window and Vulkan context'''
        self.window = VulkWindow()
        self.window.open(self.configuration)
        self.context = VulkContext()
        self.context.create(self.window, self.configuration)
        return self

    def __exit__(self, *args):
        '''Clean Vulkan resource'''
        self.window.close()
        pass

    def run(self):
        '''Start the game loop'''
        while(True):
            self.render(time_since_millis(self.last_time))
            self.last_time = millis()

    @abstractmethod
    def render(self, delta):
        return
