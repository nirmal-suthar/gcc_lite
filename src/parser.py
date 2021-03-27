#! /usr/bin/env python3

from ply import yacc
from lexer import lexer, tokens
from classes import *

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


# Precedence not needed in operator as ansi C has all 
# ambiguity fixed at grammer level
precedence = (
    ('nonassoc', 'IFX'),
    ('nonassoc', 'ELSE'),
)


operator_type={}
operator_type["+"]=["int","float","char"]
operator_type["-"]=operator_type["+"]
operator_type["*"]=operator_type["+"]
operator_type["/"]=operator_type["+"]
operator_type["%"]=["int"]

operator_type[">"]=["int","float","char"]
operator_type[">="]=operator_type[">"]
operator_type["<"]=operator_type[">"]
operator_type["<="]=operator_type[">"]
operator_type["||"]=operator_type[">"]
operator_type["&&"]=operator_type[">"]
operator_type["!"]=operator_type[">"]


operator_type["<<"]=["int"]
operator_type[">>"]=operator_type["<<"]
operator_type["|"]=["<<"]
operator_type["&"]=operator_type["|"]
operator_type["~"]=operator_type["|"]
operator_type["^"]=operator_type["|"]

types={}
types["float"]=["int","long long int", "long int" ,"float","char" ]
types["int"]=["float", "char","int"]
types["char"]=["int", "char"]
types["pointer"]=["int","float"]


# declarations
helper = SymbolTableHelper()
helper.newScope()

# --------------------------------------
#     SNIPPETS FOR ERROR CHECKINGS
# --------------------------------------
#  if helper.checkId(p[1],'current') or (p[1] in p[2].identList):
#         compilation_errors.add("Redeclaration Error", line_number.get()+1,\
#             "%s already declared"%p[1])
# if helper.checkType(p[1],'current'):
#         compilation_errors.add("Redeclaration Error", line_number.get()+1,\
#             "Type %s already declared"%p[1])
# if not helper.checkId(p[1],'default'):
#         compilation_errors.add('NameError', line_number.get()+1, '%s not declared'%p[1])
#  scope_ = helper.getNearest('func')
#     if scope_ == -1:
#         compilation_errors.add('Scope Error', line_number.get()+1, 'return is not in a function')
#         return


def allowed_type(converted_from,converted_to):
    global allowed_types
    if converted_from==converted_to:
        return True
    if "|" in converted_from or "|" in converted_to:
        if "|" in converted_from and converted_from[-1]=='p' and (converted_to[-1]=="p" or converted_to in allowed_types["pointer"]):
            return True
        return False
    if converted_to not in allowed_types.keys():
        return False
    return (converted_from in allowed_types[converted_to])

def op_allowed(op, typ):
    global operator_allowed
    if op not in operator_allowed.keys():
        return True
    return typ in operator_allowed[op]

def cast_string(place, converted_from,converted_to,t=None):
    
    if converted_from==converted_to:
        return {"place":place,"code":[]}
    if allowed_type(converted_from,converted_to)==True:
        if t==None:
            t=helper.newVar(type1_ = converted_to)
        return {"place":t,"code":[ t +" = " + converted_from+"_to_"+converted_to+"("+place+")" ]}
    return False

def phelper(p):
    p_name = sys._getframe(1).f_code.co_name
    global helper
    helper.varCount+=1
    out = (p_name[2:],cnt)
    for each in range(len(p)-1):
        if( not isinstance(p[each + 1], OBJ) ):
            helper.varCount+=1
            token = p[each + 1]
            p[each + 1] = Node()
            p[each + 1].data = token
            p[each + 1].parse = (token, cnt) 

# #############################################################################
# Helper Functions for semantic analysis      
# #############################################################################

def assign(p,x):
    if isinstance(p[x].data,str):
        return p[x].data
    else:
        return p[x].data.copy()


# #############################################################################
# Start, Empty and Error handling             
# #############################################################################

