class ASTNode:
    def __init__(self, line=None, column=None):
        self.line = line
        self.column = column

class Program(ASTNode):
    def __init__(self, statements, metadata=None, line=None, column=None):
        super().__init__(line, column)
        self.statements = statements
        self.metadata = metadata or {}

class FunctionDef(ASTNode):
    def __init__(self, name, params, defaults, body, kwargs_param=None, line=None, column=None):
        super().__init__(line, column)
        self.name = name
        self.params = params
        self.defaults = defaults # Dictionary: param_name -> default_value_expr
        self.body = body
        self.kwargs_param = kwargs_param # Name of the **kwargs parameter

class VarDecl(ASTNode):
    def __init__(self, name, expression, line=None, column=None):
        super().__init__(line, column)
        self.name = name
        self.expression = expression

class VarAssign(ASTNode):
    def __init__(self, target, expression, line=None, column=None):
        super().__init__(line, column)
        self.target = target # Can be a VariableExpr or a GetExpr
        self.expression = expression

class IfStmt(ASTNode):
    def __init__(self, condition, then_branch, elif_branches=None, else_branch=None, line=None, column=None):
        super().__init__(line, column)
        self.condition = condition
        self.then_branch = then_branch
        self.elif_branches = elif_branches or [] # List of (condition, branch)
        self.else_branch = else_branch

class WhileStmt(ASTNode):
    def __init__(self, condition, body, line=None, column=None):
        super().__init__(line, column)
        self.condition = condition
        self.body = body

class ForStmt(ASTNode):
    def __init__(self, item_name, iterable, body, line=None, column=None):
        super().__init__(line, column)
        self.item_name = item_name
        self.iterable = iterable
        self.body = body

class ReturnStmt(ASTNode):
    def __init__(self, expression, line=None, column=None):
        super().__init__(line, column)
        self.expression = expression

class BreakStmt(ASTNode):
    def __init__(self, line=None, column=None):
        super().__init__(line, column)

class ContinueStmt(ASTNode):
    def __init__(self, line=None, column=None):
        super().__init__(line, column)

class ExprStmt(ASTNode):
    def __init__(self, expression, line=None, column=None):
        super().__init__(line, column)
        self.expression = expression

class BinaryExpr(ASTNode):
    def __init__(self, left, operator, right, line=None, column=None):
        super().__init__(line, column)
        self.left = left
        self.operator = operator
        self.right = right

class UnaryExpr(ASTNode):
    def __init__(self, operator, right, line=None, column=None):
        super().__init__(line, column)
        self.operator = operator
        self.right = right

class LiteralExpr(ASTNode):
    def __init__(self, value, line=None, column=None):
        super().__init__(line, column)
        self.value = value

class ListExpr(ASTNode):
    def __init__(self, elements, line=None, column=None):
        super().__init__(line, column)
        self.elements = elements

class DictExpr(ASTNode):
    def __init__(self, keys, values, line=None, column=None):
        super().__init__(line, column)
        self.keys = keys
        self.values = values

class VariableExpr(ASTNode):
    def __init__(self, name, line=None, column=None):
        super().__init__(line, column)
        self.name = name

class CallExpr(ASTNode):
    def __init__(self, callee, arguments, keyword_arguments=None, line=None, column=None):
        super().__init__(line, column)
        self.callee = callee # Can be a VariableExpr or a dot access
        self.arguments = arguments # Positional arguments
        self.keyword_arguments = keyword_arguments or {} # Dictionary: name -> expression

class GetExpr(ASTNode):
    def __init__(self, object, name, line=None, column=None):
        super().__init__(line, column)
        self.object = object
        self.name = name

class IndexExpr(ASTNode):
    def __init__(self, object, index, line=None, column=None):
        super().__init__(line, column)
        self.object = object
        self.index = index

class YieldStmt(ASTNode):
    def __init__(self, line=None, column=None):
        super().__init__(line, column)
