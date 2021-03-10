In this milestone, you have to develop a parser for the source language that outputs the abstract syntax tree in a graphical form.

To draw the tree, use a tool called graphviz(http://www.graphviz.org/). There are two components of graphviz that you will use:

The language for describing the tree called DOT, and
A tool called dot.
For example, if graph1.dot is a DOT script describing the tree, then

$ dot -Tps graph1.dot -o graph1.ps
generates a postscript program containing the drawing of the tree. The dot tool will completely take care of the tree layout. You just have to specify in the DOT language -  the nodes, their labels and the edges. On some platforms, you get GUI tools that can directly render and display a dot file. Read about the DOT language from http://www.graphviz.org/Documentation.php

Study the documentation of YACC-equivalent tool you use to understand how actions are specified. 

Specifically you have to do the following:

Prepare or Download the token specification and grammar specification for your language.
Write/update the scanner script to detect tokens.. NOTE: In some implementation tools, scanner is always integrated with the parser.
Now take the grammar itself and convert it to a script accepted by YACC like tool. Link it with the scanner generated earlier.
Add actions to the grammar script so that the output of the parser is a DOT script representing the abstract syntax tree.
This DOT script, when processed by the graphviz tool (dot or other)  should produce a visual diagram of the tree.
Submit 5 non-trivial programs that can be processed with your compiler (milestone 2).
The leaves are to be labeled either by the token names or the lexemes (or both).

DETAILS

Continue your development in the same repository you used for the milestone 1.The TAs will use automated scripts to grade your submission, so the name of the executable will matter. For this milestone, you should generate an executable called “parser” in the bin directory

Update the README file with a brief description of your project and the steps to build and run it.
The TAs will spend approx. 15-20 minutes with you for evaluation. Make sure that your implementation builds and runs correctly with minimum number of commands. A typical example session could be:
$ cd /src 
$ make 
$ cd .. 
$ ./bin/parser ./test/test1.c -o myAST.dot      # execute the parser on test-case file test1.c and generate myAST.dot to contain AST
$ ...  # ... commands to view the generated AST ...

SUBMISSION:
1. Tag your repository version using "git tag parser".
2. Create and Submit a single page PDF. One submission per group. Describing any logistic changes since milestone 1; such as repository structure, implementation language etc. 
Also mention the output of "git show parser". 


Do not update the TAG after the deadline for the assignment is over.