import pygetwindow as gw

class WindowObject:
    def __init__(self, gw_window):
        self._win = gw_window
        
    @property
    def title(self): return self._win.title
    @property
    def x(self): return self._win.left
    @property
    def y(self): return self._win.top
    @property
    def width(self): return self._win.width
    @property
    def height(self): return self._win.height
    @property
    def is_active(self): return self._win.isActive
    
    def activate(self): 
        try:
            self._win.activate()
        except:
            pass
            
    def minimize(self): self._win.minimize()
    def maximize(self): self._win.maximize()
    def restore(self): self._win.restore()
    def close(self): self._win.close()
    def move(self, x, y): self._win.moveTo(int(x), int(y))
    def resize(self, w, h): self._win.resizeTo(int(w), int(h))
    def __repr__(self): return f"Window('{self.title}')"

class WindowWrapper:
    def get_active(self):
        win = gw.getActiveWindow()
        return WindowObject(win) if win else None
    def get_all(self):
        return [WindowObject(w) for w in gw.getAllWindows() if w.title]
    def find(self, title):
        wins = gw.getWindowsWithTitle(title)
        return [WindowObject(w) for w in wins]
    def get_by_title(self, title):
        wins = gw.getWindowsWithTitle(title)
        return WindowObject(wins[0]) if wins else None