def p_start(p):
    ''' start : translation_unit
    '''
    p[0] = ['start'] + p[1:]
    pass


# def p_empty(p):
#     """ empty :
#     """
#     p[0] = ['empty'] + p[1:]
#     pass


def p_error(p):
    position = (
        p.lexer.lexpos
        - sum(map(lambda line: len(line) + 1, p.lexer.lines[: p.lineno - 1]))
        - len(p.value)
        + 1
    )
    print(bcolors.BOLD+'{}:{}:{}:'.format(p.lexer.filename,p.lineno, position)+bcolors.ENDC,end='')
    print(bcolors.FAIL+' SyntaxError: '+bcolors.ENDC,'Unexpected token {}'.format(p.value))
    print('     {} |{}'.format(p.lineno,p.lexer.lines[p.lineno - 1][:position-1]),end='')
    print(bcolors.WARNING + bcolors.UNDERLINE + '{}'.format(
        p.lexer.lines[p.lineno - 1][position-1:position-1+len(p.value)]
        )+bcolors.ENDC+bcolors.ENDC,end='')
    print('{}'.format(p.lexer.lines[p.lineno - 1][position-1+len(p.value):]))


# #############################################################################
# Expressions            
# #############################################################################

def p_constant(p):
    ''' constant : I_CONSTANT
            | F_CONSTANT
            | C_CONSTANT
    '''
    p[0] = ['constant'] + p[1:]
    pass


def p_primary_expression(p):
    ''' primary_expression : IDENTIFIER
            | constant
            | STRING_LITERAL
            | '(' expression ')'
    '''
    p[0] = ['primary_expression'] + p[1:]
    pass

#isme grammar bada karna hoga bahut. bahut chod h isme
def p_postfix_expression(p):
    ''' postfix_expression : primary_expression
            | postfix_expression '[' expression ']'
            | postfix_expression '(' ')'
            | postfix_expression '(' argument_expression_list ')'
            | postfix_expression '.' IDENTIFIER
            | postfix_expression PTR_OP IDENTIFIER
            | postfix_expression INC_OP
            | postfix_expression DEC_OP
    '''
    p[0] = ['postfix_expression'] + p[1:]
    pass

def p_argument_expression_list(p):
    ''' argument_expression_list : assignment_expression
            | argument_expression_list ',' assignment_expression
    '''
    p[0] = ['argument_expression_list'] + p[1:]
    pass

#isko do me divide
def p_unary_expression(p):
    ''' unary_expression : postfix_expression
            | INC_OP unary_expression
            | DEC_OP unary_expression
            | unary_operator cast_expression
            | SIZEOF unary_expression
            | SIZEOF '(' type_name ')'
    '''
    p[0] = ['unary_expression'] + p[1:]
    pass

#ye same h
def p_unary_operator(p):
    ''' unary_operator : '&'
            | '*'
            | '+'
            | '-'
            | '~'
            | '!'
    '''
    p[0] = Node()
    p[0].parse = ['unary_operator'] + p[1:]
    p[0].data = assign(p,1)
    pass

#ye same h
def p_cast_expression(p):
    ''' cast_expression : unary_expression
            | '(' type_name ')' cast_expression
    '''
    p[0] = Node()
    p[0].parse = ['cast_expression'] + p[1:]

    if len(p)==2 :
        p[0].data = assign(p,1)
        p[0].code = p[1].code

    if len(p)==5:
        rex = r'\|p*a+$'
        x= re.fullmatch(rex, p[2].data["type"])
        if x!=None or not allowed_type(p[4].data["type"], p[2].data["type"]):
            print("Type casting not allowed " + str(p.lineno(0)))
        
        p[0].data = {}
        p[0].data["type"]=p[2].data["type"]

    pass

