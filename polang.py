from sys import exit
from scripts import *

from icecream import ic

Data = str | Value

# Assistants
def get_number(number: str) -> (Number | None):
    try:
        num = float(number)
        return integer if (integer := int(num)) == num else num
    except ValueError:
        return None

def check_variable(instruction: str, data: Data, inverse = False) -> Value:
    if isinstance(data, str):
        var = memory.get(data)
        assert var is not None, NAME_ERROR(data, instruction)
        return var
    elif isinstance(data, Value):
        return data

def check_variable_list(instruction: str, *data: Data) -> list[Value]:
    variable_list = []
    for d in data:
        d = check_variable(instruction, d)
        variable_list.append(d)
    return variable_list

def force_value(x):
    if isinstance(x, Value):
        return x
    return Value(x)

def is_float(number: int | float):
    return int(number) != number

EXTENSION = '.po'
RUNNING = True
EXIT_CODE = 0

SCOPE_STACK: list[str] = []
def get_active_scope() -> (str | None):
    if len(SCOPE_STACK) > 0:
        return SCOPE_STACK[-1]
    return None

# Warnings & Errors
warnings: list[str] = []
errors: list[str] = []
missing_lines = 0

# Internal interpretation file
file_content: list[str] = []

memory: dict[str, Value] = {
    STRING: Value('', True),
    NUMBER: Value(0.0, True),
    LIST:   Value([], True),
    NONE:   Value(None, True),
    'true':  Value(1, True),
    'false': Value(0, True),
    'POLANG_VERSION': Value('1.10.2'),
    'NICE': Value(69),
}

memory_func: dict[str, Macro] = {    
    'while': Macro(4, [
        'zet while.expr $1 $2 $3',
        'if while.expr call $4',
        'if while.expr call while $1 $2 $3 $4',
    ]),
    
    'for': Macro(3, [
        'set for.i $1',
        'zet for.expr lss $1 $2',
        'if for.expr call $3',
        'add for.i 1',
        'if for.expr call for for.i $2 $3',
    ])
}

# SET
def ins_set_variable(name: str, data: Data) -> Value | None:
    left = memory.get(name)
    right = check_variable('SET', data)
    if left is None:
        memory[name] = Value(right.value)
    else:
        assert not left.const, LOGIC_ERROR('Constant re declaration', f'Trying to re assign a constant value: {name} = {left.value}', 'SET')
        assert left.type == right.type, TYPE_ERROR(left, right, 'SET OP')
        memory[name].value = right.value
    return Value(memory[name].type, True)

# DEF
def ins_def_constant(name: str, data: Data) -> Value:
    ins_set_variable(name, data)
    memory[name].const = True
    return Value(name)

# ADD
def ins_add_value(name: str, add_value: Data):
    left = check_variable('ADD', name)
    assert not left.const, LOGIC_ERROR('Constant assignment', f'Trying to add a value to a constant: {left}', 'ADD') 
    right = check_variable('ADD', add_value)

    ins_return = left.value # Cach the last value before addition

    if left.type == NUMBER:
        if right.type == NUMBER:
            left.value += right.value
        elif right.type in [STRING, LIST]:
            left.value += len(right.value)
        else:
            RAISE(TYPE_ERROR(left, right, 'ADD'))
    elif left.type == STRING:
        if right.type == NONE:
            left.value += ' '  
        elif right.type == STRING:
            left.value += right.value
        elif right.type == NUMBER:
            left.value += str(right.value)
        else:
            RAISE(TYPE_ERROR(left, right, 'ADD'))
    elif left.type == LIST:
        left.value.append(right.value)
    return ins_return

