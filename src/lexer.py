#! /usr/bin/env python3

from ply import lex
from ply.lex import TOKEN
from tabulate import tabulate
import re
import sys


keywords = {
    'break':'BREAK',
    'case':'CASE',
    'char':'CHAR',
    'continue':'CONTINUE',
    'default':'DEFAULT',
    'else':'ELSE',
    'float':'FLOAT',
    'for':'FOR',
    'if':'IF',
    'int':'INT',
    'return':'RETURN',
    'sizeof':'SIZEOF',
    'struct' : 'STRUCT',
    'switch':'SWITCH',
    'typedef':'TYPEDEF',
    'void':'VOID',
    'while':'WHILE',
}

# List of token names. 
tokens = [
        # Comment
        'COMMENT',
        
        # ID
        'IDENTIFIER',
        'TYPE_NAME',

        # Constant 
        'I_CONSTANT',
        'F_CONSTANT',
        'C_CONSTANT',
        'STRING_LITERAL',

        # Bit Operator
        'OR_OP',
        'AND_OP',
        'LEFT_OP',
        'RIGHT_OP',

        # Arithmetic Assignment
        'ADD_ASSIGN',
        'SUB_ASSIGN',
        'MUL_ASSIGN',
        'DIV_ASSIGN',
        'MOD_ASSIGN',
        
        # Bit Assignment
        'AND_ASSIGN',
        'XOR_ASSIGN',
        'OR_ASSIGN',
        'LEFT_ASSIGN',
        'RIGHT_ASSIGN',

        # Misc Operator
        'INC_OP',
        'DEC_OP',
        'PTR_OP',

        # Comparison Operator
        'EQ_OP',
        'NE_OP',
        'GE_OP',
        'LE_OP',

        ] + list(keywords.values())

literals = [

        # Arithematic Operator
        '-', '+', '*', 
        '/', '%', '=',
        '>', '<',

        # Parenthesis
        '(', ')',
        '[', ']',
        '{', '}',

        # Bit Operator
        '.', '&', '!',
        '~', '|', '^',

        # Other
        ';', ',',
        ':', '?',
        ]

# Bit Operator
t_OR_OP         = r'\|\|'
t_AND_OP        = r'&&'
t_LEFT_OP       = r'<<'
t_RIGHT_OP      = r'>>'

# Arithmetic Assignment
t_ADD_ASSIGN    = r'\+='
t_MOD_ASSIGN    = r'%='
t_SUB_ASSIGN    = r'-='
t_MUL_ASSIGN    = r'\*='
t_DIV_ASSIGN    = r'/='

# Bit Assignment
t_AND_ASSIGN    = r'&='
t_XOR_ASSIGN    = r'\^='
t_OR_ASSIGN     = r'\|='
t_LEFT_ASSIGN   = r'<<='
t_RIGHT_ASSIGN  = r'>>='

# Misc Operator
t_INC_OP        = r'\+\+'
t_DEC_OP        = r'--'
t_PTR_OP        = r'->'

# Comparison Operator
t_EQ_OP         = r'=='
t_NE_OP         = r'!='
t_GE_OP         = r'>='
t_LE_OP         = r'<='

# Curly Paranthesis
@TOKEN(r'{|(<%)')
def t_LC_PAREN(t):
    t.type = '{'
    return t

@TOKEN(r'}|(%>)')
def t_RC_PAREN(t):
    t.type = '}'
    return t

# Square Parenthesis
@TOKEN(r'(\[)|(<:)')
def t_LS_PAREN(t):
    t.type = '['
    return t

@TOKEN(r'(\])|(:>)')
def t_RS_PAREN(t):
    t.type = ']'
    return t

# Identifier
struct_kw = False
@TOKEN(r'[a-zA-Z_][0-9a-zA-Z_]*')
def t_IDENTIFIER(t):
    t.type = keywords.get(t.value, 'IDENTIFIER')

    if t.type == 'IDENTIFIER' and not t.lexer.struct_kw and symtable.lookup_alias(t.value):
        # Do not convert identifier after struct keyword into typename
        t.type = 'TYPE_NAME'

    if t.type == 'STRUCT':
        t.lexer.struct_kw = True
    else:
        t.lexer.struct_kw = False
    return t

# Constants

I_DECIMAL_LIT = r'[1-9][0-9]*'
I_HEX_LIT = r'0[xX][0-9a-fA-F]+'
I_OCTAL_LIT = r'0[0-7]*'

I_SUFFIX = '(((u|U)(ll|LL|l|L)?)|((ll|LL|l|L)(u|U)?))'
F_SUFFIX = '[fFlL]'

F_EXP_LIT = r'(\d+([Ee][+-]?\d+))|((\d*\.\d+([Ee][+-]?\d+)?)|(\d+\.\d*([Ee][+-]?\d+)?))'
# TODO: add hex float number if needed (as per ANSI C spec)

@TOKEN('(('+')|('.join([F_EXP_LIT])+'))('+F_SUFFIX+')?')
def t_F_CONSTANT(t):
    return t

@TOKEN('(('+')|('.join([I_DECIMAL_LIT,I_HEX_LIT,I_OCTAL_LIT])+'))('+I_SUFFIX+')?')
def t_I_CONSTANT(t):
    return t

t_C_CONSTANT        = r'\'([^\'\\\n]|(\\.))\''
t_STRING_LITERAL    = r'\"([^"\\\n]|(\\.))*\"'

# Assuming tab equal to 1 column
t_ignore = ' \t\v\f'

# New line
def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)
    # t.lexer.pos_newline = t.lexpos #FIXME: redundant

# Handling Comments
@TOKEN(r'(//.*|/\*(\*(?!/)|[^*])*\*/)')
def t_COMMENT(t):
    # Update line number according to no. of newline.
    t.lexer.lineno += (t.value.count("\n"))
    pass

# Error function
def t_error(t):
    print("Illegal character '%s'" % t.value[0])
    t.lexer.skip(1)

# Function to find column number
def find_column(input, token):
    line_start = input.rfind('\n', 0, token.lexpos) + 1
    return (token.lexpos - line_start) + 1


# Build the lexer
lexer = lex.lex(debug = 0)
lexer.struct_kw = False

def main_lexer(ifile):
    lexer.input(ifile)
    tokenList = []
    while True:
        tok = lexer.token()
        if tok:
            lineno = str(tok.lineno)
            columnno = str(find_column(inp, tok))
            # columnno = str(tok.lexpos - lexer.pos_newline) #TODO: failing
            tokenList.append([tok.type,tok.value,lineno,columnno])
        else:
            break
    
    print(tabulate(tokenList, headers=["Token", "Lexeme", "Line#", "Column#"]))


if __name__ == "__main__":
    with open(sys.argv[1], "r") as f:
        inp = f.read()
    main_lexer(inp)

# from parser import symtable
from helper import symtable
