from . import ast_nodes as ast
from .lexer import TokenType

class AnalyzerError(Exception):
    def __init__(self, message, line=None, column=None):
        self.message = message
        self.line = line
        self.column = column
        super().__init__(self.message)

class StaticAnalyzer:
    def __init__(self, builtins=None):
        self.scopes = [{}] # Stack of scopes, each scope is name -> type
        self.functions = {} # name -> (params, return_type)
        if builtins:
            for name in builtins:
                self.scopes[0][name] = 'any'
        
    def analyze(self, program_ast):
        try:
            self.visit(program_ast)
        except AnalyzerError as e:
            print(f"Static Analysis Error: {e.message}")
            if e.line:
                print(f"  at line {e.line}, column {e.column}")
            return False
        return True

    def visit(self, node):
        method_name = f'visit_{type(node).__name__}'
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node)

    def generic_visit(self, node):
        raise Exception(f"No visit_{type(node).__name__} method for {type(node).__name__}")

    def visit_Program(self, node):
        # First pass to collect all functions
        for stmt in node.statements:
            if isinstance(stmt, ast.FunctionDef):
                self.functions[stmt.name] = (stmt.params, 'any')
        
        for stmt in node.statements:
            self.visit(stmt)

    def visit_FunctionDef(self, node):
        # New scope for function
        # Ensure parameters are treated as strings if they are Token objects
        params_dict = {}
        for p in node.params:
            name = p.value if hasattr(p, 'value') else p
            params_dict[name] = 'any'
        
        # Add kwargs_param to scope if exists
        if node.kwargs_param:
            name = node.kwargs_param if isinstance(node.kwargs_param, str) else node.kwargs_param.value
            params_dict[name] = 'dict'
            
        # Visit default values
        for name, val in node.defaults.items():
            self.visit(val)
            
        self.scopes.append(params_dict)
        for stmt in node.body:
            self.visit(stmt)
        self.scopes.pop()

    def visit_VarDecl(self, node):
        val_type = self.visit(node.expression)
        self.scopes[-1][node.name] = val_type

    def visit_VarAssign(self, node):
        val_type = self.visit(node.expression)
        if isinstance(node.target, ast.VariableExpr):
            if not self.is_defined(node.target.name):
                # In TML, if it's not 'let', it might be a global or auto-created? 
                # Usually 'set' requires existing variable.
                pass 
            self.set_type(node.target.name, val_type)
        elif isinstance(node.target, ast.GetExpr):
            self.visit(node.target)

    def visit_IfStmt(self, node):
        self.visit(node.condition)
        for stmt in node.then_branch:
            self.visit(stmt)
        for cond, branch in node.elif_branches:
            self.visit(cond)
            for stmt in branch:
                self.visit(stmt)
        if node.else_branch:
            for stmt in node.else_branch:
                self.visit(stmt)

    def visit_WhileStmt(self, node):
        self.visit(node.condition)
        for stmt in node.body:
            self.visit(stmt)

    def visit_BreakStmt(self, node):
        pass

    def visit_ContinueStmt(self, node):
        pass

    def visit_YieldStmt(self, node):
        pass

    def visit_ReturnStmt(self, node):
        if node.expression:
            self.visit(node.expression)

    def visit_ExprStmt(self, node):
        self.visit(node.expression)

    def visit_BinaryExpr(self, node):
        self.visit(node.left)
        self.visit(node.right)
        return 'any'

    def visit_UnaryExpr(self, node):
        self.visit(node.right)
        return 'any'

    def visit_LiteralExpr(self, node):
        if isinstance(node.value, bool): return 'bool'
        if isinstance(node.value, (int, float)): return 'number'
        if isinstance(node.value, str): return 'string'
        return 'any'

    def visit_VariableExpr(self, node):
        if not self.is_defined(node.name):
            # In TML, many things are built-in or global
            pass
        return self.get_type(node.name)

    def visit_CallExpr(self, node):
        self.visit(node.callee)
        for arg in node.arguments:
            self.visit(arg)
        for name, val in node.keyword_arguments.items():
            self.visit(val)
        return 'any'

    def visit_GetExpr(self, node):
        self.visit(node.object)
        return 'any'

    def visit_IndexExpr(self, node):
        self.visit(node.object)
        self.visit(node.index)
        return 'any'

    def visit_ListExpr(self, node):
        for el in node.elements:
            self.visit(el)
        return 'list'

    def visit_DictExpr(self, node):
        for k, v in zip(node.keys, node.values):
            self.visit(k)
            self.visit(v)
        return 'dict'

    def visit_ForStmt(self, node):
        self.visit(node.iterable)
        self.scopes.append({node.item_name: 'any'})
        for stmt in node.body:
            self.visit(stmt)
        self.scopes.pop()

    # Helpers
    def is_defined(self, name):
        for scope in reversed(self.scopes):
            if name in scope:
                return True
        return name in self.functions

    def get_type(self, name):
        for scope in reversed(self.scopes):
            if name in scope:
                return scope[name]
        return 'any'

    def set_type(self, name, val_type):
        for scope in reversed(self.scopes):
            if name in scope:
                scope[name] = val_type
                return
        # If not found, add to current scope? 
        # TML might have different rules for auto-globals.
        self.scopes[-1][name] = val_type
