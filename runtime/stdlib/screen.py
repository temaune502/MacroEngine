import pyautogui
import math
import time
import subprocess
import ctypes
from ctypes import wintypes
from .vector import Vector
from .constants import user32, dxva2, PHYSICAL_MONITOR, HWND_BROADCAST, WM_SYSCOMMAND, SC_MONITORPOWER

class ScreenWrapper:
    def size(self):
        s = pyautogui.size()
        return Vector(s[0], s[1])
        
    def get_color(self, x, y):
        c = pyautogui.pixel(int(x), int(y))
        return Vector(c[0], c[1], c[2])

    def find_color(self, target_color, x=0, y=0, w=None, h=None, tolerance=10):
        import numpy as np
        if w is None or h is None:
            sz = self.size()
            w = w or sz.x
            h = h or sz.y
            
        screenshot = pyautogui.screenshot(region=(int(x), int(y), int(w), int(h)))
        img = np.array(screenshot)
        
        if hasattr(target_color, 'x'):
            target = np.array([target_color.x, target_color.y, target_color.z])
        else:
            target = np.array(target_color)
            
        diff = np.abs(img - target)
        mask = np.all(diff <= tolerance, axis=-1)
        coords = np.argwhere(mask)
        
        if coords.size > 0:
            first_match = coords[0]
            return Vector(first_match[1] + x, first_match[0] + y)
        return None
        
    def find_image(self, path, confidence=0.9):
        try:
            res = pyautogui.locateOnScreen(path, confidence=confidence)
            if res:
                return Vector(res.left + res.width/2, res.top + res.height/2)
        except:
            pass
        return None

    def find_all_images(self, path, confidence=0.9):
        try:
            res = list(pyautogui.locateAllOnScreen(path, confidence=confidence))
            return [Vector(r.left + r.width/2, r.top + r.height/2) for r in res]
        except:
            return []

    def set_brightness(self, level):
        level = max(0, min(100, int(level)))
        success = False
        
        if dxva2 and user32:
            try:
                def callback(hMonitor, hdcMonitor, lprcMonitor, dwData):
                    count = wintypes.DWORD()
                    if dxva2.GetNumberOfPhysicalMonitorsFromHMONITOR(hMonitor, ctypes.byref(count)):
                        physical_monitors = (PHYSICAL_MONITOR * count.value)()
                        if dxva2.GetPhysicalMonitorsFromHMONITOR(hMonitor, count.value, physical_monitors):
                            for i in range(count.value):
                                dxva2.SetMonitorBrightness(physical_monitors[i].hPhysicalMonitor, level)
                            dxva2.DestroyPhysicalMonitors(count.value, physical_monitors)
                    return True

                MONITORENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HMONITOR, wintypes.HDC, ctypes.POINTER(wintypes.RECT), wintypes.LPARAM)
                user32.EnumDisplayMonitors(None, None, MONITORENUMPROC(callback), 0)
                success = True
            except Exception:
                pass

        try:
            cmd = f"powershell (Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods).WmiSetBrightness(1,{level})"
            subprocess.run(cmd, shell=True, capture_output=True, timeout=2)
            success = True
        except Exception:
            pass
            
        return success

    def get_brightness(self):
        if dxva2 and user32:
            try:
                brightness_list = []
                def callback(hMonitor, hdcMonitor, lprcMonitor, dwData):
                    count = wintypes.DWORD()
                    if dxva2.GetNumberOfPhysicalMonitorsFromHMONITOR(hMonitor, ctypes.byref(count)):
                        physical_monitors = (PHYSICAL_MONITOR * count.value)()
                        if dxva2.GetPhysicalMonitorsFromHMONITOR(hMonitor, count.value, physical_monitors):
                            for i in range(count.value):
                                min_b, cur_b, max_b = wintypes.DWORD(), wintypes.DWORD(), wintypes.DWORD()
                                if dxva2.GetMonitorBrightness(physical_monitors[i].hPhysicalMonitor, ctypes.byref(min_b), ctypes.byref(cur_b), ctypes.byref(max_b)):
                                    brightness_list.append(int(cur_b.value))
                            dxva2.DestroyPhysicalMonitors(count.value, physical_monitors)
                    return True

                MONITORENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HMONITOR, wintypes.HDC, ctypes.POINTER(wintypes.RECT), wintypes.LPARAM)
                user32.EnumDisplayMonitors(None, None, MONITORENUMPROC(callback), 0)
                if brightness_list:
                    return brightness_list[0]
            except Exception:
                pass

        try:
            cmd = "powershell (Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightness).CurrentBrightness"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=2)
            if result.stdout.strip():
                return int(result.stdout.strip())
        except Exception:
            pass
            
        return -1

    def monitor_on(self):
        if user32:
            user32.SendMessageW(HWND_BROADCAST, WM_SYSCOMMAND, SC_MONITORPOWER, -1)
            return True
        return False

    def monitor_off(self):
        if user32:
            user32.SendMessageW(HWND_BROADCAST, WM_SYSCOMMAND, SC_MONITORPOWER, 2)
            return True
        return False

    def wait_for_color(self, target_color, x, y, timeout=10, tolerance=10):
        start_time = time.time()
        while time.time() - start_time < timeout:
            current = self.get_color(x, y)
            if hasattr(target_color, 'x'):
                dist = math.sqrt((current.x - target_color.x)**2 + (current.y - target_color.y)**2 + (current.z - target_color.z)**2)
            else:
                dist = math.sqrt((current.x - target_color[0])**2 + (current.y - target_color[1])**2 + (current.z - target_color[2])**2)
            
            if dist <= tolerance:
                return True
            time.sleep(0.1)
        return False

    def wait_for_image(self, path, timeout=10, confidence=0.9):
        start_time = time.time()
        while time.time() - start_time < timeout:
            if self.find_image(path, confidence):
                return True
            time.sleep(0.2)
        return False

    def unmute(self):
        if not user32: return False
        VK_VOLUME_MUTE = 0xAD
        user32.keybd_event(VK_VOLUME_MUTE, 0, 0, 0)
        user32.keybd_event(VK_VOLUME_MUTE, 0, 2, 0)
        return True

    def mute(self):
        return self.unmute()
