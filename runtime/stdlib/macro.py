import os

class TickWrapper:
    def __init__(self):
        self.delta = 0.0

class MacroWrapper:
    def __init__(self, runtime_instance):
        self.active = True
        self.runtime = runtime_instance
        self.controller = runtime_instance.controller
        
    def exit(self):
        self.active = False
        self.runtime.exit_macro()

    def run(self, name, path=None):
        if self.controller is None: return
        actual_path = path if path else name
        if not actual_path.endswith(".tml"):
            actual_path += ".tml"
        if not os.path.exists(actual_path) and not os.path.isabs(actual_path):
            actual_path = os.path.join("examples", actual_path)

        if name in self.controller.runtimes:
            return
            
        try:
            with open(actual_path, "r", encoding="utf-8") as f:
                source = f.read()
            self.controller.add_runtime(name, source)
        except Exception as e:
            print(f"Error running macro {name}: {e}")

    def stop(self, name):
        if self.controller is None: return
        if name in self.controller.runtimes:
            self.controller.runtimes[name].stop()

    def is_running(self, name):
        if self.controller is None: return False
        return name in self.controller.runtimes
