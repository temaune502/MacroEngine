from .opcodes import OpCode
from . import ast_nodes as ast

class Chunk:
    def __init__(self):
        self.code = []
        self.constants = []
        self.lines = []
        self.metadata = {}
        
    def emit(self, opcode, arg=None, line=None):
        self.code.append((opcode, arg))
        self.lines.append(line)
        return len(self.code) - 1

    def add_constant(self, value):
        for i, const in enumerate(self.constants):
            if const == value:
                return i
        self.constants.append(value)
        return len(self.constants) - 1

    def patch_jump(self, offset):
        if offset is None:
            return
        self.code[offset] = (self.code[offset][0], len(self.code))

class LocalScanner:
    def __init__(self):
        self.locals = []

    def visit(self, node):
        if isinstance(node, ast.FunctionDef):
            for p in node.params:
                name = p if isinstance(p, str) else p.value
                if name not in self.locals:
                    self.locals.append(name)
            
            if node.kwargs_param:
                name = node.kwargs_param if isinstance(node.kwargs_param, str) else node.kwargs_param.value
                if name not in self.locals:
                    self.locals.append(name)
            
            for s in node.body:
                if not isinstance(s, ast.FunctionDef):
                    self.visit(s)
        elif isinstance(node, ast.VarDecl):
            if node.name not in self.locals:
                self.locals.append(node.name)
        elif isinstance(node, ast.ForStmt):
            if node.item_name not in self.locals:
                self.locals.append(node.item_name)
            for s in node.body:
                self.visit(s)
        elif isinstance(node, ast.IfStmt):
            for s in node.then_branch:
                self.visit(s)
            for _, body in node.elif_branches:
                for s in body:
                    self.visit(s)
            if node.else_branch:
                for s in node.else_branch:
                    self.visit(s)
        elif isinstance(node, ast.WhileStmt):
            for s in node.body:
                self.visit(s)

class FunctionObject:
    def __init__(self, name, arity, defaults=None, kwargs_param=None, local_names=None):
        self.name = name
        self.arity = arity
        self.defaults = defaults or {}
        self.kwargs_param = kwargs_param
        self.chunk = Chunk()
        self.locals_count = 0
        self.local_names = local_names or []
    
    def __repr__(self):
        return f"<function {self.name}>"
