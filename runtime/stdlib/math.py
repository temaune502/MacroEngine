import math
import random
from .vector import Vector

class MathWrapper:
    def __init__(self):
        self.pi = math.pi
        self.e = math.e
        
    def sin(self, x): return math.sin(x)
    def cos(self, x): return math.cos(x)
    def tan(self, x): return math.tan(x)
    def sqrt(self, x): return math.sqrt(x)
    def abs(self, x): return abs(x)
    def floor(self, x): return math.floor(x)
    def ceil(self, x): return math.ceil(x)
    def round(self, x, n=0): return round(x, n)
    def pow(self, x, y): return math.pow(x, y)
    def log(self, x, base=math.e): return math.log(x, base)
    
    def vector(self, x, y): return Vector(x, y)

    def lerp(self, a, b, t):
        if hasattr(a, 'lerp'): return a.lerp(b, t)
        return a + (b - a) * t

    def bezier(self, p0, p1, p2, t):
        inv_t = 1.0 - t
        return p0.mul(inv_t * inv_t).add(p1.mul(2 * inv_t * t)).add(p2.mul(t * t))

    def bezier3(self, p0, p1, p2, p3, t):
        inv_t = 1.0 - t
        return p0.mul(inv_t**3).add(p1.mul(3 * inv_t**2 * t)).add(p2.mul(3 * inv_t * t**2)).add(p3.mul(t**3))

    def jitter(self, v, amount):
        return Vector(
            v.x + random.uniform(-amount, amount),
            v.y + random.uniform(-amount, amount)
        )
