class Rectangle():
    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height

    def contains(self, x, y):
        return (self.x <= x and self.x + self.width >= x and
                self.y <= y and self.y + self.height >= y)

    def overlaps(self, r):
        return self.x < r.x + r.width and self.x + self.width > r.x and \
               self.y < r.y + r.height and self.y + self.height > r.y
