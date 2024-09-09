from types import FunctionType as function

# POLANG TYPE SUPPORT
Number = int | float
Any = str | Number | list | None
STRING = 'string'
NUMBER = 'number'
LIST = 'list'
NONE = 'none'
ANY = 'any'

# A polang value representation
class Value:
    def __init__(self, value: Any = None, const: bool = False):
        self.value = value
        self.const = const
        
    @property
    def type(self):
        if self.value is None:
            return NONE
        if type(self.value) in [int, float]:
            return NUMBER
        if isinstance(self.value, str):
            return STRING
        if isinstance(self.value, list):
            return LIST
        return ANY
        
    def __repr__(self) -> str:
        return f'({self.value}: {self.type})'
    
    def __str__(self) -> str:
        if self.value is None:
            return 'none'
        return str(self.value)
    
class Macro:
    def __init__(self, argc: int, code: list[str]):
        self.argc = argc
        self.code = code
        
    def __repr__(self) -> str:
        return f'f({self.argc})'