#ye same h
def p_multiplicative_expression(p):
    ''' multiplicative_expression : cast_expression
            | multiplicative_expression '*' cast_expression
            | multiplicative_expression '/' cast_expression
            | multiplicative_expression '%' cast_expression
    '''
    p[0] = Node()
    p[0].parse = ['multiplicative_expression'] + p[1:]
    p[0].placeList[1] = p[1].placeList[1]

    if len(p)==2:
        p[0].data = assign(p,1)
        p[0].place = p[1].place
        p[0].code = p[1].code


    pass

#ye same h
def p_additive_expression(p):
    ''' additive_expression : multiplicative_expression
            | additive_expression '+' multiplicative_expression
            | additive_expression '-' multiplicative_expression
    '''
    p[0] = Node()
    p[0].parse = ['additive_expression'] + p[1:]
    if len(p)==2:
        p[0].data = assign(p,1)
        p[0].code = p[1].code

    if len(p)==4:
        allowed_type = ["int", "char", "float"]
        if p[1].data["type"] not in allowed_type or p[3].data["type"] not in allowed_type:
            print("Type not compatible with +/- at lineno " + str(p.lineno(0)))
    pass

#ye same h
def p_shift_expression(p):
    ''' shift_expression : additive_expression
            | shift_expression LEFT_OP additive_expression
            | shift_expression RIGHT_OP additive_expression
    '''
    p[0] = Node()
    p[0].parse = ['shift_expression'] + p[1:]

    if len(p) == 2:
        p[0].data = assign(p,1)
        p[0].code = p[1].code
    
    if len(p)==4:
        allowed_type = ["int"]
        if not(p[1].data["type"] in allowed_type and p[3].data["type"] in allowed_type):
            print(" Type not compatible with bitwise shift operation at lineno "+p.lineno(0))
        p[0].data = {"type" : "int"}
    pass

# ye same h
def p_relational_expression(p):
    ''' relational_expression : shift_expression
            | relational_expression '<' shift_expression
            | relational_expression '>' shift_expression
            | relational_expression LE_OP shift_expression
            | relational_expression GE_OP shift_expression
    '''
    p[0] = Node()
    p[0].parse = ['relational_expression'] + p[1:]

    if len(p) == 2:
        p[0].data = assign(p,1)
        p[0].code = p[1].code
    
    if len(p)==4:
        allowed_type = ["int", "char", "float"]
        if not(p[1].data["type"] in allowed_type and p[3].data["type"] in allowed_type):
            print(" Type not compatible with relational operation at lineno "+p.lineno(0))
        p[0].data = {"type" : "int"}

    pass

#ye same h
def p_equality_expression(p):
    ''' equality_expression : relational_expression
            | equality_expression EQ_OP relational_expression
            | equality_expression NE_OP relational_expression
    '''
    p[0] = ['equality_expression'] + p[1:]
    pass

#ye same h
def p_and_expression(p):
    ''' and_expression : equality_expression
            | and_expression '&' equality_expression
    '''
    p[0] = ['and_expression'] + p[1:]
    pass

#ye same h
def p_exclusive_or_expression(p):
    ''' exclusive_or_expression : and_expression
            | exclusive_or_expression '^' and_expression
    '''
    p[0] = ['exclusive_or_expression'] + p[1:]
    pass

#ye same h
def p_inclusive_or_expression(p):
    ''' inclusive_or_expression : exclusive_or_expression
            | inclusive_or_expression '|' exclusive_or_expression
    '''
    # p[0] = ['inclusive_or_expression'] + p[1:]
    p[0] = Node()
    p[0].parse = ['logical_or_expression'] + p[1:]

    if len(p)==2:
        p[0].data = assign(p,1)
        p[0].placeList[0] = p[1].placeList[0]
        p[0].code = p[1].code 
    
    if len(p)==4:
        allowed_type = operator_type["||"]
        if not (p[1].data["type"] in allowed_type and p[3].data["type"] in allowed_type):
            print("Type not consistent for OR exp at lineno " + str(p.lineno(0)))
            exit()

        p[0].data = { "type" : "int" }
               #placelist n code part to be assigned
    pass

