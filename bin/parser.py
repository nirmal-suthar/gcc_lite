#!/usr/bin/python3
import sys
sys.path.insert(0, './src/')
from parser import parser
from parser_dot import generate_dot
import pydot
import getopt

#todo, more options can be added like getting lexer output also

def display_help():

    print("./bin/parser.py - Parser for Gcc_Lite")
    print("USAGE: ./bin/parser.py [options] file")
    print(" ")
    print("options:")
    print("  -h, --help             shows brief help")
    print("  -i, --input=FILE       specify a file for input")
    print("  -s, --string=FILE      specify a string for input")
    print("  -o, --output=FILE      specify a file to store output")
    print("  -p, --pic              store graph as png pic if value 1")
    print("  -v, --verbose          force output on stdout if value 1")

def print_usage(): 
    print("No input file or string given")
    print("Try \`./bin/parser.py --help\` for more informations.")
    sys.exit(2)

def main(argv):
    verbose = False
    outfile = "myAst.dot"
    infile = ""
    pic = False
    try:
        opts, args = getopt.getopt(argv,"s:i:o:v:p",["string=","infile=","outfile=","verbose=","pic="])
    except getopt.GetoptError:
        print('Usage 1: ./bin/parser.py [options][-s/-i/-o/-v/-p] [string]')
        sys.exit(2)
    
    for opt, arg in opts:
        if opt in ("-s", "--string"):
            infile = arg            
        elif opt in ("-i", "--infile"):
            infile = file(arg)
        elif opt in ("-o", "--outfile"):
            outfile = arg
        elif opt in ("-p", "--pic"):
            pic = True
        elif opt in ("-v", "--verbose") and arg=="1":
            verbose = True

    if infile == "":
        print_usage()
        sys.exit(2)

    syntax_tree = parser.parse(infile)

    graph = pydot.Dot('gcc_lite: Syntax Tree', graph_type='digraph')
    generate_dot(graph, syntax_tree, 0)
    graph.get_node('0')[0].set_shape('doubleoctagon')
    graph.get_node('0')[0].set_color('orange')
    graph.get_node('0')[0].set_style('filled')

    graph.write_raw(outfile)
    if(pic):
        graph.write_png("ast.png")
        print("Graph printed")
    

if __name__ == "__main__":
    if sys.argv[1] in ("-h", "--help"):
        display_help()
        sys.exit(2)
    main(sys.argv[1:])