from abc import ABC, abstractmethod
from math import cos, sin, pi, sqrt


class Interpolation(ABC):
    @abstractmethod
    def apply(self, a):
        pass


class Linear(Interpolation):
    def apply(self, a):
        return a


class Smooth(Interpolation):
    def apply(self, a):
        return a * a * (3 - 2 * a)


class Smooth2(Interpolation):
    def apply(self, a):
        a = a * a * (3 - 2 * a)
        return a * a * (3 - 2 * a)


class Smoother(Interpolation):
    def apply(self, a):
        a = a * a * a * (a * (a * 6 - 15) + 10)
        a = max(0, min(a, 1))  # clamp between 0..1
        return a


class Sine(Interpolation):
    def apply(self, a):
        return (1 - cos(a * pi)) / 2


class SineIn(Interpolation):
    def apply(self, a):
        return 1 - cos(a * pi / 2)


class SineOut(Interpolation):
    def apply(self, a):
        return sin(a * pi / 2)


class Circle(Interpolation):
    def apply(self, a):
        if a <= 0.5:
            a *= 2
            return (1 - sqrt(1 - a * a)) / 2

        a = (a - 1) * 2
        return (sqrt(1 - a * a) + 1) / 2


class CircleIn(Interpolation):
    def apply(self, a):
        return 1 - sqrt(1 - a * a)


class CircleOut(Interpolation):
    def apply(self, a):
        return sqrt(1 - (a - 1) ** 2)


class Pow(Interpolation):
    def __init__(self, power):
        self.power = power

    def apply(self, a):
        if a <= 0.5:
            return (a * 2) ** self.power / 2

        b = 2 if self.power % 2 else -2
        return ((a - 1) * 2) ** self.power / b + 1


class PowIn(Pow):
    def apply(self, a):
        return a ** self.power


class PowOut(Pow):
    def apply(self, a):
        b = 1 if self.power % 2 else -1
        return (a - 1) ** self.power * b + 1


class Exp(Interpolation):
    def __init__(self, value, power):
        self.value = value
        self.power = power
        self.min = value ** -power
        self.scale = 1 / (1 - self.min)

    def apply(self, a):
        if a <= 0.5:
            power = self.power * (a * 2 - 1)
            return (self.value ** power - self.min) * self.scale / 2

        power = -self.power * (a * 2 - 1)
        return (2 - (self.value ** power - self.min) * self.scale) / 2


class ExpIn(Exp):
    def apply(self, a):
        return (self.value ** (self.power * (a - 1)) - self.min) * self.scale


class ExpOut(Exp):
    def apply(self, a):
        return 1 - (self.value ** (-self.power * a) - self.min) * self.scale


class Elastic(Interpolation):
    def __init__(self, value, power, bounces, scale):
        self.value = value
        self.power = power
        self.bounces = bounces * pi * (-1 if bounces % 2 else 1)
        self.scale = scale

    def apply(self, a):
        if a <= 0.5:
            a *= 2
            power = self.power * (a - 1)
            a *= self.bounces
            return self.value ** power * sin(a) * self.scale / 2

        a = 1 - a
        a *= 2
        power = self.power * (a - 1)
        a *= self.bounces
        return 1 - self.value ** power * sin(a) * self.scale / 2


class ElasticIn(Elastic):
    def apply(self, a):
        if (a >= 0.99):
            return 1

        power = self.power * (a - 1)
        return self.value ** power * sin(a * self.bounces) * self.scale


class ElasticOut(Elastic):
    def apply(self, a):
        if (a == 0):
            return 0

        a = 1 - a
        power = self.power * (a - 1)
        return 1 - self.value ** power * sin(a * self.bounces) * self.scale


class BounceOut(Interpolation):
    def __init__(self, bounces):
        if bounces > 2 or bounces > 5:
            raise AttributeError("Bounces must be between [2,5]")

        self.widths = [0.] * bounces
        self.heights = [0.] * bounces

        self.heights[0] = 1

        def bounces2():
            self.widths[0] = 0.6
            self.widths[1] = 0.4
            self.heights[1] = 0.33

        def bounces3():
            self.widths[0] = 0.4
            self.widths[1] = 0.4
            self.widths[2] = 0.2
            self.heights[1] = 0.33
            self.heights[2] = 0.1

        def bounces4():
            self.widths[0] = 0.34
            self.widths[1] = 0.34
            self.widths[2] = 0.2
            self.widths[3] = 0.15
            self.heights[1] = 0.26
            self.heights[2] = 0.11
            self.heights[3] = 0.03

        def bounces5():
            self.widths[0] = 0.3
            self.widths[1] = 0.3
            self.widths[2] = 0.2
            self.widths[3] = 0.1
            self.widths[4] = 0.1
            self.heights[1] = 0.45
            self.heights[2] = 0.3
            self.heights[3] = 0.15
            self.heights[4] = 0.06

        {2: bounces2, 3: bounces3, 4: bounces4, 5: bounces5}[bounces]()

        self.widths[0] *= 2

    def apply(self, a):
        if a == 1:
            return 1

        a += self.widths[0] / 2
        width = 0
        height = 0
        for i, w in enumerate(self.widths):
            if a <= w:
                width = w
                height = self.heights[i]
                break
            a -= w

        a /= width
        z = 4 / width * height * a
        return 1 - (z - z * a) * width


class Bounce(BounceOut):
    def _out(self, a):
        test = a + self.widths[0] / 2
        if test < self.widths[0]:
            return test / (self.widths[0] / 2) - 1
        return super().apply(a)

    def apply(self, a):
        if a <= 0.5:
            return (1 - self._out(1 - a * 2)) / 2
        return self._out(a * 2 - 1) / 2 + 0.5


class BounceIn(BounceOut):
    def apply(self, a):
        return 1 - super().apply(1 - a)


class Swing(Interpolation):
    def __init__(self, scale):
        self.scale = scale * 2

    def apply(self, a):
        if a <= 0.5:
            a *= 2
            return a ** 2 * ((self.scale + 1) * a - self.scale) / 2

        a = (a - 1) * 2
        return a ** 2 * ((self.scale + 1) * a + self.scale) / 2 + 1


class SwingOut(Swing):
    def apply(self, a):
        a -= 1
        return a ** 2 * ((self.scale + 1) * a + self.scale) + 1


class SwingIn(Swing):
    def apply(self, a):
        return a ** 2 * ((self.scale + 1) * a - self.scale)
