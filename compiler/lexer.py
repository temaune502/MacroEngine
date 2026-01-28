import enum
import re

class TokenType(enum.Enum):
    # Keywords
    LET = "let"
    SET = "set"
    FUNC = "func"
    IF = "if"
    ELIF = "elif"
    ELSE = "else"
    WHILE = "while"
    FOR = "for"
    IN = "in"
    RETURN = "return"
    BREAK = "break"
    CONTINUE = "continue"
    NOT = "not"
    AND = "and"
    OR = "or"
    TRUE = "true"
    FALSE = "false"
    YIELD = "yield"

    # Literals
    IDENTIFIER = "IDENTIFIER"
    NUMBER = "NUMBER"
    STRING = "STRING"

    # Operators
    PLUS = "+"
    PLUS_PLUS = "++"
    PLUS_EQUAL = "+="
    MINUS = "-"
    MINUS_MINUS = "--"
    MINUS_EQUAL = "-="
    STAR = "*"
    STAR_EQUAL = "*="
    SLASH = "/"
    SLASH_EQUAL = "/="
    EQUAL = "="
    EQUAL_EQUAL = "=="
    BANG_EQUAL = "!="
    BANG = "!"
    GREATER = ">"
    GREATER_EQUAL = ">="
    LESS = "<"
    LESS_EQUAL = "<="

    # Punctuation
    LPAREN = "("
    RPAREN = ")"
    COLON = ":"
    COMMA = ","
    DOT = "."
    LBRACKET = "["
    RBRACKET = "]"
    LBRACE = "{"
    RBRACE = "}"

    # Structure
    INDENT = "INDENT"
    DEDENT = "DEDENT"
    NEWLINE = "NEWLINE"
    META = "META"
    EOF = "EOF"

class Token:
    def __init__(self, type, value, line, column):
        self.type = type
        self.value = value
        self.line = line
        self.column = column

    def __repr__(self):
        return f"Token({self.type}, {repr(self.value)}, {self.line}:{self.column})"

