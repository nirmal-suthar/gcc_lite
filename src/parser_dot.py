import sys
import pydot
from parser import parser

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
        raise Exception('invalid type of tree')


if __name__ == "__main__":

    # FIXME: use argparser instead of script

    with open(sys.argv[1], "r") as f:
        input_file = f.read()
    syntax_tree = parser.parse(input_file)

    graph = pydot.Dot('gcc_lite: Syntax Tree', graph_type='digraph')
    generate_dot(graph, syntax_tree, 0)
    graph.get_node('0')[0].set_shape('doubleoctagon')
    graph.get_node('0')[0].set_color('orange')
    graph.get_node('0')[0].set_style('filled')
   
    # print(graph.to_string())

    graph.write_raw(sys.argv[2])
    # graph.write_png("ast.png")
    # print('Dot file generated at: "{}" '.format(sys.argv[2]))
