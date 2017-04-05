class Color():
    def __init__(self, r=1, g=1, b=1, a=1):
        self.values = [r, g, b, a]

    @property
    def r(self):
        return self.values[0]

    @r.setter
    def r(self, value):
        self.values[0] = value

    @property
    def g(self):
        return self.values[1]

    @g.setter
    def g(self, value):
        self.values[1] = value

    @property
    def b(self):
        return self.values[2]

    @b.setter
    def b(self, value):
        self.values[2] = value

    @property
    def a(self):
        return self.values[3]

    @a.setter
    def a(self, value):
        self.values[3] = value
