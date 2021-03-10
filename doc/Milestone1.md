
In this milestone, you have to construct a scanner the source language to output the tokens in a tabular form.

Specifically you have to do the following:

Prepare or Download the token specification for your language. See Project: Source Language Features.
Modify the lexer script to detect tokens. A sample is already given on the page shared. Test it by generating a standalone scanner for the tokens and feeding it programs written in source language.  In the tutorial about Lex tools (to happen very soon), we shall discuss how to generate standalone scanners.
Submit 5 non-trivial programs that can be processed with your compiler (milestone 1).
OUTPUT

The output of the scanner should be a table describing the stream of tokens. It should list the line number and the column number where the token starts, and the lexeme associated with the token. You can ignore whitespaces from the table, but do count them for column number and line number calculations. For simplicity, you can assume all tabs use fixed number of columns (1or 4 or 8 ...). You are free to choose your own token names.

For example (note that this is just an illustration. your output can differ depending on your token names):

Input.c:

int main() {

 return 0;

}

Output of your Scanner:

ScannerOutput.png

