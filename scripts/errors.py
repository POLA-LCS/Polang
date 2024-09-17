from typing import Optional as opt
from .value import Value

# ERRORS
def ERROR_FORMAT(name: str, state: opt[str] = None, type: opt[str] = None, message: opt[str] = None):
    return f"[{name}ERROR] in {state}. {f'{type}' if type is not None else ''}{f':\n    {message}' if message is not None else ''}\n"
    
def RAISE(error: str):
    """`assert 0, error`"""
    assert 0, error
    
def PARAM_ERROR(message: str, state: opt[str], expected, provided):
    RAISE(ERROR_FORMAT('PARAMETER ', None, state, f'{message}, expected {expected} but {provided} was provided.'))

# ERROR FORMATS
def TYPE_ERROR(left: Value, right: Value, state: str):
    return ERROR_FORMAT('TYPE ', state, 'Types doesn\'t match', f'({left} --> {right})')

def NAME_ERROR(var_name: str, state: str):
    return ERROR_FORMAT('NAME ', state, 'Doesn\'t exists', f'--> {var_name}')

def INDEX_ERROR(message: str, state: str):
    return ERROR_FORMAT('INDEX ', 'Out of range', state, message)
    
def LOGIC_ERROR(type: str, message: str, state: str):
    return ERROR_FORMAT('LOGIC ', state, type, message)

def SYNTAX_ERROR(type: str, message: str, state: str):
    return ERROR_FORMAT('SYNTAX ', state, type, message)