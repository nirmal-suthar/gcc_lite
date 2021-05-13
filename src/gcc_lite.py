#! /usr/bin/env python3

import sys, argparse, pydot
import os, tempfile
from contextlib import redirect_stdout
from argparse import ArgumentParser
from parser import parser, lexer, main_lexer, bcolors
from helper import symtable, tac
from codegen import AssemblyGen
from lib import stdlib


def arg_parser():

    argparser = ArgumentParser(prog='gcc_lite', 
        description='Compiler for C programs')

    argparser.add_argument('--input', type=str, 
        help='C program file to parse', default='../test/helloworld.c')

    argparser.add_argument('-d', '--debug', action="store_true", 
        help='Generate assembly with extra information (for debugging purposes)')
    
    argparser.add_argument('-o', '--out', type=str, 
        help='File name to store generated executable')

    argparser.add_argument('-l', '--lex', action="store_true",
        help='Store output of lexer')
    
    argparser.add_argument('-D', '--dot', action="store_true",
        help='Generate AST graph as DOT format')

    argparser.add_argument('-p', '--png', action="store_true",
        help='Generate AST graph as png format')
    
    argparser.add_argument('-I', '--ir', action="store_true",
        help='Dump the generated Intermediate representation')
    
    argparser.add_argument('--sym', action="store_true",
        help='Dump the symbol table')
    
    argparser.add_argument('-S', '--asm', action="store_true",
        help='Store the generated assembly file')
    
    argparser.add_argument('-R', '--exec', action="store_true",
        help='Execute the generated program')
    
    args = argparser.parse_args()
    return args


if __name__ == "__main__":
    
    args = arg_parser()

    # if output file is not specified, then
    # create the default outfile name `a.out`
    if args.out is None:
        ofile = args.input.split('/')[-1].split('.')[0]
        args.out = 'a.out' 
    else:
        # strip the extension of outfile
        ofile = args.out.split('.')[0]

    with open(args.input, 'r') as f:
        in_file = f.read()
    
    if args.lex:
        lex_file = ofile + '.lex'
        with open(lex_file, 'w') as f:
            with redirect_stdout(f):
                main_lexer(in_file)

    # append the essential stdlib declaration
    ifile = stdlib + in_file
    lexer.filename = args.input 
    lexer.lines = ifile.split("\n")

    # try parsing the input file
    try:
        syntax_tree = parser.parse(ifile)
    except:
        print(bcolors.BOLD+f'{lexer.filename}:0:0'+bcolors.ENDC,end='')
        print(bcolors.FAIL+' SyntaxError'+bcolors.ENDC)
        exit(1)

    # unsuccessful parse will return here
    if syntax_tree is None or parser.compilation_err:
        exit(1)
        
    # generate DOT file if specified
    if args.dot or args.png:
        graph = pydot.Dot('gcc_lite: Abstract Syntax Tree', graph_type='digraph')
        AST = syntax_tree.gen_dot(graph)

        if args.dot:
            dot_file = ofile + '.dot'
            graph.write_raw(dot_file)
        if args.png:
            png_file = ofile + '.png'
            graph.write_png(png_file)

    # try generating IR and symbol table    
    try:
        syntax_tree.gen()
    except:
        print(bcolors.BOLD+f'{lexer.filename}:0:0'+bcolors.ENDC,end='')
        print(bcolors.FAIL+' IR Error'+bcolors.ENDC)
        exit(1)

    if args.sym:    
        sym_file = ofile + '.csv'
        symtable.dump_csv(sym_file)
    if args.ir:
        ir_file = ofile + '.ir'
        tac.dump_code(ir_file)

    # try generating assembly from IR
    try:
        asm = AssemblyGen(tac.func_code, debug=args.debug)
        asm.gen_assembly()
    except:
        print(bcolors.BOLD+f'{lexer.filename}:0:0'+bcolors.ENDC,end='')
        print(bcolors.FAIL+' Code Generation Error'+bcolors.ENDC)
        exit(1)

    # dump the assembly!

    # create tmpdir to store assembly if not specified
    if not args.asm:
        with tempfile.TemporaryDirectory() as tmpdir:
            asm_file = os.path.join(tmpdir, os.path.basename(ofile) + '.s')
            asm.dump_code(asm_file)
            # linking and creating executable by passing through gcc
            os.system(f"gcc -m32 --no-pie -o {args.out} {asm_file} -lm")
    # else store at specified place
    else:   
        asm_file = ofile + '.s'
        asm.dump_code(asm_file)
        # linking and creating executable by passing through gcc
        os.system(f"gcc -m32 --no-pie -o {args.out} {asm_file} -lm")

    # run the executable if specified
    if args.exec:
        os.system(f"./{args.out}")
