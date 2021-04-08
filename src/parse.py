#! /usr/bin/env python3

import sys, argparse, pydot
from argparse import ArgumentParser


def arg_parser():

    argparser = ArgumentParser(prog='gcc_lite', 
        description='Parser for C programs')

    argparser.add_argument('input', type=str, 
        help='C program file to parse')

    argparser.add_argument('-v', '--verbose', action="store_true", 
        help='Force output on stdout')

    argparser.add_argument('-d', '--debug', action="store_true", 
        help='Generate complete syntax tree for debugging purpose')
    
    argparser.add_argument('-o', '--out', type=str, 
        help='File to store generated DOT file')

    argparser.add_argument('-p', '--png', action="store_true",
         help='Generate graph as png')
    
    args = argparser.parse_args()
    return args


if __name__ == "__main__":

    args = arg_parser()

    if args.out is None:
        ofile = args.input if args.input is not None else "myAST"
        ofile = ofile.split('/')[-1].split('.')[0]
        args.out = ofile + '.dot'
    
    png_file = args.out.split('.')[-2] + '.png'

    with open(args.input, 'r') as f:
        ifile = f.read()
    
    if args.debug:
        from parser_debug import parser, lexer
    else:
        from parser import parser, lexer, symtable, compilation_err

    lexer.filename = args.input 
    lexer.lines = ifile.split("\n")

    syntax_tree = parser.parse(ifile)

    if syntax_tree is None:
        exit(1)
        
    graph = pydot.Dot('gcc_lite: Abstract Syntax Tree', graph_type='digraph')
    symtable.dump_csv(args.out.split('.')[-2] + '.csv')
    AST = syntax_tree.gen_dot(graph)

    graph.write_raw(args.out)
    print('DOT file "{}" generated.'.format(args.out))

    if args.png:
        graph.write_png(png_file)
        print("Graph generated {}".format(png_file))
