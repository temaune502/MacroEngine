from pynput import mouse, keyboard
from .constants import (
    LEFT, RIGHT, MIDDLE,
    K_A, K_B, K_C, K_D, K_E, K_F, K_G, K_H, K_I, K_J, K_K, K_L, K_M,
    K_N, K_O, K_P, K_Q, K_R, K_S, K_T, K_U, K_V, K_W, K_X, K_Y, K_Z,
    K_0, K_1, K_2, K_3, K_4, K_5, K_6, K_7, K_8, K_9,
    K_F1, K_F2, K_F3, K_F4, K_F5, K_F6, K_F7, K_F8, K_F9, K_F10, K_F11, K_F12,
    K_ENTER, K_ESC, K_SPACE, K_TAB, K_BACKSPACE, K_DELETE, K_INSERT,
    K_HOME, K_END, K_PAGE_UP, K_PAGE_DOWN, K_UP, K_DOWN, K_LEFT, K_RIGHT,
    K_SHIFT, K_CTRL, K_ALT, K_CAPS_LOCK
)
from .math import MathWrapper
from .random_mod import RandomWrapper
from .screen import ScreenWrapper
from .system import SystemWrapper, SoundWrapper
from .time_mod import TimeWrapper, sleep
from .storage import StorageWrapper
from .network import NetWrapper
from .window import WindowWrapper
from .input import MouseWrapper, KeyWrapper
from .ui import UIWrapper
from .macro import MacroWrapper, TickWrapper

def get_builtins(runtime_instance):
    """Returns a dictionary of builtin objects and functions for the VM."""
    mouse_controller = mouse.Controller()
    keyboard_controller = keyboard.Controller()
    
    mouse_obj = MouseWrapper(mouse_controller)
    key_obj = KeyWrapper(keyboard_controller)
    math_obj = MathWrapper()
    time_obj = TimeWrapper(runtime_instance)
    random_obj = RandomWrapper()
    window_obj = WindowWrapper()
    screen_obj = ScreenWrapper()
    system_obj = SystemWrapper()
    net_obj = NetWrapper()
    sound_obj = SoundWrapper()
    storage_obj = StorageWrapper(runtime_instance.name)
    tick_obj = TickWrapper()
    macro_obj = MacroWrapper(runtime_instance)
    
    # Store objects in runtime for updates and internal use
    runtime_instance.tick_obj = tick_obj
    runtime_instance.macro_obj = macro_obj
    runtime_instance.sound_obj = sound_obj
    runtime_instance.storage_obj = storage_obj

    return {
        "mouse": mouse_obj,
        "key": key_obj,
        "keyboard": key_obj,
        "time": time_obj,
        "math": math_obj,
        "random": random_obj,
        "window": window_obj,
        "win": window_obj,
        "screen": screen_obj,
        "system": system_obj,
        "net": net_obj,
        "sound": sound_obj,
        "storage": storage_obj,
        "ui": UIWrapper(runtime_instance),
        "tick": tick_obj,
        "macro": macro_obj,
        
        "left": LEFT,
        "right": RIGHT,
        "middle": MIDDLE,
        
        # Layout-independent keys
        "K_A": K_A, "K_B": K_B, "K_C": K_C, "K_D": K_D, "K_E": K_E, "K_F": K_F,
        "K_G": K_G, "K_H": K_H, "K_I": K_I, "K_J": K_J, "K_K": K_K, "K_L": K_L,
        "K_M": K_M, "K_N": K_N, "K_O": K_O, "K_P": K_P, "K_Q": K_Q, "K_R": K_R,
        "K_S": K_S, "K_T": K_T, "K_U": K_U, "K_V": K_V, "K_W": K_W, "K_X": K_X,
        "K_Y": K_Y, "K_Z": K_Z,
        "K_0": K_0, "K_1": K_1, "K_2": K_2, "K_3": K_3, "K_4": K_4, "K_5": K_5,
        "K_6": K_6, "K_7": K_7, "K_8": K_8, "K_9": K_9,
        "K_F1": K_F1, "K_F2": K_F2, "K_F3": K_F3, "K_F4": K_F4, "K_F5": K_F5,
        "K_F6": K_F6, "K_F7": K_F7, "K_F8": K_F8, "K_F9": K_F9, "K_F10": K_F10, "K_F11": K_F11, "K_F12": K_F12,
        
        "K_ENTER": K_ENTER, "K_ESC": K_ESC, "K_SPACE": K_SPACE, "K_TAB": K_TAB,
        "K_BACKSPACE": K_BACKSPACE, "K_DELETE": K_DELETE, "K_INSERT": K_INSERT,
        "K_HOME": K_HOME, "K_END": K_END, "K_PAGE_UP": K_PAGE_UP, "K_PAGE_DOWN": K_PAGE_DOWN,
        "K_UP": K_UP, "K_DOWN": K_DOWN, "K_LEFT": K_LEFT, "K_RIGHT": K_RIGHT,
        "K_SHIFT": K_SHIFT, "K_CTRL": K_CTRL, "K_ALT": K_ALT, "K_CAPS_LOCK": K_CAPS_LOCK,

        "exit": macro_obj.exit,
        "stop": macro_obj.exit,
        "sleep": lambda s: sleep(s, runtime_instance),
        "int": int,
        "float": float,
        "str": str,
        "len": len,
        "type": type,
        "print": print,
        "range": range,
        "Key": keyboard.Key,
        "None": None,
    }
