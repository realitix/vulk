import importlib
import sdl2
import sdl2.ext

from vulk import exception
from vulk.app.util import sdl2 as vulk_sdl2


class DesktopApp():
    """Launch app on desktop

    TODO: All opengl specific tonfiguration should be in Window"""

    def __init__(self, app, config, drivers_names=["opengl", "vulkan"]):
        self.app = app
        self.driver_names = drivers_names
        self.config = config

    def __enter__(self):
        self.init_driver()
        self.init_window()

    def __exit__(self, *args):
        self.window = None
        sdl2.ext.quit()

    def init_driver(self):
        for driver_name in self.driver_names:
            try:
                driver_module = importlib.import_module(
                    driver_name,
                    "vulk.graphic.driver")
                self.driver = driver_module.driver()
            except exception.VulkException:
                self.driver = None
            else:
                break
        else:
            raise exception.VulkException(
                "Can't load driver in %s" % str(self.driver_names))

    def init_window(self):
        sdl2.ext.init()
        flags = sdl2.SDL_WINDOW_SHOWN

        self.window = sdl2.ext.Window("Test", size=(800, 600), flags=flags)

    def run(self):
        with self.app() as app:
            running = True
            while running:
                events = sdl2.ext.get_events()
                if sdl2.SDL_QUIT in events:
                    running = False
                    break
                app.render()
                self.window.refresh()
