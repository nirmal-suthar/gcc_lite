#! /usr/bin/env python3

# from CS335.gcc_lite.src.parser_class import *
from ply import yacc
from lexer import lexer, tokens
from parser_class import *

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

# #############################################################################
# Start, Empty and Error handling             
# #############################################################################

def p_start(p):
    ''' start : translation_unit
    '''
    p[0] = Start(p[1])

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
            | STRING_LITERAL
    '''
    p[0] = Const(p[1], "dvalue") #FIXME: add appropriate dvalue string

def p_identifier(p):
    ''' identifier : IDENTIFIER
    '''
    p[0] = Identifier(p[1])  

def p_primary_expression(p):
    ''' primary_expression : identifier
            | constant
            | '(' expression ')'
    '''
    if len(p)==4:
        p[0] = p[2]
    else:
        p[0] = p[1]

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
    if len(p)==2:
        p[0] = p[1]
    elif len(p)==3:
        p[0] = PostfixExpr(p[1], p[2])
    else:
        p[0] = PostfixExpr(p[1], tuple(p[2:]))

def p_argument_expression_list(p):
    ''' argument_expression_list : assignment_expression
            | argument_expression_list ',' assignment_expression
    '''
    p[0] = ['argument_expression_list'] + p[1:]
    pass

def p_unary_expression(p):
    ''' unary_expression : postfix_expression
            | INC_OP unary_expression
            | DEC_OP unary_expression
            | unary_operator cast_expression
            | SIZEOF unary_expression
            | SIZEOF '(' type_name ')'
    '''
    if len(p)==2:
        p[0] = p[1]
    elif len(p)==3:
        p[0] = UnaryExpr(p[1], p[2])
    # FIXME: Once we have done all type_name 
    # related thing then sizeof(type_name)
    # should be ConstExpr
    else:
        p[0] = UnaryExpr(p[1], p[3])

def p_unary_operator(p):
    ''' unary_operator : '&'
            | '*'
            | '+'
            | '-'
            | '~'
            | '!'
    '''
    p[0] = p[1]

def p_cast_expression(p):
    ''' cast_expression : unary_expression
            | '(' type_name ')' cast_expression
    '''
    if len(p)==2:
        p[0] = p[1]
    else:
        p[0] = CastExpr(p[2], p[4])

def p_multiplicative_expression(p):
    ''' multiplicative_expression : cast_expression
            | multiplicative_expression '*' cast_expression
            | multiplicative_expression '/' cast_expression
            | multiplicative_expression '%' cast_expression
    '''
    if len(p)==2:
        p[0] = p[1]
    else:
        p[0] = OpExpr(p[1], p[2], p[3])

def p_additive_expression(p):
    ''' additive_expression : multiplicative_expression
            | additive_expression '+' multiplicative_expression
            | additive_expression '-' multiplicative_expression
    '''
    if len(p)==2:
        p[0] = p[1]
    else:
        p[0] = OpExpr(p[1], p[2], p[3])

def p_shift_expression(p):
    ''' shift_expression : additive_expression
            | shift_expression LEFT_OP additive_expression
            | shift_expression RIGHT_OP additive_expression
    '''
    if len(p)==2:
        p[0] = p[1]
    else:
        p[0] = OpExpr(p[1], p[2], p[3])

def p_relational_expression(p):
    ''' relational_expression : shift_expression
            | relational_expression '<' shift_expression
            | relational_expression '>' shift_expression
            | relational_expression LE_OP shift_expression
            | relational_expression GE_OP shift_expression
    '''
    if len(p)==2:
        p[0] = p[1]
    else:
        p[0] = OpExpr(p[1], p[2], p[3])

def p_equality_expression(p):
    ''' equality_expression : relational_expression
            | equality_expression EQ_OP relational_expression
            | equality_expression NE_OP relational_expression
    '''
    if len(p)==2:
        p[0] = p[1]
    else:
        p[0] = OpExpr(p[1], p[2], p[3])

def p_and_expression(p):
    ''' and_expression : equality_expression
            | and_expression '&' equality_expression
    '''
    if len(p)==2:
        p[0] = p[1]
    else:
        p[0] = OpExpr(p[1], p[2], p[3])

def p_exclusive_or_expression(p):
    ''' exclusive_or_expression : and_expression
            | exclusive_or_expression '^' and_expression
    '''
    if len(p)==2:
        p[0] = p[1]
    else:
        p[0] = OpExpr(p[1], p[2], p[3])

def p_inclusive_or_expression(p):
    ''' inclusive_or_expression : exclusive_or_expression
            | inclusive_or_expression '|' exclusive_or_expression
    '''
    if len(p)==2:
        p[0] = p[1]
    else:
        p[0] = OpExpr(p[1], p[2], p[3])

def p_logical_and_expression(p):
    ''' logical_and_expression : inclusive_or_expression
            | logical_and_expression AND_OP inclusive_or_expression
    '''
    if len(p)==2:
        p[0] = p[1]
    else:
        p[0] = OpExpr(p[1], p[2], p[3])

def p_logical_or_expression(p):
    ''' logical_or_expression : logical_and_expression
            | logical_or_expression OR_OP logical_and_expression
    '''
    if len(p)==2:
        p[0] = p[1]
    else:
        p[0] = OpExpr(p[1], p[2], p[3])

def p_conditional_expression(p):
    ''' conditional_expression : logical_or_expression
            | logical_or_expression '?' expression ':' conditional_expression
    '''
    if len(p)==2:
        p[0] = p[1]
    else:
        p[0] = CondExpr(p[1], p[3], p[5])


def p_assignment_expression(p):
    ''' assignment_expression : conditional_expression
            | unary_expression assignment_operator assignment_expression
    '''
    if len(p)==2:
        p[0] = p[1]
    else:
        p[0] = AssignExpr(p[1], p[3], p[5])

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
    p[0] = p[1]

def p_expression(p):
    ''' expression : assignment_expression
            | expression ',' assignment_expression
    '''
    if len(p)==2:
        p[0] = p[1]
    elif isinstance(p[1], CommaExpr):
        p[0] = p[1].copy()
        p[0].add_expr(p[5])
    else:
        p[0] = CommaExpr(p[1], p[2])

def p_constant_expression(p):
    ''' constant_expression	: conditional_expression
    '''
    p[0] = p[1]


# #############################################################################
# Declarators            
# #############################################################################


def p_declaration(p):
    ''' declaration	: declaration_specifiers ';'
	        | declaration_specifiers init_declarator_list ';'
    '''
    if len(p) == 2:
        p[0] = Declaration(p[1], None)
    else:
        p[0] = Declaration(p[1], p[2])

def p_declaration_specifiers(p):
    ''' declaration_specifiers : storage_class_specifier type_specifier
            | type_specifier
    '''
    if len(p) == 2:
        p[0] = DeclarationSpecifier(None, p[1])
    else:
        p[0] = DeclarationSpecifier(p[1], p[2])

def p_init_declarator_list(p):
    ''' init_declarator_list : init_declarator
            | init_declarator_list ',' init_declarator
    '''
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = p[1].append(p[2])


def p_init_declarator(p):
    ''' init_declarator : declarator
            | declarator '=' initializer
    '''
    if len(p) == 2:
        p[0] = InitDeclarator(p[1])
    else:
        p[0] = InitDeclarator(p[1], p[3])

def p_storage_class_specifier(p):
    ''' storage_class_specifier : TYPEDEF
        | EXTERN
        | STATIC
    '''
    p[0] = p[1]
    # p[0] = StorageSpecifier(p[1])

def p_type_specifier(p):
    ''' type_specifier : VOID
            | CHAR
            | INT
            | FLOAT
            | struct_or_union_specifier
            | TYPE_NAME
    '''
    p[0] = p[1]
    # p[0] = TypeSpecifier(p[1])

def p_struct_or_union_specifier(p):
    ''' struct_or_union_specifier : struct_or_union IDENTIFIER '{' struct_declaration_list '}'
            | struct_or_union '{' struct_declaration_list '}'
            | struct_or_union IDENTIFIER
    '''
    if len(p) == 3:
        p[0] = StructUnionSpecifier(p[1], name=p[2])
    elif len(p) == 5:
        p[0] = StructUnionSpecifier(p[1], sturct_decls_list=p[3])
    else:
        p[0] = StructUnionSpecifier(p[1], name=p[2], sturct_decls_list=p[4])

def p_struct_or_union(p):
    ''' struct_or_union : STRUCT
            | UNION
    '''
    p[0] = p[1]

def p_struct_declaration_list(p):
    ''' struct_declaration_list : struct_declaration
            | struct_declaration_list struct_declaration
    '''
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = p[1].append(p[2])

def p_struct_declaration(p):
    ''' struct_declaration : specifier_qualifier_list struct_declarator_list ';'
    '''
    p[0] = StructDeclaration(p[1], p[2])

def p_specifier_qualifier_list(p):
    ''' specifier_qualifier_list : type_specifier
    '''
    p[0] = p[1]

def p_struct_declarator_list(p):
    ''' struct_declarator_list : struct_declarator
            | struct_declarator_list ',' struct_declarator
    '''
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = p[1].append(p[2])

def p_struct_declarator(p):
    ''' struct_declarator : declarator ':' constant_expression
    '''
    p[0] = ['struct_declarator'] + p[1:]
    pass

# def p_enum_specifier(p):
#     ''' enum_specifier : ENUM '{' enumerator_list '}'
#             | ENUM IDENTIFIER '{' enumerator_list '}'
#             | ENUM IDENTIFIER
#     '''
#     p[0] = ['enum_specifier'] + p[1:]
#     pass

