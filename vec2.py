from math import sqrt


class vec2:
    def __init__(self, x: float, y: float):
        self.x: float = x
        self.y: float = y

    def __add__(self, other: vec2) -> vec2:
        return vec2(self.x + other.x, self.y + other.y)

    def __sub__(self, other: vec2) -> vec2:
        return vec2(self.x - other.x, self.y - other.y)

    def __mul__(self, scalar: float) -> vec2:
        return vec2(self.x * scalar, self.y * scalar)

    def __rmul__(self, scalar: float) -> vec2:
        return vec2(self.x * scalar, self.y * scalar)

    def length(self) -> float:
        return sqrt(self.x * self.x + self.y * self.y)


def dot(a: vec2, b: vec2) -> float:
    return a.x * b.x + a.y * b.y
