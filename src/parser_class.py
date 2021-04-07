try:
    from CS335.gcc_lite.src.helper import *
except:
    pass

from os import removedirs
from typing import Union, List
import pydot
from helper import *

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

                if len(child_list) == 1:
                    dot_list.append(child_list[0])
                else:
                    dot_list.append(child_list)
                
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
    def __init__(self, ret_type, name, args):
        super().__init__()
        self.ret_type = ret_type    # should be VarType
        self.name = name            # str
        self.args = args            # list
    
    def __str__(self):
        return 'Function(ret_type={}, name={}, args={})'.format(str(self.ret_type), self.name, self.args)
    
    # def is_defined(self):


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

        dot_list = ['VarType', 'ref_count={}'.format(obj.ref_count)]
        child_type = obj._type._gen_dot(obj._type) if isinstance(obj._type, _BASENODE) else obj._type
        dot_list.append(child_type)

        if obj.arr_offset is None or len(obj.arr_offset)==0:
            return dot_list

        dim_list = ['Array Dims']
        for dim in obj.arr_offset:
            dim_list.append(dim._gen_dot(dim))

        return dot_list

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
                else:
                    self.expr_type = _var
            else:
                self.expr_type = _var
        else:
            self.expr_type = _var

class OpExpr(BaseExpr):
    def __init__(
        self, 
        lhs: BaseExpr, 
        ops: str, 
        rhs: BaseExpr
    ):
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
            # print("Here?")

        if self.lhs.expr_type.ref_count > 0:
            if self.rhs.expr_type.ref_count > 0:
                if self.ops in ['-'] and self.rhs.expr_type.ref_count == self.lhs.expr_type.ref_count:
                    inferred_type = 'int'
                    ref_count = 0
                else:
                    compilation_err.append('Type not compatible with ops {}'.format(self.ops))
            else:
                if self.rhs.expr_type._type == 'int':
                    inferred_type = self.lhs.expr_type._type
                    ref_count = self.lhs.expr_type.ref_count
                else:
                    compilation_err.append('Type not compatible with ops {}'.format(self.ops))
        else:
            if self.rhs.expr_type.ref_count > 0:
                compilation_err.append('Type not compatible with ops {}'.format(self.ops))
            else:
                if self.rhs.expr_type._type == self.lhs.expr_type._type:
                    if self.rhs.expr_type._type in self.ops_type[self.ops]:
                        inferred_type = self.lhs.expr_type._type
                        ref_count = self.lhs.expr_type.ref_count
                    else:
                        compilation_err.append('Type not compatible with ops {}'.format(self.ops))
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
                    else:
                        compilation_err.append('Type not compatible with ops {}'.format(self.ops))

        self.expr_type = VarType(ref_count, inferred_type)

class UnaryExpr(OpExpr):
    def __init__(self, ops, rhs):
        super().__init__(None, ops, rhs)
        self.get_type()

    def get_type(self):

        ref_count = 0
        inferred_type = 'int'

        if self.ops == 'sizeof':
            inferred_type = 'int'
            ref_count = 0
        elif self.ops in ['--', '++', '+', '-']:
            if self.rhs.expr_type.ref_count == 0:
                if self.rhs.expr_type._type not in self.ops_type[self.ops]:
                    compilation_err.append('Type not compatible with ops {}'.format(self.ops)) 
                
                inferred_type = 'int'
                ref_count = 0

            else:
                if self.ops in ['-', '+']:
                    compilation_err.append('wrong type argument to unary minus')
                inferred_type = self.rhs.expr_type._type
                ref_count = self.rhs.expr_type.ref_count

        elif self.ops in ['!', '~']:
            if self.rhs.expr_type._type not in self.ops_type[self.ops]:
                compilation_err.append('Type not compatible with ops {}'.format(self.ops)) 
            
            inferred_type = 'int'
            ref_count = 0
        else:
            if not isinstance(self.rhs, Identifier):
                compilation_err('RHS should be an indentifier')

            ref_count = self.rhs.expr_type.ref_count \
                + (1 if self.ops == '&' else -1)    
            
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

        if self.ops in ['--', '++']:
            if self.lhs.expr_type.ref_count == 0:
                if self.lhs.expr_type._type not in self.ops_type[self.ops]:
                    compilation_err.append('Type not compatible with ops {}'.format(self.ops)) 
                
                inferred_type = 'int'
                ref_count = 0

            else:
                # pointer increment operation which returns the same type
                inferred_type = self.lhs.expr_type._type
                ref_count = self.lhs.expr_type.ref_count

        # struct deference child 
        elif self.ops == '.':
            if isinstance(self.lhs.expr_type, StructType):
                if self.lhs.expr_type._type.is_defined():
                    struct_var = self.lhs.expr_type._type.variables.get(self.rhs, None)
                    if struct_var is None:
                        compilation_err.append('{} has no member named {}'.format(self.lhs.expr_type._type.name, self.rhs))
                    inferred_type = struct_var._type
                    ref_count = struct_var.ref_count
                else:
                    compilation_err.append('Incomplete struct {}'.format(self.lhs.expr_type._type.name))
            else:
                compilation_err.append('Dereferencing invalid struct type')
        # function calling
        elif self.ops == '(':
            arg_list = [] if self.rhs is None else self.rhs
            # sanity checking of function args and 
            if isinstance(self.lhs.expr_type, Function):
                func = self.lhs.expr_type
                if func is None:
                    compilation_err.append('{} is not callable'.format(self.lhs))

                if len(arg_list) == len(func.args):
                    inferred_type = func.ret_type._type
                    ref_count = func.ret_type.ref_count
                else:
                    compilation_err.append('too few/many arguments to function {}'.format(func.name))
            else:
                compilation_err.append('called object is not a function or function pointer')
            
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
            else:
                compilation_err.append('Array subscript is not an integer')
        
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
        else:
            if self.type.ref_count > 0:
                if self.expr.expr_type._type in ['int', 'char']:
                    self.expr_type = self.type
                else:
                    compilation_err.append('Cannot convert float to pointer')
            else:
                self.expr_type = self.type

