from ply import lex
from ply.lex import TOKEN
import re
import sys

keywords = {
    'include':'INCLUDE',
    'asm':'ASM',
    'bool':'BOOL',
    'break':'BREAK',
    'case':'CASE',
    'char':'CHAR',
    'const':'CONST',
    'continue':'CONTINUE',
    'default':'DEFAULT',
    'delete':'DELETE',
    'do':'DO',
    'double':'DOUBLE',
    'else':'ELSE',
    'enum':'ENUM',
    'extern':'EXTERN',
    'float':'FLOAT',
    'for':'FOR',
    'goto':'GOTO',
    'if':'IF',
    'int':'INT',
    'long':'LONG',
    'return':'RETURN',
    'short':'SHORT',
    'signed':'SIGNED',
    'sizeof':'SIZEOF',
    'static':'STATIC',
    'struct' : 'STRUCT',
    'switch':'SWITCH',
    'typedef':'TYPEDEF',
    'union':'UNION',
    'unsigned':'UNSIGNED',
    'void':'VOID',
    'volatile':'VOLATILE',
    'while':'WHILE',
}

# List of token names. 
tokens = [
        # id and no
        'IDENTIFIER',
        'NUMBER',

        # arithematic operator
        'PLUSOP',
        'MINUSOP',
        'DIVOP',
        'MULTOP',
        'MODOP',

        'XOROP',
        'SOROP',
        'OROP',
        'SANDOP',
        'ANDOP',
        
        'ADD_ASSIGNOP',
        'SUB_ASSIGNOP',
        'MUL_ASSIGNOP',
        'DIV_ASSIGNOP',
        'MOD_ASSIGNOP',
        
        'AND_ASSIGNOP',
        'XOR_ASSIGNOP',
        'OR_ASSIGNOP',

        'INCOP',
        'DECOP',
        'BNOP',
        'LSHIFTOP',
        'RSHIFTOP',
        'LSHIFTEQOP',
        'RSHIFTEQOP',

        'LSHIFT',
        'RSHIFT',
        'LSHIFTEQ',
        'RSHIFTEQ',

        #comparison operator, =
        'EQCOMP',
        'NEQCOMP',
        'GTCOMP',
        'GTECOMP',
        'LTCOMP',
        'LTECOMP',
        'EQUAL',

        # Parenthesis
        'LPAREN',
        'RPAREN',
        'LCPAREN',
        'RCPAREN',
        'LSPAREN',
        'RSPAREN',

        # Quotes
        'SQUOTE',
        'DQUOTE',

        # OTHER
        'COMMA',
        'DOT',
        'SEMICOLON',
        'COLON',
        ] + list(keywords.values())


# Arithematic Operator
t_PLUSOP    = r'\+'
t_MINUSOP   = r'-'
t_DIVOP     = r'/'
t_MULTOP    = r'\*'
t_MODOP     = r'\%'

t_XOROP     = r'\^'
t_SOROP     = r'\|' #single or
t_OROP      = r'\|\|'
t_SANDOP    = r'\&'  #single and
t_ANDOP     = r'\&\&'

t_ADD_ASSIGNOP  = r'\+='
t_MOD_ASSIGNOP   = r'\%\='
t_SUB_ASSIGNOP = r'-='
t_MUL_ASSIGNOP  = r'\*='
t_DIV_ASSIGNOP   = r'/='

t_AND_ASSIGNOP  = r'\&\='
t_XOR_ASSIGNOP   = r'\^='
t_OR_ASSIGNOP   = r'\|='

t_INCOP   = r'\+\+'
t_DECOP  = r'--'
t_BNOP      = r'\~'
t_LSHIFT    = r'<<'
t_RSHIFT    = r'>>'
t_LSHIFTEQ = r'<<='
t_RSHIFTEQ = r'>>='

# Comparison Operator
t_EQCOMP    = r'=='
t_NEQCOMP   = r'!='
t_GTCOMP    = r'>'
t_GTECOMP   = r'>='
t_LTCOMP    = r'<'
t_LTECOMP   = r'<='
t_EQUAL     = r'='

# Parenthesis
t_LPAREN   = r'\('
t_RPAREN   = r'\)'
t_LCPAREN   = r'\{'
t_RCPAREN   = r'\}'
t_LSPAREN   = r'\['
t_RSPAREN   = r'\]'

# Quotes
t_SQUOTE    = r'\''
t_DQUOTE    = r'\"'

# Other
t_COMMA         = r','
t_DOT           = r'\.'
t_SEMICOLON     = r';'
t_COLON         = r':'

@TOKEN(r'[a-zA-Z_][0-9a-zA-Z_]*')
def t_IDENTIFIER(t):
    t.type = keywords.get(t.value, 'IDENTIFIER')
    return t

decimal_lit = r'[1-9][0-9]*'
hex_lit = r'0[xX][0-9a-fA-F]+'
octal_lit = r'0[0-7]*'

t_NUMBER = '(' + decimal_lit + '|' + hex_lit + '|' + octal_lit + ')'

def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)
    t.lexer.pos_newline = t.lexpos

# Assuming tab equal to 1 column
t_ignore = ' \t'

def t_COMMENT(t):
    r'((//)[^\n\r]*)|(/\*([^*]|[\r\n]|(\*+([^*/]|[\r\n])))*\*+/)'
    pass

def t_error(t):
    print("Illegal character '%s'" % t.value[0])
    t.lexer.skip(1)

# function to find column number
def find_column(input, token):
    line_start = input.rfind('\n', 0, token.lexpos) + 1
    return (token.lexpos - line_start) + 1

if __name__ == "__main__":

    # Build the lexer
    lexer = lex.lex(debug = 0)
    lexer.pos_newline = -1 # to calculate column number from lexpos
    
    with open(sys.argv[1], "r") as f:
        inp = f.read()
    lexer.input(inp)
    
    print("Token", "Lexeme", "Line#", "Column#", sep="\t\t\t")
    while True:
        tok = lexer.token()
        if tok:
            print(tok.type, tok.value, tok.lineno, tok.lexpos - lexer.pos_newline, sep="\t\t\t")
            # print(tok)
        else:
            break
