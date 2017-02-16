class Rectangle():
    def __init__(self, x=0, y=0, width=0, height=0):
        self.x = x
        self.y = y
        self.width = width
        self.height = height

    def set(self, rectangle):
        self.x = rectangle.x
        self.y = rectangle.y
        self.width = rectangle.width
        self.height = rectangle.height

    def __repr__(self):
        return 'Rectangle[x={}, y={}, width={}, height={}]'.format(
            self.x, self.y, self.width, self.height)

    def contains(self, x, y):
        return (self.x <= x and self.x + self.width >= x and
                self.y <= y and self.y + self.height >= y)

    def overlaps(self, r):
        return self.x < r.x + r.width and self.x + self.width > r.x and \
               self.y < r.y + r.height and self.y + self.height > r.y
