# gcc_lite
C-Compiler (project+assignment) for course CS335, 2021 - II 

**Source language** :- C

**Implementation language** :- Python

**Target language** :- x86 assembly language

## Structure

### For installing Dependencies
```bash 
$ make dep
# OR
$ pip install --ignore-installed -r ./requirements.txt  
```
### For building executable
```bash
$ make
$ make clean # For removing the build
```

###For running the compiler: 

```bash
./bin/gcc_lite [-o outfile] <input_file>` eg. `./bin/parser tests/helloworld.c`
```

### For more informations about usage
```bash
usage: gcc_lite [-h] [--input INPUT] [-d] [-o OUT] [-l] [-D] [-p] [-I] [--sym] [-S] [-R]

Compiler for C programs

optional arguments:
  -h, --help         show this help message and exit
  --input INPUT      C program file to parse
  -d, --debug        Generate assembly with extra information (for debugging purposes)
  -o OUT, --out OUT  File name to store generated executable
  -l, --lex          Store output of lexer
  -D, --dot          Generate AST graph as DOT format
  -p, --png          Generate AST graph as png format
  -I, --ir           Dump the generated Intermediate representation
  --sym              Dump the symbol table
  -S, --asm          Store the generated assembly file
  -R, --exec         Execute the generated program
```


## Features

### Basic Features
- Native data types: Int, Char, Float
- Variables and Expressions
- Conditional: if, if-else, switch-case
- Loops: for, while, do-while
- Break, Continue
- Switch Case
- Arrays: Single and multidimensional
- Input,output
- Functions, recursion
- Pointers: Single and multilevel
- Simple library functions
- Arithmetic operators
- Logical and bitwise operators
- Struct user defined data type
- Typedef

### Advanced Features
- Dynamic memory allocation (malloc, free)
- Register allocation optimization using conditional spilling
- File Handling
- Fork and exec system calls
- Storage Optimization for Char and string
- Nested Struct and Array Initializers
- Multidimensional arrays as function parameters
- Short circuit expression evaluation

## Members
- [Dev Chauhan](https://github.com/dev-chauhan)
- [Hitesh Gupta](https://github.com/hitesh-gupta-2111)
- [Naman Biyani](https://github.com/namanbiyani)
- [Nirmal Suthar](https://github.com/nirmal-suthar)

## Acknowledgments

* Amey Karkare (Course Instructor CS335)

## License

This project is licensed under the MIT License

## References

- [PLY for Lexing and Parsing](http://www.dabeaz.com/ply/)
- [Grammar-lex](https://www.lysator.liu.se/c/ANSI-C-grammar-l.html)
- [Grammar-yacc](https://www.lysator.liu.se/c/ANSI-C-grammar-y.html)
- [Stanford 3AC Examples](https://web.stanford.edu/class/archive/cs/cs143/cs143.1128/handouts/240%20TAC%20Examples.pdf )

