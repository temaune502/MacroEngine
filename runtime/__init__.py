import threading
import time
from .vm.vm import VM
from .vm.base import VMRuntimeError
from compiler.compiler import Compiler
from compiler.lexer import Lexer
from compiler.parser import Parser
from compiler.analyzer import StaticAnalyzer
from services.cache_manager import BytecodeCache
from .stdlib import get_builtins

class MacroRuntime:
    _cache = BytecodeCache()
    _cleanup_done = False

    def __init__(self, name, source, controller=None):
        # Periodic cache cleanup (only once per run)
        if not MacroRuntime._cleanup_done:
            MacroRuntime._cache.cleanup()
            MacroRuntime._cleanup_done = True

        self.name = name
        self.source = source
        self.controller = controller
        self.vm = VM()
        self.error = None
        
        # Internal state placeholders (will be filled by get_builtins)
        self.tick_obj = None
        self.macro_obj = None
        self.sound_obj = None
        self.storage_obj = None
        
        # Setup globals from builtins.py
        self.vm.globals.update(get_builtins(self))
        
        # Try to load from cache
        try:
            self.chunk, self.functions = self._cache.get(source)
            
            if self.chunk is None:
                # Compile if not in cache
                print(f"[{self.name}] Compiling source...")
                lexer = Lexer(source)
                tokens = lexer.tokenize()
                parser = Parser(tokens)
                ast_tree = parser.parse()
                
                # 2. Аналіз коду на етапі побудови AST
                print(f"[{self.name}] Analyzing AST...")
                analyzer = StaticAnalyzer(builtins=self.vm.globals.keys())
                if not analyzer.analyze(ast_tree):
                    print(f"[{self.name}] Warning: Static analysis found potential issues.")

                compiler = Compiler()
                self.chunk = compiler.compile(ast_tree)
                self.functions = compiler.functions
                
                # Save to cache
                self._cache.set(source, self.chunk, self.functions)
            else:
                print(f"[{self.name}] Loaded from cache.")
        except Exception as e:
            self.error = str(e)
            self.chunk = None
            self.functions = {}
            print(f"[{self.name}] Compilation error: {e}")
        
        self.initialized = False
        self.should_exit = (self.error is not None)
        self.is_processing_tick = False # New flag to prevent tick overlap
        self._cleaned_up = False
        self.thread = None
        self.event_queue = []
        self.event_lock = threading.Lock()

    @property
    def is_running(self):
        return self.thread and self.thread.is_alive()

    def start(self):
        """Starts the macro in its own thread."""
        if self.error or self.should_exit: return
        self.thread = threading.Thread(target=self._run_loop, name=f"TML-Run-{self.name}", daemon=True)
        self.thread.start()

    def _run_loop(self):
        """Internal execution loop running in a separate thread."""
        try:
            print(f"[{self.name}] Initializing VM...")
            
            # Metadata configuration
            meta = self.chunk.metadata if self.chunk else {}
            
            # 1. Function remapping
            init_func = meta.get("init", meta.get("on_init", "on_init"))
            tick_func = meta.get("tick", meta.get("on_tick", "on_tick"))
            exit_func = meta.get("exit", meta.get("on_exit", "on_exit"))
            hotkey_func = meta.get("hotkey", meta.get("on_hotkey", "on_hotkey"))
            
            # Store remapped names for later use
            self._tick_func_name = tick_func
            self._exit_func_name = exit_func
            self._hotkey_func_name = hotkey_func

            # 2. VM Run (Top-level code)
            print(f"[{self.name}] Running top-level code...")
            self.vm.run(self.chunk, self.functions)
            
            # 3. Call Init (if exists)
            if init_func in self.functions or init_func in self.vm.globals:
                # Check if it's already yielded from top-level
                if self.vm.is_yielded:
                    print(f"[{self.name}] Top-level code yielded, skipping {init_func} until resume.")
                else:
                    print(f"[{self.name}] Calling {init_func}...")
                    self.vm.call_function(init_func)
            
            self.initialized = True
            print(f"[{self.name}] Macro initialized.")
            
            # 4. Tick loop
            last_tick = time.perf_counter()
            has_on_tick = tick_func in self.functions or tick_func in self.vm.globals
            
            # Check for no_tick metadata
            no_tick = meta.get("no_tick", False)
            if no_tick:
                print(f"[{self.name}] Tick system disabled via @meta.")
            
            # Check for infinite execution mode (no tick, no limit)
            is_infinite = no_tick and (meta.get("no_limit", False) or meta.get("instruction_limit") == -1)
            if is_infinite:
                print(f"[{self.name}] Entering infinite execution mode.")
            
            # Performance settings
            target_fps = meta.get("fps", 60)
            if target_fps <= 0: target_fps = 60
            frame_time = 1.0 / target_fps
            min_sleep = meta.get("min_sleep", 0.005)

            while not self.should_exit:
                # 4.1 Process events (hotkeys, etc.)
                self.process_events()

                # 4.2 Resume if yielded
                if self.vm.is_yielded:
                    self.vm.resume()
                    if is_infinite and not self.vm.is_yielded:
                        # If we were in infinite mode and it finished, exit loop
                        break

                # 4.3 Tick (only if not in infinite mode or yielded)
                if not is_infinite and has_on_tick and not no_tick and not self.is_processing_tick and not self.vm.is_yielded:
                    now = time.perf_counter()
                    delta = now - last_tick
                    last_tick = now
                    
                    try:
                        self.is_processing_tick = True
                        self.vm.call_function(tick_func, delta)
                    except Exception as e:
                        error_msg = f"L{e.line}: {e.message}" if isinstance(e, VMRuntimeError) and e.line else str(e)
                        print(f"[{self.name}] Tick error: {error_msg}")
                        break
                    finally:
                        self.is_processing_tick = False
                    
                    # Adaptive sleep based on metadata
                    elapsed = time.perf_counter() - now
                    sleep_time = max(min_sleep, frame_time - elapsed)
                    time.sleep(sleep_time)
                else:
                    # If no on_tick, sleep longer to save CPU while waiting for events
                    time.sleep(0.05)
                
        except Exception as e:
            if isinstance(e, VMRuntimeError) and e.line:
                self.error = f"L{e.line}: {e.message}"
            else:
                self.error = str(e)
            print(f"[{self.name}] Runtime error: {self.error}")
        finally:
            self.exit_macro()

    def process_events(self):
        """Processes pending events from the queue."""
        with self.event_lock:
            if not self.event_queue:
                return
            events = self.event_queue[:]
            self.event_queue.clear()
        
        for hotkey_obj in events:
            self.handle_hotkey_signal(hotkey_obj)

    def exit_macro(self):
        """Clean up and call on_exit."""
        # Ensure we only run cleanup once
        if getattr(self, "_cleaned_up", False):
            return
        self._cleaned_up = True
        
        self.should_exit = True
        
        # Get remapped exit function name
        exit_func = getattr(self, "_exit_func_name", "on_exit")

        try:
            # Force reset yield state so on_exit can run
            self.vm.is_yielded = False
            print(f"[{self.name}] Running {exit_func} cleanup...")
            self.vm.call_function(exit_func)
        except Exception as e:
            # Only print error if it's not "function not found" unless it's explicitly remapped
            if not (isinstance(e, Exception) and "not found" in str(e).lower() and exit_func == "on_exit"):
                error_msg = f"L{e.line}: {e.message}" if isinstance(e, VMRuntimeError) and e.line else str(e)
                print(f"[{self.name}] Error in {exit_func}: {error_msg}")
            
        if self.macro_obj:
            self.macro_obj.active = False

        # Close and remove dedicated overlay
        if self.controller:
            overlay = self.controller.get_overlay(self.name)
            if overlay:
                try:
                    overlay.signals.show_overlay.emit(False)
                except:
                    pass

    def handle_hotkey_signal(self, hotkey_obj):
        """Called when a hotkey event is dispatched to this runtime."""
        hotkey_func = getattr(self, "_hotkey_func_name", "on_hotkey")
        try:
            self.vm.call_function(hotkey_func, hotkey_obj)
        except Exception as e:
            # Ignore "not found" if not explicitly remapped
            if not (isinstance(e, Exception) and "not found" in str(e).lower() and hotkey_func == "on_hotkey"):
                error_msg = f"L{e.line}: {e.message}" if isinstance(e, VMRuntimeError) and e.line else str(e)
                print(f"[{self.name}] Error in {hotkey_func}: {error_msg}")

    def stop(self):
        self.should_exit = True
