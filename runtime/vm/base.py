from compiler import FunctionObject

class VMRuntimeError(Exception):
    def __init__(self, message, line=None):
        self.message = message
        self.line = line
        super().__init__(self.message)

class CallFrame:
    def __init__(self, function, ip, stack_start):
        self.function = function # FunctionObject or None for global
        self.ip = ip
        self.stack_start = stack_start
