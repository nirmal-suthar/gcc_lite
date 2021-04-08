#! /usr/bin/env python3

try:
    from CS335.gcc_lite.src.parser_class import *
except:
    pass

from ply import yacc


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
        symtable.push_scope('Function')
        for name, _type in p[-2][3][0]:
            symtable.add_var(name, _type)
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
    ''' postfix_expression : postfix_expression '(' ')'
            | postfix_expression '(' argument_expression_list ')'
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
        p.type = p[1]
        p.is_typedef = False
    else:
        p[0] = DeclarationSpecifier(p[1], p[2])
        p.type = p[2]
        p.is_typedef = (p[1] == 'typedef')

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
        | STATIC
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
    p[0] = p[1]
    lookup_alias = symtable.lookup_alias(p[1])
    p.type = lookup_alias._type
    
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

    if len(p) == 2:
        p[0] = StructDeclarator(p[1])
    else:
        p[0] = StructDeclarator(p[1], p[3])

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
        p[0] = ([],False)
    else:
        p[0] = p[2]  

def p_function_declarator(p):
    ''' function_declarator : IDENTIFIER '(' parameter_type_list ')'
            | pointer IDENTIFIER '(' parameter_type_list ')'
    '''
    if len(p)==5:
        (param_list, is_ellipsis) = p[3]
        p[0] = FuncDirectDecl(0, p[1], param_list, is_ellipsis)
    else:
        (param_list, is_ellipsis) = p[4]
        p[0] = FuncDirectDecl(p[1], p[2], param_list, is_ellipsis)
        

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
            | parameter_list ',' ELLIPSIS
    '''
    if len(p) == 2:
        p[0] = (p[1], False)
    else:
        p[0] = (p[1], True)

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
        p[0] = LabeledStmt((p[1],p[2]), p[3])

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
    ''' selection_statement : IF '(' expression ')' statement %prec IFX
            | IF '(' expression ')' statement ELSE statement
            | SWITCH '(' expression ')' switch_scope statement
    '''
    if len(p)==6:
        p[0] = SelectionStmt(p[1], p[3], p[5])
    else:
        p[0] = SelectionStmt(p[1], p[3], p[5], p[7])

def p_iteration_statement(p):
    ''' iteration_statement : WHILE '(' expression ')' loop_scope statement
            | FOR '(' expression_statement expression_statement ')' loop_scope statement
            | FOR '(' expression_statement expression_statement expression ')' loop_scope statement
    '''
    if len(p)==7:
        p[0] = IterStmt(p[1], p[3], p[6]) 
    elif len(p)==8:
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
        p1, p2, p3, (p4, is_ellipsis) = p[1]
        # p[0] = FuncDef(p1, p2, p3, p4, p[3], is_ellipsis)
        p[0] = FuncDef(p1, p2, p3, p4, p[2], is_ellipsis)

def p_function_definition(p):
    ''' function_definition : declaration_specifiers IDENTIFIER param_list func_scope
        | declaration_specifiers pointer IDENTIFIER param_list func_scope
    '''
    if len(p) == 5:
        p[0] = (p[1], 0, p[2], p[3])
        symtable.add_func(Function(VarType(0, p[1].type_spec), p[2], p[3][0], p[3][1]))
    else:
        p[0] = (p[1], p[2], p[3], p[4])
        symtable.add_func(Function(VarType(p[2], p[1].type_spec), p[3], p[4][0], p[4][1]))
        
# def _parse(ifile):
#         symtable = SymbolTable()
#         compilation_err = []

#         # # lexer
#         # lexer = lexer

#         # Build the parser
#         parser = yacc.yacc()

#         return parser.parse(ifile)

# if __name__ == '__main__':




from os import removedirs
from typing import Union, List
import pydot
# from helper import *



# #############################################################################
# Misc.            
# #############################################################################

class _BASENODE:
    def __init__(self):
        self.attr_ignore = ['attr_ignore']

    @staticmethod
    def _gen_dot(obj):
        """Get a list of node and edge declarations."""

        dot_list = []

        if isinstance(obj, (str, int, float, tuple, dict)):
            dot_list.append(obj)
        elif isinstance(obj, _BASENODE):
            dot_list.append(repr(obj.__class__.__name__))
        elif isinstance(obj, list):
            # dot_list.append('List')
            pass
        else:
            raise Exception('Invalid type {}'.format(type(obj)))
        
        if isinstance(obj, list):
            # Avoid None child node, empty strings, and empty lists
            FILTERED_LIST = [None, "", []]    

            for child in filter(lambda x: not x in FILTERED_LIST, obj):
                _gen_dot_func = child._gen_dot if isinstance(child, _BASENODE) else _BASENODE._gen_dot
                dot_list.append(_gen_dot_func(child))                

        elif isinstance(obj, _BASENODE):
            for attr in obj.__dict__:
                child = getattr(obj, attr)
                if (
                    child is None
                    or child == ""
                    or child == []
                    or attr in obj.attr_ignore
                ):
                    continue
                
                child_list = [] 
                if isinstance(child, list):
                    child_list.append(repr(attr))

                _gen_dot_func = child._gen_dot if isinstance(child, _BASENODE) else _BASENODE._gen_dot
                child_list = child_list + _gen_dot_func(child)

                dot_list.append(child_list)
                # if len(child_list) == 1:
                #     dot_list.append(child_list[0])
                # else:
                #     dot_list.append(child_list)
                
        return dot_list

# #############################################################################
# Type and scope related classes            
# #############################################################################