# def p_enumerator_list(p):
#     ''' enumerator_list : enumerator
#             | enumerator_list ',' enumerator
#     '''
#     p[0] = ['enumerator_list'] + p[1:]
#     pass

# def p_enumerator(p):
#     ''' enumerator : IDENTIFIER
#             | IDENTIFIER '=' constant_expression
#     '''
#     p[0] = ['enumerator'] + p[1:]
#     pass

# def p_type_qualifier(p):
#     ''' type_qualifier : CONST
#             | VOLATILE
#     '''
#     p[0] = ['type_qualifier'] + p[1:]
#     pass

def p_declarator(p):
    ''' declarator : pointer direct_declarator
            | direct_declarator
    '''
    if len(p) == 2:
        p[0] = Declarator(0, p[1])
    else:
        p[0] = Declarator(p[1], p[2])

def p_direct_declarator_0(p):
    ''' direct_declarator : IDENTIFIER
            | '(' declarator ')'
    '''
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = p[2]

def p_direct_declarator(p):
    ''' direct_declarator : direct_declarator '[' constant_expression ']'
            | direct_declarator '[' ']'
            | direct_declarator '(' parameter_type_list ')'
            | direct_declarator '(' ')'
    '''
    p[0] = DirectDecl(p[1], p[2:])

