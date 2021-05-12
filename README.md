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

### For generating dot file (parser) and dump of symbol table in `csv` format
```bash
$ ./bin/parser -o myAST.dot /tests/helloworld.c 

# For generates a postscript program containing the drawing of the tree 
$ dot -Tps myAST.dot -o myAST.ps 
# Alternatively, for generating .png file
$ ./bin/parser -o myAST.dot --png /tests/helloworld.c
```


### For more informations
```
$ ./bin/parser -h
```

## Features

### Basic
- Native data types: Int, Char, Float
- Variables and Expressions
- Conditional: if, if-else, switch-case
- Loops: for, while, do-while
- Break, Continue
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
- Dynamic memory allocation:
- Register allocation optimization
- 

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

