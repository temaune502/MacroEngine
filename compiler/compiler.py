from .opcodes import OpCode
from . import ast_nodes as ast
from .lexer import TokenType
from .base import Chunk, LocalScanner, FunctionObject

class Compiler:
    def __init__(self):
        self.chunk = Chunk()
        self.functions = {}
        self.locals = [] 
        self.scope_depth = 0
        self.current_line = 0
        self.loop_start_stack = []
        self.break_jumps_stack = [] 

    def compile(self, program):
        self.chunk.metadata = program.metadata
        for stmt in program.statements:
            self.compile_statement(stmt)
        self.emit_op(OpCode.PUSH_CONST, self.chunk.add_constant(None))
        self.emit_op(OpCode.RETURN)
        
        self._optimize_chunk(self.chunk)
        for func in self.functions.values():
            self._optimize_chunk(func.chunk)
            
        return self.chunk

    def emit_op(self, op, arg=None):
        return self.chunk.emit(op, arg, self.current_line)

    def add_constant(self, val):
        return self.chunk.add_constant(val)

    def _optimize_chunk(self, chunk):
        if not chunk.code:
            return
            
        code = chunk.code
        lines = chunk.lines
        to_remove = [False] * len(code)
        replacements = {} 
        
        i = 0
        while i < len(code):
            op, arg = code[i]
            
            if op == OpCode.SET_LOCAL and i + 1 < len(code):
                next_op, next_arg = code[i+1]
                if next_op == OpCode.POP:
                    replacements[i] = (OpCode.SET_LOCAL_POP, arg)
                    to_remove[i+1] = True
                    i += 2
                    continue
            
            if op == OpCode.SET_GLOBAL and i + 1 < len(code):
                next_op, next_arg = code[i+1]
                if next_op == OpCode.POP:
                    replacements[i] = (OpCode.SET_GLOBAL_POP, arg)
                    to_remove[i+1] = True
                    i += 2
                    continue

            if op == OpCode.JUMP_IF_FALSE and i + 1 < len(code):
                next_op, next_arg = code[i+1]
                if next_op == OpCode.POP:
                    replacements[i] = (OpCode.JUMP_IF_FALSE_POP, arg)
                    to_remove[i+1] = True
                    i += 2
                    continue
            
            if op == OpCode.JUMP_IF_TRUE and i + 1 < len(code):
                next_op, next_arg = code[i+1]
                if next_op == OpCode.POP:
                    replacements[i] = (OpCode.JUMP_IF_TRUE_POP, arg)
                    to_remove[i+1] = True
                    i += 2
                    continue

            if op == OpCode.PUSH_CONST and i + 1 < len(code):
                const_val = chunk.constants[arg]
                next_op, next_arg = code[i+1]
                if const_val is None and next_op == OpCode.RETURN:
                    replacements[i] = (OpCode.RETURN_NONE, None)
                    to_remove[i+1] = True
                    i += 2
                    continue
            
            i += 1

        new_indices = [0] * (len(code) + 1)
        current_new = 0
        for idx in range(len(code)):
            new_indices[idx] = current_new
            if not to_remove[idx]:
                current_new += 1
        new_indices[len(code)] = current_new
        
        optimized = []
        optimized_lines = []
        for idx in range(len(code)):
            if to_remove[idx]:
                continue
            
            op, arg = code[idx]
            line = lines[idx]
            if idx in replacements:
                op, arg = replacements[idx]
            
            if op in (OpCode.JUMP, OpCode.JUMP_IF_FALSE, OpCode.JUMP_IF_TRUE, 
                      OpCode.JUMP_IF_FALSE_POP, OpCode.JUMP_IF_TRUE_POP, OpCode.LOOP, OpCode.FOR_ITER):
                if arg is not None and 0 <= arg < len(new_indices):
                    arg = new_indices[arg]
            
            optimized.append((op, arg))
            optimized_lines.append(line)
            
        for i in range(len(optimized)):
            op, arg = optimized[i]
            if op in (OpCode.JUMP, OpCode.JUMP_IF_FALSE, OpCode.JUMP_IF_TRUE, 
                      OpCode.JUMP_IF_FALSE_POP, OpCode.JUMP_IF_TRUE_POP, OpCode.LOOP, OpCode.FOR_ITER):
                if arg is not None and 0 <= arg < len(optimized):
                    target_op, target_arg = optimized[arg]
                    if target_op == OpCode.JUMP:
                        if target_arg is not None:
                            optimized[i] = (op, target_arg)
                    elif op in (OpCode.JUMP_IF_FALSE_POP, OpCode.JUMP_IF_TRUE_POP) and target_op == OpCode.POP:
                        optimized[i] = (op, arg + 1)

        chunk.code = optimized
        chunk.lines = optimized_lines

    def compile_statement(self, stmt):
        if stmt.line: self.current_line = stmt.line
        if isinstance(stmt, ast.FunctionDef):
            evaluated_defaults = {}
            for param, expr in stmt.defaults.items():
                if isinstance(expr, ast.LiteralExpr):
                    evaluated_defaults[param] = expr.value
                else:
                    evaluated_defaults[param] = None

            local_scanner = LocalScanner()
            local_scanner.visit(stmt)
            
            if stmt.kwargs_param and stmt.kwargs_param not in local_scanner.locals:
                local_scanner.locals.append(stmt.kwargs_param)

            func_compiler = Compiler()
            func_compiler.functions = self.functions 
            func_compiler.locals = local_scanner.locals
            func_compiler.scope_depth = 1 
            
            for s in stmt.body:
                func_compiler.compile_statement(s)
            
            if not func_compiler.chunk.code or func_compiler.chunk.code[-1][0] != OpCode.RETURN:
                func_compiler.emit_op(OpCode.PUSH_CONST, func_compiler.add_constant(None))
                func_compiler.emit_op(OpCode.RETURN)
            
            func_compiler._optimize_chunk(func_compiler.chunk)
            
            func_obj = FunctionObject(
                stmt.name, 
                len(stmt.params), 
                defaults=evaluated_defaults,
                kwargs_param=stmt.kwargs_param,
                local_names=local_scanner.locals
            )
            func_obj.chunk = func_compiler.chunk
            func_obj.locals_count = len(local_scanner.locals)
            
            self.functions[stmt.name] = func_obj
            
        elif isinstance(stmt, ast.VarDecl):
            self.compile_expression(stmt.expression)
            if self.scope_depth > 0:
                try:
                    local_idx = self.locals.index(stmt.name)
                    self.emit_op(OpCode.SET_LOCAL, local_idx)
                    self.emit_op(OpCode.POP) 
                except ValueError:
                    self.locals.append(stmt.name)
                    self.emit_op(OpCode.SET_LOCAL, len(self.locals) - 1)
                    self.emit_op(OpCode.POP)
            else:
                idx = self.chunk.add_constant(stmt.name)
                self.emit_op(OpCode.DEFINE_GLOBAL, idx)
                
        elif isinstance(stmt, ast.VarAssign):
            if isinstance(stmt.target, ast.VariableExpr) and self.scope_depth == 0:
                var_name = stmt.target.name
                if isinstance(stmt.expression, ast.BinaryExpr) and stmt.expression.operator == TokenType.PLUS:
                    left = stmt.expression.left
                    right = stmt.expression.right
                    
                    if isinstance(left, ast.VariableExpr) and left.name == var_name:
                        if isinstance(right, ast.LiteralExpr) and right.value == 1:
                            self.emit_op(OpCode.INC_GLOBAL, self.chunk.add_constant(var_name))
                            return
                        else:
                            self.compile_expression(right)
                            self.emit_op(OpCode.ADD_GLOBAL, self.chunk.add_constant(var_name))
                            return
                    elif isinstance(right, ast.VariableExpr) and right.name == var_name:
                        if isinstance(left, ast.LiteralExpr) and left.value == 1:
                            self.emit_op(OpCode.INC_GLOBAL, self.chunk.add_constant(var_name))
                            return
                        else:
                            self.compile_expression(left)
                            self.emit_op(OpCode.ADD_GLOBAL, self.chunk.add_constant(var_name))
                            return

            if isinstance(stmt.target, ast.GetExpr):
                self.compile_expression(stmt.target.object)
                self.compile_expression(stmt.expression)
                self.emit_op(OpCode.SET_ATTR_FAST, self.chunk.add_constant(stmt.target.name))
                return

            self.compile_expression(stmt.expression)
            self.compile_assign_target(stmt.target)
            self.emit_op(OpCode.POP) 
            
        elif isinstance(stmt, ast.IfStmt):
            self.compile_expression(stmt.condition)
            then_jump = self.emit_op(OpCode.JUMP_IF_FALSE, 0)
            self.emit_op(OpCode.POP) 
            
            for s in stmt.then_branch:
                self.compile_statement(s)
            
            else_jump = self.emit_op(OpCode.JUMP, 0)
            self.chunk.patch_jump(then_jump)
            self.emit_op(OpCode.POP) 
            
            for elif_cond, elif_body in stmt.elif_branches:
                self.compile_expression(elif_cond)
                next_elif_jump = self.emit_op(OpCode.JUMP_IF_FALSE, 0)
                self.emit_op(OpCode.POP)
                for s in elif_body:
                    self.compile_statement(s)
                self.emit_op(OpCode.JUMP, else_jump) 
                self.chunk.patch_jump(next_elif_jump)
                self.emit_op(OpCode.POP)
                
            if stmt.else_branch:
                for s in stmt.else_branch:
                    self.compile_statement(s)
            
            self.chunk.patch_jump(else_jump)

        elif isinstance(stmt, ast.WhileStmt):
            start = len(self.chunk.code)
            self.loop_start_stack.append(start)
            self.break_jumps_stack.append([])
            
            self.compile_expression(stmt.condition)
            exit_jump = self.emit_op(OpCode.JUMP_IF_FALSE, 0)
            self.emit_op(OpCode.POP) 
            
            for s in stmt.body:
                self.compile_statement(s)
            
            self.emit_op(OpCode.LOOP, start)
            self.chunk.patch_jump(exit_jump)
            self.emit_op(OpCode.POP) 
            
            for jump in self.break_jumps_stack.pop():
                self.chunk.patch_jump(jump)
            self.loop_start_stack.pop()

        elif isinstance(stmt, ast.ForStmt):
            self.break_jumps_stack.append([])
            
            self.compile_expression(stmt.iterable)
            self.emit_op(OpCode.GET_ITER)
            
            start = len(self.chunk.code)
            self.loop_start_stack.append(start)
            
            exit_jump = self.emit_op(OpCode.FOR_ITER, 0)
            
            if self.scope_depth > 0:
                try:
                    local_idx = self.locals.index(stmt.item_name)
                    self.emit_op(OpCode.SET_LOCAL, local_idx)
                except ValueError:
                    self.locals.append(stmt.item_name)
                    self.emit_op(OpCode.SET_LOCAL, len(self.locals) - 1)
            else:
                idx = self.chunk.add_constant(stmt.item_name)
                self.emit_op(OpCode.SET_GLOBAL, idx)
            self.emit_op(OpCode.POP) 
            
            for s in stmt.body:
                self.compile_statement(s)
            
            self.emit_op(OpCode.LOOP, start)
            self.chunk.patch_jump(exit_jump)
            
            for jump in self.break_jumps_stack.pop():
                self.chunk.patch_jump(jump)
            self.loop_start_stack.pop()

        elif isinstance(stmt, ast.BreakStmt):
            if not self.break_jumps_stack:
                raise SyntaxError("Cannot use 'break' outside of loop")
            jump = self.emit_op(OpCode.JUMP, 0)
            self.break_jumps_stack[-1].append(jump)

        elif isinstance(stmt, ast.ContinueStmt):
            if not self.loop_start_stack:
                raise SyntaxError("Cannot use 'continue' outside of loop")
            self.emit_op(OpCode.LOOP, self.loop_start_stack[-1])

        elif isinstance(stmt, ast.ExprStmt):
            self.compile_expression(stmt.expression)
            self.emit_op(OpCode.POP)

        elif isinstance(stmt, ast.ReturnStmt):
            if stmt.expression:
                self.compile_expression(stmt.expression)
            else:
                self.emit_op(OpCode.PUSH_CONST, self.chunk.add_constant(None))
            self.emit_op(OpCode.RETURN)

        elif isinstance(stmt, ast.YieldStmt):
            self.emit_op(OpCode.YIELD)

    def compile_assign_target(self, target):
        if isinstance(target, ast.VariableExpr):
            if self.scope_depth > 0:
                try:
                    local_idx = self.locals.index(target.name)
                    self.emit_op(OpCode.SET_LOCAL, local_idx)
                    return
                except ValueError:
                    pass
            idx = self.chunk.add_constant(target.name)
            self.emit_op(OpCode.SET_GLOBAL, idx)
        elif isinstance(target, ast.GetExpr):
            self.compile_expression(target.object)
            idx = self.chunk.add_constant(target.name)
            self.emit_op(OpCode.SET_ATTR, idx)
        elif isinstance(target, ast.IndexExpr):
            self.compile_expression(target.object)
            self.compile_expression(target.index)
            self.emit_op(OpCode.INDEX_SET)
        else:
            raise SyntaxError(f"Invalid assignment target: {target}")

    def compile_expression(self, expr):
        if expr.line: self.current_line = expr.line
        if isinstance(expr, ast.LiteralExpr):
            if expr.value is None:
                self.emit_op(OpCode.PUSH_CONST, self.chunk.add_constant(None))
            elif expr.value is True:
                self.emit_op(OpCode.PUSH_TRUE)
            elif expr.value is False:
                self.emit_op(OpCode.PUSH_FALSE)
            else:
                idx = self.chunk.add_constant(expr.value)
                self.emit_op(OpCode.PUSH_CONST, idx)
                
        elif isinstance(expr, ast.ListExpr):
            for element in expr.elements:
                self.compile_expression(element)
            self.emit_op(OpCode.BUILD_LIST, len(expr.elements))
            
        elif isinstance(expr, ast.DictExpr):
            for key, value in zip(expr.keys, expr.values):
                self.compile_expression(key)
                self.compile_expression(value)
            self.emit_op(OpCode.BUILD_MAP, len(expr.keys))
            
        elif isinstance(expr, ast.VariableExpr):
            if self.scope_depth > 0:
                try:
                    local_idx = self.locals.index(expr.name)
                    self.emit_op(OpCode.GET_LOCAL, local_idx)
                    return
                except ValueError:
                    pass
            
            idx = self.chunk.add_constant(expr.name)
            self.emit_op(OpCode.GET_GLOBAL, idx)
            
        elif isinstance(expr, ast.BinaryExpr):
            op = expr.operator
            if op == TokenType.AND:
                self.compile_expression(expr.left)
                jump = self.emit_op(OpCode.JUMP_IF_FALSE, 0)
                self.emit_op(OpCode.POP)
                self.compile_expression(expr.right)
                self.chunk.patch_jump(jump)
            elif op == TokenType.OR:
                self.compile_expression(expr.left)
                jump = self.emit_op(OpCode.JUMP_IF_TRUE, 0)
                self.emit_op(OpCode.POP)
                self.compile_expression(expr.right)
                self.chunk.patch_jump(jump)
            else:
                self.compile_expression(expr.left)
                self.compile_expression(expr.right)
                
                mapping = {
                    TokenType.PLUS: OpCode.ADD,
                    TokenType.MINUS: OpCode.SUB,
                    TokenType.STAR: OpCode.MUL,
                    TokenType.SLASH: OpCode.DIV,
                    TokenType.EQUAL_EQUAL: OpCode.EQUAL,
                    TokenType.BANG_EQUAL: OpCode.NOT_EQUAL,
                    TokenType.GREATER: OpCode.GREATER,
                    TokenType.GREATER_EQUAL: OpCode.GREATER_EQUAL,
                    TokenType.LESS: OpCode.LESS,
                    TokenType.LESS_EQUAL: OpCode.LESS_EQUAL,
                }
                if op in mapping:
                    self.emit_op(mapping[op])
                else:
                    raise SyntaxError(f"Unknown binary operator: {op}")
                    
        elif isinstance(expr, ast.UnaryExpr):
            self.compile_expression(expr.right)
            if expr.operator == TokenType.MINUS:
                self.emit_op(OpCode.NEGATE)
            elif expr.operator == TokenType.BANG or expr.operator == TokenType.NOT:
                self.emit_op(OpCode.NOT)
                
        elif isinstance(expr, ast.CallExpr):
            self.compile_expression(expr.callee)
            for arg in expr.arguments:
                self.compile_expression(arg)
            
            if expr.keyword_arguments:
                kw_names = []
                for name, val in expr.keyword_arguments.items():
                    self.compile_expression(val)
                    kw_names.append(name)
                self.emit_op(OpCode.CALL_KW, (len(expr.arguments), kw_names))
            else:
                self.emit_op(OpCode.CALL, len(expr.arguments))
                
        elif isinstance(expr, ast.GetExpr):
            self.compile_expression(expr.object)
            idx = self.chunk.add_constant(expr.name)
            self.emit_op(OpCode.GET_ATTR, idx)
            
        elif isinstance(expr, ast.IndexExpr):
            self.compile_expression(expr.object)
            self.compile_expression(expr.index)
            self.emit_op(OpCode.INDEX_GET)