#ye same
def p_logical_and_expression(p):
    ''' logical_and_expression : inclusive_or_expression
            | logical_and_expression AND_OP inclusive_or_expression
    '''
    # p[0] = ['logical_and_expression'] + p[1:]
    p[0] = Node()
    p[0].parse = ['logical_and_expression'] + p[1:]

    if len(p)==2:
        p[0].data = assign(p,1)
        p[0].placeList[0] = p[1].placeList[0]
        p[0].code = p[1].code 

    if len(p)==4:
        allowed_type = operator_type["&&"]
        if not (p[1].data["type"] in allowed_type and p[3].data["type"] in allowed_type):
            print("Type not consistent for AND exp at lineno " + str(p.lineno(0)))
            exit()

        p[0].data = { "type" : "int" } 
        p[0].placeList[0] = helper.newVar(type_="int")
        t=cast_string(p[1].placeList[0],p[1].data["type"],"int")
        t1=cast_string(p[3].placeList[0],p[3].data["type"],"int")
        p[0].code = p[1].code + p[3].code + t["code"] +t1["code"]+ [ p[0].placeList[0] + " = " + t["place"] + str(p[2].data) + t1["place"] ]

    pass

def p_logical_or_expression(p):
    ''' logical_or_expression : logical_and_expression
            | logical_or_expression OR_OP logical_and_expression
    '''
    p[0] = Node()
    p[0].parse = ['logical_or_expression'] + p[1:]

    if len(p)==2:
        p[0].data = assign(p,1)
        p[0].placeList[0] = p[1].placeList[0]
        p[0].code = p[1].code 

    if len(p)==4:
        allowed_type = operator_type["||"]
        if not (p[1].data["type"] in allowed_type and p[3].data["type"] in allowed_type):
            print("Type not consistent for AND exp at lineno " + str(p.lineno(0)))
            exit()
        p[0].data = { "type" : "int" } 
        p[0].placeList[0] = helper.newVar(type_="int")
        t=cast_string(p[1].placeList[0],p[1].data["type"],"int")
        t1=cast_string(p[3].placeList[0],p[3].data["type"],"int")
        p[0].code = p[1].code + p[3].code + t["code"] +t1["code"]+ [ p[0].placeList[0] + " = " + t["place"] + str(p[2].data) + t1["place"] ]

    pass

#ye same h
def p_conditional_expression(p):
    ''' conditional_expression : logical_or_expression
            | logical_or_expression '?' expression ':' conditional_expression
    '''
    # p[0] = ['conditional_expression'] + p[1:]
    p[0] = Node()
    p[0].parse = ['conditional_expression'] + p[1:]
    if len(p) == 2:
        p[0].data = assign(p,1)
        p[0].placeList[0] = p[1].placeList[0]
        p[0].code = p[1].code 
    else:
        allowed_type = operator_type["||"]
        if p[1].data["type"] not in allowed_type:
            print("Expected integer, char or float, found something else at lineno " + str(p.lineno(0)))
            exit()
        if p[3].data["type"] != p[5].data["type"]:
            print("Type not consistent at lineno " + str(p.lineno(0)))
            exit()
        p[0].data = { "type" : p[3].data["type"] }
        #placelist n code part to be assigned

    pass

#same h
def p_assignment_expression(p):
    ''' assignment_expression : conditional_expression
            | unary_expression assignment_operator assignment_expression
    '''
    p[0] = Node()
    p[0].parse = ['assignment_expression'] + p[1:]
    p[0].placeList[1] = p[1].placeList[1]

    temp = p[1].placeList[1] if p[1].placeList[1] != None else  p[1].placeList[0]

    if len(p)==2:
        p[0].data = assign(p,1)
        p[0].placeList[0] = p[1].placeList[0]
        p[0].code = p[1].code.copy() 
    else:

    pass

