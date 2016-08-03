import importlib
import sdl2
import sdl2.ext

from vulk import exception
from vulk.app.util import sdl2 as vulk_sdl2


class DesktopContainer():
    """Launch app on desktop

    """

    def __init__(self, app, config=None, driver_names=["opengl", "vulkan"]):
        self.app = app
        self.driver_names = driver_names

        self.config = {
            'title': 'Vulk',
            'size': (400, 400),
            'position': (sdl2.video.SDL_WINDOWPOS_UNDEFINED,
                         sdl2.video.SDL_WINDOWPOS_UNDEFINED)
        }
        self.config.update(config if config else {})

        self.init_driver()

    def init_driver(self):
        for driver_name in self.driver_names:
            try:
                driver_module = importlib.import_module(
                    "vulk.graphic.driver.%s" % driver_name)
                self.driver = driver_module.driver()
            except exception.VulkError:
                self.driver = None
            else:
                break
        else:
            raise exception.VulkError(
                "Can't load driver in %s" % str(self.driver_names))

    def run(self):
        win = vulk_sdl2.OpenGLWindow(
            self.config['title'], self.config['size'],
            self.config['position'], (1, 3))

        with win as window:
            with self.app() as app:
                while True:
                    events = sdl2.ext.get_events()
                    if sdl2.SDL_QUIT in [e.type for e in events]:
                        break
                    app.render()
                    window.refresh()