class StructType(_BASENODE):
    def __init__(self, name=None, variables=None):
        super().__init__()
        # For use in named struct decls which are not 
        # yet defined
        self.name = name

        # For use in lambda struct and defined struct
        self.variables = variables

    def __str__(self):
        return 'struct {} {{ {} }}'.format(self.name, self.variables)

    def is_defined(self):
        if self.variables is not None:
            return True
        
        self.variables = symtable.lookup_struct(self.name)
        return self.variables is not None

    def _get_size(self):
        raise Exception('TODO')

class Function(_BASENODE):
    def __init__(self, ret_type, name, args, is_ellipsis=False, is_defined=False):
        super().__init__()
        self.ret_type = ret_type        # should be VarType
        self.name = name                # str
        self.args = args                # list
        self.is_ellipsis = is_ellipsis  # is_ellipsis function
    
    def __str__(self):
        return 'Function(ret_type={}, name={}, args={}, is_ellipsis={})'.format(str(self.ret_type), self.name, self.args, self.is_ellipsis)


class VarType(_BASENODE):
    def __init__(self, ref_count, _type, arr_offset=None):
        super().__init__()
        self.ref_count = ref_count
        self._type = _type
        self.arr_offset = arr_offset

    def __str__(self):
        if isinstance(self._type, str):
            type_string = self._type
        else:
            type_string = str(self._type)
        return type_string + " " + "*" * self.ref_count
    
    def __repr__(self):
        return str(self)

    def __eq__(self, other):
        if not isinstance(other, VarType):
            return False
        return self.ref_count == other.ref_count and self._type == other._type
    
    @staticmethod
    def _gen_dot(obj):
        """Get a list of node and edge declarations."""
        return ['type = ' + repr(obj)]

class ScopeName:
    def __init__(self, name):
        super().__init__()
        self.name = name

# #############################################################################
# Expressions            
# #############################################################################

class BaseExpr(_BASENODE) :
       
    def __init__(self, t_name):
        super().__init__()
        self.t_name = t_name
        self.attr_ignore.append('t_name')

        # default type for error reporting
        self.expr_type = VarType(0, 'int')

    ops_type = {
        # arithmetic operators
        '+' : ['int', 'float', 'char'],
        '-' : ['int', 'float', 'char'],
        '*' : ['int', 'float', 'char'],
        '/' : ['int', 'float', 'char'],
        '%' : ['int'],

        # comparsion operators
        '>' : ['int', 'float', 'char'],
        '>=' : ['int', 'float', 'char'],
        '<' : ['int', 'float', 'char'],
        '<=' : ['int', 'float', 'char'],
        
        # bool operators
        '||' : ['int', 'float', 'char'],
        '&&' : ['int', 'float', 'char'],
        '!' : ['int', 'float', 'char'],
        
        # bits operators
        '<<' : ['int'],
        '>>' : ['int'],
        '|' : ['int'],
        '&' : ['int'],
        '~' : ['int'],
        '^' : ['int'],
    }

    cast_type = {
        'int'     : ['int', 'float', 'char'],
        'float'   : ['int', 'float', 'char'],
        'char'    : ['int', 'char'],
        'pointer' : ['int', 'float', 'char'],
    }

    def op_allowed(self, op, _type):
        if op not in _BASENODE.ops_type.keys():
            return True
        return _type in _BASENODE.ops_type.keys[op]

    # def print_compilation_error(msg, line):
    #     print("Error at line : " + str(line) + " :: " + msg)
    #     exit()

    # #used for type conversion
    # def allowed_typecast(converted_from,converted_to):
    #     global allowed_types
    #     if converted_from==converted_to:
    #         return True
    #     # if "|" in converted_from or "|" in converted_to:
    #     #     if "|" in converted_from and converted_from[-1]=='p' and (converted_to[-1]=="p" or converted_to in allowed_types["pointer"]):
    #     #         return True
    #     #     return False
    #     if converted_to not in allowed_types.keys():
    #         return False
    #     return (converted_from in allowed_types[converted_to])

    # def get_expr_type(expr):
    #     #function to get type of an expression
    #     pass

class Const(BaseExpr):
    def __init__(self, const, dvalue):
        super().__init__("Constant")
        self.const = const
        self.dvalue = dvalue
        self.get_type()

    def get_type(self):
        if self.dvalue == 'int':
            self.expr_type = VarType(0, 'int')
        elif self.dvalue == 'float':
            self.expr_type = VarType(0, 'float')
        elif self.dvalue == 'char':
            self.expr_type = VarType(0, 'char')
        elif self.dvalue == 'STRING_LITERAL':
            self.expr_type = VarType(1, 'char')
        else:
            compilation_err.append('Unknown Constant type')
            parser.error = compilation_err[-1]
            parser_error()

    @staticmethod
    def _gen_dot(obj):
        dot_list = ['Const', obj.expr_type._gen_dot(obj.expr_type), obj.const]
        return dot_list

class Identifier(BaseExpr):
    def __init__(self, name: str):
        super().__init__("Identifier")
        self.name = name
        self.get_type()

    def get_type(self):
        _var = symtable.lookup_var(self.name)
        if _var is None:
            _var = symtable.lookup_func(self.name)
            if _var is None:
                _var = symtable.lookup_struct(self.name)
                if _var is None:
                    compilation_err.append('Undeclared Variable {}'.format(self.name))
                    parser.error = compilation_err[-1]
                    parser_error()
                else:
                    self.expr_type = _var
            else:
                self.expr_type = _var
        else:
            self.expr_type = _var
        # print(self.name, self.expr_type)