def p_pointer(p):
    ''' pointer : '*'
            | '*' pointer
    '''
    if len(p) == 2:
        p[0] = 1
    else:
        p[0] = p[2]+1

# def p_type_qualifier_list(p):
#     ''' type_qualifier_list : type_qualifier
#             | type_qualifier_list type_qualifier
#     '''
#     p[0] = ['type_qualifier_list'] + p[1:]
#     pass

def p_parameter_type_list(p):
    ''' parameter_type_list : parameter_list
            | parameter_list ',' ELLIPSIS
    '''
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = p[1].append(p[3])

def p_parameter_list(p):
    ''' parameter_list : parameter_declaration
            | parameter_list ',' parameter_declaration
    '''
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = p[1].append(p[3])

def p_parameter_declaration(p):
    ''' parameter_declaration : declaration_specifiers declarator
            | declaration_specifiers abstract_declarator
            | declaration_specifiers
    '''
    if len(p) == 2:
        p[0] = ParamsDecl(p[1])
    else:
        p[0] = ParamsDecl(p[1], p[2])

# def p_identifier_list(p):
#     ''' identifier_list : IDENTIFIER
#             | identifier_list ',' IDENTIFIER
#     '''
#     p[0] = ['identifier_list'] + p[1:]
#     pass

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
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = Initializers(p[2])

