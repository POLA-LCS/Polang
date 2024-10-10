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

def check_variable(instruction: str, data: Data) -> Value:
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
X = -1

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
    'POLANG_VERSION': Value('1.10.2', True),
    'NICE': Value(69, True),
}

memory_macros: dict[str, Macro] = {    
    'while': Macro(4, [
        'zet while.expr $1 $2 $3',
        'if while.expr call $4',
        'if while.expr call while $1 $2 $3 $4',
    ]),
    
    'for': Macro(3, [
        'set for.i $1',
        'zet for.expr lt $1 $2',
        'if for.expr call $3',
        'add for.i 1',
        'if for.expr call for for.i $2 $3',
    ])
}

# SET
def inst_set_variable(name: str, data: Data) -> Value | None:
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
def inst_def_constant(name: str, data: Data) -> Value:
    inst_set_variable(name, data)
    memory[name].const = True
    return Value(name)

# ADD
def inst_add_value(name: str, *add_value: Data):
    left = check_variable('ADD', name)
    assert not left.const, LOGIC_ERROR('Constant assignment', f'Trying to add a value to a constant: {left}', 'ADD') 
    right = [check_variable('ADD', av) for av in add_value]

    inst_return = left.value # Catch the last value before addition

    if left.type == NUMBER:
        for val in right:
            if val.type == NUMBER:
                left.value += val.value
            elif val.type in [STRING, LIST]:
                left.value += len(val.value)
            else:
                RAISE(TYPE_ERROR(left, val, 'ADD'))
    elif left.type == STRING:
        for val in right:
            if val.type == NONE:
                left.value += ' '  
            elif val.type == STRING:
                left.value += val.value
            elif val.type == NUMBER:
                left.value += str(val.value)
            else:
                RAISE(TYPE_ERROR(left, right, 'ADD'))
    elif left.type == LIST:
        last = left.value
        left.value = []
        left.value = last + [val.value for val in right]
    return inst_return

# SUB
def inst_sub_value(name: str, sub_value: Data):
    left = check_variable('SUB', name)
    assert not left.const, LOGIC_ERROR('Constant assignment', f'Trying to substract a value to a constant: {name}', 'SUB') 
    right = check_variable('SUB', sub_value)
    
    inst_return = left.value # Catch the last value before substraction
    
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
    return inst_return
    
# SUM
def inst_sum_values(*data: Data):
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
def inst_stdout(*data: Data):
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
def inst_exit_program(exit_code: Data | None = None):
    exit_code = check_variable('EXIT', exit_code)
    global RUNNING, EXIT_CODE
    RUNNING = False
    assert exit_code.type == NUMBER, LOGIC_ERROR('Exit code is not a number', f'--> {exit_code}', 'EXIT')
    EXIT_CODE = int(exit_code.value)

# TYPE    
def inst_typeof(data: Data):
    data = check_variable('TYPE', data)
    return data.type
        
# EQ
def inst_is_equal(left: Data, right: Data):
    left, right = check_variable_list('EQ', left, right)
    return int(left.value == right.value)

# LT
def inst_is_less(left: Data, right: Data):
    left, right = check_variable_list('LT', left, right)
    return int(left.value < right.value)

# GT
def inst_is_greater(left: Data, right: Data):
    left, right = check_variable_list('GT', left, right)
    return int(left.value > right.value)
    
# PUT
def inst_stdin(name: str):
    var = check_variable('PUT', name)
    try:
        input_value = input()
    except EOFError:
        RAISE(ERROR_FORMAT('INPUT ', 'PUT', 'Keyboard interruption', 'perhaps you pressed Ctrl + C?'))
    if var.type == NUMBER:
        assert (number_compatible := get_number(input_value)) is not None, TYPE_ERROR(var, Value(input_value), 'PUT INS')
        inst_set_variable(name, Value(number_compatible))
    elif var.type == LIST:
        chunks = input_value.split(' ')
        tokens = [force_value(lex_chunk(value)) for value in chunks]
        for value in tokens:
            inst_add_value(name, value)
    else:
        inst_set_variable(name, Value(input_value))  

# USE
def inst_use_polang_file(line: int, module: str):
    global file_content
    assert module.endswith(EXTENSION), PARAM_ERROR('Input must be a polang file', 'USE')
    with open(module, 'r') as polang_file:
        file_content.pop(line)
        file_content = file_content[:line + 1] + [''] + polang_file.read().split('\n') + file_content[line:]