class OpExpr(BaseExpr):
    def __init__(
        self, 
        lhs: BaseExpr, 
        ops: str, 
        rhs: BaseExpr
    ):
        self.ops_type['=='] = ['int', 'char', 'float']
        self.ops_type['!='] = ['int', 'char', 'float']
        super().__init__("Expression")
        self.lhs = lhs
        self.ops = ops
        self.rhs = rhs
        self.get_type()

    def get_type(self):
        
        ref_count = 0
        inferred_type = 'int'

        if (
            self.lhs.expr_type._type not in self.ops_type[self.ops] and
            self.rhs.expr_type._type not in self.ops_type[self.ops]
        ):
            compilation_err.append('Type not compatible with ops {}'.format(self.ops))
            parser.error = compilation_err[-1]
            parser_error()

        # if lhs is pointer
        if self.lhs.expr_type.ref_count > 0:
            # if rhs is pointer -> only '-' works
            if self.rhs.expr_type.ref_count > 0:
                if self.ops in ['-'] and self.rhs.expr_type.ref_count == self.lhs.expr_type.ref_count:
                    inferred_type = 'int'
                    ref_count = 0
                else:
                    compilation_err.append('Type not compatible with ops {}'.format(self.ops))
                    parser.error = compilation_err[-1]
                    parser_error()
            # lhs is pointer and rhs is int => pointer add and sub
            else:
                if self.rhs.expr_type._type == 'int' or self.rhs.expr_type._type == 'char':
                    inferred_type = self.lhs.expr_type._type
                    ref_count = self.lhs.expr_type.ref_count
                else:
                    compilation_err.append('Type not compatible with ops {}'.format(self.ops))
                    parser.error = compilation_err[-1]
                    parser_error()
        # if lhs is not pointer
        else:
            # lhs is int and rhs is pointer
            if self.rhs.expr_type.ref_count > 0:
                if self.ops in ['+']:
                    if self.lhs.expr_type._type == 'int' or self.lhs.expr_type._type == 'char':
                        inferred_type = self.rhs.expr_type._type
                        ref_count = self.rhs.expr_type.ref_count
                    else:
                        compilation_err.append('Type not compatible with ops {}'.format(self.ops))
                        parser.error = compilation_err[-1]
                        parser_error()
                else:
                    compilation_err.append('Type not compatible with ops {}'.format(self.ops))
                    parser.error = compilation_err[-1]
                    parser_error()
            # if lhs and rhs are both NOT pointer
            else:
                if self.rhs.expr_type._type == self.lhs.expr_type._type:
                    if self.rhs.expr_type._type in self.ops_type[self.ops]:
                        inferred_type = self.lhs.expr_type._type
                        ref_count = self.lhs.expr_type.ref_count
                    else:
                        compilation_err.append('Type not compatible with ops {}'.format(self.ops))
                        parser.error = compilation_err[-1]
                        parser_error()
                else:
                    if self.rhs.expr_type._type in self.ops_type[self.ops]:
                        if self.lhs.expr_type._type in self.ops_type[self.ops]:
                            if self.rhs.expr_type._type == 'float' or self.lhs.expr_type._type == 'float':
                                inferred_type = 'float'
                                ref_count = 0
                            else:
                                inferred_type = 'int'
                                ref_count = 0
                            self.lhs = CastExpr(VarType(ref_count, inferred_type), self.lhs)
                            self.rhs = CastExpr(VarType(ref_count, inferred_type), self.rhs)
                        else:
                            compilation_err.append('Type not compatible with ops {}'.format(self.ops))
                            parser.error = compilation_err[-1]
                            parser_error()
                    else:
                        compilation_err.append('Type not compatible with ops {}'.format(self.ops))
                        parser.error = compilation_err[-1]
                        parser_error()

        self.expr_type = VarType(ref_count, inferred_type)

class UnaryExpr(OpExpr):
    def __init__(self, ops, rhs):
        super().__init__(None, ops, rhs)
        self.get_type()

    def get_type(self):

        ref_count = 0
        inferred_type = 'int'

        # sizeof ops
        if self.ops == 'sizeof':
            inferred_type = 'int'
            ref_count = 0
        # arithmetic ops
        elif self.ops in ['--', '++', '+', '-']:
            if self.rhs.expr_type.ref_count == 0:
                if self.rhs.expr_type._type not in self.ops_type[self.ops]:
                    compilation_err.append('Type not compatible with ops {}'.format(self.ops)) 
                    parser.error = compilation_err[-1]
                    parser_error()
                
                inferred_type = 'int'
                ref_count = 0

            else:
                if self.ops in ['-', '+']:
                    compilation_err.append('wrong type argument to unary minus')
                    parser.error = compilation_err[-1]
                    parser_error()
                inferred_type = self.rhs.expr_type._type
                ref_count = self.rhs.expr_type.ref_count
        # bool ops
        elif self.ops in ['!', '~']:
            if self.rhs.expr_type._type not in self.ops_type[self.ops]:
                compilation_err.append('Type not compatible with ops {}'.format(self.ops)) 
                parser.error = compilation_err[-1]
                parser_error()
            
            inferred_type = 'int'
            ref_count = 0
        # error reporting
        elif self.ops == '*':
            if self.rhs.expr_type.ref_count > 0:
                inferred_type = self.rhs.expr_type._type
                ref_count = self.rhs.expr_type.ref_count - 1
            else:
                compilation_err.append('Can not dereference a non pointer') 
                parser.error = compilation_err[-1]
                parser_error()
        elif self.ops == '&':
            if not isinstance(self.rhs, Identifier):
                compilation_err.append('RHS should be an indentifier')
                parser.error = compilation_err[-1]
                parser_error()
            else:
                ref_count = self.rhs.expr_type.ref_count + 1
                inferred_type = self.rhs.expr_type._type
        
        self.expr_type = VarType(ref_count, inferred_type)

