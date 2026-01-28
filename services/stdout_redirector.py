import time
import sys
from PyQt6.QtCore import QObject, pyqtSignal

class StdoutRedirector(QObject):
    text_written = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.buffer = ""
        self.last_emit = 0
        self._is_writing = False
        self._original_stdout = sys.stdout

    def write(self, text):
        # Prevent recursion if printing inside signal handler
        if self._is_writing:
            if self._original_stdout:
                self._original_stdout.write(str(text))
            return

        self._is_writing = True
        try:
            self.buffer += str(text)
            current_time = time.time()
            
            # Emit every 50ms or if newline found, but don't block
            if "\n" in self.buffer or current_time - self.last_emit > 0.05:
                self.text_written.emit(self.buffer)
                self.buffer = ""
                self.last_emit = current_time
        finally:
            self._is_writing = False

    def flush(self):
        if self.buffer:
            self.text_written.emit(self.buffer)
            self.buffer = ""
