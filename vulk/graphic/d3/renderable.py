from vulk.math.matrix import Matrix4
from vulk.graphic.model import MeshPart


class Renderable():
    def __init__(self):
        self.world_transform = Matrix4()
        self.mesh_part = MeshPart()
        self.material = None
        self.environment = None
        self.shader = None