# SUB
def ins_sub_value(name: str, sub_value: Data):
    left = check_variable('SUB', name)
    assert not left.const, LOGIC_ERROR('Constant assignment', f'Trying to substract a value to a constant: {name}', 'SUB') 
    right = check_variable('SUB', sub_value)
    
    ins_return = left.value # Catch the last value before substraction
    
    if left.type == NUMBER:
        if right.type == NUMBER:
            left.value -= right.value
        elif right.type == STRING:
            left.value -= len(right.value)
        else:
            RAISE(TYPE_ERROR(left, right, 'SUB'))
    elif left.type == STRING:
        if right.type == STRING:
            left.value = left.value.replace(right.value, '')
        elif right.type == NUMBER:
            left.value = left.value[:-int(right.value)]
        else:
            RAISE(TYPE_ERROR(left, right, 'SUB'))
    elif left.type == LIST:
        if right.type == NUMBER:
            left.value.pop(int(right.value))
        elif right.type == STRING:
            left.value = left.value[:-len(right.value)]
        else:
            RAISE(TYPE_ERROR(left, right, 'SUB'))
    return ins_return
    
# SUM
def ins_sum_values(*data: Data):
    sum_type = None
    data = check_variable_list('SUM', *data)
    for d in data:
        if sum_type is None:
            if d.type == NONE:
                continue
            sum_type = d.type
            if sum_type == NUMBER:
                sum_value = 0
            elif sum_type == STRING:
                sum_value = ''
            elif sum_type == LIST:
                sum_value = []
        assert d.type == sum_type, TYPE_ERROR(d, sum_type, 'SUM')
        sum_value += d.value
    return sum_value
    
# OUT
def ins_stdout(*data: Data):
    if len(data) == 0:
        print()
    
    data = check_variable_list('OUT', *data)
    
    def print_value(value: Value):
        if value.type == NONE:
            print(' ', end='')
        elif value.type == LIST:
            print('[', end='')
            size = len(value.value)
            for v in range(size - 1):
                print(value.value[v], end=', ')
            if size > 0:
                print(value.value[-1], end='')
            print(']', end='')
        else:
            print(value.value, end='')
        
    for d in data:
        print_value(d)

# EXIT
def ins_exit_program(exit_code: Data | None = None):
    exit_code = check_variable('EXIT', exit_code)
    global RUNNING, EXIT_CODE
    RUNNING = False
    assert exit_code.type == NUMBER, LOGIC_ERROR('Exit code is not a number', f'--> {exit_code}', 'EXIT')
    EXIT_CODE = int(exit_code.value)

# TYPE    
def ins_typeof(data: Data):
    data = check_variable('TYPE', data)
    return data.type
        
# EQU
def ins_is_equal(left: Data, right: Data):
    left, right = check_variable_list('EQU', left, right)
    return int(left.value == right.value)

# LSS
def ins_is_less(left: Data, right: Data):
    left, right = check_variable_list('LSS', left, right)
    return int(left.value < right.value)

# GTR
def ins_is_greater(left: Data, right: Data):
    left, right = check_variable_list('GTR', left, right)
    return int(left.value > right.value)
    
# PUT
def ins_stdin(name: str):
    var = check_variable('PUT', name)
    try:
        input_value = input()
    except EOFError:
        RAISE(ERROR_FORMAT('INPUT ', 'PUT', 'Keyboard interruption', 'perhaps you pressed Ctrl + C?'))
    if var.type == NUMBER:
        assert (number_compatible := get_number(input_value)) is not None, TYPE_ERROR(var, Value(input_value), 'PUT INS')
        ins_set_variable(name, Value(number_compatible))
    elif var.type == LIST:
        chunks = input_value.split(' ')
        tokens = [force_value(lex_chunk(value)) for value in chunks]
        for value in tokens:
            ins_add_value(name, value)
    else:
        ins_set_variable(name, Value(input_value))  

# USE
def ins_use_polang_file(line: int, module: str):
    global file_content
    assert module.endswith(EXTENSION), PARAM_ERROR('Input must be a polang file', 'USE')
    with open(module, 'r') as polang_file:
        file_content.pop(line)
        file_content = file_content[:line + 1] + [''] + polang_file.read().split('\n') + file_content[line:]

