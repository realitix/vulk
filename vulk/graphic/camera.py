from abc import ABCMeta, abstractmethod

from vulk.math.vector import Vector3
from vulk.math.matrix import Matrix4


class Camera(metaclass=ABCMeta):
    def __init__(self):
        self.position = Vector3()
        self.direction = Vector3()
        self.up = Vector3()
        self.projection = Matrix4()
        self.view = Matrix4()
        self.combined = Matrix4()
        self.inv_projection_view = Matrix4()
        self.near = 1
        self.far = 100
        self.viewport_width = 0
        self.viewport_height = 0

    @abstractmethod
    def update(self):
        pass


class PerspectiveCamera(Camera):
    def __init__(self, fov, viewport_width, viewport_height):
        super().__init__()
        self.fov = fov
        self.viewport_width = viewport_width
        self.viewport_height = viewport_height
        self.tmp = Vector3()

    def update(self):
        aspect = self.viewport_width / self.viewport_height
        self.projection.to_projection(abs(self.near), abs(self.far),
                                      self.fov, aspect)
        self.view.to_look_at(Vector3().set(self.position).add(self.direction),
                             self.up)
        self.combined.set(self.projection).mul(self.view)