#same h
def p_assignment_operator(p):
    ''' assignment_operator : '='
            | MUL_ASSIGN
            | DIV_ASSIGN
            | MOD_ASSIGN
            | ADD_ASSIGN
            | SUB_ASSIGN
            | LEFT_ASSIGN
            | RIGHT_ASSIGN
            | AND_ASSIGN
            | XOR_ASSIGN
            | OR_ASSIGN
    '''
    p[0] = Node()
    p[0].parse = ['assignment_operator'] + p[1:]
    p[0].data = p[1].data
    pass

#same h
def p_expression(p):
    ''' expression : assignment_expression
            | expression ',' assignment_expression
    '''
    p[0] = Node() 
    p[0].parse=['expression'] + p[1:]
    p[0].code = p[1].code.copy()
    if len(p)==2:
        p[0].data = {}
    else:
        p[0].data = assign(p,1)

    pass

def p_constant_expression(p):
    ''' constant_expression	: conditional_expression
    '''
    p[0] = ['constant_expression'] + p[1:]
    pass


# #############################################################################
# Declarators            
# #############################################################################


def p_declaration(p):
    ''' declaration	: declaration_specifiers ';'
	        | declaration_specifiers init_declarator_list ';'
    '''
    p[0] = ['declaration']
    if len(p)==4:
        p[0] += p[1:]
    pass

def p_declaration_specifiers(p):
    ''' declaration_specifiers : storage_class_specifier
            | storage_class_specifier declaration_specifiers
            | type_specifier
            | type_specifier declaration_specifiers
            | type_qualifier
            | type_qualifier declaration_specifiers
    '''
    p[0] = ['declaration_specifiers']
    #  + p[1:]
    pass

def p_init_declarator_list(p):
    ''' init_declarator_list : init_declarator
            | init_declarator_list ',' init_declarator
    '''
    p[0] = ['init_declarator_list'] + p[1:]
    pass


def p_init_declarator(p):
    ''' init_declarator : declarator
            | declarator '=' initializer
    '''
    p[0] = ['init_declarator']
    if len(p) == 4:
        p[0] += p[1:]

    pass

def p_storage_class_specifier(p):
    ''' storage_class_specifier : TYPEDEF
        | EXTERN
        | STATIC
        | AUTO
        | REGISTER
    '''
    p[0] = ['storage_class_specifier'] + p[1:]
    pass

def p_type_specifier(p):
    ''' type_specifier : VOID
            | CHAR
            | SHORT
            | INT
            | LONG
            | FLOAT
            | DOUBLE
            | SIGNED
            | UNSIGNED
            | struct_or_union_specifier
            | enum_specifier
            | TYPE_NAME
    '''
    p[0] = ['type_specifier'] 
    # + p[1:]
    pass

def p_struct_or_union_specifier(p):
    ''' struct_or_union_specifier : struct_or_union IDENTIFIER '{' struct_declaration_list '}'
            | struct_or_union '{' struct_declaration_list '}'
            | struct_or_union IDENTIFIER
    '''
    p[0] = ['struct_or_union_specifier'] + p[1:]
    pass

def p_struct_or_union(p):
    ''' struct_or_union : STRUCT
            | UNION
    '''
    p[0] = ['struct_or_union'] + p[1:]
    pass

def p_struct_declaration_list(p):
    ''' struct_declaration_list : struct_declaration
            | struct_declaration_list struct_declaration
    '''
    p[0] = ['struct_declaration_list'] + p[1:]
    pass

def p_struct_declaration(p):
    ''' struct_declaration : specifier_qualifier_list struct_declarator_list ';'
    '''
    p[0] = ['struct_declaration'] + p[1:]
    pass