# ZET
def ins_set_variable_call(name: str, func_name: str, *args):
    assert (func := instructions.get(func_name)) is not None, NAME_ERROR(func_name, 'ZET')
    return ins_set_variable(name, force_value(func[1](*args)))
    
# DEL
def ins_delete(*names: str):
    for n in names:
        if not isinstance(n, str):
            warnings.append(f'Trying to DELETE not a name: {n}') 
        elif n in memory:
            memory.pop(n)
        elif n in memory_func:
            memory_func.pop(n)
        else:
            warnings.append(f'Trying to DELETE an unknown name: {n}')

# ERR
def ins_error(*args):
    RAISE(ERROR_FORMAT(f'{args[0]} ', *args[1:]))

# FUN 
def ins_macro(name: str, cant_arguments: Value | None):
    assert name not in memory, ERROR_FORMAT('NAME ', 'FUN DECLARATION', f'There\'s already a variable called', f'{name}')
    assert name not in memory_func, ERROR_FORMAT('NAME ', 'FUN DECLARATION', f'Macro already exists', f'{name}')
    
    memory_func[name] = Macro(
        cant_arguments.value if cant_arguments is not None else -1,
        [],
    )
    
    global SCOPE_STACK
    SCOPE_STACK.append(name)
    
# END
def ins_end_macro():
    global SCOPE_STACK
    
    if get_active_scope() is not None:
        SCOPE_STACK.pop()
    else:
        warnings.append(f'Trying to END a macro that is not active.')

import re

# Format a line to match the arguments
def format_line(line: str, func_name: str, *args: Value):
    chunk_list = line.split(' ')
    for c, chunk in enumerate(chunk_list):
        if (match := re.match(r'\$(\d+)*', chunk)) is not None:
            for g in match.groups():
                if (template_num := int(g)) > len(args) and memory_func[func_name][0] > -1:
                    RAISE(ERROR_FORMAT('FUNCTION ', 'FUNCTION EXECUTION', 'Template argument exceed the total of arguments'))
                try:
                    replace_arg = args[template_num - 1]
                    if isinstance(replace_arg, Value):
                        if replace_arg.type == STRING:
                            replace_arg = '\'' + replace_arg.value + '\''
                        else:
                            replace_arg = replace_arg.value
                        
                    chunk_list[c] = chunk.replace(f'${template_num}', f'{replace_arg}')
                except IndexError as ierr:
                    chunk_list[c] = ''
                    warnings.append(f'Argument ${template_num} of {func_name} not provided.')
    formated = ''
    for c in chunk_list:
        formated += str(c) + ' '
    return formated
                
# CALL
def ins_call_macro(name: str, *argv):
    assert (func := memory_func.get(name)) is not None, ERROR_FORMAT('FUNC ', 'CALL', None, f'Object is not callable: {name}')
    if func.argc > -1 and len(argv) > func.argc:
        PARAM_ERROR('Too many arguments in user function call', f'{name}', func.argc, len(argv))
    for l, line in enumerate(func.code):
        exe_line = format_line(line, name, *argv)
        if (ret := evaluate_line(l + 1, exe_line)) is not None:
            return ret
    return None
    
# MEM
def ins_get_memory_value():
    memory_str = ''
    for key, val in memory.items():
        memory_str += f'{key} -> {val}\n'
    return memory_str

# INDEX
def ins_get_index_value(sizeable: Data, index_value: Data):
    sizeable = check_variable('INDEX', sizeable)
    assert sizeable.type != NONE, ERROR_FORMAT('NONE ', 'INDEX', 'Index access', 'none type variable does not support index.')
    index_value = check_variable('INDEX', index_value)
    assert index_value.type == NUMBER, TYPE_ERROR(f'{Value(NUMBER)}', index_value.value, 'INDEX')
    try:
        if sizeable.type == NUMBER:
            return Value(float(str(sizeable.value)[int(index_value.value)]))
        if sizeable.type in [STRING, LIST]:
            return Value(sizeable.value[int(index_value.value)])            
    except IndexError as inderr:
        RAISE(INDEX_ERROR(index_value.value, 'INDEX OP'))

