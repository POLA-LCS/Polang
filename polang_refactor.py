from sys import argv
from icecream import ic as DEBUG

TABS = 4

def get_file_content(file_path: str):
    with open(file_path, 'r') as file:
        return file.read().replace('\n', '\0')
    
def get_line_info(line: str) -> tuple[int, int]:
    if line == '':
        return
    indentation = 0
    space_count = 0
    while line[0] == ' ':
        space_count += 1
        if space_count >= TABS:
            indentation += 1
            space_count = 0
        line = line[1:]
    return (indentation, space_count, line)
    
T_LITERAL_INTEGER = 'LIT_INT'
class Token:
    def __init__(self, type: str, value: str | None = None):
        self.type = type
        self.value = value
    
    def __repr__(self) -> str:
        if self.value is None:
            return f'Token({self.type})'
        return f'Token({self.type}, {self.value})'
    
class Lexer:
    def __init__(self, code: str):
        self.code = code
        self.length = len(self.code)
        self.pos = 0
    
    def tokenize_number(self) -> Token:
        number = ''
        while self.pos < self.length and self.code[self.pos].isdigit():
            number += self.code[self.pos]
            self.pos += 1
        return Token(T_LITERAL_INTEGER, number)
            
    def get_next_token(self):
        while self.pos < self.length:
            current = self.code[self.pos]
            if current == '\0':
                self.pos += 1
                return Token('EOL')
            if current.isdigit():
                return self.tokenize_number()
            if current == '+':
                self.pos += 1
                return Token('PLUS_OP')
            if current == '-':
                self.pos += 1
                return Token('SUB_OP')
            if current == '=':
                self.pos += 1
                return Token('EQUAL_OP')
            if current == '(':
                self.pos += 1
                return Token('LPAREN')
            if current == ')':
                self.pos += 1
                return Token('RPAREN')
            else:
                self.pos += 1
       
file_content = get_file_content(argv[1])
file_content_info = [get_line_info(line) for line in file_content.split('\0')]
lexer = Lexer(file_content)

DEBUG(
    lexer.get_next_token()
)