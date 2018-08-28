from vulk.math.vector import Vector3


class MeshPart():
    def __init__(self):
        self.primitive = 0
        self.offset = 0
        self.size = 0
        self.mesh = None
        self.center = Vector3()
        self.half_extents = Vector3()
        self.radius = 0

    def render(self, cmd):
        self.mesh.render(cmd, self.offset, self.size)
