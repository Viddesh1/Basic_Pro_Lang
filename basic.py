########################################
# IMPORTS
########################################

from string_with_arrows import *

########################################
# CONSTANTS
########################################

DIGITS = "0123456789"

########################################
# ERROR
########################################

class Error:
    "Creating a custom error class"
    def __init__(self, pos_start, pos_end, error_name, details):
        self.pos_start = pos_start
        self.pos_end = pos_end
        self.error_name = error_name
        self.details = details

    def as_string(self):
        result = f"{self.error_name}: {self.details}\n"
        result += f"File {self.pos_start.fn}, line {self.pos_start.ln + 1} "
        result += "\n\n" + string_with_arrows(self.pos_start.ftxt, self.pos_start, self.pos_end)
        return result
    
# Creating a subclass of the error
class IllegalCharError(Error):
    def __init__(self, pos_start, pos_end, details):
        super().__init__(pos_start, pos_end, "Illegal Characters", details = details)

# Creating a custom error class for below terminal output.
# basic terminal > 123 12 +
# INT:123
class InvalidSyntaxError(Error):
    def __init__(self, pos_start, pos_end, details = ""):
        super().__init__(pos_start, pos_end, error_name = "Invalid Syntax Error", details = details)


########################################
# POSITION
########################################

class Position:
    def __init__(self, idx, ln, col, fn, ftxt):
        self.idx = idx
        self.ln = ln
        self.col = col
        self.fn = fn
        self.ftxt = ftxt

    def advance(self, current_char = None):
        self.idx += 1
        self.col += 1

        if current_char == "\n":
            self.ln += 1
            self.col = 0

        return self
    
    def copy(self):
        # Creates a copy of the position
        return Position(self.idx, self.ln, self.col, self.fn, self.ftxt)

########################################
# TOKENS
########################################

TT_INT = "INT"
TT_FLOAT = "FLOAT"
TT_PLUS = "PLUS"
TT_MINUS = "MINUS"
TT_MUL = "MUL"
TT_DIV = "DIV"
TT_LPAREN = "LPAREN"
TT_RPAREN = "RPAREN"
TT_EOF = "EOF" # End of the File inside the parser.

class Token:
    def __init__(self, type, value = None, pos_start = None, pos_end = None):
        self.type = type
        self.value = value

        # This is implemented because we want out custom error class from token.
        if pos_start is not None:
            self.pos_start = pos_start.copy()
            self.pos_end = pos_start.copy()
            self.pos_end.advance()

        if pos_end is not None:
            self.pos_end = pos_end.copy()

    def __repr__(self):
        if self.value:
            return f"{self.type}:{self.value}"
        else:
            return f"{self.type}"
        
########################################
# LEXER
########################################

class Lexer:
    def __init__(self, fn, text):
        self.fn = fn
        self.text = text
        self.pos = Position(-1, 0, -1, fn, text) # Position(Index, Row, Column, file name, terminal text)
        self.current_char = None
        self.advance()

    def advance(self):
        "Advance to the next character in the text"
        self.pos.advance(self.current_char)
        self.current_char = self.text[self.pos.idx] if self.pos.idx < len(self.text) else None

    def make_tokens(self):
        tokens = []

        while self.current_char != None:
            if self.current_char in " \t": # Skipping space and tab space.
                self.advance()
            elif self.current_char in DIGITS:
                tokens.append(self.make_number())
            elif self.current_char == "+":
                tokens.append(Token(TT_PLUS, pos_start = self.pos))
                self.advance()
            elif self.current_char == "-":
                tokens.append(Token(TT_MINUS, pos_start = self.pos))
                self.advance()
            elif self.current_char == "*":
                tokens.append(Token(TT_MUL, pos_start = self.pos))
                self.advance()
            elif self.current_char == "/":
                tokens.append(Token(TT_DIV, pos_start = self.pos))
                self.advance()
            elif self.current_char == "(":
                tokens.append(Token(TT_LPAREN, pos_start = self.pos))
                self.advance()
            elif self.current_char == ")":
                tokens.append(Token(TT_RPAREN, pos_start = self.pos))
                self.advance()
            else: # Illegal characters
                pos_start = self.pos.copy() # Creating a copy of the position.
                char = self.current_char
                self.advance()
                return [], IllegalCharError(pos_start, self.pos, "'" + char + "'")
            
        tokens.append(Token(TT_EOF, pos_start = self.pos))
        return tokens, None


    def make_number(self):
        """ Making the number either integer or float"""
        num_str = ""
        dot_count = 0
        pos_start = self.pos.copy()
        
        while self.current_char != None and self.current_char in DIGITS + ".":
            if self.current_char == ".":
                if dot_count == 1:
                    break
                dot_count += 1
                num_str += "."
            else:
                num_str += self.current_char
            self.advance()

        if dot_count == 0:
            return Token(TT_INT, int(num_str), pos_start, self.pos)
        else:
            return Token(TT_FLOAT, float(num_str), pos_start, self.pos)
        