def p_initializer_list(p):
    ''' initializer_list : initializer
            | initializer_list ',' initializer
    '''
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = p[1].append(p[3])

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
    p[0] = p[1]

def p_labeled_statement(p):
    ''' labeled_statement : IDENTIFIER ':' statement
            | CASE constant_expression ':' statement
            | DEFAULT ':' statement
    '''
    if len(p)==4:
        p[0] = LabeledStmt(p[1], p[3])
    else:
        p[0] = LabeledStmt((p[1],p[2]), p[3])

# FIXME: same func name works?? No

def p_compound_statement_0(p):
    ''' compound_statement : '{' declaration_list '}'
    '''
    p[0] = CompoundStmt(p[2], None)

def p_compound_statement(p):
    ''' compound_statement : '{' '}'
            | '{' statement_list '}'
            
            | '{' declaration_list statement_list '}'
    '''
    
    decls=None
    stmts=None

    if len(p) == 4:
        stmts = p[2]
    elif len(p) == 5:
        decls = p[2]
        stmts = p[3]

    p[0] = CompoundStmt(decls, stmts)


def p_declaration_list(p):
    ''' declaration_list : declaration
            | declaration_list declaration
    '''
    p[0] = p[1:]

def p_statement_list(p):
    ''' statement_list : statement
            | statement_list statement
    '''
    p[0] = p[1:]

def p_expression_statement(p):
    ''' expression_statement : ';'
	        | expression ';'
    '''
    if len(p)==2:
        p[0] = ExprStmt(None)
    else:
        p[0] = ExprStmt(p[1])

def p_selection_statement(p):
    ''' selection_statement : IF '(' expression ')' statement %prec IFX
            | IF '(' expression ')' statement ELSE statement
            | SWITCH '(' expression ')' statement
    '''
    if len(p)==6:
        p[0] = SelectionStmt(p[1], p[3], p[5])
    else:
        p[0] = SelectionStmt(p[1], p[3], p[5], p[7])

def p_iteration_statement(p):
    ''' iteration_statement : WHILE '(' expression ')' statement
            | FOR '(' expression_statement expression_statement ')' statement
            | FOR '(' expression_statement expression_statement expression ')' statement
    '''
    if len(p)==6:
        p[0] = IterStmt(p[1], p[3], p[5]) 
    elif len(p)==7:
        p[0] = IterStmt(p[1], (p[3](),p[4](),None), p[6]) 
    else:
        p[0] = IterStmt(p[1], (p[3](),p[4](),p[5]), p[7]) 

def p_jump_statement(p):
    ''' jump_statement : GOTO IDENTIFIER ';'
            | CONTINUE ';'
            | BREAK ';'
            | RETURN ';'
            | RETURN expression ';'
    '''
    if len(p)==3:
        p[0] = JumpStmt(p[1])
    else:
        p[0] = JumpStmt(p[1], p[2])
    
# #############################################################################
# External declaration and function definitions            
# #############################################################################

def p_translation_unit(p):
    ''' translation_unit : external_declaration
	        | translation_unit external_declaration
    '''
    if len(p)==2:
        p[0] = [p[1]]
    else:
        p[0] = p[1].append(p[2])

def p_external_declaration(p):
    ''' external_declaration : function_definition
	        | declaration
    '''
    p[0] = p[1]

def p_function_definition(p):
    ''' function_definition : declaration_specifiers declarator compound_statement
    '''
    p[0] = FuncDef(p[1], p[2], p[3])

# Build the parser
parser = yacc.yacc()
