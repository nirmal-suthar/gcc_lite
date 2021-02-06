# gcc_lite
C-Compiler (project+assignment) for course CS335, 2021 - II 

## Members
- [Naman Biyani](https://github.com/namanbiyani)
- [Dev Chauhan](https://github.com/dev-chauhan)
- [Atharv Tyagi](https://github.com/atharvtyagi)
- [Hitesh Gupta](https://github.com/hitesh-gupta-2111)
- [Nirmal Suthar](https://github.com/nirmal-suthar)

## Usage

### For building executable
```bash
$ cd src
$ make
$ cd ..
```

### For executing scanner
```bash
$ ./bin/lexer /tests/test1.c
```

### Available option
```
./bin/lexer - token scanner for C programs
USAGE:  ./bin/lexer [options] file...
 
options:
  -h, --help             shows brief help
  -o, --output=FILE      specify a file to store output
  -v, --verbose          force output on stdout
```