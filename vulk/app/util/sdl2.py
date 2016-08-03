import sdl2
import sdl2.ext


class OpenGLWindow(sdl2.ext.Window):
    def __init__(self, title, size, versions=(3, 4), depth_size=24,
                 position=None, flags=sdl2.SDL_WINDOW_SHOWN):
        self.versions = versions
        self.depth_size = depth_size

        self.init_attributes()

        flags |= sdl2.SDL_WINDOW_OPENGL
        super().__init__(title, size, position=position, flags=flags)

        self.init_opengl_context()

    def __del__(self):
        if getattr(self, "glcontext", None):
            sdl2.video.SDL_GL_DeleteContext(self.glcontext)
            self.glcontext = None

        super().__del__()

    def init_opengl_context(self):
        self.glcontext = sdl2.video.SDL_GL_CreateContext(self.window)
        if self.glcontext == 0:
            sdl2.video.SDL_DestroyWindow(self.window)
            self.window = None
            sdl2.ext.quit()
            raise sdl2.ext.SDLError()

    def init_attributes(self):
        attributes = {
            sdl2.SDL_GL_CONTEXT_MINOR_VERSION: self.versions[0],
            sdl2.SDL_GL_CONTEXT_MAJOR_VERSION: self.versions[1],
            sdl2.SDL_GL_DOUBLEBUFFER: 1,
            sdl2.SDL_GL_DEPTH_SIZE: self.depth_size,
            sdl2.SDL_GL_ACCELERATED_VISUAL: 0}

        for key, value in attributes.items():
            sdl2.video.SDL_GL_SetAttribute(key, value)

    def refresh(self):
        sdl2.video.SDL_GL_SwapWindow(self.window)
