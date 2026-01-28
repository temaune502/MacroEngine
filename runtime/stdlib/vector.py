import math

class Vector:
    def __init__(self, x=0, y=0, z=0):
        self.x = float(x)
        self.y = float(y)
        self.z = float(z)
    
    def add(self, other):
        return Vector(self.x + other.x, self.y + other.y, self.z + getattr(other, 'z', 0))
    
    def sub(self, other):
        return Vector(self.x - other.x, self.y - other.y, self.z - getattr(other, 'z', 0))
    
    def mul(self, scalar):
        return Vector(self.x * scalar, self.y * scalar, self.z * scalar)
    
    def length(self):
        return math.sqrt(self.x**2 + self.y**2 + self.z**2)
    
    def normalize(self):
        l = self.length()
        if l == 0: return Vector(0, 0, 0)
        return Vector(self.x / l, self.y / l, self.z / l)
    
    def lerp(self, other, t):
        return Vector(
            self.x + (other.x - self.x) * t,
            self.y + (other.y - self.y) * t,
            self.z + (getattr(other, 'z', 0) - self.z) * t
        )

    def __repr__(self):
        return f"Vector({self.x}, {self.y}, {self.z})"