#######################################
# NODES
#######################################
# Creating a class called NumberNode for parser to parse the tokens in the form of nodes.
class NumberNode:
    def __init__(self, tok):
        self.tok = tok

    def __repr__(self):
        return f"{self.tok}"
    
# Creating the class BinOpNode to perform add, subtract, multiply and divide operations
class BinOpNode:
    def __init__(self, left_tok, op_tok, right_tok):
        self.left_tok = left_tok
        self.op_tok = op_tok
        self.right_tok = right_tok

    def __repr__(self):
        return f"({self.left_tok}, {self.op_tok}, {self.right_tok})"
    
# TODO: Will add one more Node class. 

# Now!, It is time to add error to the parser.
#######################################
# PARSER RESULT
#######################################
# Instead of returing the NumberNode() in each function we can return an parse result.
# So, Parse result will check if there is any errors.

class ParseResult:
    def __init__(self):
        self.error = None
        self.node = None

    def register(self, res):
        # This is going to check the parse result and node.
        if isinstance(res, ParseResult):
            if res.error:
                self.error = res.error
            return res.node
        
        return res

    def success(self, node):
        self.node = node
        return self

    def failure(self, error):
        self.error = error
        return self


#######################################
# PARSER
#######################################

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.tok_idx = -1
        self.advance()

    def advance(self):
        self.tok_idx += 1
        if self.tok_idx < len(self.tokens):
            self.current_tok = self.tokens[self.tok_idx]
        return self.current_tok
    
    def parse(self):
        res = self.expr()
        if not res.error and self.current_tok.type != TT_EOF:
            return res.failure(
                InvalidSyntaxError(
                self.current_tok.pos_start,
                self.current_tok.pos_end,
                "Expected '+', '-', '*' or '/'"
                )
                )
        return res
    
    ######
    # Creating methods according to the grammer of the programming language
    def factor(self):
        res = ParseResult()
        tok = self.current_tok

        if tok.type in (TT_INT, TT_FLOAT):
            res.register(self.advance())
            return res.success(NumberNode(tok))
        
        return res.failure(
            InvalidSyntaxError(
            tok.pos_start, 
            tok.pos_end, 
            details = "Expected int or float")
            )
        
    def term(self):
        return self.bin_op(self.factor, (TT_MUL, TT_DIV))
    
    def expr(self):
        return self.bin_op(self.term, (TT_PLUS, TT_MINUS))

    #############

    def bin_op(self, func, ops):
        res = ParseResult()
        left = res.register(func())
        if res.error:
            return res

        while self.current_tok.type in ops:
            op_tok = self.current_tok
            res.register(self.advance())
            right = res.register(func())
            if res.error:
                return res
            left = BinOpNode(left, op_tok, right)
        
        return res.success(left)


#######################################
# RUN
#######################################

def run(fn, text):
    lexer = Lexer(fn, text)
    tokens, error = lexer.make_tokens()
    if error:
        return None, error

    # Generate Abstract Syntax Tree
    parser = Parser(tokens)
    ast = parser.parse()

    return ast.node, ast.error