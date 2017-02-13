from abc import ABC, abstractmethod

from vulk.math.vector import Vector3
from vulk.math.matrix import Matrix4, ProjectionMatrix, ViewMatrix


class Camera(ABC):
    def __init__(self):
        self.position = Vector3()
        self.direction = Vector3()
        self.up = Vector3()
        self.projection = ProjectionMatrix()
        self.view = ViewMatrix()
        self.combined = Matrix4()
        self.inv_projection_view = Matrix4()
        self.near = 1.0
        self.far = 100.0
        self.viewport_width = 0.0
        self.viewport_height = 0.0

    def unproject(self, position, viewport_x, viewport_y,
                  viewport_width, viewport_height):
        '''
        Unproject `position` to view matrix.
        Allow to get world coordinate from screen coordinate.

        *Parameters:*

        - `position`: `Vector3` screen position right-handed.
                      z(0) = near plane, z(1) = far plane
        '''
        x = position.x - viewport_x
        y = position.y - viewport_y
        position.x = (2 * x) / viewport_width - 1
        position.y = (2 * y) / viewport_height - 1
        return position.prj(self.inv_projection_view)

    @abstractmethod
    def update(self, update_frustum=True):
        pass


class OrthographicCamera(Camera):
    def __init__(self, viewport_width, viewport_height):
        super().__init__()

        self.zoom = 1.0
        self.near = 0.0

        self.to_orthographic(viewport_width, viewport_height)

    def to_orthographic(self, viewport_width, viewport_height):
        self.viewport_width = viewport_width
        self.viewport_height = viewport_height

        self.up.set(0, -1, 0)
        self.direction.set(0, 0, 1)
        self.position.set(self.zoom * self.viewport_width / 2.0,
                          self.zoom * self.viewport_height / 2.0, 0)

        self.update()

    def update(self, update_frustum=True):
        self.projection.to_orthographic(
            self.zoom * -self.viewport_width / 2,
            self.zoom * self.viewport_width / 2,
            self.zoom * -self.viewport_height / 2,
            self.zoom * self.viewport_height / 2,
            self.near, self.far
        )

        target = Vector3(self.position).add(self.direction)
        self.view.to_look_at(self.position, target, self.up)
        self.combined.set(self.projection).mul(self.view)
        self.inv_projection_view.set(self.combined).inv()


class PerspectiveCamera(Camera):
    def __init__(self, fov, viewport_width, viewport_height):
        super().__init__()
        self.fov = fov
        self.viewport_width = viewport_width
        self.viewport_height = viewport_height
        self.tmp = Vector3()

    def update(self, update_frustum=True):
        pass
