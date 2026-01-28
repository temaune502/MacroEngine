import os
import time
import ctypes
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLabel, QListWidget, QMenu, QListWidgetItem)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QColor
from services.config_manager import ConfigManager
import time

class MacroManagerWindow(QMainWindow):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.setWindowTitle("TML Macro Manager")
        self.setFixedSize(400, 600)
        
        self.setup_ui()
        self.refresh_macros()
        
        # Timer for UI updates only
        self.ui_timer = QTimer()
        self.ui_timer.timeout.connect(self.update_ui_status)
        self.ui_timer.start(100) # Update UI every 100ms is enough

    def closeEvent(self, event):
        super().closeEvent(event)

    def setup_ui(self):
        self.setStyleSheet("""
            QMainWindow, QWidget { background-color: #1e1e1e; color: #ccc; }
            QListWidget { 
                background-color: #252526; 
                border: 1px solid #333; 
                color: #ccc; 
                outline: none; 
                border-radius: 4px;
            }
            QListWidget::item { padding: 8px 12px; border-bottom: 1px solid #2d2d2d; }
            QListWidget::item:selected { background: #37373d; color: white; border-radius: 4px; }
            QListWidget::item:hover { background: #2a2d2e; }
            
            QPushButton { 
                background-color: #3c3c3c; 
                color: #ccc; 
                border: 1px solid #444; 
                padding: 8px; 
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover { background: #4a4a4a; color: white; border: 1px solid #555; }
            QPushButton#stopAll { background-color: #8b0000; color: white; border: none; }
            QPushButton#stopAll:hover { background-color: #a00000; }
        """)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        header = QHBoxLayout()
        title = QLabel("TML ENGINE")
        title.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        title.setStyleSheet("color: #858585; letter-spacing: 1px;")
        header.addWidget(title)
        header.addStretch()
        
        self.status_dot = QLabel("●")
        self.status_dot.setStyleSheet("color: #a6e22e; font-size: 14px;") # Green for active
        header.addWidget(self.status_dot)
        
        self.macro_list = QListWidget()
        self.macro_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.macro_list.customContextMenuRequested.connect(self.show_context_menu)
        
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        
        self.btn_editor = QPushButton("Open Editor")
        self.btn_editor.clicked.connect(self.open_editor)
        
        self.btn_stop_all = QPushButton("Stop All")
        self.btn_stop_all.setObjectName("stopAll")
        self.btn_stop_all.clicked.connect(self.controller.stop_all)

        self.btn_console = QPushButton("Console")
        self.btn_console.clicked.connect(self.toggle_console)
        self.console_visible = False
        
        btn_layout.addWidget(self.btn_editor)
        btn_layout.addWidget(self.btn_console)
        btn_layout.addWidget(self.btn_stop_all)
        
        layout.addLayout(header)
        layout.addWidget(self.macro_list)
        layout.addLayout(btn_layout)

    def toggle_console(self):
        try:
            kernel32 = ctypes.windll.kernel32
            user32 = ctypes.windll.user32
            hwnd = kernel32.GetConsoleWindow()
            if hwnd:
                if self.console_visible:
                    user32.ShowWindow(hwnd, 0) # SW_HIDE
                    self.btn_console.setText("Console")
                else:
                    user32.ShowWindow(hwnd, 5) # SW_SHOW
                    self.btn_console.setText("Hide")
                self.console_visible = not self.console_visible
        except Exception as e:
            print(f"Error toggling console: {e}")

    def refresh_macros(self):
        self.macro_list.clear()
        config = ConfigManager.load()
        hotkeys = config.get("hotkeys", {})
        
        if os.path.exists("examples"):
            for root, dirs, files in os.walk("examples"):
                for f in sorted(files):
                    if f.endswith(".tml"):
                        full_path = os.path.join(root, f)
                        rel_path = os.path.relpath(full_path, "examples").replace("\\", "/")
                        
                        display = rel_path
                        if rel_path in hotkeys:
                            display = f"{rel_path} [{hotkeys[rel_path].upper()}]"
                        
                        item = QListWidgetItem(display)
                        item.setData(Qt.ItemDataRole.UserRole, rel_path)
                        self.macro_list.addItem(item)

    def update_ui_status(self):
        # 0. Cleanup finished runtimes
        self.controller.cleanup_finished()
        
        # Update visual status of runtimes
        with self.controller.lock:
            running = list(self.controller.runtimes.keys())
            
        for i in range(self.macro_list.count()):
            item = self.macro_list.item(i)
            filename = item.data(Qt.ItemDataRole.UserRole)
            if filename in running:
                item.setBackground(QColor(46, 125, 50)) # Solid Green (Material Green 800)
                item.setForeground(QColor(255, 255, 255)) # White text
            else:
                item.setBackground(Qt.GlobalColor.transparent)
                item.setForeground(QColor(204, 204, 204)) # Default light gray

    def show_context_menu(self, pos):
        item = self.macro_list.itemAt(pos)
        if not item: return
        filename = item.data(Qt.ItemDataRole.UserRole)
        
        menu = QMenu()
        if filename in self.controller.runtimes:
            stop_act = menu.addAction("Stop")
            stop_act.triggered.connect(lambda: self.controller.stop_macro(filename))
        else:
            run_act = menu.addAction("Run")
            run_act.triggered.connect(lambda: self.run_macro(filename))
            
        menu.exec(self.macro_list.mapToGlobal(pos))

    def run_macro(self, filename):
        path = os.path.join("examples", filename)
        if not os.path.exists(path):
            # Try recursive search if not found in root examples
            for root, dirs, files in os.walk("examples"):
                if filename in files:
                    path = os.path.join(root, filename)
                    break

        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    source = f.read()
                
                # Create a dedicated overlay for this macro
                from ui.overlay import HUDOverlay
                overlay = HUDOverlay()
                self.controller.set_overlay(filename, overlay)
                
                self.controller.add_runtime(filename, source)
            except Exception as e:
                print(f"Error running macro {filename}: {e}")

    def on_stdout_written(self, text):
        """Forward stdout to editor console if it exists and is visible."""
        try:
            if hasattr(self, 'editor_win') and self.editor_win:
                # Check if editor window is not being destroyed
                if not self.editor_win.isHidden():
                    self.editor_win.on_stdout_written(text)
        except:
            pass

    def open_editor(self):
        from ui.editor_window import MacroEditorWindow
        if not hasattr(self, 'editor_win'):
            self.editor_win = MacroEditorWindow(self.controller, self)
        self.editor_win.show()
        self.editor_win.raise_()
        self.editor_win.activateWindow()

    def update_hotkeys(self):
        self.refresh_macros()
        if hasattr(self, 'on_hotkeys_updated'):
            self.on_hotkeys_updated()
