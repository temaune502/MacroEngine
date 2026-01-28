import sys
import os
import ctypes

# 1. Fix DPI Awareness (GUI Layer)
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

# 1.1 Hide Console on Startup
try:
    kernel32 = ctypes.windll.kernel32
    user32 = ctypes.windll.user32
    hwnd = kernel32.GetConsoleWindow()
    if hwnd:
        user32.ShowWindow(hwnd, 0) # 0 = SW_HIDE
except Exception:
    pass

os.environ["QT_QPA_PLATFORM"] = "windows:dpiawareness=0"
os.environ["QT_LOGGING_RULES"] = "qt.qpa.window=false"

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QPalette, QColor
from PyQt6.QtCore import Qt

# 2. Add tml to path


from runtime.controller import RuntimeController
from ui.manager_window import MacroManagerWindow
from services.hotkey_service import HotkeyService
from services.config_manager import ConfigManager

class TMLApp:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setStyle("Fusion")
        self.apply_dark_theme()
        
        # Library Instance
        self.controller = RuntimeController()
        
        # GUI Windows
        self.manager_win = MacroManagerWindow(self.controller)
        
        # GUI Services
        self.hotkey_service = HotkeyService(self.controller)
        self.hotkey_service.macro_triggered.connect(self.handle_global_hotkey)
        self.update_hotkey_bindings()
        self.hotkey_service.start()
        
        # Connect signals
        self.manager_win.on_hotkeys_updated = self.update_hotkey_bindings
        
        # Redirect stdout to editor console
        from services.stdout_redirector import StdoutRedirector
        self.stdout_redir = StdoutRedirector()
        self.stdout_redir.text_written.connect(self.manager_win.on_stdout_written)
        sys.stdout = self.stdout_redir

    def apply_dark_theme(self):
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor(53, 53, 53))
        palette.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.Base, QColor(25, 25, 25))
        palette.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.Button, QColor(53, 53, 53))
        palette.setColor(QPalette.ColorRole.ButtonText, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
        self.app.setPalette(palette)

    def update_hotkey_bindings(self):
        config = ConfigManager.load()
        self.hotkey_service.set_bindings(config.get("hotkeys", {}))

    def handle_global_hotkey(self, filename, action):
        if action == "toggle":
            if filename in self.controller.runtimes:
                print(f"Hotkey: Stopping {filename}")
                self.controller.stop_macro(filename)
            else:
                print(f"Hotkey: Starting {filename}")
                path = os.path.join("examples", filename)
                if not os.path.exists(path):
                    # Try recursive search if not found in root examples
                    for root, dirs, files in os.walk("examples"):
                        if filename in files:
                            path = os.path.join(root, filename)
                            break
                
                if os.path.exists(path):
                    with open(path, "r", encoding="utf-8") as f:
                        source = f.read()
                    
                    # Create a dedicated overlay for this macro
                    from ui.overlay import HUDOverlay
                    overlay = HUDOverlay()
                    self.controller.set_overlay(filename, overlay)
                    
                    self.controller.add_runtime(filename, source)

    def run(self):
        self.manager_win.show()
        res = self.app.exec()
        self.hotkey_service.stop()
        sys.exit(res)

if __name__ == "__main__":
    try:
        app = TMLApp()
        app.run()
    except Exception as e:
        import traceback
        print(f"CRITICAL ERROR DURING STARTUP:\n{e}")
        traceback.print_exc()
        input("Press Enter to exit...")