# ZET
def inst_set_variable_call(name: str, func_name: str, *args):
    if (func := instructions.get(func_name)):
        return inst_set_variable(name, force_value(func[1](*args)))
    else:
        return inst_set_variable(name, force_value(inst_call_macro(func_name, *args)))
    
# DEL
def inst_delete(*names: str):
    for n in names:
        if not isinstance(n, str):
            warnings.append(f'Trying to DELETE not a name: {n}') 
        elif n in memory:
            memory.pop(n)
        elif n in memory_macros:
            memory_macros.pop(n)
        else:
            warnings.append(f'Trying to DELETE an unknown name: {n}')

# ERR
def inst_error(*args):
    RAISE(ERROR_FORMAT(f'{args[0]} ', *args[1:]))

# MAC 
def inst_macro(name: str, cant_arguments: Value | None):
    assert name not in memory, ERROR_FORMAT('NAME ', 'MAC DECLARATION', f'There\'s already a variable called', f'{name}')
    assert name not in memory_macros, ERROR_FORMAT('NAME ', 'MAC DECLARATION', f'Macro already exists', f'{name}')
    
    memory_macros[name] = Macro(
        cant_arguments.value if cant_arguments is not None else -1,
        [],
    )
    
    global SCOPE_STACK
    SCOPE_STACK.append(name)
    
# END
def inst_end_macro():
    global SCOPE_STACK
    
    if get_active_scope() is not None:
        SCOPE_STACK.pop()
    else:
        warnings.append(f'Trying to END a macro that is not active.')

import re

# Format a line to match the arguments
def format_line(line: str, func_name: str, *args: Value | str):
    # ic(line, func_name, args)
    chunk_list = line.split(' ')
    for c, chunk in enumerate(chunk_list):
        if (match := re.match(r'\$(\d+)', chunk)) is not None:
            for g in match.groups():
                if (template_num := int(g)) > len(args) and memory_macros[func_name][0] > X:
                    RAISE(ERROR_FORMAT('FUNCTION ', 'FUNCTION EXECUTION', 'Template argument exceed the total of arguments'))
                try:
                    replace_arg = args[template_num - 1]
                    if isinstance(replace_arg, Value):
                        if replace_arg.type == STRING:
                            replace_arg = '\'' + replace_arg.value + '\''
                        else:
                            replace_arg = replace_arg.value
                        
                    chunk_list[c] = chunk.replace(f'${template_num}', f'{replace_arg}')
                except IndexError:
                    chunk_list[c] = ''
                    warnings.append(f'Argument ${template_num} of {func_name} not provided.')
        elif (match := re.match(r'\$\*', chunk)) is not None:
            chunk_list[c] = chunk.replace('$*', f'{' '.join([str(arg) for arg in args])}')
    formated = ''
    for c in chunk_list:
        formated += str(c) + ' '
    return formated
                
# CALL
def inst_call_macro(name: str, *argv):
    assert (func := memory_macros.get(name)) is not None, ERROR_FORMAT('FUNC ', 'CALL', None, f'Object is not callable: {name}')
    if func.argc > X and len(argv) > func.argc:
        PARAM_ERROR('Too many arguments in user function call', f'{name}', func.argc, len(argv))
    for l, line in enumerate(func.code):
        exe_line = format_line(line, name, *argv)
        if (ret := evaluate_line(l + 1, exe_line)) is not None:
            return ret
    return None
    
# MEMORY
def inst_get_memory_value():
    memory_str = ''
    for key, val in memory.items():
        memory_str += f'{key} -> {val}\n'
    return Value(memory_str, True)

# MEMORY.FUNCTIONS
def inst_get_memory_functions():
    func_str = ''
    for key, val in memory_macros.items():
        func_str += f'{key} -> {val}\n'
    return Value(func_str, True)

# INDEX
def inst_get_index_value(sizeable: Data, index_value: Data):
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
def inst_set_index_value(sizeable: Data, index_value: Data, new_value: Data):
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
def inst_eval_if(negate: bool, expression_value: Data, func: str, *args):
    expression_value = check_variable('IF EVAL', expression_value)
    assert (return_function := instructions.get(func)) is not None, NAME_ERROR(func, 'NOT CONDITION' if negate else 'IF CONDITION')
    if (argc := len(args)) > return_function[0] and return_function[0] > X:
        PARAM_ERROR('Too many arguments', 'IF CONDITION CALL', return_function[0], argc)
    if argc < return_function[0]:
        PARAM_ERROR('Not enough arguments', 'IF CONDITION CALL', return_function[0], argc)
    if_eval = expression_value.value not in [None, 0, '', []]
    if negate:
        if_eval = not if_eval
    if if_eval:
        return_function[1](*args)

