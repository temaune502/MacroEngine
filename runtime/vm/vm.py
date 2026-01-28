from compiler.opcodes import OpCode
from compiler import FunctionObject
from .base import VMRuntimeError, CallFrame

class VM:
    def __init__(self, globals=None):
        self.stack = []
        self.globals = globals if globals is not None else {}
        self.frames = []
        self.chunk = None
        self.functions = {}
        self.instruction_count = 0
        self.total_instruction_count = 0
        self.instruction_limit = 1000 # 5. Ліміт інструкцій на тик
        self.is_yielded = False

    def run(self, chunk, functions=None):
        self.chunk = chunk
        self.functions = functions or {}
        
        # Apply metadata settings
        if self.chunk and hasattr(self.chunk, 'metadata'):
            meta = self.chunk.metadata
            if "instruction_limit" in meta:
                limit = meta["instruction_limit"]
                # Allow disabling limit with -1 or large number
                self.instruction_limit = float('inf') if limit == -1 else limit
            elif meta.get("no_limit", False):
                self.instruction_limit = float('inf')

        self.frames = [CallFrame(None, 0, 0)]
        self.instruction_count = 0
        self.is_yielded = False
        
        return self._execute()

    def _pop(self, context="stack"):
        if not self.stack:
            raise RuntimeError(f"Stack underflow in {context}")
        return self.stack.pop()

    def _finish_frame(self, res, start_frame_count):
        frame = self.frames.pop()
        
        # Clean up local stack
        while len(self.stack) > frame.stack_start:
            self.stack.pop()
        
        # Pop function object if it was a function call
        if frame.stack_start > 0:
            if self.stack:
                self.stack.pop()
        
        if len(self.frames) < start_frame_count:
            return res, True
        
        self.stack.append(res)
        return res, False

    def _call_func(self, num_args, kwargs, start_frame_count):
        func_idx = -num_args - 1
        func = self.stack[func_idx]
        
        if isinstance(func, FunctionObject):
            # User-defined function
            pos_args = []
            for _ in range(num_args):
                pos_args.append(self.stack.pop())
            pos_args.reverse()
            self.stack.pop() # Pop function object
            
            call_args = [None] * func.locals_count
            params_provided = set()
            
            # Fill positional
            for i in range(min(len(pos_args), func.arity)):
                call_args[i] = pos_args[i]
                params_provided.add(func.local_names[i])
            
            # Fill keywords
            extra_kwargs = {}
            for name, val in kwargs.items():
                if name in func.local_names[:func.arity]:
                    idx = func.local_names.index(name)
                    call_args[idx] = val
                    params_provided.add(name)
                elif func.kwargs_param:
                    extra_kwargs[name] = val
                else:
                    raise TypeError(f"Function {func.name} got unexpected keyword argument '{name}'")
            
            # Fill defaults
            for i in range(func.arity):
                name = func.local_names[i]
                if name not in params_provided:
                    if name in func.defaults:
                        call_args[i] = func.defaults[name]
                    else:
                        raise TypeError(f"Function {func.name} missing required argument: '{name}'")
            
            # Fill **kwargs
            if func.kwargs_param:
                idx = func.local_names.index(func.kwargs_param)
                call_args[idx] = extra_kwargs
            
            # Setup frame
            stack_start = len(self.stack)
            for val in call_args:
                self.stack.append(val)
                
            self.frames.append(CallFrame(func, 0, stack_start))
            
        elif callable(func):
            # Native function
            pos_args = []
            for _ in range(num_args):
                pos_args.append(self.stack.pop())
            pos_args.reverse()
            self.stack.pop() # Pop function object
            
            try:
                res = func(*pos_args, **kwargs)
                self.stack.append(res)
            except Exception as e:
                raise RuntimeError(f"Error calling native function {func}: {e}")
        else:
            raise RuntimeError(f"Object {func} is not callable")

    def get_current_line(self):
        if not self.frames:
            return 0
        frame = self.frames[-1]
        if frame.ip is None:
            return 0
        chunk = frame.function.chunk if frame.function else self.chunk
        if not chunk or not chunk.lines:
            return 0
        idx = max(0, frame.ip - 1)
        if idx >= len(chunk.lines):
            return chunk.lines[-1] if chunk.lines else 0
        return chunk.lines[idx]

    def _execute(self):
        start_frame_count = len(self.frames)
        while len(self.frames) >= start_frame_count:
            try:
                self.instruction_count += 1
                self.total_instruction_count += 1
                
                # Check limit only if it's not infinity
                if self.instruction_limit != float('inf') and self.instruction_count > self.instruction_limit:
                    self.is_yielded = True
                    return None 

                frame = self.frames[-1]
                if frame.ip is None:
                    raise VMRuntimeError(f"Critical VM Error: frame.ip is None", line=self.get_current_line())
                
                chunk = frame.function.chunk if frame.function else self.chunk
                
                if frame.ip >= len(chunk.code):
                    res, finished = self._finish_frame(None, start_frame_count)
                    if finished: return res
                    continue
                    
                op, arg = chunk.code[frame.ip]
                frame.ip += 1
                
                if op == OpCode.PUSH_CONST:
                    self.stack.append(chunk.constants[arg])
                elif op == OpCode.PUSH_TRUE:
                    self.stack.append(True)
                elif op == OpCode.PUSH_FALSE:
                    self.stack.append(False)
                elif op == OpCode.POP:
                    self.stack.pop()
                elif op == OpCode.DEFINE_GLOBAL:
                    name = chunk.constants[arg]
                    self.globals[name] = self.stack.pop()
                elif op == OpCode.GET_GLOBAL:
                    name = chunk.constants[arg]
                    if name in self.globals:
                        self.stack.append(self.globals[name])
                    elif name in self.functions:
                        self.stack.append(self.functions[name])
                    else:
                        raise RuntimeError(f"Undefined variable '{name}'")
                elif op == OpCode.SET_GLOBAL:
                    name = chunk.constants[arg]
                    if name not in self.globals:
                        raise RuntimeError(f"Undefined variable '{name}'")
                    self.globals[name] = self.stack[-1]
                elif op == OpCode.SET_GLOBAL_POP:
                    name = chunk.constants[arg]
                    if name not in self.globals:
                        raise RuntimeError(f"Undefined variable '{name}'")
                    self.globals[name] = self.stack.pop()
                elif op == OpCode.GET_LOCAL:
                    idx = frame.stack_start + arg
                    self.stack.append(self.stack[idx])
                elif op == OpCode.SET_LOCAL:
                    idx = frame.stack_start + arg
                    self.stack[idx] = self.stack[-1]
                elif op == OpCode.SET_LOCAL_POP:
                    idx = frame.stack_start + arg
                    self.stack[idx] = self.stack.pop()
                elif op == OpCode.GET_ATTR:
                    obj = self.stack.pop()
                    name = chunk.constants[arg]
                    val = getattr(obj, name)
                    self.stack.append(val)
                elif op == OpCode.SET_ATTR:
                    obj = self.stack.pop()
                    val = self.stack.pop()
                    name = chunk.constants[arg]
                    setattr(obj, name, val)
                    self.stack.append(val)
                elif op == OpCode.SET_ATTR_POP:
                    obj = self.stack.pop()
                    val = self.stack.pop()
                    name = chunk.constants[arg]
                    setattr(obj, name, val)
                elif op == OpCode.ADD:
                    b = self.stack.pop()
                    a = self.stack.pop()
                    self.stack.append(a + b)
                elif op == OpCode.SUB:
                    b = self.stack.pop()
                    a = self.stack.pop()
                    self.stack.append(a - b)
                elif op == OpCode.MUL:
                    b = self.stack.pop()
                    a = self.stack.pop()
                    self.stack.append(a * b)
                elif op == OpCode.DIV:
                    b = self.stack.pop()
                    a = self.stack.pop()
                    self.stack.append(a / b)
                elif op == OpCode.EQUAL:
                    b = self.stack.pop()
                    a = self.stack.pop()
                    self.stack.append(a == b)
                elif op == OpCode.NOT_EQUAL:
                    b = self.stack.pop()
                    a = self.stack.pop()
                    self.stack.append(a != b)
                elif op == OpCode.GREATER:
                    b = self.stack.pop()
                    a = self.stack.pop()
                    self.stack.append(a > b if a is not None and b is not None else False)
                elif op == OpCode.GREATER_EQUAL:
                    b = self.stack.pop()
                    a = self.stack.pop()
                    self.stack.append(a >= b if a is not None and b is not None else False)
                elif op == OpCode.LESS:
                    b = self.stack.pop()
                    a = self.stack.pop()
                    self.stack.append(a < b if a is not None and b is not None else False)
                elif op == OpCode.LESS_EQUAL:
                    b = self.stack.pop()
                    a = self.stack.pop()
                    self.stack.append(a <= b if a is not None and b is not None else False)
                elif op == OpCode.NOT:
                    self.stack.append(not self.stack.pop())
                elif op == OpCode.NEGATE:
                    self.stack.append(-self.stack.pop())
                elif op == OpCode.JUMP:
                    frame.ip = arg
                elif op == OpCode.JUMP_IF_FALSE:
                    if not self.stack[-1]: frame.ip = arg
                elif op == OpCode.JUMP_IF_FALSE_POP:
                    if not self.stack.pop(): frame.ip = arg
                elif op == OpCode.JUMP_IF_TRUE:
                    if self.stack[-1]: frame.ip = arg
                elif op == OpCode.JUMP_IF_TRUE_POP:
                    if self.stack.pop(): frame.ip = arg
                elif op == OpCode.INC_GLOBAL:
                    name = chunk.constants[arg]
                    self.globals[name] = self.globals.get(name, 0) + 1
                elif op == OpCode.ADD_GLOBAL:
                    name = chunk.constants[arg]
                    val = self.stack.pop()
                    self.globals[name] = self.globals.get(name, 0) + val
                elif op == OpCode.SET_ATTR_FAST:
                    name = chunk.constants[arg]
                    val = self.stack.pop()
                    obj = self.stack.pop()
                    setattr(obj, name, val)
                elif op == OpCode.LOOP:
                    frame.ip = arg
                elif op == OpCode.BUILD_LIST:
                    elements = [self.stack.pop() for _ in range(arg)][::-1]
                    self.stack.append(elements)
                elif op == OpCode.BUILD_MAP:
                    mapping = {}
                    for _ in range(arg):
                        val = self.stack.pop()
                        key = self.stack.pop()
                        mapping[key] = val
                    self.stack.append(mapping)
                elif op == OpCode.GET_ITER:
                    self.stack.append(iter(self.stack.pop()))
                elif op == OpCode.FOR_ITER:
                    iterator = self.stack[-1]
                    try:
                        self.stack.append(next(iterator))
                    except StopIteration:
                        self.stack.pop()
                        frame.ip = arg
                elif op == OpCode.INDEX_GET:
                    index = self.stack.pop()
                    obj = self.stack.pop()
                    if isinstance(obj, dict): self.stack.append(obj[index])
                    else: self.stack.append(obj[int(index)])
                elif op == OpCode.INDEX_SET:
                    index = self.stack.pop()
                    obj = self.stack.pop()
                    val = self.stack.pop()
                    if isinstance(obj, dict): obj[index] = val
                    else: obj[int(index)] = val
                    self.stack.append(val)
                elif op == OpCode.CALL:
                    self._call_func(arg, {}, start_frame_count)
                elif op == OpCode.CALL_KW:
                    num_pos_args, kw_names = arg
                    kwargs = {name: self.stack.pop() for name in reversed(kw_names)}
                    self._call_func(num_pos_args, kwargs, start_frame_count)
                elif op == OpCode.RETURN:
                    res = self.stack.pop()
                    res, finished = self._finish_frame(res, start_frame_count)
                    if finished: return res
                elif op == OpCode.RETURN_NONE:
                    res, finished = self._finish_frame(None, start_frame_count)
                    if finished: return res
                elif op == OpCode.YIELD:
                    self.is_yielded = True
                    return None
            except VMRuntimeError:
                raise
            except Exception as e:
                raise VMRuntimeError(str(e), line=self.get_current_line()) from e
        return None

    def resume(self):
        if not self.is_yielded:
            return None
        self.is_yielded = False
        self.instruction_count = 0
        return self._execute()

    def call_function(self, name, *args):
        self.instruction_count = 0
        if name in self.globals:
            func = self.globals[name]
        elif name in self.functions:
            func = self.functions[name]
        else:
            return None
            
        if not isinstance(func, FunctionObject):
            return None
            
        self.stack.append(func)
        stack_start = len(self.stack)
        for arg in args:
            self.stack.append(arg)
            
        for _ in range(func.arity, func.locals_count):
            self.stack.append(None)
            
        self.frames.append(CallFrame(func, 0, stack_start))
        return self._execute()
