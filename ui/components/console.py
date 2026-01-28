from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QFrame, QSplitter, QTextBrowser, 
                             QTableWidget, QHeaderView, QCheckBox)
from PyQt6.QtCore import Qt

class ConsoleWidget(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        self.setStyleSheet("background: #1e1e1e; border-top: 1px solid #333;")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 10)
        
        header = QHBoxLayout()
        lbl_console = QLabel("DEBUG CONSOLE")
        lbl_console.setStyleSheet("color: #858585; font-weight: bold; font-size: 10px;")
        
        self.btn_clear = QPushButton("Clear")
        self.btn_clear.setFixedWidth(50)
        self.btn_clear.setStyleSheet("""
            QPushButton { background: transparent; color: #858585; border: 1px solid #444; font-size: 9px; padding: 2px; }
            QPushButton:hover { color: #ccc; border: 1px solid #666; }
        """)
        
        header.addWidget(lbl_console)
        header.addStretch()
        
        lbl_memory = QLabel("MEMORY INSPECTOR")
        lbl_memory.setStyleSheet("color: #858585; font-weight: bold; font-size: 10px; margin-right: 10px;")
        header.addWidget(lbl_memory)
        
        self.cb_hide_funcs = QCheckBox("Hide Functions")
        self.cb_hide_funcs.setStyleSheet("""
            QCheckBox { color: #858585; font-size: 10px; font-weight: bold; margin-right: 10px; }
            QCheckBox::indicator { width: 12px; height: 12px; }
        """)
        header.addWidget(self.cb_hide_funcs)
        
        self.cb_log_vars = QCheckBox("Log Changes")
        self.cb_log_vars.setStyleSheet("""
            QCheckBox { color: #858585; font-size: 10px; font-weight: bold; margin-right: 10px; }
            QCheckBox::indicator { width: 12px; height: 12px; }
        """)
        header.addWidget(self.cb_log_vars)
        
        self.cb_highlight_execution = QCheckBox("Highlight Execution")
        self.cb_highlight_execution.setStyleSheet("""
            QCheckBox { color: #858585; font-size: 10px; font-weight: bold; margin-right: 10px; }
            QCheckBox::indicator { width: 12px; height: 12px; }
        """)
        header.addWidget(self.cb_highlight_execution)
        header.addWidget(self.btn_clear)
        
        layout.addLayout(header)
        
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.setStyleSheet("QSplitter::handle { background-color: #333; width: 2px; }")
        
        self.console = QTextBrowser()
        self.console.setReadOnly(True)
        self.console.setOpenExternalLinks(False)
        self.console.setStyleSheet("background: #1e1e1e; color: #d4d4d4; font-family: 'Consolas'; border: none;")
        
        self.memory_inspector = QTableWidget()
        self.memory_inspector.setColumnCount(2)
        self.memory_inspector.setHorizontalHeaderLabels(["Variable", "Value"])
        self.memory_inspector.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.memory_inspector.setStyleSheet("""
            QTableWidget { 
                background: #1e1e1e; 
                color: #d4d4d4; 
                gridline-color: #333; 
                border: none;
                font-family: 'Consolas';
                font-size: 11px;
            }
            QHeaderView::section {
                background: #252526;
                color: #858585;
                border: none;
                font-size: 10px;
                font-weight: bold;
                padding: 4px;
            }
        """)
        
        self.splitter.addWidget(self.console)
        self.splitter.addWidget(self.memory_inspector)
        self.splitter.setStretchFactor(0, 3)
        self.splitter.setStretchFactor(1, 1)
        
        layout.addWidget(self.splitter)

    def clear(self):
        self.console.clear()

    def append(self, text):
        self.console.append(text)

    def update_memory(self, runtime, current_file, last_vars_state):
        if not runtime:
            self.memory_inspector.setRowCount(0)
            return {}

        try:
            hide_funcs = self.cb_hide_funcs.isChecked()
            log_enabled = self.cb_log_vars.isChecked()
            filtered_vars = []
            current_vars_state = {}

            # 1. Global Variables
            globals_dict = runtime.vm.globals
            for name, value in globals_dict.items():
                if name.startswith("K_") or name in [
                    "mouse", "key", "keyboard", "time", "math", "random", 
                    "window", "screen", "system", "net", "tick", "macro",
                    "left", "right", "middle", "exit", "stop", "sleep",
                    "int", "float", "str", "len", "type", "print", "Key", "None"
                ]:
                    continue
                
                is_callable = callable(value)
                if is_callable and hide_funcs:
                    continue
                    
                val_str = str(value)
                var_key = f"global {name}"
                current_vars_state[var_key] = val_str
                
                if len(val_str) > 50: val_str = val_str[:47] + "..."
                filtered_vars.append((var_key, val_str))

            # 2. Local Variables
            for depth, frame in enumerate(runtime.vm.frames):
                if frame.function:
                    func_name = frame.function.name
                    local_names = getattr(frame.function, "local_names", [])
                    
                    for i, name in enumerate(local_names):
                        stack_idx = frame.stack_start + i
                        if stack_idx < len(runtime.vm.stack):
                            val = runtime.vm.stack[stack_idx]
                            val_str = str(val)
                            var_key = f"local {func_name}.{name}"
                            current_vars_state[var_key] = val_str
                            
                            if len(val_str) > 50: val_str = val_str[:47] + "..."
                            filtered_vars.append((var_key, val_str))

            # Logging
            if log_enabled:
                import os, datetime
                if not os.path.exists("logs"): os.makedirs("logs")
                log_path = os.path.join("logs", "variables.log")
                
                with open(log_path, "a", encoding="utf-8") as f:
                    for var_key, current_val in current_vars_state.items():
                        last_val = last_vars_state.get(var_key)
                        if last_val != current_val:
                            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                            f.write(f"[{timestamp}] [{current_file}] {var_key}: {last_val} -> {current_val}\n")
            
            # 3. Functions
            if not hide_funcs:
                for func_name in runtime.functions:
                    filtered_vars.append((f"func {func_name}", "<function>"))

            # Update Table
            from PyQt6.QtWidgets import QTableWidgetItem
            self.memory_inspector.setRowCount(len(filtered_vars))
            for i, (name, val_str) in enumerate(filtered_vars):
                self.memory_inspector.setItem(i, 0, QTableWidgetItem(name))
                self.memory_inspector.setItem(i, 1, QTableWidgetItem(val_str))
                
            return current_vars_state
        except:
            return last_vars_state