class PostfixExpr(OpExpr):
    def __init__(self, lhs, ops, rhs=None):
        self.ops_type['++'] = ['int', 'char', 'float']
        self.ops_type['--'] = ['int', 'char', 'float']
        super().__init__(lhs, ops, rhs)
 
    def get_type(self):
        
        ref_count = 0
        inferred_type = 'int'
        arr_offset = []

        # arithmetic ops
        if self.ops in ['--', '++']:
            if self.lhs.expr_type.ref_count == 0:
                if self.lhs.expr_type._type not in self.ops_type[self.ops]:
                    compilation_err.append('Type not compatible with ops {}'.format(self.ops)) 
                    parser.error = compilation_err[-1]
                    parser_error()
                
                inferred_type = 'int'
                ref_count = 0

            else:
                # pointer increment operation which returns the same type
                inferred_type = self.lhs.expr_type._type
                ref_count = self.lhs.expr_type.ref_count

        # struct child accessing 
        elif self.ops == '.':
            if isinstance(self.lhs.expr_type._type, StructType) and self.lhs.expr_type.ref_count == 0:
                if self.lhs.expr_type._type.is_defined():
                    struct_var = self.lhs.expr_type._type.variables.get(self.rhs, None)
                    if struct_var is None:
                        compilation_err.append('{} has no member named {}'.format(self.lhs.expr_type._type.name, self.rhs))
                        parser.error = compilation_err[-1]
                        parser_error()
                    inferred_type = struct_var._type
                    ref_count = struct_var.ref_count
                else:
                    compilation_err.append('Incomplete struct {}'.format(self.lhs.expr_type._type.name))
                    parser.error = compilation_err[-1]
                    parser_error()
            else:
                compilation_err.append('Dereferencing invalid struct type')
                parser.error = compilation_err[-1]
                parser_error()
        # struct deferencing child
        elif self.ops == '->':
            if self.lhs.expr_type.ref_count == 1 and isinstance(self.lhs.expr_type._type, StructType):
                if self.lhs.expr_type._type.is_defined():
                    # print(self.lhs.expr_type)
                    struct_var = self.lhs.expr_type._type.variables.get(self.rhs, None)
                    if struct_var is None:
                        compilation_err.append('{} has no member named {}'.format(self.lhs.expr_type._type.name, self.rhs))
                        parser.error = compilation_err[-1]
                        parser_error()
                    inferred_type = struct_var._type
                    ref_count = struct_var.ref_count
                else:
                    compilation_err.append('Incomplete struct {}'.format(self.lhs.expr_type._type.name))
                    parser.error = compilation_err[-1]
                    parser_error()
            else:
                compilation_err.append('Dereferencing invalid struct type')
                parser.error = compilation_err[-1]
                parser_error()
        # function calling
        elif self.ops == '(':
            arg_list = [] if self.rhs is None else self.rhs
            # sanity checking of function args and 
            if isinstance(self.lhs.expr_type, Function):
                func = self.lhs.expr_type
                if func is None:
                    compilation_err.append('{} is not callable'.format(self.lhs))
                    parser.error = compilation_err[-1]
                    parser_error()

                if len(arg_list) == len(func.args):
                    inferred_type = func.ret_type._type
                    ref_count = func.ret_type.ref_count
                else:
                    compilation_err.append('too few/many arguments to function {}'.format(func.name))
                    parser.error = compilation_err[-1]
                    parser_error()
            else:
                compilation_err.append('called object is not a function or function pointer')
                parser.error = compilation_err[-1]
                parser_error()
            
        # array reference
        elif self.ops == '[':
            if self.rhs.expr_type == VarType(0, 'int'):
                # print(self.lhs.expr_type, self.rhs.expr_type)
                if self.lhs.expr_type.ref_count > 0:
                    inferred_type = self.lhs.expr_type._type
                    if len(self.lhs.expr_type.arr_offset) > 1:
                        ref_count = self.lhs.expr_type.ref_count
                        arr_offset = self.lhs.expr_type.arr_offset[1:]
                    elif len(self.lhs.expr_type.arr_offset) == 1:
                        ref_count = self.lhs.expr_type.ref_count - 1
                        arr_offset = self.lhs.expr_type.arr_offset[1:]
                    else:
                        ref_count = self.lhs.expr_type.ref_count - 1
                else:
                    compilation_err.append('Subscripted value is neither array nor pointer')
                    parser.error = compilation_err[-1]
                    parser_error()
            else:
                compilation_err.append('Array subscript is not an integer')
                parser.error = compilation_err[-1]
                parser_error()
        
        self.expr_type = VarType(ref_count, inferred_type, arr_offset)
            
class CastExpr(BaseExpr):
    def __init__(self, _type, Expr):
        super().__init__("Cast Expression")
        self.type = _type
        self.expr = Expr
        self.get_type()

    def get_type(self):
        if self.expr.expr_type.ref_count > 0:
            if self.type.ref_count > 0:
                self.expr_type = self.type
            else:
                if self.expr.expr_type._type in ['int', 'char']:
                    self.expr_type = self.type
                else:
                    compilation_err.append('Cannot convert pointer to float')
                    parser.error = compilation_err[-1]
                    parser_error()
        else:
            if self.type.ref_count > 0:
                if self.expr.expr_type._type in ['int', 'char']:
                    self.expr_type = self.type
                else:
                    compilation_err.append('Cannot convert float to pointer')
                    parser.error = compilation_err[-1]
                    parser_error()
            else:
                self.expr_type = self.type
    
    @staticmethod
    def _gen_dot(obj):
        dot_list = ['Type Casting', obj.type._gen_dot(obj.type)]
        dot_list.append(obj.expr._gen_dot(obj.expr))
        return dot_list

