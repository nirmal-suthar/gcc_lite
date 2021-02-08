from ply import lex
from ply.lex import TOKEN
from tabulate import tabulate
import re
import sys

keywords = {
    'asm':'ASM',
    'break':'BREAK',
    'case':'CASE',
    'char':'CHAR',
    'const':'CONST',
    'continue':'CONTINUE',
    'default':'DEFAULT',
    'do':'DO',
    'double':'DOUBLE',
    'else':'ELSE',
    'enum':'ENUM',
    'extern':'EXTERN',
    'float':'FLOAT',
    'for':'FOR',
    'goto':'GOTO',
    'if':'IF',
    'inline':'INLINE',
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
    '_Alignas':'ALIGNAS',
    '_Alignof':'ALIGNOF',
    '_Atomic':'ATOMIC',
    '_Bool':'BOOL',
    '_Complex':'COMPLEX',
    '_Generic':'GENERIC',
    '_Imaginary':'IMAGINARY',
    '_Noreturn':'NORETURN',
    '_Static_assert':'STATIC_ASSERT',
    '_Thread_local':'THREAD_LOCAL',
    '__func__':'FUNC_NAME',
}

# List of token names. 
tokens = [
        # ID
        'IDENTIFIER',

        # Constant 
        'I_CONSTANT',
        'F_CONSTANT',
        'B_CONSTANT',
        'C_CONSTANT',
        'STRING_LITERAL',

        # Arithematic Operator
        'MINUS_OP',
        'PLUS_OP',
        'MULT_OP',
        'DIV_OP',
        'MOD_OP',

        # Bit Operator
        'XOR_OP',
        'OR_OP',
        'S_OR_OP',
        'S_AND_OP',
        'AND_OP',
        'NOT_OP',
        'LSHIFT_OP',
        'RSHIFT_OP',

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
        'LSHIFT_ASSIGN',
        'RSHIFT_ASSIGN',

        # Misc Operator
        'INC_OP',
        'DEC_OP',
        'PTR_OP',
        'BN_OP',

        # Comparison Operator
        'EQ_OP',
        'NEQ_OP',
        'GT_OP',
        'GEQ_OP',
        'LT_OP',
        'LEQ_OP',
        'EQUAL',

        # Parenthesis
        'L_PAREN',
        'R_PAREN',
        'LC_PAREN',
        'RC_PAREN',
        'LS_PAREN',
        'RS_PAREN',

        # Other
        'COMMA',
        'DOT',
        'SEMICOLON',
        'COLON',
        'ELLIPSIS',
        'QMARK',
        ] + list(keywords.values())


# Arithematic Operator
t_PLUS_OP       = r'\+'
t_MINUS_OP      = r'-'
t_DIV_OP        = r'/'
t_MULT_OP       = r'\*'
t_MOD_OP        = r'%'

# Bit Operator
t_XOR_OP        = r'\^'
t_S_OR_OP       = r'\|' #single or
t_OR_OP         = r'\|\|'
t_S_AND_OP      = r'&'  #single and
t_AND_OP        = r'&&'
t_NOT_OP        = r'!'
t_LSHIFT_OP     = r'<<'
t_RSHIFT_OP     = r'>>'

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
t_LSHIFT_ASSIGN = r'<<='
t_RSHIFT_ASSIGN = r'>>='

# Misc Operator
t_INC_OP        = r'\+\+'
t_DEC_OP        = r'--'
t_PTR_OP        = r'->'
t_BN_OP         = r'~'

# Comparison Operator
t_EQ_OP         = r'=='
t_NEQ_OP        = r'!='
t_GT_OP         = r'>'
t_GEQ_OP        = r'>='
t_LT_OP         = r'<'
t_LEQ_OP        = r'<='
t_EQUAL         = r'='

# Parenthesis
t_L_PAREN       = r'\('
t_R_PAREN       = r'\)'
t_LC_PAREN      = r'{|(<%)'
t_RC_PAREN      = r'}|(%>)'
t_LS_PAREN      = r'(\[)|(<:)'
t_RS_PAREN      = r'(\])|(:>)'

# Other
t_COMMA         = r','
t_DOT           = r'\.'
t_SEMICOLON     = r';'
t_COLON         = r':'
t_ELLIPSIS      = r'\.\.\.'
t_QMARK         = r'\?'

@TOKEN(r'[a-zA-Z_][0-9a-zA-Z_]*')
def t_IDENTIFIER(t):
    t.type = keywords.get(t.value, 'IDENTIFIER')
    return t

# constants
 
I_DECIMAL_LIT = r'[1-9][0-9]*'
I_HEX_LIT = r'0[xX][0-9a-fA-F]+'
I_OCTAL_LIT = r'0[0-7]*'

I_SUFFIX = '(((u|U)(ll|LL|l|L)?)|((ll|LL|l|L)(u|U)?))'
F_SUFFIX = '[fFlL]'

F_EXP_LIT = r'(\d+([Ee][+-]?\d+))|((\d*\.\d+([Ee][+-]?\d+)?)|(\d+\.\d*([Ee][+-]?\d+)?))'
# TODO: add hex float number if needed (as per ANSCI C spec)

t_I_CONSTANT = '(('+')|('.join([I_DECIMAL_LIT,I_HEX_LIT,I_OCTAL_LIT])+'))('+I_SUFFIX+')?'
t_F_CONSTANT = '(('+')|('.join([F_EXP_LIT])+'))('+F_SUFFIX+')?'
t_B_CONSTANT = '(true)|(false)'
t_C_CONSTANT = r'\'([^\'\\\n]|(\\.))?\''
t_STRING_LITERAL    = r'\"([^"\\\n]|(\\.))*\"'

# Assuming tab equal to 1 column
t_ignore = ' \t\v\f'

# New line
def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)
    t.lexer.pos_newline = t.lexpos

# Hnadling Oneline Comment
def t_oneline_comment(t):
    r'//(.)*'
    pass

# STARTS: Handling Mutliline Comment 

# States for Multiline Comment handling
states = (
    ('mcomment', 'exclusive'),
)

# multiline comment begins
def t_mcomment(t):
    r'/\*'
    t.lexer.push_state('mcomment')

# handle newline in mcomment state
def t_mcomment_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)
    t.lexer.pos_newline = t.lexpos

# multiline comment ends
def t_mcomment_end(t):
    r'.*\*/'
    t.lexer.pop_state()

# ignore anything that ends with newline in multiline comment
t_mcomment_ignore_comment = r'.+'

# ignore and error rule for mcomment
t_mcomment_ignore = ''

def t_mcomment_error(t):
    print("Incorrect comment syntax")

# ENDS: Handling Mutliline Comment 

# Error function
def t_error(t):
    print("Illegal character '%s'" % t.value[0])
    t.lexer.skip(1)

# Function to find column number
def find_column(input, token):
    line_start = input.rfind('\n', 0, token.lexpos) + 1
    return (token.lexpos - line_start) + 1

if __name__ == "__main__":

    # Build the lexer
    lexer = lex.lex(debug = 0)

    # Calculate column number from lexpos
    lexer.pos_newline = -1 
    
    with open(sys.argv[1], "r") as f:
        inp = f.read()
    lexer.input(inp)
    

    tokenList = []
    while True:
        tok = lexer.token()
        if tok:
            lineno = str(tok.lineno)
            columnno = str(tok.lexpos - lexer.pos_newline)
            tokenList.append([tok.type,tok.value,lineno,columnno])
        else:
            break
    
    print(tabulate(tokenList, headers=["Token", "Lexeme", "Line#", "Column#"]))