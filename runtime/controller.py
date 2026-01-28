import time
import threading
from pynput import keyboard
from . import MacroRuntime
from ui.overlay import HUDOverlay

class RuntimeController:
    """
    Core library class to manage multiple TML runtimes.
    Treat this as part of the 'tml' library.
    """
    def __init__(self):
        self.runtimes = {}
        self.overlays = {} # Map runtime name -> HUDOverlay instance
        self.is_running = False
        self.event_queue = []
        self.lock = threading.Lock()

    def set_overlay(self, name, overlay):
        """Assigns an overlay to a specific runtime."""
        with self.lock:
            self.overlays[name] = overlay

    def get_overlay(self, name):
        """Returns the overlay for a specific runtime."""
        with self.lock:
            return self.overlays.get(name)

    def add_runtime(self, name, source):
        """Compiles and starts a new runtime instance in a background thread."""
        def task():
            try:
                # Compilation happens here (inside the thread)
                runtime = MacroRuntime(name, source, self)
                with self.lock:
                    self.runtimes[name] = runtime
                runtime.start()
            except Exception as e:
                print(f"Failed to start runtime {name}: {e}")

        threading.Thread(target=task, name=f"TML-Comp-{name}", daemon=True).start()

    def cleanup_finished(self):
        """Removes runtimes that have finished execution."""
        with self.lock:
            if not self.runtimes:
                return
            finished = [name for name, r in self.runtimes.items() if not r.is_running]
            if not finished:
                return
            for name in finished:
                del self.runtimes[name]

    def dispatch_key_event(self, key_obj):
        """Library method to inject key events into running macros."""
        # We don't want to hold the global lock while iterating runtimes if possible,
        # but runtimes dict can change. Let's take a quick snapshot.
        with self.lock:
            active_runtimes = list(self.runtimes.values())
            
        for runtime in active_runtimes:
            with runtime.event_lock:
                # Limit queue size to prevent memory issues if macro is blocked
                if len(runtime.event_queue) < 100:
                    runtime.event_queue.append(key_obj)

    def stop_macro(self, name):
        """Stops a specific macro by name."""
        with self.lock:
            if name in self.runtimes:
                self.runtimes[name].stop()

    def stop_all(self):
        """Stops all running macros."""
        with self.lock:
            for runtime in self.runtimes.values():
                runtime.stop()
            self.runtimes = {}