class AssignExpr(OpExpr):
    def __init__(self, lhs, ops, rhs):
        super().__init__(lhs, ops, rhs)

    def get_type(self):
        
        # compatability is checked in CastExpr
        self.rhs = CastExpr(self.rhs.expr_type, self.rhs)
        self.expr_type = self.lhs.expr_type

class CondExpr(BaseExpr):
    def __init__(self, cond, if_expr, else_expr):
        super().__init__("Conditional Expr")
        self.cond = cond
        self.if_expr = if_expr
        self.else_expr = else_expr

class CommaExpr(BaseExpr):
    def __init__(self, *expr):
        super().__init__("Comma Expression")
        self.expr_list = expr
        self.get_type()

    def add_expr(self, expr):
        self.expr_list.append(expr)
    
    def get_type(self):
        self.expr_type = self.expr_list[-1].expr_type

# #############################################################################
# Declarators            
# #############################################################################

class _BaseDecl(_BASENODE):
    def __init__(self, t_name):
        super().__init__()
        self.t_name = 'TODO'
        self.attr_ignore.append('t_name')
    

class InitDeclarator(_BaseDecl):
    def __init__(self, declarator, initializer=None):
        super().__init__('TODO')

        self.declarator = declarator
        self.initializer = initializer
        self.expr_type = VarType(self.declarator.ref_count, parser.type, self.declarator.arr_offset)

        if self.initializer is not None and parser.is_typedef:
            compilation_err.append('can not initialize typedef {}', self.declarator.name)
            parser.error = compilation_err[-1]
            parser_error()

        if self.initializer is not None:
            
            if isinstance(self.initializer, Initializers):
                raise Exception('Array initializer not handled')
            
            if self.initializer.expr_type.ref_count == 0:
                if self.expr_type.ref_count + len(self.expr_type.arr_offset) == 0:
                    if self.initializer.expr_type._type == parser.type:
                        pass

                    
                    else:
                        self.initializer = CastExpr(self.expr_type, self.initializer)
                else:
                    if self.initializer.expr_type._type == 'float':
                        compilation_err.append('Can not assign float to pointer')
                        parser.error = compilation_err[-1]
                        parser_error()
                    else:
                        self.initializer = CastExpr(self.expr_type, self.initializer)
            else:
                if self.expr_type.ref_count + len(self.expr_type.arr_offset) == 0:
                    if self.expr_type._type == 'float':
                        compilation_err.append('Can not typecast pointer to float')
                        parser.error = compilation_err[-1]
                        parser_error()
                    else:
                        self.initializer = CastExpr(self.expr_type, self.initializer)
                else:
                    if self.initializer.expr_type.ref_count == self.expr_type.ref_count + len(self.expr_type.arr_offset):
                        pass
                    else:
                        self.initializer = CastExpr(self.expr_type, self.initializer)
        # dot: print only if initiaizer is not empty

class Specifier(_BaseDecl):
    def __init__(self, specifier_name):
        super().__init__("Specifier")
        self.specifier_name = specifier_name
        self.attr_ignore.append('specifier_name')

class StructUnionSpecifier(Specifier):
    def __init__(
        self, 
        struct_union: str, 
        name=None, 
        decls_list=None
    ):
        super().__init__("Struct or Union Specifier")
        self.struct_union = struct_union
        self.name = name
        self.decls_list = decls_list
        self.variables = None

        # compute variables list of decls_list if not None
        if self.decls_list is not None:
            self.compute_variables()
        
        # name and decls_list both given => add to symtable 
        # and check for redeclaration error 
        if self.decls_list is not None and self.name is not None:
            struct_type = StructType(self.name, self.variables)
            symtable.add_struct(self.name, struct_type)

        # lambda structs => name in StructType None
        elif self.decls_list is not None and self.name is None:
            struct_type = StructType(None, self.variables)

        # ony name given => try lookup struct in symtable, if not
        # found then give only name in hope it gets resolved later.
        elif self.decls_list is None and self.name is not None:
            lookup_type = symtable.lookup_struct(self.name)
            if lookup_type is None:
                struct_type = StructType(self.name, None)
            else:
                struct_type = lookup_type
            
        self.struct_type = struct_type

    def compute_variables(self):
        self.variables = {}
        
        for declaration in self.decls_list:
      
            d_spec = declaration.specifier
            d_init_list = declaration.init_list
            d_type = d_spec.type_spec 
            
            is_void = d_type == 'void'
            is_struct = d_type is StructType  
            
            for init_decl in d_init_list:
                decl = init_decl.declarator

                vartype = VarType(decl.ref_count, d_type, decl.arr_offset)

                # Sanity checking of arr offset
                if not all(map(lambda x: isinstance(x, Const) and x.dvalue=='int', decl.arr_offset)):
                    compilation_err.append('Only Int constant in array declaration')
                    parser.error = compilation_err[-1]
                    parser_error()

                # void declaration checking
                if is_void and vartype.ref_count==0:
                    compilation_err.append('cannot assign variable of type void')
                    parser.error = compilation_err[-1]
                    parser_error()
                
                # struct declaration checking
                if is_struct and not d_type.is_defined() and vartype.ref_count==0:
                    # print(1, is_struct and not d_type.is_defined() and vartype.ref_count==0)
                    compilation_err.append('storage of struct named {} not avaiable'.format(d_type.name))
                    parser.error = compilation_err[-1]
                    parser_error()

                # Add declaration in variables
                if decl.name in self.variables:
                    compilation_err.append('Redeclaration of variable named {} inside struct'.format(decl.name))
                    parser.error = compilation_err[-1]
                    parser_error()

                self.variables[decl.name] = vartype

