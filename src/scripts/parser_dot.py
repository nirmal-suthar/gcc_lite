#! /usr/bin/env python3

import sys, argparse, pydot
from argparse import ArgumentParser

FILTERED_LIST = [';','{','}']

def remove_redundancy(tree):
    newList = tree[:1]

    for child in tree[1:]:
        if child in FILTERED_LIST:
            continue
        elif type(child) is list:
            child = remove_redundancy(child)
            if child != []:
                newList.append(child)
        elif type(child) is str:
            newList.append(child)
        # else:
        #     raise Exception('remove: Invalid type {}'.format(type(child)))
        

    if len(newList) == 1:
        return []
    if len(newList) == 2:
        return newList[1]
    
    return newList


def generate_dot(graph, tree, node_idx):
    """ Node and edge declarations."""
    if type(tree) is str:
        graph.add_node(pydot.Node(node_idx, label=repr(tree), shape='house', style='filled', color='yellowgreen'))
        return node_idx
    elif type(tree) is list:
        graph.add_node(pydot.Node(node_idx, label=repr(tree[0]), shape='egg'))
        cur_idx = node_idx
        for child in tree[1:]:
            if child == []:
                continue
            graph.add_edge(pydot.Edge(node_idx, cur_idx+1))
            cur_idx = generate_dot(graph, child, cur_idx+1)
        return cur_idx
    else:
        raise Exception('Invalid type {}'.format(type(tree)))


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
        from parser import parser, lexer

    lexer.filename = args.input 
    lexer.lines = ifile.split("\n")

    syntax_tree = parser.parse(ifile)

    if syntax_tree is None:
        exit(1)

    if args.debug:
        AST_tree = syntax_tree
    else:
        AST_tree = ['start',remove_redundancy(syntax_tree)]
    
    graph = pydot.Dot('gcc_lite: Abstract Syntax Tree', graph_type='digraph')
    generate_dot(graph, AST_tree, 0)
    graph.get_node('0')[0].set_shape('doubleoctagon')
    graph.get_node('0')[0].set_color('orange')
    graph.get_node('0')[0].set_style('filled')
   
    if args.verbose:
        print(AST_tree)
    
    graph.write_raw(args.out)
    print('DOT file "{}" generated.'.format(args.out))

    if args.png:
        graph.write_png(png_file)
        print("Graph generated {}".format(png_file))
