import pyperclip
import pyautogui
import os
import winsound
import ctypes
from ctypes import wintypes
from .constants import user32, HWND_BROADCAST, WM_INPUTLANGCHANGEREQUEST

class SystemWrapper:
    def set_clipboard(self, text):
        pyperclip.copy(str(text))
        
    def get_clipboard(self):
        return pyperclip.paste()
        
    def alert(self, text, title="TML Alert"):
        pyautogui.alert(text=str(text), title=title)

    def set_keyboard_layout(self, lang_id):
        layouts = {'en': '00000409', 'uk': '00000422', 'ru': '00000419'}
        hex_id = layouts.get(lang_id.lower(), lang_id)
        if not user32: return False
        try:
            layout = user32.LoadKeyboardLayoutW(hex_id, 1)
            if not layout: return False
            user32.ActivateKeyboardLayout(layout, 0)
            hwnd = user32.GetForegroundWindow()
            if hwnd:
                user32.PostMessageW(hwnd, WM_INPUTLANGCHANGEREQUEST, 0, layout)
            user32.PostMessageW(HWND_BROADCAST, WM_INPUTLANGCHANGEREQUEST, 0, layout)
            return True
        except Exception:
            return False

    def get_keyboard_layout(self):
        if not user32: return ""
        layout_id = user32.GetKeyboardLayout(0)
        return hex(layout_id & 0xFFFF)

class SoundWrapper:
    def beep(self, freq=1000, duration=200):
        winsound.Beep(int(freq), int(duration))
        
    def play(self, filename):
        if os.path.exists(filename):
            winsound.PlaySound(filename, winsound.SND_FILENAME | winsound.SND_ASYNC)

    def set_volume(self, level):
        if not user32: return False
        try:
            level = max(0, min(100, int(level)))
            VK_VOLUME_DOWN = 0xAE
            VK_VOLUME_UP = 0xAF
            for _ in range(50):
                user32.keybd_event(VK_VOLUME_DOWN, 0, 0, 0)
                user32.keybd_event(VK_VOLUME_DOWN, 0, 2, 0)
            steps = int(level / 2)
            for _ in range(steps):
                user32.keybd_event(VK_VOLUME_UP, 0, 0, 0)
                user32.keybd_event(VK_VOLUME_UP, 0, 2, 0)
            return True
        except Exception:
            return False

    def get_volume(self):
        try:
            CLSCTX_ALL = 0x17
            CLSCTX_INPROC_SERVER = 0x1
            CLSID_MMDeviceEnumerator = "{BCDE0395-E52F-467C-8E3D-C4579291692E}"
            IID_IMMDeviceEnumerator = "{A95664D2-9614-4F35-A746-DE8DB63617E6}"
            IID_IAudioEndpointVolume = "{5CDF2C82-841E-4546-9722-0CF74078229A}"
            HRESULT = ctypes.c_long

            class _GUID(ctypes.Structure):
                _fields_ = [("Data1", wintypes.DWORD), ("Data2", wintypes.WORD),
                           ("Data3", wintypes.WORD), ("Data4", wintypes.BYTE * 8)]
                
            def str_to_guid(s):
                import re
                m = re.match(r"\{?([\dA-F]{8})-([\dA-F]{4})-([\dA-F]{4})-([\dA-F]{2})([\dA-F]{2})-([\dA-F]{12})\}?", s, re.I)
                if not m: return None
                d = m.groups()
                g = _GUID()
                g.Data1, g.Data2, g.Data3 = int(d[0], 16), int(d[1], 16), int(d[2], 16)
                g.Data4[0], g.Data4[1] = int(d[3], 16), int(d[4], 16)
                for i in range(6): g.Data4[i+2] = int(d[5][i*2:i*2+2], 16)
                return g

            class IUnknown(ctypes.Structure):
                _fields_ = [("lpVtbl", ctypes.POINTER(ctypes.c_void_p))]

            ctypes.windll.ole32.CoInitialize(None)
            try:
                clsid_enum = str_to_guid(CLSID_MMDeviceEnumerator)
                iid_enum = str_to_guid(IID_IMMDeviceEnumerator)
                enumerator = ctypes.POINTER(IUnknown)()
                res = ctypes.windll.ole32.CoCreateInstance(
                    ctypes.byref(clsid_enum), None, CLSCTX_INPROC_SERVER,
                    ctypes.byref(iid_enum), ctypes.byref(enumerator)
                )
                if res != 0: return -1
                get_def_proto = ctypes.WINFUNCTYPE(HRESULT, ctypes.c_void_p, ctypes.c_int, ctypes.c_int, ctypes.POINTER(ctypes.c_void_p))
                get_def = get_def_proto(enumerator.contents.lpVtbl[4])
                device = ctypes.c_void_p()
                if get_def(enumerator, 0, 0, ctypes.byref(device)) != 0: return -1
                class IMMDevice(ctypes.Structure): _fields_ = [("lpVtbl", ctypes.POINTER(ctypes.c_void_p))]
                device_ptr = ctypes.cast(device, ctypes.POINTER(IMMDevice))
                activate_proto = ctypes.WINFUNCTYPE(HRESULT, ctypes.c_void_p, ctypes.POINTER(_GUID), wintypes.DWORD, ctypes.c_void_p, ctypes.POINTER(ctypes.c_void_p))
                activate = activate_proto(device_ptr.contents.lpVtbl[3])
                iid_vol = str_to_guid(IID_IAudioEndpointVolume)
                vol_interface = ctypes.c_void_p()
                if activate(device, ctypes.byref(iid_vol), CLSCTX_ALL, None, ctypes.byref(vol_interface)) != 0: return -1
                class IAudioEndpointVolume(ctypes.Structure): _fields_ = [("lpVtbl", ctypes.POINTER(ctypes.c_void_p))]
                vol_ptr = ctypes.cast(vol_interface, ctypes.POINTER(IAudioEndpointVolume))
                get_scal_proto = ctypes.WINFUNCTYPE(HRESULT, ctypes.c_void_p, ctypes.POINTER(ctypes.c_float))
                get_scal = get_scal_proto(vol_ptr.contents.lpVtbl[9])
                current_vol = ctypes.c_float()
                if get_scal(vol_interface, ctypes.byref(current_vol)) == 0:
                    return int(current_vol.value * 100)
            finally:
                ctypes.windll.ole32.CoUninitialize()
        except Exception:
            pass
        return -1