class DeclarationSpecifier(Specifier):
    def __init__(
        self, 
        storage_type_spec, 
        type_spec: Union[str, StructUnionSpecifier]
    ):
        super().__init__("Declaration Specifier")
        self.storage_type_spec = storage_type_spec
        self.type_spec = type_spec

        if isinstance(self.type_spec, StructUnionSpecifier):
            self.type_spec = self.type_spec.struct_type

class StructDeclaration(_BaseDecl):
    def __init__(
        self, 
        specifier: DeclarationSpecifier, 
        init_list: List[InitDeclarator] = []
    ): 
        super().__init__('TODO')
        self.specifier = specifier
        self.init_list = init_list

class StructDeclarator(_BaseDecl):
    def __init__(self, declarator, expr=None):
        super().__init__('TODO')
        self.declarator = declarator
        # FIXME: const expr set to None for simpler behaviour
        self.constexpr = None
        # self.constexpr = expr

class Declarator(_BaseDecl):
    def __init__(self, ref_count, name, arr_offset):
        super().__init__('TODO')

        # NOTE: don't add symtab function here as
        # this is used in function parameter_list
        # where symtab addition is not required

        self.ref_count = ref_count
        self.name = name
        self.arr_offset = arr_offset

class FuncDirectDecl(_BaseDecl):
    def __init__(
        self, 
        ref_count: int, 
        name: str, 
        param_list: List[tuple],
        is_ellipsis: bool = False
    ):
        super().__init__('TODO')
        self.ref_count = ref_count
        self.name = name
        self.param_list = param_list
        self.is_ellipsis = is_ellipsis

class Declaration(_BaseDecl):
    def __init__(
        self, 
        specifier: DeclarationSpecifier, 
        init_list: List[InitDeclarator] = []
    ):
        super().__init__('TODO')
        self.specifier = specifier
        self.init_list = init_list

        _type = self.specifier.type_spec
        storage_type = self.specifier.storage_type_spec

        self.is_static = storage_type == 'static'
        self.is_typedef = storage_type == 'typedef'
        self.is_void = _type == 'void'
        self.is_struct = isinstance(_type, StructType)
        if self.is_typedef:
            for init_decl in self.init_list:
                decl = init_decl.declarator

                # Function declaration !
                if isinstance(decl, FuncDirectDecl):    
                    vartype = VarType(decl.ref_count, _type)
                    # add alias as a function type
                    symtable.add_typedef(decl.name, Function(vartype, decl.name, decl.param_list, decl.is_ellipsis))
                    continue

                vartype = VarType(decl.ref_count, _type, decl.arr_offset)

                # Sanity checking of arr offset
                if not all(map(lambda x: isinstance(x, Const) and x.dvalue=='int', decl.arr_offset)):
                    compilation_err.append('Only Int constant in array declaration')
                    parser.error = compilation_err[-1]
                    parser_error()

                if self.is_void and vartype.ref_count==0:
                    compilation_err.append('cannot assign variable of type void')
                    parser.error = compilation_err[-1]
                    parser_error()
                
                # struct declaration checking
                if self.is_struct and not _type.is_defined() and vartype.ref_count==0:
                    compilation_err.append('storage of struct named {} not avaiable'.format(_type.name))
                    parser.error = compilation_err[-1]
                    parser_error()

                # Add declaration in symtab
                symtable.add_typedef(decl.name, vartype)

        for init_decl in self.init_list:

            decl = init_decl.declarator

            # Function declaration !
            if isinstance(decl, FuncDirectDecl):    
                vartype = VarType(decl.ref_count, _type)
                symtable.add_func(Function(vartype, decl.name, decl.param_list))
                continue

            vartype = VarType(decl.ref_count, _type, decl.arr_offset)
            # print("declaring", decl.name, vartype)
            # Sanity checking of arr offset
            if not all(map(lambda x: isinstance(x, Const) and x.dvalue=='int', decl.arr_offset)):
                compilation_err.append('Only Int constant in array declaration')
                parser.error = compilation_err[-1]
                parser_error()

            if self.is_void and vartype.ref_count==0:
                compilation_err.append('cannot assign variable of type void')
                parser.error = compilation_err[-1]
                parser_error()
            
            # struct declaration checking
            if self.is_struct and not _type.is_defined() and vartype.ref_count==0:
                compilation_err.append('storage of struct named {} not avaiable'.format(_type.name))
                parser.error = compilation_err[-1]
                parser_error()

            # Add declaration in symtab
            symtable.add_var(decl.name, vartype, self.is_static)
            # print("decl ", decl.name, vartype)

    @staticmethod
    def _gen_dot(obj):
        """Get a list of node and edge declarations."""
        return []

# #############################################################################
# Initializers            
# #############################################################################

class Initializers(_BASENODE):
    def __init__(self, init_list):
        super().__init__()
        self.init_list = init_list


# #############################################################################
# Statements            
# #############################################################################

class Statement(_BASENODE):
    def __init__(self, name):
        super().__init__()
        self.name = name
        self.attr_ignore.append('name')

class LabeledStmt(Statement):
    def __init__(self, case, stmt):
        super().__init__("Labeled Statement")
        self.case = case
        self.stmt = stmt

class CompoundStmt(Statement):
    def __init__(
        self, 
        decls: List[Declaration], 
        stmts: List[Statement]
    ):
        super().__init__("Compound Statment")
        self.decl_list = decls
        self.stmt_list = stmts

    @staticmethod
    def _gen_dot(obj):
        """Get a list of node and edge declarations."""
        dot_list = ['CompoundStmt']

        if isinstance(obj.decl_list, list):
            for decl in obj.decl_list:
                dot_list.append(decl._gen_dot(decl))

        if isinstance(obj.stmt_list, list):        
            for stmt in obj.stmt_list:
                dot_list.append(stmt._gen_dot(stmt))
        
        return dot_list
        

