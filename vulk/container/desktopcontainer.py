import sdl2
import sdl2.ext

from vulk.container.basecontainer import BaseContainer
from vulk.container.util import sdl2 as vulk_sdl2


class DesktopContainer(BaseContainer):
    """Launch app on desktop
    """

    def __init__(self, app, user_config=None,
                 driver_names=("opengl", "vulkan")):
        config = {
            'title': 'Vulk',
            'size': (400, 400),
            'position': (sdl2.video.SDL_WINDOWPOS_UNDEFINED,
                         sdl2.video.SDL_WINDOWPOS_UNDEFINED)
        }
        config.update(user_config if user_config else {})
        super().__init__(app, config, driver_names)

    def run(self):
        win = vulk_sdl2.OpenGLWindow(
            self.config['title'], self.config['size'],
            self.config['position'], (1, 3))

        with win as window:
            with self.app(self.driver) as app:
                while True:
                    events = sdl2.ext.get_events()
                    if sdl2.SDL_QUIT in [e.type for e in events]:
                        break
                    app.render()
                    window.refresh()
