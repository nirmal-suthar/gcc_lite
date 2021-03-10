# gcc_lite
C-Compiler (project+assignment) for course CS335, 2021 - II 

## Members
- [Naman Biyani](https://github.com/namanbiyani)
- [Dev Chauhan](https://github.com/dev-chauhan)
- [Hitesh Gupta](https://github.com/hitesh-gupta-2111)
- [Nirmal Suthar](https://github.com/nirmal-suthar)

## Usage

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

### For generating dot file (parser)
```bash
$ ./bin/parser -o myAST.dot /tests/helloworld.c 

# For generates a postscript program containing the drawing of the tree 
$ dot -Tps myAST.dot -o myAST.ps 
# Alternatively, for generating .png file
$ ./bin/parser -o myAST.dot -png /tests/helloworld.c
```


### For more informations
```
$ ./bin/parser -h
```