import os
import time
from PyQt6.QtCore import QObject, pyqtSignal, QTimer
from PyQt6.QtWidgets import QMessageBox
from ui.overlay import HUDOverlay

class RuntimeManager(QObject):
    stats_updated = pyqtSignal(int, int) # ips, total
    status_updated = pyqtSignal(str, str) # text, color
    error_occurred = pyqtSignal(str)
    
    def __init__(self, controller, parent_window):
        super().__init__()
        self.controller = controller
        self.window = parent_window
        self.last_total_instr = 0
        self.last_stats_time = time.time()
        
    def run_macro(self, current_file, source, limit):
        if not current_file or not source.strip():
            return
            
        self.window.console_widget.console.append(f"[Editor] Running {current_file}...")
        
        # Create a dedicated overlay for this macro
        overlay = HUDOverlay()
        self.controller.set_overlay(current_file, overlay)
        
        self.controller.add_runtime(current_file, source)
        
        # Check for immediate compilation errors
        with self.controller.lock:
            runtime = self.controller.runtimes.get(current_file)
            if runtime and runtime.error:
                self.handle_runtime_error(current_file, runtime.error)
                return

        # Set initial limit for the new runtime
        QTimer.singleShot(100, lambda: self.apply_initial_speed(current_file, limit))

    def apply_initial_speed(self, current_file, limit):
        with self.controller.lock:
            if current_file in self.controller.runtimes:
                self.controller.runtimes[current_file].vm.instruction_limit = limit

    def stop_macro(self, current_file):
        if current_file:
            self.window.console_widget.console.append(f"[Editor] Stopping {current_file}...")
            self.controller.stop_macro(current_file)
        else:
            self.window.console_widget.console.append("[Editor] No macro to stop.")

    def handle_runtime_error(self, current_file, error_msg):
        if error_msg.startswith("L") and ":" in error_msg:
            try:
                line_part = error_msg.split(":")[0][1:]
                rest = error_msg.split(":", 1)[1]
                error_msg = f"<a href='line:{line_part}' style='color: #f44336; text-decoration: none;'>[Error at Line {line_part}]</a> <span style='color: #f44336;'>{rest}</span>"
            except:
                error_msg = f"<span style='color: #f44336;'>[Error] {error_msg}</span>"
        else:
            error_msg = f"<span style='color: #f44336;'>[Error] {error_msg}</span>"
            
        self.window.console_widget.console.append(error_msg)
        self.controller.stop_macro(current_file)

    def update_stats(self):
        now = time.time()
        elapsed = now - self.last_stats_time
        if elapsed >= 0.5:
            total_instr = 0
            with self.controller.lock:
                for r in self.controller.runtimes.values():
                    total_instr += r.vm.total_instruction_count
            
            delta_instr = total_instr - self.last_total_instr
            ips = int(delta_instr / elapsed)
            
            self.stats_updated.emit(ips, total_instr)
            self.last_total_instr = total_instr
            self.last_stats_time = now

    def get_status(self, current_file):
        is_running = False
        with self.controller.lock:
            if current_file in self.controller.runtimes:
                runtime = self.controller.runtimes[current_file]
                if runtime and runtime.is_running:
                    is_running = True
        
        if is_running:
            return "RUNNING", "#a6e22e"
        else:
            return "READY", "#858585"
