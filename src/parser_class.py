try:
    from CS335.gcc_lite.src.helper import *
except:
    pass

from CS335.gcc_lite.src.parser_debug import p_shift_expression
from typing import Union, List
import pydot
# from helper import *

symtable = SymbolTable()
compilation_err = []

# #############################################################################
# Type and scope related classes            
# #############################################################################

class StructType:
    def __init__(self, name=None, variables=None):
        # For use in named struct decls which are not 
        # yet defined
        self.name = name

        # For use in lambda struct and defined struct
        self.variables = variables

    def is_defined(self):
        if self.variables is not None:
            return True
        
        self.variables = symtable.lookup_struct(self.name)
        return self.variables is not None

    def _get_size(self):
        raise Exception('TODO')

class Function:
    def __init__(self, ret_type, name, args):
        self.ret_type = ret_type    # should be VarType
        self.name = name            # str
        self.args = args            # list

class VarType:
    def __init__(self, ref_count, _type, arr_offset=None):
        self.ref_count = ref_count
        self._type = _type
        self.arr_offset = arr_offset

class ScopeName:
    def __init__(self, name):
        self.name = name

# #############################################################################
# Misc.            
# #############################################################################

class _BASENODE():
    def __init__(self):
        self.attr_ignore = ['attr_ignore']

    @staticmethod
    def _gen_dot(graph, obj, node_idx):
        """Get a list of node and edge declarations."""

        if isinstance(obj, (str, int, float, tuple)):
            graph.add_node(pydot.Node(node_idx, label=repr(obj), shape='house', style='filled', color='yellowgreen'))
        elif isinstance(obj, _BASENODE):
            graph.add_node(pydot.Node(node_idx, label=obj.__class__.__name__, shape='egg'))
        elif isinstance(obj, list):
            pass
        else:
            raise Exception('Invalid type {}'.format(type(obj)))
        
        cur_idx = node_idx

        if isinstance(obj, list):
            
            for child in obj:
                # Avoid None child node, empty strings, and empty lists
                if (
                    child is None
                    or child == ""
                    or child == []
                ):
                    continue
                
                _gen_dot_func = obj._gen_dot if isinstance(obj, _BASENODE) else _BASENODE._gen_dot

                graph.add_edge(pydot.Edge(node_idx, cur_idx+1))
                cur_idx = _gen_dot_func(graph, child, cur_idx+1)                

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
                
                graph.add_edge(pydot.Edge(node_idx, cur_idx+1))
                
                if isinstance(child, list):
                    graph.add_node(pydot.Node(cur_idx+1, label=attr, shape='egg'))

                _gen_dot_func = obj._gen_dot if isinstance(obj, _BASENODE) else _BASENODE._gen_dot
                cur_idx = _gen_dot_func(graph, child, cur_idx+1)                
                
        return cur_idx



# #############################################################################
# Expressions            
# #############################################################################

class BaseExpr(_BASENODE) :
       
    def __init__(self, t_name):
        super().__init__()
        self.t_name = t_name
        self.attr_ignore.append('t_name')

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
        # self.get_type()

    def get_type(self):
        if self.dvalue is 'int':
            self._type = VarType(0, 'int')
        elif self.dvalue is 'float':
            self._type = VarType(0, 'float')
        elif self.dvalue is 'char':
            self._type = VarType(0, 'char')
        elif self.dvalue is 'STRING_LITERAL':
            self._type = VarType(1, 'char')
        else:
            raise Exception('Unknown Constant type')

class Identifier(BaseExpr):
    def __init__(self, ident):
        super().__init__("Identifier")
        self.ident = ident
        self.get_type()

    def get_type(self):
        _var = symtable.lookup_var(self.ident)
        if _var is None:
            compilation_err.append('Undeclared Variable')
        else:
            self._type = VarType(_var.ref_count, _var._type)
        

class OpExpr(BaseExpr):
    def __init__(self, lhs, ops, rhs):
        super().__init__("Expression")
        self.lhs = lhs
        self.ops = ops
        self.rhs = rhs
        self.get_type()

        # lhs_type = get_expr_type(self.lhs)
        # rhs_type = get_expr_type(self.rhs)
        # if lhs_type not in operator_type[ops] or rhs_type not in operator_type[ops]:
        #     print_compilation_error("Type mismatch error",lhs.lineno(0))

    def get_type(self):
        
        if self.lhs._type._type is not self.ops_type[self.ops] and self.rhs._type._type is not self.ops_type[self.ops]:
            compilation_err.append('Type not compatible with ops {}'.format(self.ops)) 

        if self.lhs._type.ref_count > 0:
            if self.rhs._type.ref_count > 0:
                if self.ops in ['-'] and self.rhs._type.ref_count == self.lhs._type.ref_count:
                    inferred_type = 'int'
                    ref_count = 0
                else:
                    compilation_err.append('Type not compatible with ops {}'.format(self.ops))
            else:
                if self.rhs._type._type == 'int':
                    inferred_type = self.lhs._type._type
                    ref_count = self.lhs._type.ref_count
                else:
                    compilation_err.append('Type not compatible with ops {}'.format(self.ops))
        else:
            if self.rhs._type.ref_count > 0:
                compilation_err.append('Type not compatible with ops {}'.format(self.ops))
            else:
                if self.rhs._type._type == self.lhs._type._type:
                    if self.rhs._type._type in self.ops_type[self.ops]:
                        inferred_type = self.lhs._type._type
                        ref_count = self.lhs._type.ref_count
                    else:
                        compilation_err.append('Type not compatible with ops {}'.format(self.ops))
                else:
                    if self.rhs._type._type in self.ops_type[self.ops]:
                        if self.lhs._type._type in self.ops_type[self.ops]:
                            if self.rhs._type._type == 'float' or self.lhs._type._type == 'float':
                                inferred_type = 'float'
                                ref_count = 0
                            else:
                                inferred_type = 'int'
                                ref_count = 0
                            self.lhs = CastExpr(VarType(ref_count, inferred_type), self.lhs)
                            self.rhs = CastExpr(VarType(ref_count, inferred_type), self.rhs)
                        else:
                            compilation_err.append('Type not compatible with ops {}'.format(self.ops))
                    else:
                        compilation_err.append('Type not compatible with ops {}'.format(self.ops))

        self._type(ref_count, inferred_type)

