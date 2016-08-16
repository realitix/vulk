from vulk.math import vector


class Plane():
    OnPlane = 1
    Back = 2
    Front = 3

    def __init__(self, normal=None, distance=0):
        if not normal:
            normal = vector.Vector3(0, 0, 0)

        self.normal = normal
        self.distance = distance

    def setFromVector3(self, v0, v1, v2):
        tmp = [v1.x - v2.x, v1.y - v2.y, v1.z - v2.z]
        self.normal.set(v0).sub(v1).crs(tmp).nor()
        self.distance = -v0.dot(self.normal)