# ASSIGN
def ins_set_index_value(sizeable: Data, index_value: Data, new_value: Data):
    sizeable = check_variable('INDEX', sizeable)
    assert not sizeable.const, RAISE(ERROR_FORMAT('CONST ', 'ASSIGN', None, f'Cannot re assign a constant value: {sizeable}.'))
    assert sizeable.type in [LIST, STRING], ERROR_FORMAT('INDEX ', 'ASSIGN', 'Index access', f'Value type does not support item assignment: {sizeable}')
    index_value = check_variable('INDEX', index_value)
    assert index_value.type == NUMBER, TYPE_ERROR(f'{NUMBER}', index_value.value, 'ASSIGN')
    new_value = check_variable('ASSIGN', new_value)
    try:
        index = int(index_value.value)
        if sizeable.type == LIST:
            sizeable.value[int(index_value.value)] = new_value.value
        elif sizeable.type == STRING:
            sizeable.value = sizeable.value[:index] + new_value.value + sizeable.value[index + 1:]
    except IndexError as inderr:
        RAISE(INDEX_ERROR(index_value.value, 'ASSIGN'))

# IF / NOT
def ins_eval_if(negate: bool, expression_value: Data, func: str, *args):
    expression_value = check_variable('IF EVAL', expression_value)
    assert (return_function := instructions.get(func)) is not None, NAME_ERROR(func, 'NOT CONDITION' if negate else 'IF CONDITION')
    if (argc := len(args)) > return_function[0] and return_function[0] > -1:
        PARAM_ERROR('Too many arguments', 'IF CONDITION CALL', return_function[0], argc)
    if argc < return_function[0]:
        PARAM_ERROR('Not enough arguments', 'IF CONDITION CALL', return_function[0], argc)
    if_eval = expression_value.value not in [None, 0, '', []]
    if negate:
        if_eval = not if_eval
    if if_eval:
        return_function[1](*args)

# RET
def ins_return(name_value: Data) -> Value:
    name_value = check_variable('RETURN', name_value)
    return name_value 

# VERIFIES IF A CHUNK IS SOMETHING
def lex_chunk(chunk: str) -> (Value | str):
    if (chunk[0] == '\'') and (chunk[-1] == '\''):
        return Value(chunk[1:-1], False)
    elif chunk == '.':
        return Value()
    elif (funk := get_number(chunk)) is not None:
        return Value(funk, False)
    elif chunk[0] == '[' and chunk[-1] == ']':
        return Value([], True)
    else:
        return chunk

instructions: dict[str, tuple[int, function]] = {
    # setters
    'set':   (2, ins_set_variable),
    'def':   (2, ins_def_constant),
    'add':   (2, ins_add_value),
    'sub':   (2, ins_sub_value),
    'sum':   (-1, ins_sum_values),
    
    # functional
    'zet':   (-1, ins_set_variable_call),
    'err':   (-1, ins_error),
    'mac':   (2, ins_macro),
    'end':   (-1, ins_end_macro),
    'ret':   (1, ins_return),
    'call':  (-1, ins_call_macro),

    # conditionals
    'if':    (-1, ins_eval_if),
    'not':   (-1, ins_eval_if),

    # std out, in
    'out':   (-1, ins_stdout),
    'put':   (1, ins_stdin),
    
    # info
    'type':  (1, ins_typeof),
    'equ':   (2, ins_is_equal),
    'lss':   (2, ins_is_less),
    'gtr':   (2, ins_is_greater),
    'mem':   (0, ins_get_memory_value),
    'mem_func': (0, lambda: memory_func),
    'index': (2, ins_get_index_value),
    'assign': (3, ins_set_index_value),

    # expand
    'use':   (1, ins_use_polang_file),
    
    'del':   (-1, ins_delete),
    'exit':  (1, ins_exit_program),
}