def p_specifier_qualifier_list(p):
    ''' specifier_qualifier_list : type_specifier specifier_qualifier_list
            | type_specifier
            | type_qualifier specifier_qualifier_list
            | type_qualifier
    '''
    p[0] = ['specifier_qualifier_list'] + p[1:]
    pass

def p_struct_declarator_list(p):
    ''' struct_declarator_list : struct_declarator
            | struct_declarator_list ',' struct_declarator
    '''
    p[0] = ['struct_declarator_list'] + p[1:]
    pass

def p_struct_declarator(p):
    ''' struct_declarator : declarator
            | ':' constant_expression
            | declarator ':' constant_expression
    '''
    p[0] = ['struct_declarator'] + p[1:]
    pass

def p_enum_specifier(p):
    ''' enum_specifier : ENUM '{' enumerator_list '}'
            | ENUM IDENTIFIER '{' enumerator_list '}'
            | ENUM IDENTIFIER
    '''
    p[0] = ['enum_specifier'] + p[1:]
    pass

def p_enumerator_list(p):
    ''' enumerator_list : enumerator
            | enumerator_list ',' enumerator
    '''
    p[0] = ['enumerator_list'] + p[1:]
    pass

def p_enumerator(p):
    ''' enumerator : IDENTIFIER
            | IDENTIFIER '=' constant_expression
    '''
    p[0] = ['enumerator'] + p[1:]
    pass

def p_type_qualifier(p):
    ''' type_qualifier : CONST
            | VOLATILE
    '''
    p[0] = ['type_qualifier'] + p[1:]
    pass

def p_declarator(p):
    ''' declarator : pointer direct_declarator
            | direct_declarator
    '''
    p[0] = ['declarator'] + p[1:]
    pass

def p_direct_declarator(p):
    ''' direct_declarator : IDENTIFIER
            | '(' declarator ')'
            | direct_declarator '[' constant_expression ']'
            | direct_declarator '[' ']'
            | direct_declarator '(' parameter_type_list ')'
            | direct_declarator '(' identifier_list ')'
            | direct_declarator '(' ')'
    '''
    p[0] = ['direct_declarator'] + p[1:]
    pass

def p_pointer(p):
    ''' pointer : '*'
            | '*' type_qualifier_list
            | '*' pointer
            | '*' type_qualifier_list pointer
    '''
    p[0] = ['pointer'] + p[1:]
    pass

def p_type_qualifier_list(p):
    ''' type_qualifier_list : type_qualifier
            | type_qualifier_list type_qualifier
    '''
    p[0] = ['type_qualifier_list'] + p[1:]
    pass

def p_parameter_type_list(p):
    ''' parameter_type_list : parameter_list
            | parameter_list ',' ELLIPSIS
    '''
    p[0] = ['parameter_type_list'] + p[1:]
    pass

def p_parameter_list(p):
    ''' parameter_list : parameter_declaration
            | parameter_list ',' parameter_declaration
    '''
    p[0] = ['parameter_list'] + p[1:]
    pass

def p_parameter_declaration(p):
    ''' parameter_declaration : declaration_specifiers declarator
            | declaration_specifiers abstract_declarator
            | declaration_specifiers
    '''
    p[0] = ['parameter_declaration'] + p[1:]
    pass

def p_identifier_list(p):
    ''' identifier_list : IDENTIFIER
            | identifier_list ',' IDENTIFIER
    '''
    p[0] = ['identifier_list'] + p[1:]
    pass

def p_type_name(p):
    ''' type_name : specifier_qualifier_list
            | specifier_qualifier_list abstract_declarator
    '''
    p[0] = ['type_name'] + p[1:]
    pass

def p_abstract_declarator(p):
    ''' abstract_declarator : pointer
            | direct_abstract_declarator
            | pointer direct_abstract_declarator
    '''
    p[0] = ['abstract_declarator'] + p[1:]
    pass

