from .lexer import TokenType, Token
from . import ast_nodes as ast

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.current = 0

    def parse(self):
        statements = []
        metadata = {}
        while not self.is_at_end():
            if self.match(TokenType.META):
                meta_token = self.previous()
                try:
                    import json
                    # Clean meta content from @meta {...} to {...}
                    meta_str = meta_token.value
                    if meta_str.startswith("@meta"):
                        meta_str = meta_str[5:].strip()
                    
                    # Basic JSON-like parsing for metadata
                    # We can use json.loads if the user follows JSON format
                    # or a simpler parser. Let's try json first.
                    try:
                        # Replace single quotes with double quotes for JSON
                        json_str = meta_str.replace("'", '"')
                        # Add double quotes to keys if they don't have them
                        import re
                        # More robust regex for keys (handling spaces and nested braces)
                        json_str = re.sub(r'(\{|,)\s*(\w+)\s*:', r'\1"\2":', json_str)
                        # Handle boolean/null
                        json_str = json_str.replace("true", "True").replace("false", "False").replace("null", "None")
                        
                        # Use eval for a more flexible "Python-dict-like" parsing 
                        # but safely via literal_eval if possible or just json.loads
                        try:
                            import ast as py_ast
                            data = py_ast.literal_eval(json_str)
                        except:
                            # Fallback to json after fixing booleans back
                            json_str = json_str.replace("True", "true").replace("False", "false").replace("None", "null")
                            data = json.loads(json_str)
                        
                        metadata.update(data)
                    except:
                        # If JSON fails, just store the raw string for now or handle simple cases
                        pass
                except Exception as e:
                    print(f"Warning: Failed to parse metadata at line {meta_token.line}: {e}")
                continue

            stmt = self.declaration()
            if stmt:
                statements.append(stmt)
        return ast.Program(statements, metadata=metadata)

    def declaration(self):
        try:
            line = self.peek().line
            column = self.peek().column
            stmt = None
            if self.match(TokenType.FUNC): stmt = self.function_declaration()
            elif self.match(TokenType.LET): stmt = self.var_declaration()
            elif self.match(TokenType.SET): stmt = self.var_assignment()
            else: stmt = self.statement()
            
            if stmt and not stmt.line:
                stmt.line = line
                stmt.column = column
            return stmt
        except Exception as e:
            self.synchronize()
            print(f"Error: {e}")
            return None

    def function_declaration(self):
        token = self.previous() # FUNC token
        name = self.consume(TokenType.IDENTIFIER, "Expect function name.").value
        self.consume(TokenType.LPAREN, "Expect '(' after function name.")
        parameters = []
        defaults = {}
        kwargs_param = None
        
        if not self.check(TokenType.RPAREN):
            while True:
                if self.match(TokenType.STAR):
                    self.consume(TokenType.STAR, "Expect second '*' for kwargs.")
                    kwargs_param = self.consume(TokenType.IDENTIFIER, "Expect kwargs parameter name.").value
                    break
                
                param_name = self.consume(TokenType.IDENTIFIER, "Expect parameter name.").value
                parameters.append(param_name)
                
                if self.match(TokenType.EQUAL):
                    defaults[param_name] = self.expression()
                
                if not self.match(TokenType.COMMA): break
                
        self.consume(TokenType.RPAREN, "Expect ')' after parameters.")
        self.consume(TokenType.COLON, "Expect ':' before function body.")
        body = self.block()
        # Add implicit return None to ensure frame is popped
        body.append(ast.ReturnStmt(ast.LiteralExpr(None, line=token.line), line=token.line))
        return ast.FunctionDef(name, parameters, defaults, body, kwargs_param, line=token.line, column=token.column)

    def var_declaration(self):
        token = self.previous() # LET token
        name = self.consume(TokenType.IDENTIFIER, "Expect variable name.").value
        self.consume(TokenType.EQUAL, "Expect '=' after variable name.")
        initializer = self.expression()
        self.consume(TokenType.NEWLINE, "Expect newline after variable declaration.")
        return ast.VarDecl(name, initializer, line=token.line, column=token.column)

    def var_assignment(self):
        token = self.previous() # SET token
        target = self.call() # This will parse IDENTIFIER or IDENTIFIER.IDENTIFIER etc.
        
        # Handle increment/decrement
        if self.match(TokenType.PLUS_PLUS):
            self.consume(TokenType.NEWLINE, "Expect newline after '++'.")
            # x++ is equivalent to x = x + 1
            expression = ast.BinaryExpr(target, TokenType.PLUS, ast.LiteralExpr(1.0, line=token.line), line=token.line)
            return ast.VarAssign(target, expression, line=token.line, column=token.column)
        if self.match(TokenType.MINUS_MINUS):
            self.consume(TokenType.NEWLINE, "Expect newline after '--'.")
            # x-- is equivalent to x = x - 1
            expression = ast.BinaryExpr(target, TokenType.MINUS, ast.LiteralExpr(1.0, line=token.line), line=token.line)
            return ast.VarAssign(target, expression, line=token.line, column=token.column)

        # Handle compound assignments
        operator = None
        if self.match(TokenType.PLUS_EQUAL): operator = TokenType.PLUS
        elif self.match(TokenType.MINUS_EQUAL): operator = TokenType.MINUS
        elif self.match(TokenType.STAR_EQUAL): operator = TokenType.STAR
        elif self.match(TokenType.SLASH_EQUAL): operator = TokenType.SLASH
        elif self.match(TokenType.EQUAL): operator = None
        else: raise SyntaxError(f"Expect '=' or compound assignment after target at {self.peek()}")

        expression = self.expression()
        if operator:
            # x += 1 is equivalent to x = x + 1
            expression = ast.BinaryExpr(target, operator, expression, line=token.line, column=token.column)
            
        self.consume(TokenType.NEWLINE, "Expect newline after variable assignment.")
        return ast.VarAssign(target, expression, line=token.line, column=token.column)

    def statement(self):
        if self.match(TokenType.IF): return self.if_statement()
        if self.match(TokenType.WHILE): return self.while_statement()
        if self.match(TokenType.FOR): return self.for_statement()
        if self.match(TokenType.RETURN): return self.return_statement()
        if self.match(TokenType.BREAK): return self.break_statement()
        if self.match(TokenType.CONTINUE): return self.continue_statement()
        if self.match(TokenType.YIELD): return self.yield_statement()
        if self.match(TokenType.NEWLINE): return None # Skip empty lines
        return self.expression_statement()

    def break_statement(self):
        token = self.previous()
        self.consume(TokenType.NEWLINE, "Expect newline after 'break'.")
        return ast.BreakStmt(line=token.line, column=token.column)

    def continue_statement(self):
        token = self.previous()
        self.consume(TokenType.NEWLINE, "Expect newline after 'continue'.")
        return ast.ContinueStmt(line=token.line, column=token.column)

    def yield_statement(self):
        token = self.previous() # YIELD
        self.consume(TokenType.NEWLINE, "Expect newline after 'yield'.")
        return ast.YieldStmt(line=token.line, column=token.column)

    def if_statement(self):
        token = self.previous() # IF
        condition = self.expression()
        self.consume(TokenType.COLON, "Expect ':' after if condition.")
        then_branch = self.block()
        
        elif_branches = []
        while self.match(TokenType.ELIF):
            elif_cond = self.expression()
            self.consume(TokenType.COLON, "Expect ':' after elif condition.")
            elif_body = self.block()
            elif_branches.append((elif_cond, elif_body))
            
        else_branch = None
        if self.match(TokenType.ELSE):
            self.consume(TokenType.COLON, "Expect ':' after else.")
            else_branch = self.block()
            
        return ast.IfStmt(condition, then_branch, elif_branches, else_branch, line=token.line, column=token.column)

    def while_statement(self):
        token = self.previous() # WHILE
        condition = self.expression()
        self.consume(TokenType.COLON, "Expect ':' after while condition.")
        body = self.block()
        return ast.WhileStmt(condition, body, line=token.line, column=token.column)

    def for_statement(self):
        token = self.previous() # FOR
        item_name = self.consume(TokenType.IDENTIFIER, "Expect variable name after 'for'.").value
        self.consume(TokenType.IN, "Expect 'in' after variable name.")
        iterable = self.expression()
        self.consume(TokenType.COLON, "Expect ':' after iterable.")
        body = self.block()
        return ast.ForStmt(item_name, iterable, body, line=token.line, column=token.column)

    def return_statement(self):
        token = self.previous() # RETURN
        value = None
        if not self.check(TokenType.NEWLINE):
            value = self.expression()
        self.consume(TokenType.NEWLINE, "Expect newline after return.")
        return ast.ReturnStmt(value, line=token.line, column=token.column)

    def expression_statement(self):
        expr = self.expression()
        self.consume(TokenType.NEWLINE, "Expect newline after expression.")
        return ast.ExprStmt(expr, line=expr.line, column=expr.column)

    def block(self):
        self.consume(TokenType.NEWLINE, "Expect newline before block.")
        self.consume(TokenType.INDENT, "Expect indentation for block.")
        statements = []
        while not self.check(TokenType.DEDENT) and not self.is_at_end():
            stmt = self.declaration()
            if stmt:
                statements.append(stmt)
        self.consume(TokenType.DEDENT, "Expect dedent at end of block.")
        return statements

    # Expressions
    def expression(self):
        return self.logical_or()

    def logical_or(self):
        expr = self.logical_and()
        while self.match(TokenType.OR):
            operator = self.previous()
            right = self.logical_and()
            expr = ast.BinaryExpr(expr, operator.type, right, line=operator.line, column=operator.column)
        return expr

    def logical_and(self):
        expr = self.equality()
        while self.match(TokenType.AND):
            operator = self.previous()
            right = self.equality()
            expr = ast.BinaryExpr(expr, operator.type, right, line=operator.line, column=operator.column)
        return expr

    def equality(self):
        expr = self.comparison()
        while self.match(TokenType.EQUAL_EQUAL, TokenType.BANG_EQUAL):
            operator = self.previous()
            right = self.comparison()
            expr = ast.BinaryExpr(expr, operator.type, right, line=operator.line, column=operator.column)
        return expr

    def comparison(self):
        expr = self.term()
        while self.match(TokenType.GREATER, TokenType.GREATER_EQUAL, TokenType.LESS, TokenType.LESS_EQUAL):
            operator = self.previous()
            right = self.term()
            expr = ast.BinaryExpr(expr, operator.type, right, line=operator.line, column=operator.column)
        return expr

    def term(self):
        expr = self.factor()
        while self.match(TokenType.PLUS, TokenType.MINUS):
            operator = self.previous()
            right = self.factor()
            expr = ast.BinaryExpr(expr, operator.type, right, line=operator.line, column=operator.column)
        return expr

    def factor(self):
        expr = self.unary()
        while self.match(TokenType.STAR, TokenType.SLASH):
            operator = self.previous()
            right = self.unary()
            expr = ast.BinaryExpr(expr, operator.type, right, line=operator.line, column=operator.column)
        return expr

    def unary(self):
        if self.match(TokenType.NOT, TokenType.BANG, TokenType.MINUS):
            operator = self.previous()
            right = self.unary()
            return ast.UnaryExpr(operator.type, right, line=operator.line, column=operator.column)
        return self.call()

    def call(self):
        expr = self.primary()
        while True:
            if self.match(TokenType.LPAREN):
                expr = self.finish_call(expr)
            elif self.match(TokenType.DOT):
                token = self.previous()
                name = self.consume(TokenType.IDENTIFIER, "Expect property name after '.'.").value
                expr = ast.GetExpr(expr, name, line=token.line, column=token.column)
            elif self.match(TokenType.LBRACKET):
                token = self.previous()
                index = self.expression()
                self.consume(TokenType.RBRACKET, "Expect ']' after index.")
                expr = ast.IndexExpr(expr, index, line=token.line, column=token.column)
            else:
                break
        return expr

    def finish_call(self, callee):
        token = self.previous() # LPAREN
        arguments = []
        keyword_arguments = {}
        
        if not self.check(TokenType.RPAREN):
            while True:
                # Check if it's a keyword argument: IDENTIFIER = expression
                if self.check(TokenType.IDENTIFIER) and self.peek_next() and self.peek_next().type == TokenType.EQUAL:
                    name = self.advance().value
                    self.advance() # Consume EQUAL
                    value = self.expression()
                    keyword_arguments[name] = value
                else:
                    if keyword_arguments:
                        raise SyntaxError("Positional argument cannot follow keyword argument")
                    arguments.append(self.expression())
                
                if not self.match(TokenType.COMMA): break
                
        self.consume(TokenType.RPAREN, "Expect ')' after arguments.")
        return ast.CallExpr(callee, arguments, keyword_arguments, line=callee.line, column=callee.column)

    def peek_next(self):
        if self.current + 1 >= len(self.tokens): return None
        return self.tokens[self.current + 1]

    def dict_expression(self):
        token = self.previous() # LBRACE
        keys = []
        values = []
        
        self.consume_optional_newlines()
        
        if not self.check(TokenType.RBRACE):
            while True:
                self.consume_optional_newlines()
                keys.append(self.expression())
                self.consume_optional_newlines()
                self.consume(TokenType.COLON, "Expect ':' after dictionary key.")
                self.consume_optional_newlines()
                values.append(self.expression())
                self.consume_optional_newlines()
                if not self.match(TokenType.COMMA): break
                self.consume_optional_newlines()
                
        self.consume_optional_newlines()
        self.consume(TokenType.RBRACE, "Expect '}' after dictionary elements.")
        return ast.DictExpr(keys, values, line=token.line, column=token.column)

    def list_expression(self):
        token = self.previous() # LBRACKET
        elements = []
        
        self.consume_optional_newlines()
        
        if not self.check(TokenType.RBRACKET):
            while True:
                self.consume_optional_newlines()
                elements.append(self.expression())
                self.consume_optional_newlines()
                if not self.match(TokenType.COMMA): break
                self.consume_optional_newlines()
                
        self.consume_optional_newlines()
        self.consume(TokenType.RBRACKET, "Expect ']' after list elements.")
        return ast.ListExpr(elements, line=token.line, column=token.column)

    def consume_optional_newlines(self):
        while self.match(TokenType.NEWLINE, TokenType.INDENT, TokenType.DEDENT):
            pass

    def primary(self):
        token = self.peek()
        line, col = token.line, token.column
        
        if self.match(TokenType.FALSE): return ast.LiteralExpr(False, line=line, column=col)
        if self.match(TokenType.TRUE): return ast.LiteralExpr(True, line=line, column=col)
        if self.match(TokenType.NUMBER, TokenType.STRING):
            val = self.previous().value
            return ast.LiteralExpr(val, line=line, column=col)
        if self.match(TokenType.LBRACKET): 
            expr = self.list_expression()
            expr.line, expr.column = line, col
            return expr
        
        if self.match(TokenType.LBRACE):
            expr = self.dict_expression()
            expr.line, expr.column = line, col
            return expr
        
        if self.match(TokenType.IDENTIFIER):
            return ast.VariableExpr(self.previous().value, line=line, column=col)

        if self.match(TokenType.LPAREN):
            expr = self.expression()
            self.consume(TokenType.RPAREN, "Expect ')' after expression.")
            return expr
        
        raise SyntaxError(f"Expect expression at {self.peek()}")

    # Helpers
    def match(self, *types):
        for type in types:
            if self.check(type):
                self.advance()
                return True
        return False

    def check(self, type):
        if self.is_at_end(): return False
        return self.peek().type == type

    def advance(self):
        if not self.is_at_end(): self.current += 1
        return self.previous()

    def is_at_end(self):
        return self.peek().type == TokenType.EOF

    def peek(self):
        return self.tokens[self.current]

    def previous(self):
        return self.tokens[self.current - 1]

    def consume(self, type, message):
        if self.check(type): return self.advance()
        raise SyntaxError(f"{message} at {self.peek()}")

    def synchronize(self):
        self.advance()
        while not self.is_at_end():
            if self.previous().type == TokenType.NEWLINE: return
            if self.peek().type in {TokenType.FUNC, TokenType.LET, TokenType.SET, TokenType.IF, TokenType.WHILE, TokenType.RETURN}:
                return
            self.advance()

if __name__ == "__main__":
    from .lexer import Lexer
    import os
    
    example_path = "example.tml"
    if os.path.exists(example_path):
        with open(example_path, "r", encoding="utf-8") as f:
            source = f.read()
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast_tree = parser.parse()
        print("Successfully parsed AST")
    else:
        print(f"File {example_path} not found")