def interpret_line(line_num: int, ins: str, chunks: list[str]):
    tokens = [lex_chunk(c) for c in chunks[1:]]
    if ins == 'if':
        ins_eval_if(False, *tokens)
    elif ins == 'not':
        ins_eval_if(True, *tokens)
    elif ins == 'call':
        if (ret_value := ins_call_macro(*tokens)) is not None:
            return ret_value
    elif ins == 'ret':
        return ins_return(*tokens)
    elif ins == 'exit':
        ins_exit_program(tokens[0])  
    elif ins == 'use':
        ins_use_polang_file(line_num, tokens[0])
    else:
        instructions[ins][1](*tokens)

def evaluate_line(line_num: int, line: str):
    chunks = line.split()
    while '' in chunks:
        chunks.remove('')
    if chunks == [] or chunks[0] == '%':
        return
    args = len(chunks) - 1
    
    ic(line_num, line, chunks, args, SCOPE_STACK)
    if SCOPE_STACK != []:
        if chunks[0] == 'mac':
            SCOPE_STACK.append(chunks[1])
        elif chunks[0] == 'end':
            ins_end_macro()
        else:
            memory_func[get_active_scope()].code.append(line)
    else:
        assert (ins := chunks[0]) in instructions.keys(), SYNTAX_ERROR(f'First chunk is not a valid instruction', f'--> {ins}', SCOPE_STACK)
        
        # Infinite arguments
        if (ins_paramc := instructions[ins][0]) < 0:
            pass
        
        elif ins_paramc < args:
            PARAM_ERROR(f'Too many arguments:', f'{ins}', f'{ins_paramc}', f'{args}')
        elif ins_paramc > args:
            PARAM_ERROR(f'Not enough arguments:', f'{ins}', f'{ins_paramc}', f'{args}')

        return interpret_line(line_num, ins, chunks)
        
def interpret(error_registry: bool, strict_errors: bool):
    file_lines_q = len(file_content)
    ln = 0
    while ln < file_lines_q: 
        if not RUNNING:
            break
        try:
            evaluate_line(ln, file_content[ln])
        except AssertionError as ass:
            err = (f'ln -> {ln + 1}: {ass}')
            if strict_errors:
                print(err)
                ins_exit_program(Value(-1))
            elif error_registry:
                errors.append(err)
            else:
                print(err)
        file_lines_q = len(file_content)
        ln += 1
        
def get_file_content(file_path: str):
    with open(file_path, 'r') as file:
        return file.read().split('\n')   
        
def display_usage():
    print('USAGE:')
    print('    polang <input.po> [options]  :  Interprets an input.\n')
    print('OPTIONS:')
    print('    --strict  :  Terminates the execution when an error is encounter.')
    print('    --warn    :  Displays all the warnings at the end of the execution.')
    print('    --error   :  Shows all the errors at the end of the execution.')
        
def main(argc: int, argv: list[str]):    
    if argc == 1:
        display_usage()
        return 0
    
    if argc >= 2:
        assert (input_file := argv[1]).endswith(EXTENSION), ERROR_FORMAT('USAGE ', None, 'Input file', 'does not match with the ".po" extension.')
    
        global file_content
        file_content = get_file_content(input_file)
        
        error_display = ('--error' in argv[2:])
        strict_errors = ('--strict' in argv[2:])

        interpret(error_display, strict_errors)

        if '--warn' in argv[2:]:
            for w in warnings:
                print(f'[!] {w}')
                
        if error_display:
            for e in errors:
                print(e)
    
    exit(EXIT_CODE)

from sys import argv

if __name__ == '__main__':
    try:
        main(len(argv), argv)
    except AssertionError as ass:
        print(ass)