import OpenGL.GLU as glu
import OpenGL.GL as gl


class TODO():
    def __init__(self):
        ext = gl.glGetString(gl.GL_EXTENSIONS)
        print(glu.gluCheckExtension("GL_ARB_conservative_depth",ext))

driver = TODO
