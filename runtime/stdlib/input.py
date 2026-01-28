import time
from .vector import Vector
from .constants import user32, LEFT, RIGHT, MIDDLE

class MouseWrapper:
    def __init__(self, controller):
        self.controller = controller
    
    @property
    def x(self): return self.controller.position[0]
    @property
    def y(self): return self.controller.position[1]
    @property
    def pos(self): return Vector(self.controller.position[0], self.controller.position[1])
    
    def move(self, x, y=None):
        if y is None and hasattr(x, 'x'):
            self.controller.position = (int(x.x), int(x.y))
        else:
            self.controller.position = (int(x), int(y))
        
    def move_rel(self, dx, dy=None):
        curr_x, curr_y = self.controller.position
        if dy is None and hasattr(dx, 'x'):
            self.controller.position = (int(curr_x + dx.x), int(curr_y + dx.y))
        else:
            self.controller.position = (int(curr_x + dx), int(curr_y + dy))

    def click(self, button=LEFT): self.controller.click(button)

    def is_pressed(self, button=LEFT):
        if not user32: return False
        vk_map = {LEFT: 0x01, RIGHT: 0x02, MIDDLE: 0x04}
        vk = vk_map.get(button, 0x01)
        return bool(user32.GetAsyncKeyState(vk) & 0x8000)
        
    def double_click(self, button): self.controller.click(button, 2)
    def press(self, button): self.controller.press(button)
    def release(self, button): self.controller.release(button)
    def scroll(self, dx, dy): self.controller.scroll(int(dx), int(dy))

    def smooth_move(self, target_x, target_y=None, duration=0.2):
        if target_y is None and hasattr(target_x, 'x'):
            tx, ty = target_x.x, target_x.y
        else:
            tx, ty = target_x, target_y
        start_pos = self.controller.position
        start_time = time.time()
        while True:
            elapsed = time.time() - start_time
            t = min(1.0, elapsed / duration)
            smooth_t = t * t * (3 - 2 * t)
            curr_x = start_pos[0] + (tx - start_pos[0]) * smooth_t
            curr_y = start_pos[1] + (ty - start_pos[1]) * smooth_t
            self.controller.position = (int(curr_x), int(curr_y))
            if t >= 1.0: break
            time.sleep(0.01)

    def smooth_move_rel(self, dx, dy=None, duration=0.2):
        curr_pos = self.controller.position
        if dy is None and hasattr(dx, 'x'):
            self.smooth_move(curr_pos[0] + dx.x, curr_pos[1] + dx.y, duration)
        else:
            self.smooth_move(curr_pos[0] + dx, curr_pos[1] + dy, duration)

    def move_bezier(self, p1, p2, p3, duration=0.5):
        p0 = Vector(self.controller.position[0], self.controller.position[1])
        start_time = time.time()
        while True:
            elapsed = time.time() - start_time
            t = min(1.0, elapsed / duration)
            inv_t = 1.0 - t
            res = p0.mul(inv_t**3).add(p1.mul(3 * inv_t**2 * t)).add(p2.mul(3 * inv_t * t**2)).add(p3.mul(t**3))
            self.controller.position = (int(res.x), int(res.y))
            if t >= 1.0: break
            time.sleep(0.01)

class KeyWrapper:
    def __init__(self, controller):
        self.controller = controller
    def type(self, text): self.controller.type(str(text))
    def press(self, key): self.controller.press(key)
    def release(self, key): self.controller.release(key)
    def tap(self, key): self.controller.tap(key)
    def is_pressed(self, key):
        if not user32: return False
        if hasattr(key, 'value') and hasattr(key.value, 'vk'): vk = key.value.vk
        elif hasattr(key, 'vk'): vk = key.vk
        elif isinstance(key, int): vk = key
        else: return False
        return bool(user32.GetAsyncKeyState(vk) & 0x8000)