class UnaryExpr(OpExpr):
    def __init__(self, ops, rhs):
        super().__init__(None, ops, rhs)
        self.get_type()

def get_type(self):

        if self.ops is 'sizeof':
            inferred_type = 'int'
            ref_count = 0
        elif self.ops in ['--', '++', '+', '-']:
            if self.rhs._type.ref_count is 0:
                if self.rhs._type._type not in _BASENODE.ops_type[self.ops]:
                    compilation_err.append('Type not compatible with ops {}'.format(self.ops)) 
                
                inferred_type = 'int'
                ref_count = 0

            else:
                if self.ops in ['-', '+']:
                    compilation_err.append('wrong type argument to unary minus')
                inferred_type = self.rhs._type._type
                ref_count = self.rhs._type.ref_count

        elif self.ops in ['!', '~']:
            if self.rhs._type._type not in _BASENODE.ops_type[self.ops]:
                compilation_err.append('Type not compatible with ops {}'.format(self.ops)) 
            
            inferred_type = 'int'
            ref_count = 0
        else:
            if not isinstance(self.rhs, Identifier):
                compilation_err('RHS should be an indentifier')

            ref_count = self.rhs._type.ref_count \
                + (1 if self.ops is '&' else -1)    
            
            inferred_type = self.rhs._type._type
        
        self._type = VarType(ref_count, inferred_type)

class PostfixExpr(OpExpr):
    def __init__(self, lhs, ops, rhs=None):
        super().__init__(lhs, ops, rhs)

    def get_type(self):
        
        # simple operation
        if self.ops in ['--', '++']:
            if self.lhs._type.ref_count is 0:
                if self.lhs._type._type not in _BASENODE.ops_type[self.ops]:
                    compilation_err.append('Type not compatible with ops {}'.format(self.ops)) 
                
                inferred_type = 'int'
                ref_count = 0

            else:
                # pointer increment operation which returns the same type
                inferred_type = self.lhs._type._type
                ref_count = self.lhs._type.ref_count

        # struct deference child 
        elif self.ops is '.':
            if isinstance(self.lhs._type._type, StructType):
                struct_var = self.lhs._type._type.variables[self.rhs]
                if struct_var is None:
                    compilation_err.append('{} has no member named {}'.format(self.lhs._type._type.name, self.rhs))
                inferred_type = struct_var._type
                ref_count = struct_var.ref_count
            else:
                compilation_err.append('Dereferencing invalid struct type')
        # function calling
        elif self.ops is '(':
            arg_list = [] if self.rhs is None else self.rhs
            # sanity checking of function args and 
            if isinstance(self.lhs, str):
                func = symtable.lookup_func(self.lhs)
                if func is None:
                    compilation_err.append('{} is not callable'.format(self.lhs))

                if len(arg_list) == len(func.args):
                    inferred_type = func.ret_type._type
                    ref_count = func.ret_type.ref_count
                else:
                    compilation_err.append('too few/many arguments to function {}'.format(func.name))
            else:
                compilation_err.append('called object is not a function or function pointer')
            # set return type as type of function
            raise Exception('TODO')
        # array reference
        elif self.ops is '[':
            if self.rhs._type == VarType(0, 'int'):
                if self.lhs._type.ref_count > 0:
                    inferred_type = self.lhs._type._type
                    ref_count = self.lhs._type.ref_count - 1
                else:
                    compilation_err.append('Subscripted value is neither array nor pointer')
            else:
                compilation_err.append('Array subscript is not an integer')
            
class CastExpr(BaseExpr):
    def __init__(self, _type, Expr):
        super().__init__("Cast Expression")
        self.type = _type
        self.expr = Expr

    def get_type(self):
        raise Exception('TODO')
        # curr_type = get_expr_type(self.expr)
        # if not allowed_typecast(curr_type,type)
        #     print_compilation_error("Type conversion error",expr.lineno(0))

