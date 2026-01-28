import platform
import ctypes
from ctypes import wintypes
from pynput import mouse, keyboard

# Constants for Windows API
GWL_STYLE = -16
WS_VISIBLE = 0x10000000
SW_MINIMIZE = 6
SW_MAXIMIZE = 3
SW_RESTORE = 9

# Hotkey Modifiers
MOD_ALT = 0x0001
MOD_CONTROL = 0x0002
MOD_SHIFT = 0x0004
MOD_WIN = 0x0008
WM_HOTKEY = 0x0312

# Window Message Constants
WM_CLOSE = 0x0010
WM_SYSCOMMAND = 0x0112
SC_MONITORPOWER = 0xF170
HWND_BROADCAST = 0xFFFF
WM_INPUTLANGCHANGEREQUEST = 0x0050

user32 = None
kernel32 = None
gdi32 = None
dxva2 = None

if platform.system() == "Windows":
    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32
    gdi32 = ctypes.windll.gdi32
    try:
        dxva2 = ctypes.windll.dxva2
    except Exception:
        dxva2 = None

class PHYSICAL_MONITOR(ctypes.Structure):
    _fields_ = [("hPhysicalMonitor", wintypes.HANDLE),
                ("szPhysicalMonitorDescription", wintypes.WCHAR * 128)]

# Layout-independent Virtual Keys (Windows VK codes)
def vk(code):
    return keyboard.KeyCode.from_vk(code)

# Alphabet (Layout-independent via VK)
K_A = vk(0x41); K_B = vk(0x42); K_C = vk(0x43); K_D = vk(0x44); K_E = vk(0x45)
K_F = vk(0x46); K_G = vk(0x47); K_H = vk(0x48); K_I = vk(0x49); K_J = vk(0x4A)
K_K = vk(0x4B); K_L = vk(0x4C); K_M = vk(0x4D); K_N = vk(0x4E); K_O = vk(0x4F)
K_P = vk(0x50); K_Q = vk(0x51); K_R = vk(0x52); K_S = vk(0x53); K_T = vk(0x54)
K_U = vk(0x55); K_V = vk(0x56); K_W = vk(0x57); K_X = vk(0x58); K_Y = vk(0x59)
K_Z = vk(0x5A)

# Numbers
K_0 = vk(0x30); K_1 = vk(0x31); K_2 = vk(0x32); K_3 = vk(0x33); K_4 = vk(0x34)
K_5 = vk(0x35); K_6 = vk(0x36); K_7 = vk(0x37); K_8 = vk(0x38); K_9 = vk(0x39)

# F-Keys
K_F1 = keyboard.Key.f1; K_F2 = keyboard.Key.f2; K_F3 = keyboard.Key.f3
K_F4 = keyboard.Key.f4; K_F5 = keyboard.Key.f5; K_F6 = keyboard.Key.f6
K_F7 = keyboard.Key.f7; K_F8 = keyboard.Key.f8; K_F9 = keyboard.Key.f9
K_F10 = keyboard.Key.f10; K_F11 = keyboard.Key.f11; K_F12 = keyboard.Key.f12

# Special Keys
K_ENTER = keyboard.Key.enter; K_ESC = keyboard.Key.esc; K_SPACE = keyboard.Key.space
K_TAB = keyboard.Key.tab; K_BACKSPACE = keyboard.Key.backspace
K_DELETE = keyboard.Key.delete; K_INSERT = keyboard.Key.insert
K_HOME = keyboard.Key.home; K_END = keyboard.Key.end
K_PAGE_UP = keyboard.Key.page_up; K_PAGE_DOWN = keyboard.Key.page_down
K_UP = keyboard.Key.up; K_DOWN = keyboard.Key.down
K_LEFT = keyboard.Key.left; K_RIGHT = keyboard.Key.right
K_SHIFT = keyboard.Key.shift; K_CTRL = keyboard.Key.ctrl
K_ALT = keyboard.Key.alt; K_CAPS_LOCK = keyboard.Key.caps_lock

# Mouse Buttons
LEFT = mouse.Button.left
RIGHT = mouse.Button.right
MIDDLE = mouse.Button.middle
