import importlib
import sdl2
import sdl2.ext

from vulk import exception


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
        if self.driver.technology == "opengl":
            sdl2.video.SDL_GL_DeleteContext(self.glcontext)
            self.glcontext = None

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

    def init_opengl_window_attributes(self):
        sdl2.video.SDL_GL_SetAttribute(sdl2.SDL_GL_CONTEXT_MINOR_VERSION, 3)
        sdl2.video.SDL_GL_SetAttribute(sdl2.SDL_GL_CONTEXT_MAJOR_VERSION, 4)
        sdl2.video.SDL_GL_SetAttribute(sdl2.SDL_GL_DOUBLEBUFFER, 1)
        sdl2.video.SDL_GL_SetAttribute(sdl2.SDL_GL_DEPTH_SIZE, 24)

    def init_opengl_context(self):
        self.glcontext = sdl2.video.SDL_GL_CreateContext(self.window.window)
        if self.glcontext == 0:
            self.window = None
            sdl2.ext.quit()
            raise sdl2.ext.SDLError()

    def init_window(self):
        sdl2.ext.init()
        flags = sdl2.SDL_WINDOW_SHOWN

        if self.driver.technology == "opengl":
            self.glcontext = sdl2.video.SDL_GLContext(0)
            self.init_opengl_window_attributes()
            flags |= sdl2.SDL_WINDOW_OPENGL

        self.window = sdl2.ext.Window("Test", size=(800, 600), flags=flags)

        if self.driver.technology == "opengl":
            self.init_opengl_context()

    def refresh_window(self):
        if self.driver.technology == "opengl":
            sdl2.video.SDL_GL_SwapWindow(self.window.window)

    def run(self):
        with self.app() as app:
            running = True
            while running:
                events = sdl2.ext.get_events()
                if sdl2.SDL_QUIT in events:
                    running = False
                    break
                app.render()
                self.refresh_window()