class AssignExpr(OpExpr):
    def __init__(self, lhs, ops, rhs):
        super().__init__(lhs, ops, rhs)

    def get_type(self):
        
        # compatability is checked in CastExpr
        self.rhs = CastExpr(self.lhs.expr_type, self.lhs)
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
    def __init__(self, declarator, initializer=None, parser_type=None, is_typedef=False):
        super().__init__('TODO')

        self.declarator = declarator
        self.initializer = initializer
        self.expr_type = VarType(self.declarator.ref_count, parser_type, self.declarator.arr_offset)

        if self.initializer is not None and is_typedef:
            compilation_err.append('can not initialize typedef {}', self.declarator.name)

        if self.initializer is not None:
            
            if isinstance(self.initializer, Initializers):
                raise Exception('Array initializer not handled')
            
            if self.initializer.expr_type.ref_count == 0:
                if self.expr_type.ref_count + len(self.expr_type.arr_offset) == 0:
                    if self.initializer.expr_type._type == parser_type:
                        pass
                    else:
                        self.initializer = CastExpr(self.expr_type, self.initializer)
                else:
                    if self.initializer.expr_type._type == 'float':
                        compilation_err.append('Can not assign float to pointer')
                    else:
                        self.initializer = CastExpr(self.expr_type, self.initializer)
            else:
                if self.expr_type.ref_count + len(self.expr_type.arr_offset) == 0:
                    if self.expr_type._type == 'float':
                        compilation_err.append('Can not typecast pointer to float')
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
                    compilation_err.append('Redeclaration of variable named {} inside struct'.format(decl.name))

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
        elif isinstance(self.type_spec, Identifier):
            raise Exception('Aliases not supported')

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
        param_list: List[tuple]
    ):
        super().__init__('TODO')
        self.ref_count = ref_count
        self.name = name
        self.param_list = param_list

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
            for init_decl in self.init_list:
                decl = init_decl.declarator

                # Function declaration !
                if isinstance(decl, FuncDirectDecl):    
                    vartype = VarType(decl.ref_count, _type)
                    # add alias as a function type
                    symtable.add_typedef(decl.name, Function(vartype, decl.name, decl.param_list))
                    continue

                vartype = VarType(decl.ref_count, _type, decl.arr_offset)

                # Sanity checking of arr offset
                if not all(map(lambda x: isinstance(x, Const) and x.dvalue=='int', decl.arr_offset)):
                    compilation_err.append('Only Int constant in array declaration')

                if self.is_void and vartype.ref_count==0:
                    compilation_err.append('cannot assign variable of type void')
                
                # struct declaration checking
                if self.is_struct and _type.is_defined() and vartype.ref_count==0:
                    compilation_err.append('storage of struct named {} not avaiable'.format(_type.name))

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

            if self.is_void and vartype.ref_count==0:
                compilation_err.append('cannot assign variable of type void')
            
            # struct declaration checking
            if self.is_struct and _type.is_defined() and vartype.ref_count==0:
                compilation_err.append('storage of struct named {} not avaiable'.format(_type.name))

            # Add declaration in symtab
            symtable.add_var(decl.name, vartype, self.is_static)

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
        
        for decl in obj.decl_list:
            dot_list.append(decl._gen_dot(decl))
        
        for stmt in obj.stmt_list:
            dot_list.append(stmt._gen_dot(stmt))
        

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
    def _gen_dot(obj):
        """Get a list of node and edge declarations."""

        dot_list = ['Start']

        # Avoid None child node, empty strings, and empty lists
        FILTERED_LIST = [None, "", []]    

        for child in filter(lambda x: not x in FILTERED_LIST, obj.units):         
          dot_list.append(child._gen_dot(child))                
                
        return dot_list

    def gen_dot(self, graph, node_idx=0):
        """Get a list of node and edge declarations."""

        def remove_redundancy(tree):
            newList = tree[:1]

            for child in tree[1:]:
                if type(child) is list:
                    child = remove_redundancy(child)
                    if child != []:
                        newList.append(child)
                elif type(child) is str:
                    newList.append(child)
                # else:
                #     raise Exception('remove: Invalid type {}'.format(type(child)))
                
            # if len(newList) == 1:
            #     return []
            # if len(newList) == 2:
            #     return newList[1]
            
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

        tree = self._gen_dot(self)
        AST = remove_redundancy(tree)
        generate_dot(graph, AST, node_idx)
        return tree


class FuncDef(Node):
    def __init__(
        self, 
        specifier: DeclarationSpecifier, 
        ref_count: int, 
        name: str, 
        param_list: List[tuple], 
        stmt: CompoundStmt
    ):
        super().__init__('Function Definition')
        self.specifier = specifier
        self.ref_count = ref_count
        self.name = name
        self.param_list = param_list
        self.stmt = stmt
        self.vartype = VarType(self.ref_count, self.specifier.type_spec)
        symtable.add_func(Function(self.vartype, self.name, self.param_list))

    @staticmethod
    def _gen_dot(obj):
        """Get a list of node and edge declarations."""

        dot_list = ['FuncDef']
        
        # ret_type
        dot_list.append(obj.vartype._gen_dot(obj.vartype))                

        # func name
        dot_list.append(repr(obj.name))

        # param list
        dot_list.append(_BASENODE._gen_dot(obj.param_list))                

        # compound stmt
        dot_list.append(obj.stmt._gen_dot(obj.stmt))                
    
        return dot_list