import ctypes
import sdl2


class OpenGLWindow(sdl2.ext.Window):
    def __init__(self, title, size, position, required_version):
        self.required_version = required_version
        self.flags = sdl2.SDL_WINDOW_SHOWN | sdl2.SDL_WINDOW_OPENGL
        self._title = title
        self._size = size
        self.position = position

    def __enter__(self):
        sdl2.ext.init()

        self._init_window_attributes()

        window = sdl2.video.SDL_CreateWindow(
            bytes(self._title, "utf-8"), self.position[0], self.position[1],
            self._size[0], self._size[1], self.flags)

        if not window:
            raise sdl2.ext.SDLError()

        self.window = window.contents

        self._init_opengl_context()

        return self

    def __exit__(self, *args):
        sdl2.video.SDL_GL_DeleteContext(self.glcontext)
        self.glcontext = None
        sdl2.video.SDL_DestroyWindow(self.window)
        self.window = None
        sdl2.ext.quit()

    def _init_opengl_context(self):
        self.glcontext = sdl2.video.SDL_GL_CreateContext(self.window)
        if self.glcontext == 0:
            sdl2.video.SDL_DestroyWindow(self.window)
            self.window = None
            sdl2.ext.quit()
            raise sdl2.ext.SDLError()

    def _init_window_attributes(self):
        attributes = {
            sdl2.SDL_GL_CONTEXT_MINOR_VERSION: 3,
            sdl2.SDL_GL_CONTEXT_MAJOR_VERSION: 3,
            sdl2.SDL_GL_DOUBLEBUFFER: 1,
            sdl2.SDL_GL_DEPTH_SIZE: 16,
            sdl2.SDL_GL_CONTEXT_PROFILE_MASK: sdl2.SDL_GL_CONTEXT_PROFILE_CORE
        }

        for key, value in attributes.items():
            sdl2.video.SDL_GL_SetAttribute(key, value)

    def refresh(self):
        sdl2.video.SDL_GL_SwapWindow(self.window)

    @property
    def title(self):
        return self.title

    @title.setter
    def title(self, value):
        """The title of the window."""
        self._title = value
        sdl2.video.SDL_SetWindowTitle(self.window, value)

    @property
    def size(self):
        """The size of the window."""
        w, h = ctypes.c_int(), ctypes.c_int()
        sdl2.video.SDL_GetWindowSize(self.window, ctypes.byref(w),
                                     ctypes.byref(h))
        return w.value, h.value

    def show(self):
        """Show the window on the display."""
        sdl2.video.SDL_ShowWindow(self.window)

    def hide(self):
        """Hides the window."""
        sdl2.video.SDL_HideWindow(self.window)

    def maximize(self):
        """Maximizes the window to the display's dimensions."""
        sdl2.video.SDL_MaximizeWindow(self.window)

    def minimize(self):
        """Minimizes the window to an iconified state in the system tray."""
        sdl2.video.SDL_MinimizeWindow(self.window)