class Lexer:
    def __init__(self, source):
        self.source = source
        self.tokens = []
        self.start = 0
        self.current = 0
        self.line = 1
        self.column = 1
        
        self.indent_stack = [0]
        
        self.keywords = {
            "let": TokenType.LET,
            "set": TokenType.SET,
            "func": TokenType.FUNC,
            "if": TokenType.IF,
            "elif": TokenType.ELIF,
            "else": TokenType.ELSE,
            "while": TokenType.WHILE,
            "for": TokenType.FOR,
            "in": TokenType.IN,
            "return": TokenType.RETURN,
            "break": TokenType.BREAK,
            "continue": TokenType.CONTINUE,
            "not": TokenType.NOT,
            "and": TokenType.AND,
            "or": TokenType.OR,
            "true": TokenType.TRUE,
            "false": TokenType.FALSE,
            "yield": TokenType.YIELD,
        }

    def tokenize(self):
        # Pre-process multiline @meta
        source = self.source
        meta_pattern = r'@meta\s*\{'
        meta_matches = list(re.finditer(meta_pattern, source))
        
        # We'll replace @meta blocks with placeholders to not interfere with line-by-line tokenization
        # then inject META tokens at correct positions
        meta_tokens_to_inject = []
        
        for match in reversed(meta_matches):
            start_pos = match.start()
            # Find matching brace
            brace_count = 0
            found_end = False
            for i in range(match.end() - 1, len(source)):
                if source[i] == '{': brace_count += 1
                elif source[i] == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        meta_full_content = source[start_pos:i+1]
                        # Calculate line/col
                        prefix = source[:start_pos]
                        line = prefix.count('\n') + 1
                        last_nl = prefix.rfind('\n')
                        col = start_pos - last_nl if last_nl != -1 else start_pos + 1
                        
                        meta_tokens_to_inject.append((line, col, meta_full_content))
                        
                        # Replace with spaces to maintain line/col for other tokens
                        replacement = ' ' * len(meta_full_content)
                        source = source[:start_pos] + replacement + source[i+1:]
                        found_end = True
                        break
            if not found_end:
                # Let it fail during normal tokenization if not found
                pass

        lines = source.splitlines()
        for i, line_content in enumerate(lines):
            self.line = i + 1
            self.column = 1
            self.current = 0
            
            # Inject META tokens for this line
            for m_line, m_col, m_content in [t for t in meta_tokens_to_inject if t[0] == self.line]:
                self.tokens.append(Token(TokenType.META, m_content, m_line, m_col))
            
            # Handle indentation at the start of the line
            # If the line is now all spaces (because of @meta replacement), skip it
            if not line_content.strip() or line_content.strip().startswith("#"):
                continue
            
            indent = 0
            for char in line_content:
                if char == ' ':
                    indent += 1
                elif char == '\t':
                    indent += 4 # Assume 4 spaces for tab
                else:
                    break
            
            if indent > self.indent_stack[-1]:
                self.indent_stack.append(indent)
                self.tokens.append(Token(TokenType.INDENT, indent, self.line, 1))
            elif indent < self.indent_stack[-1]:
                while indent < self.indent_stack[-1]:
                    self.indent_stack.pop()
                    self.tokens.append(Token(TokenType.DEDENT, indent, self.line, 1))
                if indent != self.indent_stack[-1]:
                    raise SyntaxError(f"Invalid indentation at line {self.line}")

            self.tokenize_line(line_content[indent:], indent + 1)
            self.tokens.append(Token(TokenType.NEWLINE, "\n", self.line, len(line_content) + 1))

        # Close any remaining indents
        while len(self.indent_stack) > 1:
            self.indent_stack.pop()
            self.tokens.append(Token(TokenType.DEDENT, 0, self.line + 1, 1))
            
        self.tokens.append(Token(TokenType.EOF, "", self.line + 1, 1))
        return self.tokens

    def tokenize_line(self, content, start_col):
        i = 0
        while i < len(content):
            char = content[i]
            col = start_col + i
            
            if char.isspace():
                i += 1
                continue
                
            if char == '#': # Comment
                break
                
            if char == '(':
                self.tokens.append(Token(TokenType.LPAREN, "(", self.line, col))
                i += 1
            elif char == ')':
                self.tokens.append(Token(TokenType.RPAREN, ")", self.line, col))
                i += 1
            elif char == ':':
                self.tokens.append(Token(TokenType.COLON, ":", self.line, col))
                i += 1
            elif char == ',':
                self.tokens.append(Token(TokenType.COMMA, ",", self.line, col))
                i += 1
            elif char == '.':
                self.tokens.append(Token(TokenType.DOT, ".", self.line, col))
                i += 1
            elif char == '[':
                self.tokens.append(Token(TokenType.LBRACKET, "[", self.line, col))
                i += 1
            elif char == ']':
                self.tokens.append(Token(TokenType.RBRACKET, "]", self.line, col))
                i += 1
            elif char == '{':
                self.tokens.append(Token(TokenType.LBRACE, "{", self.line, col))
                i += 1
            elif char == '}':
                self.tokens.append(Token(TokenType.RBRACE, "}", self.line, col))
                i += 1
            elif char == '+':
                if i + 1 < len(content) and content[i+1] == '+':
                    self.tokens.append(Token(TokenType.PLUS_PLUS, "++", self.line, col))
                    i += 2
                elif i + 1 < len(content) and content[i+1] == '=':
                    self.tokens.append(Token(TokenType.PLUS_EQUAL, "+=", self.line, col))
                    i += 2
                else:
                    self.tokens.append(Token(TokenType.PLUS, "+", self.line, col))
                    i += 1
            elif char == '-':
                if i + 1 < len(content) and content[i+1] == '-':
                    self.tokens.append(Token(TokenType.MINUS_MINUS, "--", self.line, col))
                    i += 2
                elif i + 1 < len(content) and content[i+1] == '=':
                    self.tokens.append(Token(TokenType.MINUS_EQUAL, "-=", self.line, col))
                    i += 2
                else:
                    self.tokens.append(Token(TokenType.MINUS, "-", self.line, col))
                    i += 1
            elif char == '*':
                if i + 1 < len(content) and content[i+1] == '=':
                    self.tokens.append(Token(TokenType.STAR_EQUAL, "*=", self.line, col))
                    i += 2
                else:
                    self.tokens.append(Token(TokenType.STAR, "*", self.line, col))
                    i += 1
            elif char == '/':
                if i + 1 < len(content) and content[i+1] == '=':
                    self.tokens.append(Token(TokenType.SLASH_EQUAL, "/=", self.line, col))
                    i += 2
                else:
                    self.tokens.append(Token(TokenType.SLASH, "/", self.line, col))
                    i += 1
            elif char == '=':
                if i + 1 < len(content) and content[i+1] == '=':
                    self.tokens.append(Token(TokenType.EQUAL_EQUAL, "==", self.line, col))
                    i += 2
                else:
                    self.tokens.append(Token(TokenType.EQUAL, "=", self.line, col))
                    i += 1
            elif char == '!':
                if i + 1 < len(content) and content[i+1] == '=':
                    self.tokens.append(Token(TokenType.BANG_EQUAL, "!=", self.line, col))
                    i += 2
                else:
                    self.tokens.append(Token(TokenType.BANG, "!", self.line, col))
                    i += 1
            elif char == '>':
                if i + 1 < len(content) and content[i+1] == '=':
                    self.tokens.append(Token(TokenType.GREATER_EQUAL, ">=", self.line, col))
                    i += 2
                else:
                    self.tokens.append(Token(TokenType.GREATER, ">", self.line, col))
                    i += 1
            elif char == '<':
                if i + 1 < len(content) and content[i+1] == '=':
                    self.tokens.append(Token(TokenType.LESS_EQUAL, "<=", self.line, col))
                    i += 2
                else:
                    self.tokens.append(Token(TokenType.LESS, "<", self.line, col))
                    i += 1
            elif char == '@':
                # Unexpected @ outside of pre-processed @meta
                raise SyntaxError(f"Unexpected character '@' at line {self.line}:{col}")
            elif char == '"':
                # String literal
                start_i = i
                i += 1
                string_val = ""
                while i < len(content) and content[i] != '"':
                    string_val += content[i]
                    i += 1
                if i >= len(content):
                    raise SyntaxError(f"Unterminated string at line {self.line}:{col}")
                i += 1
                self.tokens.append(Token(TokenType.STRING, string_val, self.line, col))
            elif char.isdigit():
                # Number literal
                start_i = i
                num_str = ""
                while i < len(content) and (content[i].isdigit() or content[i] == '.'):
                    num_str += content[i]
                    i += 1
                self.tokens.append(Token(TokenType.NUMBER, float(num_str), self.line, col))
            elif char.isalpha() or char == '_':
                # Identifier or Keyword
                start_i = i
                ident = ""
                while i < len(content) and (content[i].isalnum() or content[i] == '_'):
                    ident += content[i]
                    i += 1
                
                if ident in self.keywords:
                    self.tokens.append(Token(self.keywords[ident], ident, self.line, col))
                else:
                    self.tokens.append(Token(TokenType.IDENTIFIER, ident, self.line, col))
            else:
                raise SyntaxError(f"Unexpected character '{char}' at line {self.line}:{col}")
