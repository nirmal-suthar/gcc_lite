
**AST Generation post Semantic Analysis**

In the next milestone, you extend the project to perform semantic analysis. The goal is to convert your program into an AST Representation to be used by later stages (Intermediate and Final code generation, optimization, etc.). Once again, you will use "actions" in your lexer/parser to achieve the desired outcome.

1.  As you process the program, the information contained in the declarations is stored in the symbol table. This information includes the types of variables and functions, and the sizes and offsets of variables.
2.  When you process the non-declarative part, then two things happen:

(a) The information in the symbol table is used to ensure that the variables are used within the scope of their declarations and are used in a type-correct manner. If they are not, then the program is rejected.

(b) If the program is syntactically and semantically (type and scope) correct, a tree structure called an AST is generated (you have already generated AST earlier, without worrying about the semantics).

AST along with the information in the symbol table is used to generate code. In this assignment,  **you will construct the symbol table, do the semantic checks and then generate ASTs.**  You will need to define the AST nodes corresponding to various constructs in the program. Remember that AST does away with the redundancy in the parse tree.

You can create the following two-level symbol table structure.

1.  A global symbol table that maps function names to their local symbol tables.
2.  A local symbol table for every function that contains the relevant information for the parameters and the local variables of the function.

Make sure your symbol table is "extensible" since you might discover the need to store new information as the project progresses.

Along with the construction of the symbol table, process the non-declarative part of the program to create an AST. Perform semantic checks to ensure that semantically incorrect programs are rejected.

Your compiler's output for  **good programs**  will consist of:

(a) A dump of the symbol table of each function as a CSV file (the columns of CSV can be of your choice), and

(b) A dump of the AST of the functions in the dot format (this part should already be ready as Milestone 2).

For  **bad programs,**  your compiler should mention the error that caused the program to be rejected (not just "error at line YYY").  
  
Acceptable errors could look like (but not limited to):

-   "Type mismatch in line 72",
-   "Incompatible operator + with operand of type string",
-   "Undeclared variable on line 38”.

Here are some more things that you have to keep in mind:

1.  **Operator/Function disambiguation:**  This will be a good time to pin down the exact operator function that will be used in an expression. For example, for x + y,: (a) If x and y are both int-s, resolve the + to (say) +int. (b) If x and y are both floats, resolve the + to +float.
2.  **Type Casting:**  Continuing with the above example of x + y, if x is an int and y is a float, cast x to a float and resolve the + to +float. The AST will correspond to +float (to-float (x), y).
3.  Here is an (incomplete) list of errors that you have to look out for:

-   All forms of type errors. Examples: Array index not being an integer. Variables being declared as being the void type.
-   All form of scoping errors.
-   Non-context-free restrictions on the language. For example, an array indexed with more indices than its dimension and functions being passed with lesser than required number of parameters.
-   Field access (x.f) applied to non structure/union variables (x in this case) or to a structure/union variable without having the appropriate field (f in this case).
-   and more ...

**SUBMISSION:**

1. Tag your repository version using "**git tag semantics**".  
2. Create and Submit a single page PDF. One submission per group. Describing any logistic changes since milestone 2; such as repository structure, implementation language etc.  
Also mention the output of "**git show semantics**".

  
Do not update the TAG after the deadline for the assignment is over.