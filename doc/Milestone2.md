## Objective
In this milestone, we have to develop a parser for the source language that outputs the abstract syntax tree in a graphical form.

To draw the tree, we use a tool called graphviz(http://www.graphviz.org/). There are two components of graphviz that we have used:

The language for describing the tree called DOT, and
A tool called dot.
For example, if graph1.dot is a DOT script describing the tree, then

`$ dot -Tps graph1.dot -o graph1.ps`
generates a postscript program containing the drawing of the tree. The dot tool will completely take care of the tree layout. We just have to specify in the DOT language -  the nodes, their labels and the edges. On some platforms, we get GUI tools that can directly render and display a dot file. Read about the DOT language from http://www.graphviz.org/Documentation.php

Specifically we have to do the following:

1. Prepare or Download the token specification and grammar specification for your language.
2. Write/update the scanner script to detect tokens.. NOTE: In some implementation tools, scanner is always integrated with the parser.
3. Now take the grammar itself and convert it to a script accepted by YACC like tool. Link it with the scanner generated earlier.
4. Add actions to the grammar script so that the output of the parser is a DOT script representing the abstract syntax tree.
5. This DOT script, when processed by the graphviz tool (dot or other)  should produce a visual diagram of the tree.
6. Submit 5 non-trivial programs that can be processed with your compiler (milestone 2).

The leaves are to be labeled either by the token names or the lexemes (or both).

Do not update the TAG after the deadline for the assignment is over.