def p_direct_abstract_declarator(p):
    ''' direct_abstract_declarator : '(' abstract_declarator ')'
            | '[' ']'
            | '[' constant_expression ']'
            | direct_abstract_declarator '[' ']'
            | direct_abstract_declarator '[' constant_expression ']'
            | '(' ')'
            | '(' parameter_type_list ')'
            | direct_abstract_declarator '(' ')'
            | direct_abstract_declarator '(' parameter_type_list ')'
    '''
    p[0] = ['direct_abstract_declarator'] + p[1:]
    pass


# #############################################################################
# Initializers            
# #############################################################################

def p_initializer(p):
    ''' initializer : assignment_expression
            | '{' initializer_list '}'
            | '{' initializer_list ',' '}'
    '''
    p[0] = ['initializer'] + p[1:]
    pass

def p_initializer_list(p):
    ''' initializer_list : initializer
            | initializer_list ',' initializer
    '''
    p[0] = ['initializer_list'] + p[1:]
    pass


# #############################################################################
# Statements            
# #############################################################################

def p_statement(p):
    ''' statement : labeled_statement
            | compound_statement
            | expression_statement
            | selection_statement
            | iteration_statement
            | jump_statement
    '''
    p[0] = ['statement'] + p[1:]
    pass

def p_labeled_statement(p):
    ''' labeled_statement : IDENTIFIER ':' statement
            | CASE constant_expression ':' statement
            | DEFAULT ':' statement
    '''
    p[0] = ['labeled_statement'] + p[1:]
    pass

def p_compound_statement(p):
    ''' compound_statement : '{' '}'
            | '{' statement_list '}'
            | '{' declaration_list '}'
            | '{' declaration_list statement_list '}'
    '''
    p[0] = ['compound_statement'] + p[1:]
    pass

def p_declaration_list(p):
    ''' declaration_list : declaration
            | declaration_list declaration
    '''
    p[0] = ['declaration_list'] + p[1:]
    pass

def p_statement_list(p):
    ''' statement_list : statement
            | statement_list statement
    '''
    p[0] = ['statement_list'] + p[1:]
    pass

def p_expression_statement(p):
    ''' expression_statement : ';'
	        | expression ';'
    '''
    p[0] = ['expression_statement'] + p[1:]
    pass

def p_selection_statement(p):
    ''' selection_statement : IF '(' expression ')' statement %prec IFX
            | IF '(' expression ')' statement ELSE statement
            | SWITCH '(' expression ')' statement
    '''
    p[0] = ['selection_statement'] + p[1:]
    pass

def p_iteration_statement(p):
    ''' iteration_statement : WHILE '(' expression ')' statement
            | DO statement WHILE '(' expression ')' ';'
            | FOR '(' expression_statement expression_statement ')' statement
            | FOR '(' expression_statement expression_statement expression ')' statement
    '''
    p[0] = ['iteration_statement'] + p[1:]
    pass

def p_jump_statement(p):
    ''' jump_statement : GOTO IDENTIFIER ';'
            | CONTINUE ';'
            | BREAK ';'
            | RETURN ';'
            | RETURN expression ';'
    '''
    p[0] = ['jump_statement'] + p[1:]
    pass

# #############################################################################
# External declaration and function definitions            
# #############################################################################

#aasis me h, imse dec_seq bnaay h usne
def p_translation_unit(p):
    ''' translation_unit : external_declaration
	        | translation_unit external_declaration
    '''
    p[0] = ['translation_unit'] + p[1:]
    pass


def p_external_declaration(p):
    ''' external_declaration : function_definition
	        | declaration
    '''
    p[0] = ['external_declaration'] + p[1:]
    pass

def p_function_definition(p):
    ''' function_definition : declaration_specifiers declarator declaration_list compound_statement
            | declaration_specifiers declarator compound_statement
            | declarator declaration_list compound_statement
            | declarator compound_statement
    '''
    p[0] = ['function_definition'] + p[1:]
    pass

# Build the parser
parser = yacc.yacc()