# RET
def inst_return(*name_value: str | Data) -> Value:
    name = name_value
    name_value = check_variable('RETURN', name[0])
    inst_delete(*name)
    return name_value

# EXIST
def inst_variable_exist(*names: str) -> int:
    return Value(int(all([n in memory for n in names])))

# METHOD
def inst_assign_method(name: str, *macros: str):
    for mac in macros:
        if mac not in memory_macros:
            warnings.append(f'Not existing macro cannot be a method... ({mac}).')
        else:
            new_name = name + '.' + mac
            inst_macro(new_name, Value(memory_macros[mac].argc - 1))
            global SCOPE_STACK
            SCOPE_STACK.pop()
            for line in memory_macros[mac].code:
                memory_macros[new_name].code.append(
                    format_line(line, mac, name, *[f'${i}' for i in range(1, memory_macros[mac].argc + 1)])
                )

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
    'set':   (2, inst_set_variable),
    'def':   (2, inst_def_constant),
    'add':   (X, inst_add_value),
    'sub':   (2, inst_sub_value),
    'sum':   (X, inst_sum_values),
    
    # functional
    'zet':    (X, inst_set_variable_call),
    'err':    (X, inst_error),
    'mac':    (2, inst_macro),
    'end':    (X, inst_end_macro),
    'ret':    (X, inst_return),
    'call':   (X, inst_call_macro),
    'method': (X, inst_assign_method),

    # conditionals
    'if':    (X, inst_eval_if),
    'not':   (X, inst_eval_if),

    # std out, in
    'out':   (X, inst_stdout),
    'put':   (1, inst_stdin),
    
    # info
    'type':        (1, inst_typeof),
    'eq':          (2, inst_is_equal),
    'lt':          (2, inst_is_less),
    'gt':          (2, inst_is_greater),
    'exist':       (X, inst_variable_exist),
    
    'memory':      (0, inst_get_memory_value),
    'memory.func': (0, inst_get_memory_functions),
    
    'index':       (2, inst_get_index_value),
    'assign':      (3, inst_set_index_value),

    # expand
    'use':   (1, inst_use_polang_file),
    
    'del':   (X, inst_delete),
    'exit':  (1, inst_exit_program),
}

def interpret_line(line_num: int, inst: str, chunks: list[str]):
    tokens = [lex_chunk(c) for c in chunks[1:]]
    if inst == 'if':
        inst_eval_if(False, *tokens)
    elif inst == 'not':
        inst_eval_if(True, *tokens)
    elif inst == 'call':
        if (ret_value := inst_call_macro(*tokens)) is not None:
            return ret_value
    elif inst == 'ret':
        return inst_return(*tokens)
    elif inst == 'exit':
        inst_exit_program(tokens[0])  
    elif inst == 'use':
        inst_use_polang_file(line_num, tokens[0])
    else:
        instructions[inst][1](*tokens)

def evaluate_line(line_num: int, line: str):
    chunks = line.split()
    while '' in chunks:
        chunks.remove('')
    if chunks == [] or chunks[0] == '%':
        return
    args = len(chunks) - 1
    
    if len(SCOPE_STACK) > 0:
        if chunks[0] == 'mac':
            inst_macro(*[lex_chunk(chunk) for chunk in chunks[1:]])
        elif chunks[0] == 'end':
            inst_end_macro()
        else:
            memory_macros[get_active_scope()].code.append(line)
    else:
        assert (inst := chunks[0]) in instructions.keys(), SYNTAX_ERROR(f'First chunk is not a valid instruction', f'--> {inst}', SCOPE_STACK[-1] if SCOPE_STACK != [] else 'GLOBAL')
        
        # Infinite arguments
        if (inst_paramc := instructions[inst][0]) < 0:
            pass
        
        elif inst_paramc < args:
            PARAM_ERROR(f'Too many arguments:', f'{inst}', f'{inst_paramc}', f'{args}')
        elif inst_paramc > args:
            PARAM_ERROR(f'Not enough arguments:', f'{inst}', f'{inst_paramc}', f'{args}')

        return interpret_line(line_num, inst, chunks)
        
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
                inst_exit_program(Value(-1))
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