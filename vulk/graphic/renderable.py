class Renderable():
    def __init__(self, world_transform, mesh_part, material, bones=None,
                 shader=None):
        self.world_transform = world_transform
        self.mesh_part = mesh_part
        self.material = material
        self.bones = bones
        self.shader = shader
