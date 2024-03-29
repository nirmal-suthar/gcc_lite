#! /usr/bin/env python3

from ply import yacc
from lib import stdlib

def parser_error(error_str=None):
    # subtracting stdlib offset for correct position info
    stdlib_offset = len(stdlib.split('\n')) - 1

    parser.compilation_err = True
    print(bcolors.BOLD+f'{lexer.filename}:{lexer.lineno - stdlib_offset}:0'+bcolors.ENDC,end='')
    if error_str == None:
        error_str = parser.error
    print(bcolors.FAIL+' Error:'+bcolors.ENDC, error_str)
    print('     {} |{}'.format(lexer.lineno - stdlib_offset,lexer.lines[lexer.lineno - 1]))


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

def p_empty(p):
    """ empty :
    """
    p[0] = None

def p_push_scope(p):
    ''' push_scope : empty
    '''
    if isinstance(p[-2], ScopeName):
        symtable.push_scope(p[-2].name)
    elif isinstance(p[-2], tuple):
        _, _, func_name, args = p[-2]
        func = symtable.lookup_func(func_name)
        symtable.push_scope('Function', func=func)
        func.scope_id = len(symtable.all_scope) - 1
        if func.ret_type.is_struct_type():
            # return address of struct is stored in ret@ symbol
            symtable.add_var("ret@", func.ret_type.get_pointer_type(), is_param=True)

        for name, _type in args:
            symtable.add_var(name, _type, is_param=True)
    else:
        symtable.push_scope()

    p[0] = None

def p_pop_scope(p):
    ''' pop_scope : empty
    '''
    symtable.pop_scope()
    p[0] = None

def p_func_scope(p):
    ''' func_scope : empty
    '''
    p[0] = ScopeName('Function')

def p_loop_scope(p):
    ''' loop_scope : empty
    '''
    p[0] = ScopeName('Loop')

def p_switch_scope(p):
    ''' switch_scope : empty
    '''
    p[0] = ScopeName('Switch')

def p_error(p):
    # subtracting stdlib offset for correct position info
    stdlib_offset = len(stdlib.split('\n')) - 1

    position = (
        p.lexer.lexpos
        - sum(map(lambda line: len(line) + 1, p.lexer.lines[: p.lineno - 1]))
        - len(p.value)
        + 1
    )
    print(f'{bcolors.BOLD}{p.lexer.filename}:{p.lineno - stdlib_offset}:{position}:{bcolors.ENDC}',end='')
    print(f'{bcolors.FAIL} SyntaxError: {bcolors.ENDC}Unexpected token {p.value}')
    print(f'     {p.lineno - stdlib_offset} |{p.lexer.lines[p.lineno - 1][:position-1]}',end='')
    print(bcolors.WARNING + bcolors.UNDERLINE + '{}'.format(
        p.lexer.lines[p.lineno - 1][position-1:position-1+len(p.value)]
        )+bcolors.ENDC+bcolors.ENDC,end='')
    print(f'{p.lexer.lines[p.lineno - 1][position-1+len(p.value):]}')


# #############################################################################
# Expressions            
# #############################################################################

def p_constant_i(p):
    ''' constant : I_CONSTANT
    '''
    p[0] = Const(p[1], "int")

def p_constant_f(p):
    ''' constant : F_CONSTANT
    '''
    p[0] = Const(p[1], "float")

def p_constant_c(p):
    ''' constant : C_CONSTANT
    '''
    p[0] = Const(p[1], "char")