class ExprStmt(Statement):
    def __init__(self, expr):
        super().__init__("Expression Statement")
        self.expr = expr
    def __call__(self):
        return self.expr

class SelectionStmt(Statement):
    def __init__(self, select_type, select_expr, if_stmt, else_stmt=None):
        super().__init__("Selection Statement")
        self.select_type = select_type
        self.select_expr = select_expr
        self.if_stmt = if_stmt
        self.else_stmt = else_stmt

class IterStmt(Statement):
    def __init__(self, iter_type, iter_expr, stmt):
        super().__init__("Iteration Statement")
        self.iter_type = iter_type
        self.iter_expr = iter_expr
        self.stmt = stmt

class JumpStmt(Statement):
    def __init__(self, jump_type, expr=None):
        super().__init__("Jump Statement")
        self.jump_type = jump_type
        self.expr = expr
        if self.jump_type == 'break':
            if not symtable.check_break_scope():
                parser.error = 'break not allowed without loop or switch'
                parser_error()
        elif self.jump_type == 'continue':
            if not symtable.check_continue_scope():
                parser.error = 'continue not allowed without loop'
                parser_error()


# #############################################################################
# External declaration and function definitions            
# #############################################################################

class Node(_BASENODE):
    def __init__(self, t_name):
        super().__init__()
        self.t_name = t_name
        self.attr_ignore.append('t_name')

class Start(Node):
    def __init__(self, units):
        super().__init__("Start")
        self.units = units
        # self.dot_attr = {'Start': self.units}

    @staticmethod
    def _gen_dot(obj):
        """Get a list of node and edge declarations."""

        dot_list = ['Start']

        # Avoid None child node, empty strings, and empty lists
        FILTERED_LIST = [None, "", []]    

        for child in filter(lambda x: not x in FILTERED_LIST, obj.units):         
          dot_list.append(child._gen_dot(child))                
                
        return dot_list

    def gen_dot(self, graph):
        """Get a list of node and edge declarations."""

        def leaf_redundancy(tree):
            if isinstance(tree,list) and len(tree) == 1:
                return tree[0]
            elif isinstance(tree,list) and len(tree) > 1:
                newList = tree[:1]
                for child in tree[1:]:
                    newList.append(leaf_redundancy(child))
                return newList
            else:
                return tree

        def remove_redundancy(tree):
            newList = tree[:1]

            for child in tree[1:]:
                if type(child) is list:
                    child = remove_redundancy(child)
                    if child != []:
                        newList.append(child)
                else:
                    newList.append(repr(child))
                # elif type(child) is str:
                #     newList.append(child)
                # else:
                #     raise Exception('remove: Invalid type {}'.format(type(child)))
                
            if len(newList) == 1:
                return []
            if len(newList) == 2:
                return newList[1]
            
            return newList

        def generate_dot(graph, tree, node_idx):
            """ Node and edge declarations."""
            if type(tree) is str:
                graph.add_node(pydot.Node(node_idx, label=repr(tree), shape='house', style='filled', color='yellowgreen'))
                return node_idx
            elif type(tree) is list:
                graph.add_node(pydot.Node(node_idx, label=repr(tree[0]), shape='egg'))
                cur_idx = node_idx
                for child in tree[1:]:
                    if child == []:
                        continue
                    graph.add_edge(pydot.Edge(node_idx, cur_idx+1))
                    cur_idx = generate_dot(graph, child, cur_idx+1)
                return cur_idx
            else:
                raise Exception('Invalid type {}'.format(type(tree)))

        
        syn_tree = self._gen_dot(self)
        tree = leaf_redundancy(syn_tree)
        AST = remove_redundancy(tree)

        if AST == [] or AST is None or AST[0] != 'Start':
            AST = ['Start', AST]
        
        generate_dot(graph, AST, 0)
        graph.get_node('0')[0].set_shape('doubleoctagon')
        graph.get_node('0')[0].set_color('orange')
        graph.get_node('0')[0].set_style('filled')
    
        return AST


class FuncDef(Node):
    def __init__(
        self, 
        specifier: DeclarationSpecifier, 
        ref_count: int, 
        name: str, 
        param_list: List[tuple], 
        stmt: CompoundStmt,
        is_ellipsis: bool = False
    ):
        super().__init__('Function Definition')
        self.specifier = specifier
        self.ref_count = ref_count
        self.name = name
        self.param_list = param_list
        self.stmt = stmt
        self.vartype = VarType(self.ref_count, self.specifier.type_spec)
        self.is_ellipsis = is_ellipsis
        # symtable.add_func(Function(self.vartype, self.name, self.param_list))

    @staticmethod
    def _gen_dot(obj):
        """Get a list of node and edge declarations."""
        dot_list = ['FuncDef']
        
        # ret_type
        dot_list.append(obj.vartype._gen_dot(obj.vartype))                

        # func name
        dot_list.append(repr(obj.name))

        # param list
        dot_list.append(_BASENODE._gen_dot(obj.param_list) + (['...'] if obj.is_ellipsis else []))                

        # compound stmt
        dot_list.append(obj.stmt._gen_dot(obj.stmt))                
    
        return dot_list

import csv
# from parser import parser, lexer, bcolors

def parser_error(error_str=None):
    parser.compilation_err = True
    print(bcolors.BOLD+'{}:{}:'.format(lexer.filename,lexer.lineno)+bcolors.ENDC,end='')
    print(bcolors.FAIL+' SyntaxError: '+bcolors.ENDC,parser.error)
    print('     {} |{}'.format(lexer.lineno,lexer.lines[lexer.lineno - 1]))