class AssignExpr(OpExpr):
    def __init__(self, lhs, ops, rhs):
        super().__init__(lhs, ops, rhs)

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
    
    def add_expr(self, expr):
        self.expr_list.append(expr)

# #############################################################################
# Declarators            
# #############################################################################

class _BaseDecl(_BASENODE):
    def __init__(self, t_name):
        super().__init__()
        self.t_name = 'TODO'
        self.attr_ignore.append('t_name')
    
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
        self.is_struct = _type is StructType

        if self.is_typedef:
            # TODO: store symbols as aliases of _type
            raise Exception('not supported')

        for init_decl in init_list:
            decl = init_decl.declarator

            vartype = VarType(decl.ref_count, _type, decl.arr_offset)

            # Sanity checking of arr offset
            if not all(map(lambda x: isinstance(x, Const) and x.dvalue=='int', decl.arr_offset)):
                compilation_err.append('Only Int constant in array declaration')

            if self.is_void and vartype.ref_count==0:
                compilation_err.append('cannot assign variable of type void')
            
            # struct declaration checking
            if self.is_struct and _type.is_defined() and vartype.ref_count==0:
                compilation_err.append('storage of struct named {} not avaiable'.format(d_type.name))

            # Add declaration in symtab
            symtable.add_var(decl.name, vartype, self.is_static)

class InitDeclarator(_BaseDecl):
    def __init__(self, declarator, initializer=None):
        super().__init__('TODO')
        self.declarator = declarator
        self.initializer = initializer

        if self.initializer is not None:
            
            # check type leftside and if
            # compatible then init it.
            raise Exception('Not supported')
            
        # dot: print only if initiaizer is not empty

class Specifier(_BaseDecl):
    def __init__(self, specifier_name):
        super().__init__("Specifier")
        self.specifier_name = specifier_name
        self.attr_ignore.append('specifier_name')

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
        elif isinstance(self.type_spec, Identifier):
            raise Exception('Aliases not supported')

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

        # compute variables list of decls_list
        self.compute_variables()
        
        # name and decls_list both given => add to symtable 
        # and check for redeclaration error 
        if self.decls_list is not None and self.name is not None:
            struct_type = StructType(self.name, self.decls_list.variables)
            symtable.add_struct(self.name, struct_type)

        # lambda structs => name in StructType None
        elif self.decls_list is not None and self.name is None:
            struct_type = StructType(None, self.decls_list.variables)

        # ony name given => try lookup struct in symtable, if not
        # found then give only name in hope it gets resolved later.
        elif self.decls_list is None and self.name is not None:
            lookup_type = symtable.lookup_struct(self.name)
            if lookup_type is None:
                struct_type = StructType(self.name, None)
            else:
                struct_type = StructType(self.name, lookup_type)
            
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

                # void declaration checking
                if is_void and vartype.ref_count==0:
                    compilation_err.append('cannot assign variable of type void')
                
                # struct declaration checking
                if is_struct and d_type.is_defined() and vartype.ref_count==0:
                    compilation_err.append('storage of struct named {} not avaiable'.format(d_type.name))

                # Add declaration in variables
                if decl.name in self.variables:
                    compilation_err.append('Redeclaration of variable named {} inside struct'.format(name))

                self.variables[self.name] = vartype

                
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
        self.constexpr = expr

        if self.constexpr is not None:
            raise Exception('not supported')

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
        param_list: List[ParamsDecl]
    ):
        super().__init__('TODO')
        self.ref_count = ref_count
        self.name = name
        self.param_list = param_list

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
    def __init__(self, decls, stmts):
        super().__init__("Compound Statment")
        self.decl_list = decls
        self.stmt_list = stmts

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
    def _gen_dot(graph, obj, node_idx):
        """Get a list of node and edge declarations."""

        graph.add_node(pydot.Node(node_idx, label=obj.__class__.__name__, 
                shape='doubleoctagon', color='orange', style='filled'
            )
        )
        cur_idx = node_idx
            
        for child in obj.units:
            # Avoid None child node, empty strings, and empty lists
            if (
                child is None
                or child == ""
                or child == []
            ):
                continue
            
            graph.add_edge(pydot.Edge(node_idx, cur_idx+1))
            cur_idx = child._gen_dot(graph, child, cur_idx+1)                
                
        return cur_idx

    def gen_dot(self, graph, node_idx=0):
        """Get a list of node and edge declarations."""
        self._gen_dot(graph, self, node_idx)
        print('Dot graph generated')

class FuncDef(Node):
    def __init__(
        self, 
        specifier: DeclarationSpecifier, 
        ref_count: int, 
        name: str, 
        args_list: List[ParamsDecl], 
        stmt: CompoundStmt
    ):
        super().__init__('Function Definition')
        self.specifier = specifier
        self.ref_count = ref_count
        self.name = name
        self.args_list = args_list
        self.stmt = stmt

        # check for conflicting name function
        if symtable.lookup_func(name) is not None:
            compilation_err.append("conflicting name of function")
        else:
            self.add_to_symtab()

    def add_to_symtab(self):
        vartype = VarType(self.ref_count, self.specifier)
        symtable.add_func(Function(vartype, self.name, self.args_list))