def p_constant_s(p):
    ''' constant : STRING_LITERAL
    '''
    p[0] = Const(p[1], "STRING_LITERAL")

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
            | postfix_expression INC_OP
            | postfix_expression DEC_OP
    '''
    if len(p)==2:
        p[0] = p[1]
    elif len(p)==3:
        p[0] = PostfixExpr(p[1], p[2])

def p_postfix_expression_arr(p):
    ''' postfix_expression : postfix_expression '[' expression ']'
    '''
    p[0] = PostfixExpr(p[1], '[', p[3])

def p_postfix_expression_call(p):
    ''' postfix_expression : IDENTIFIER '(' ')'
            | IDENTIFIER '(' argument_expression_list ')'
    '''
    if len(p) == 4:
        p[0] = PostfixExpr(p[1], '(', None)
    else:
        p[0] = PostfixExpr(p[1], '(', p[3])

def p_postfix_expression_ptr(p):
    ''' postfix_expression : postfix_expression '.' IDENTIFIER
            | postfix_expression PTR_OP IDENTIFIER
    '''
    p[0] = PostfixExpr(p[1], p[2], p[3])

def p_argument_expression_list(p):
    ''' argument_expression_list : assignment_expression
            | argument_expression_list ',' assignment_expression
    '''
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = p[1] + [p[3]]

def p_unary_expression(p):
    ''' unary_expression : postfix_expression
            | INC_OP unary_expression
            | DEC_OP unary_expression
            | unary_operator cast_expression
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
        p[0] = AssignExpr(p[1], p[2], p[3])

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
    '''
    p[0] = p[1]

def p_constant_expression(p):
    ''' constant_expression	: conditional_expression
    '''
    p[0] = p[1]


# #############################################################################
# Declarators            
# #############################################################################


def p_declaration(p):
    ''' declaration	: declaration_specifiers ';'
    '''
    p[0] = Declaration(p[1], [])

def p_declaration_1(p):
    ''' declaration	: declaration_declarator ';'
    '''
    p[0] = p[1]

def p_declaration_declarator(p):
    ''' declaration_declarator	: declaration_specifiers init_declarator_list
    '''
    p[0] = Declaration(p[1], p[2])

def p_declaration_specifiers(p):
    ''' declaration_specifiers : storage_class_specifier type_specifier
            | type_specifier
    '''
    if len(p) == 2:
        p[0] = DeclarationSpecifier(None, p[1])
        if isinstance(p[1], StructUnionSpecifier):
            parser.type = p[1].get_struct_type()
        else:
            if re.fullmatch('typedef@(?P<type_name>[^ ]*)', p[1]):
                parser.type = parser.typedef_type
            else:
                parser.type = p[1]
        parser.is_typedef = False
        parser.is_static = False
    else:
        p[0] = DeclarationSpecifier(p[1], p[2])
        if isinstance(p[2], StructUnionSpecifier):
            parser.type = p[2].get_struct_type()
        else:
            if re.fullmatch('typedef@(?P<type_name>[^ ]*)', p[2]):
                parser.type = parser.typedef_type
            else:
                parser.type = p[2]
        parser.is_typedef = (p[1] == 'typedef')
        parser.is_static = (p[1] == 'static')

def p_init_declarator_list(p):
    ''' init_declarator_list : init_declarator
            | init_declarator_list ',' init_declarator
    '''
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = p[1] + [p[3]]


def p_init_declarator(p):
    ''' init_declarator : declarator
            | declarator '=' initializer
            | function_declarator
    '''
    if len(p) == 2:
        p[0] = InitDeclarator(p[1])
    else:
        p[0] = InitDeclarator(p[1], p[3])

def p_storage_class_specifier(p):
    ''' storage_class_specifier : TYPEDEF
    '''
    p[0] = p[1]

def p_type_specifier(p):
    ''' type_specifier : VOID
            | CHAR
            | INT
            | FLOAT
            | struct_or_union_specifier
    '''
    p[0] = p[1]

def p_type_specifier_typedef(p):
    ''' type_specifier : TYPE_NAME
    '''
    p[0] = 'typedef@' + p[1]
    # print(p[1], symtable.cur_scope().aliases)
    lookup_alias = symtable.lookup_alias(p[1])
    parser.typedef_type = lookup_alias
    
    # TODO: handle typedef with pointer types e.g. typedef int *ab, **xyz (by using something like p.ref_type)

def p_struct_or_union_specifier(p):
    ''' struct_or_union_specifier : struct_or_union IDENTIFIER '{' struct_declaration_list '}'
            | struct_or_union '{' struct_declaration_list '}'
            | struct_or_union IDENTIFIER
    '''
    if len(p) == 3:
        p[0] = StructUnionSpecifier(p[1], name=p[2])
    elif len(p) == 5:
        p[0] = StructUnionSpecifier(p[1], decls_list=p[3])
    else:
        p[0] = StructUnionSpecifier(p[1], name=p[2], decls_list=p[4])
    # comm['struct_kw'] = False

def p_struct_or_union(p):
    ''' struct_or_union : STRUCT
    '''
    p[0] = p[1]

def p_struct_declaration_list(p):
    ''' struct_declaration_list : struct_declaration
            | struct_declaration_list struct_declaration
    '''
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = p[1] + [p[2]]

def p_struct_declaration(p):
    ''' struct_declaration : specifier_qualifier_list ';'
        | specifier_qualifier_list struct_declarator_list ';'
    '''
    if len(p) == 3:
        p[0] = StructDeclaration(p[1], [])
    else:
        p[0] = StructDeclaration(p[1], p[2])

def p_specifier_qualifier_list(p):
    ''' specifier_qualifier_list : type_specifier
    '''
    p[0] = DeclarationSpecifier(None, p[1])

def p_struct_declarator_list(p):
    ''' struct_declarator_list : struct_declarator
            | struct_declarator_list ',' struct_declarator
    '''
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = p[1] + [p[3]]

def p_struct_declarator(p):
    ''' struct_declarator : declarator
    '''
    p[0] = p[1]

def p_declarator(p):
    ''' declarator : pointer direct_declarator
            | direct_declarator
    '''
    if len(p) == 2:
        (rcount, ident, args) = p[1]
        p[0] = Declarator(rcount, ident, args)
    else:
        (rcount, ident, args) = p[2]
        p[0] = Declarator(p[1]+rcount, ident, args)

def p_direct_declarator(p):
    ''' direct_declarator : IDENTIFIER
            | '(' declarator ')'
            | direct_declarator '[' constant_expression ']'
    '''
    if len(p) == 2:
        p[0] = (0,p[1],[])
    elif len(p) == 4:
        p[0] = (p[2].ref_count, p[2].name, p[2].arr_offset)
    else:
        (rcount, ident, args) = p[1]
        if args == []:
            p[0] = (rcount+1, ident, [p[3]])
        else:
            p[0] = (rcount, ident, args + [p[3]])

def p_param_list(p):
    ''' param_list : '(' parameter_type_list ')'
            | '(' ')'
    '''
    if len(p) == 3:
        p[0] = []
    else:
        p[0] = p[2]  

def p_function_declarator(p):
    ''' function_declarator : IDENTIFIER '(' parameter_type_list ')'
            | pointer IDENTIFIER '(' parameter_type_list ')'
    '''
    if len(p)==5:
        p[0] = FuncDirectDecl(0, p[1], p[3])
    else:
        p[0] = FuncDirectDecl(p[1], p[2], p[4])

def p_function_declarator1(p):
    ''' function_declarator : IDENTIFIER '(' ')'
            | pointer IDENTIFIER '(' ')'
    '''
    if len(p)==4:
        p[0] = FuncDirectDecl(0, p[1], [])
    else:
        p[0] = FuncDirectDecl(p[1], p[2], [])
        
def p_pointer(p):
    ''' pointer : '*'
            | '*' pointer
    '''
    if len(p) == 2:
        p[0] = 1
    else:
        p[0] = p[2]+1

def p_parameter_type_list(p):
    ''' parameter_type_list : parameter_list
    '''
    p[0] = p[1]

def p_parameter_list(p):
    ''' parameter_list : parameter_declaration
            | parameter_list ',' parameter_declaration
    '''
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = p[1] + [p[3]]

def p_parameter_declaration(p):
    '''parameter_declaration : declaration_specifiers declarator
    '''
    _type = VarType(p[2].ref_count, p[1].type_spec, p[2].arr_offset)
    p[0] = (p[2].name, _type)

def p_type_name(p):
    ''' type_name : specifier_qualifier_list
            | specifier_qualifier_list abstract_declarator
    '''
    _type = p[1].type_spec
    if len(p) == 2:
        p[0] = VarType(0, _type, None)
    else:
        (rcount, arr_dim) = p[2]
        p[0] = VarType(rcount, _type, arr_dim)

def p_abstract_declarator(p):
    ''' abstract_declarator : pointer
            | direct_abstract_declarator
            | pointer direct_abstract_declarator
    '''
    if len(p) == 2:
        if isinstance(p[1], int):
            p[0] = (p[1], [])
        else:
            p[0] = (0, p[1])
    else:
        p[0] = (p[1], p[2])

def p_direct_abstract_declarator(p):
    ''' direct_abstract_declarator : '[' constant_expression ']'
            | direct_abstract_declarator '[' constant_expression ']'
    '''
    if len(p) == 4:
        p[0] = [p[2]]
    else:
        p[0] = p[1] + [p[3]]


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
        p[0] = p[1] + [p[3]]

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
    ''' labeled_statement : CASE constant_expression ':' statement
            | DEFAULT ':' statement
    '''
    if len(p)==4:
        p[0] = LabeledStmt(p[1], p[3])
    else:
        p[0] = LabeledStmt((p[1],p[2]), p[4])

def p_compound_statement_0(p):
    ''' compound_statement : '{' push_scope declaration_list pop_scope '}'
    '''
    p[0] = CompoundStmt(p[3], None)

def p_compound_statement(p):
    ''' compound_statement : '{' push_scope pop_scope '}' 
            | '{' push_scope statement_list pop_scope '}'   
            | '{' push_scope  declaration_list statement_list pop_scope '}' 
    '''
    
    decls=None
    stmts=None

    if len(p) == 6:
        stmts = p[3]
    elif len(p) == 7:
        decls = p[3]
        stmts = p[4]

    p[0] = CompoundStmt(decls, stmts)

def p_declaration_list(p):
    ''' declaration_list : declaration
            | declaration_list declaration
    '''
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = p[1] + [p[2]]

def p_statement_list(p):
    ''' statement_list : statement
            | statement_list statement
    '''
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = p[1] + [p[2]]

def p_expression_statement(p):
    ''' expression_statement : ';'
	        | expression ';'
    '''
    if len(p)==2:
        p[0] = ExprStmt(None)
    else:
        p[0] = ExprStmt(p[1])

def p_selection_statement(p):
    # Added markers to be used for backpaching
    ''' selection_statement : IF '(' expression ')' statement %prec IFX
            | IF '(' expression ')' statement ELSE statement
            | SWITCH '(' expression ')' switch_scope statement
    '''

    # parsing is not happening correctly with this rule
    # selection_statement : IF '(' expression ')' M1 statement M2 %prec IFX


    if len(p)==6:
        p[0] = SelectionStmt(p[1], p[3], p[5])
        # tac.backpatch(p[3].truelist,p[5])
        # tac.backpatch(p[3].falselist,p[7])
    elif len(p) == 7:
        p[0] = SelectionStmt(p[1], p[3], p[6])
    else:
        p[0] = SelectionStmt(p[1], p[3], p[5], p[7])


def p_iteration_statement_while(p):
    ''' iteration_statement : WHILE '(' expression ')' loop_scope statement
    '''
    p[0] = IterStmt(p[1], p[3], p[6]) 
    
def p_iteration_statement_for(p):
    ''' iteration_statement : FOR '(' expression_statement expression_statement ')' loop_scope statement
            | FOR '(' expression_statement expression_statement expression ')' loop_scope statement
    '''
    if len(p)==8:
        p[0] = IterStmt(p[1], (p[3](),p[4](),None), p[7])
    else:
        p[0] = IterStmt(p[1], (p[3](),p[4](),p[5]), p[8]) 

def p_jump_statement(p):
    ''' jump_statement : CONTINUE ';'
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
        p[0] = p[1] + [p[2]]

def p_external_declaration(p):
    ''' external_declaration :  function_definition compound_statement
	        | declaration
    '''
    if len(p) == 2:
        p[0] = p[1]
    else:
        spec, ref, name, args = p[1]
        p[0] = FuncDef(spec, ref, name, args, p[2])

def p_function_definition(p):
    ''' function_definition : declaration_specifiers IDENTIFIER param_list func_scope
        | declaration_specifiers pointer IDENTIFIER param_list func_scope
    '''
    if len(p) == 5:
        p[0] = (p[1], 0, p[2], p[3])
        vartype = VarType(0, p[1].type_spec)    
        symtable.add_func(Function(vartype, p[2], p[3]))
    else:
        p[0] = (p[1], p[2], p[3], p[4])
        vartype = VarType(p[2], p[1].type_spec)    
        symtable.add_func(Function(vartype, p[3], p[4]))

from lexer import lexer, tokens, main_lexer

parser = yacc.yacc()
parser.type = None
parser.is_typedef = False
parser.error = ''
parser.compilation_err = False

from parser_class import *
