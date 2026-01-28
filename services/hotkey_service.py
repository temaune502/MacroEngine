import os
from pynput import keyboard
from PyQt6.QtCore import QObject, pyqtSignal

class HotkeyService(QObject):
    """
    GUI-level service to listen for global hotkeys and trigger macro actions.
    """
    macro_triggered = pyqtSignal(str, str) # filename, action ('start' or 'stop')

    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.hotkeys = {} # key_str -> filename
        self.listener = None
        self.pressed_keys = set()

    def set_bindings(self, hotkeys_dict):
        """Updates the active hotkey bindings. Supports multiple macros per hotkey."""
        self.hotkeys = {} # key_str -> list of filenames
        for filename, hotkey_str in hotkeys_dict.items():
            if not hotkey_str:
                continue
            
            # Normalize hotkey string
            parts = hotkey_str.lower().replace(" ", "").split('+')
            norm_parts = []
            for p in parts:
                p = p.replace("ctrl_l", "ctrl").replace("ctrl_r", "ctrl")
                p = p.replace("shift_l", "shift").replace("shift_r", "shift")
                p = p.replace("alt_l", "alt").replace("alt_r", "alt").replace("alt_gr", "alt")
                if p:
                    norm_parts.append(p)
            
            # Sort parts to ensure consistent matching (e.g. ctrl+alt vs alt+ctrl)
            # But keep modifiers first for readability if needed, though sort() is safer
            norm_parts.sort()
            norm_hotkey = "+".join(norm_parts)
            
            if norm_hotkey not in self.hotkeys:
                self.hotkeys[norm_hotkey] = []
            self.hotkeys[norm_hotkey].append(filename)
        
        # Clear pressed keys on binding update to prevent ghost triggers
        self.pressed_keys.clear()
        print(f"[HotkeyService] Bindings updated: {self.hotkeys}")

    def start(self):
        if not self.listener:
            self.listener = keyboard.Listener(on_press=self._on_press, on_release=self._on_release)
            self.listener.name = "TML-HotkeyListener"
            self.listener.start()
            print("[HotkeyService] Listener started")

    def stop(self):
        if self.listener:
            self.listener.stop()
            self.listener = None
            print("[HotkeyService] Listener stopped")

    def _get_key_name(self, key):
        """Standardizes key names across different platforms and pynput versions."""
        try:
            # 1. Special keys (Key.ctrl, Key.alt, etc.)
            if isinstance(key, keyboard.Key):
                name = key.name.lower()
                if name.startswith('ctrl'): return 'ctrl'
                if name.startswith('shift'): return 'shift'
                if name.startswith('alt'): return 'alt'
                if name.startswith('cmd') or name.startswith('win'): return 'win'
                return name

            # 2. KeyCode (letters, numbers, etc.)
            if isinstance(key, keyboard.KeyCode):
                # Try vk first (more reliable for some keys)
                if key.vk:
                    # A-Z
                    if 65 <= key.vk <= 90: return chr(key.vk + 32)
                    # 0-9
                    if 48 <= key.vk <= 57: return chr(key.vk)
                    # Numpad 0-9
                    if 96 <= key.vk <= 105: return chr(key.vk - 48)
                    # F1-F12
                    if 112 <= key.vk <= 123: return f"f{key.vk - 111}"
                
                # Try char
                if key.char:
                    # Handle ctrl+char combinations (\x01 etc)
                    if ord(key.char) < 32:
                        try: return chr(ord(key.char) + 96)
                        except: pass
                    return key.char.lower()
                
                # Fallback for KeyCode
                return str(key).replace("'", "").lower()

            # 3. Final Fallback
            k_str = str(key).replace("'", "").lower()
            if k_str.startswith('key.'): k_str = k_str[4:]
            return k_str.split('_')[0]
        except Exception:
            return str(key).lower()

    def _on_press(self, key):
        # 1. Dispatch key to internal library
        try:
            self.controller.dispatch_key_event(key)
        except Exception as e:
            print(f"[HotkeyService] Error dispatching key: {e}")

        # 2. Track pressed keys for combinations
        key_name = self._get_key_name(key)
        self.pressed_keys.add(key_name)
        
        # Anti-stuck: if too many keys pressed, something is wrong
        if len(self.pressed_keys) > 10:
            self.pressed_keys.clear()
            self.pressed_keys.add(key_name)

        # 3. Build current combination string
        current_parts = sorted(list(self.pressed_keys))
        combo_str = "+".join(current_parts)
        
        # Also try "shorter" version (only modifiers + current key)
        # to support fast typing or overlapping presses
        modifiers = []
        for mod in ['ctrl', 'alt', 'shift', 'win']:
            if mod in self.pressed_keys:
                modifiers.append(mod)
        
        short_combo = []
        if key_name not in ['ctrl', 'alt', 'shift', 'win']:
            short_combo = sorted(modifiers + [key_name])
        else:
            short_combo = sorted(modifiers)
            
        short_combo_str = "+".join(short_combo)

        # Check for matches
        target_filenames = []
        
        
        # Priority 1: Exact full combination (e.g. ctrl+alt+s)
        if combo_str in self.hotkeys:
            target_filenames = self.hotkeys[combo_str]
        # Priority 2: Short combination (modifiers + last key)
        elif short_combo_str in self.hotkeys:
            target_filenames = self.hotkeys[short_combo_str]

        if target_filenames:
            # Use real monotonic time for debouncing
            import time
            current_time = time.monotonic()
            if not hasattr(self, '_last_trigger_time'): self._last_trigger_time = 0
            if not hasattr(self, '_last_trigger_combo'): self._last_trigger_combo = ""
            
            # Debounce: 300ms for the same combo
            if combo_str != self._last_trigger_combo or (current_time - self._last_trigger_time) > 0.3:
                print(f"[HotkeyService] Triggering {len(target_filenames)} macros for {short_combo_str}")
                for filename in target_filenames:
                    self.macro_triggered.emit(filename, "toggle")
                
                self._last_trigger_time = current_time
                self._last_trigger_combo = combo_str
                
                # Clear keys after trigger to prevent chain reactions or multiple triggers from one press
                self.pressed_keys.clear()

    def _on_release(self, key):
        key_name = self._get_key_name(key)
        if key_name in self.pressed_keys:
            self.pressed_keys.remove(key_name)
