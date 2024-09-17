# Polang - A Simple Macro-Based Language

## Introduction
Polang is a lightweight interpreted programming language built around a macro system. The language allows for basic operations, variable manipulation, and macro-based control flow structures like loops and conditionals. Polang supports dynamic typing, handling various data types such as numbers, strings, and lists.

## Features
- **Dynamic Typing:** Supports data types such as strings, numbers, lists, and `None`.
- **Variable and Constant Declaration:** Declare variables using `set` and constants using `def`.
- **Arithmetic Operations:** Perform basic operations like addition, subtraction, and summation with `add`, `sub`, and `sum`.
- **Conditionals:** Evaluate conditions with `if` and `not`.
- **Macros:** Create reusable code snippets with `mac` and `call` them in different parts of the program.
- **Input/Output:** Handle standard input and output using `put` and `out`.
- **Indexing:** Access and assign indexed values of lists and strings with `index` and `assign`.
- **File Inclusion:** Import other Polang files using `use`.

## Data Types
Polang supports the following data types:
- **String**: Textual data enclosed in single quotes.
- **Number**: Floating-point or integer values.
- **List**: A collection of items enclosed in square brackets.
- **None**: Represents an absence of a value.
- **Boolean**: Represented as `1` for true and `0` for false.

### Special Constants:
- `STRING`: Represents an empty string.
- `NUMBER`: Represents `0.0`.
- `LIST`: Represents an empty list.
- `NONE`: Represents no value.
- `'true'`: A boolean true (value 1).
- `'false'`: A boolean false (value 0).
- `'POLANG_VERSION'`: The current version of Polang.
- `'NICE'`: Special constant set to 69.

## Built-in Functions
Polang offers several built-in instructions (functions), each with specific behavior.

### Variable Operations
- `set <name> <value>`: Sets or updates a variable.
- `def <name> <value>`: Declares a constant.
- `add <name> <value(s)>`: Adds values to the variable.
- `sub <name> <value>`: Subtracts a value from the variable.
- `sum <value(s)>`: Sums a series of values.

### Macros and Control Flow
- `mac <name> <argument_count>`: Defines a macro with the specified number of arguments.
- `end`: Ends the definition of a macro.
- `call <macro_name> <args>`: Calls a previously defined macro.
- `if <condition> <func> <args>`: Executes the function if the condition is true.
- `not <condition> <func> <args>`: Executes the function if the condition is false.

### Input/Output
- `out <values>`: Prints the values to the console.
- `put <name>`: Takes input from the user and stores it in the variable.

### Memory and Type Handling
- `type <value>`: Returns the type of the value.
- `memory`: Outputs the memory state.
- `memory.functions`: Outputs the current functions and macros in memory.

### Conditionals and Comparisons
- `eq <left> <right>`: Returns 1 if the values are equal, 0 otherwise.
- `lt <left> <right>`: Returns 1 if the left value is less than the right value.
- `gt <left> <right>`: Returns 1 if the left value is greater than the right value.

### Indexing and Assignment
- `index <collection> <index>`: Returns the value at the specified index.
- `assign <collection> <index> <new_value>`: Assigns a new value to the specified index.

### Miscellaneous
- `use <file_name>`: Includes the specified Polang file.
- `del <names>`: Deletes variables or functions from memory.
- `exit <exit_code>`: Terminates the program with the specified exit code.
- `err <args>`: Throws an error with the specified message.

## Example Code

### Hello World
```polang
out 'Hello, World!'