class ScopeTable:
    def __init__(self, scope_depth=0, parent=None, scope_id=0, scope_type='Other'):
        self.scope_id = scope_id        # scope id
        self.scope_depth = scope_depth  # scope depth
        self.parent = parent            # parent scopeTable
        self.variables = {}             # for identifiers
        self.aliases = {}               # for typedefs
        self.structs = {}               # for structs and union
        self.metadata = scope_type      # will include function, loop or ifelse


    def lookup_var(self, name):
        if name in self.variables:
            return True
        return False
        # return self.parent.lookup_var(name) if self.parent is not None else False
    
    def lookup_struct(self, name):
        if name in self.structs:
            return True
        return False
        # return self.parent.lookup_struct(name) if self.parent is not None else False
    
    def lookup_alias(self, name):
        return self.aliases.get(name, None)
        # return self.parent.lookup_alias(name) if self.parent is not None else False
        
class SymbolTable():
    def __init__(self):

        self.function = {} # for function (func can only be declared in global mode)
        self.global_scope = ScopeTable()
        self.global_scope.metadata = 'Global'
        self.all_scope = [self.global_scope]

        self.scope_stack = [self.global_scope]
    
    def cur_depth(self):
        return len(self.scope_stack)

    def cur_scope(self):
        assert len(self.scope_stack) >= 1
        return self.scope_stack[-1]
    
    def check_break_scope(self):
        scope = self.cur_scope()
        while scope:
            if scope.metadata in ['Loop', 'Switch']:
                return True
            scope = scope.parent
        return False

    def check_continue_scope(self):
        scope = self.cur_scope()
        while scope:
            if scope.metadata in ['Loop']:
                return True
            scope = scope.parent
        return False

    def push_scope(self, scope_type='Other') -> None:
        new_scope = ScopeTable(self.cur_depth(), self.scope_stack[-1], len(self.all_scope), scope_type)
        self.all_scope.append(new_scope)
        self.scope_stack.append(new_scope)

    def pop_scope(self) -> None:
        self.scope_stack.pop()

    def lookup_var(self, name):
        scope = self.cur_scope()
        while scope:
            if scope.lookup_var(name):
                return scope.variables[name]
            scope = scope.parent
        return None

    def lookup_struct(self, name):
        scope = self.cur_scope()
        while scope:
            if scope.lookup_struct(name):
                return scope.structs[name]
            scope = scope.parent
        return None

    def lookup_alias(self, id):
        return self.cur_scope().lookup_alias(id)

    def lookup_func(self, name):
        if name in self.function:
            return self.function[name]
        return None

    def get_size(self, dtype):
        raise Exception('TODO')

    def add_var(self, name, vtype, is_static = False):
        scope = self.global_scope if is_static else self.cur_scope()
        if scope.lookup_var(name):
            compilation_err.append('Redeclaration of variable named {}'.format(name))
            # parser.error = compilation_err[-1]
            parser_error()
            return

        scope.variables[name] = vtype

    def add_struct(self, name, struct_type):
        if self.cur_scope().lookup_struct(name):
            compilation_err.append('Redeclaration of struct named {}'.format(name))
            # parser.error = compilation_err[-1]
            parser_error()
            return

        self.cur_scope().structs[name] = struct_type

    def add_typedef(self, alias, actual):
        cur_scope = self.cur_scope()
        lookup_alias = cur_scope.lookup_alias(alias)
        if lookup_alias is None:
            cur_scope.aliases[alias] = actual
        elif lookup_alias == actual:
            pass
        else:
            compilation_err.append('Redeclaration of type/alias named {}'.format(alias))
            # parser.error = compilation_err[-1]
            parser_error()
        
    def add_func(self, func) -> None:
        if func.name in self.function:
            compilation_err.append('Redeclaration of function named {}'.format(func.name))
            # parser.error = compilation_err[-1]
            parser_error()
            return
                
        self.function[func.name] = func

    def dump_csv(self, filename):
        with open(filename, 'w', newline='') as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(['Table Id', 'Parent Id', 'Table Type', 'Symbol Id', 'Symbol Name', 'Symbol Type', 'Symbol Other Information'])
            scope_id = 0
            parent_id = 'null'
            idx = 0
            for key in self.function:
                row = [scope_id, parent_id, self.all_scope[scope_id].metadata, idx, key, 'function', str(self.function[key])]
                writer.writerow(row)
                idx += 1
            
            for _ in range(len(self.all_scope)):
                cur_scope = self.all_scope[scope_id]
                for key in cur_scope.structs:
                    row = [scope_id, parent_id, cur_scope.metadata, idx, key, 'struct', str(cur_scope.structs[key])]
                    writer.writerow(row)
                    idx += 1
                
                for key in cur_scope.variables:
                    row = [scope_id, parent_id, cur_scope.metadata, idx, key, 'variable', str(cur_scope.variables[key])]
                    writer.writerow(row)
                    idx += 1
                
                for key in cur_scope.aliases:
                    row = [scope_id, parent_id, cur_scope.metadata, idx, key, 'type alias', str(cur_scope.aliases[key])]
                    writer.writerow(row)
                    idx += 1
                
                scope_id += 1
                if scope_id != len(self.all_scope):
                    parent_id = self.all_scope[scope_id].parent.scope_id
                idx = 0

symtable = SymbolTable()
compilation_err = []

from lexer import lexer, tokens

parser = yacc.yacc()
parser.type = None
parser.is_typedef = False
parser.error = ''
parser.compilation_err = False