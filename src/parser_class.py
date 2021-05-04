from os import removedirs
from typing import Union, List
import pydot
from parser import parser, parser_error
from helper import *
import copy
from collections import OrderedDict

ADDR_SIZE = 4
INT_SIZE = 4
CHAR_SIZE = 4
FLOAT_SIZE = 4

# #############################################################################
# Misc.            
# #############################################################################

class _BASENODE:
    def __init__(self):
        self.attr_ignore = ['attr_ignore']
        self.nextlist = []
        self.breaklist = []
        self.continuelist = []
        self.truelist = []
        self.falselist = []
        self.returnlist = []

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

        # For offset of each variable
        self.size = 0
        if self.variables:
            self.set_offsets()

    def get_size(self):
        return self.size
        # size = 0
        # for var in self.variables:
        #     size += self.variables[var].get_size()
        # return size

    def __str__(self):
        return 'struct {} {{ {} }}'.format(self.name, self.variables)

    def is_defined(self):
        if self.variables is not None:
            return True
        
        sym_type = symtable.lookup_struct(self.name)
        if sym_type is not None:
            self.variables = sym_type.variables
            # create offsets for each variable
            self.set_offsets()

        return self.variables is not None

    def set_offsets(self):
        self.offsets = {}
        for key, value in self.variables.items():
            self.offsets[key] = self.size
            self.size += value.get_size()
    
    def get_offset(self, name):
        return self.offsets[name]
    
    def get_first_element_type(self):
        # returns type of first element in struct
        name, vartype = next(iter(self.variables.items()))
        return vartype
    
    def get_element_type(self, name):
        return self.variables[name]
    
    def _get_size(self):
        raise Exception('TODO')

class Function(_BASENODE):
    def __init__(self, ret_type, name, args, is_declared=False):
        super().__init__()
        self.ret_type = ret_type        # should be VarType
        self.name = name                # str
        self.args = args                # list
        self.is_declared = is_declared  # declaration or definition 
    
    def param_size(self):
        size = 0
        for name, vartype in self.args:
            size += vartype.get_size()
        return size
        
    def __str__(self):
        return 'Function(ret_type={}, name={}, args={}, is_declared={})'.format(str(self.ret_type), self.name, self.args, self.is_declared)

class VarType(_BASENODE):
    def __init__(self, ref_count, _type, arr_offset=None):
        super().__init__()
        self.ref_count = ref_count
        self._type = _type
        self.arr_offset = arr_offset
        self.is_tmp = False

    def get_size(self):
        # different size for tmp variables, e.g. t#1 of type struct will require only ADDR_SIZE bytes to store addr of struct
        if self.ref_count > 0:
            if self.arr_offset is None or self.arr_offset == []:
                return ADDR_SIZE
            else:
                if self.is_tmp:
                    return ADDR_SIZE
                size = self.get_ref_size() * int(self.arr_offset[0].const)
                return size
        else:
            if isinstance(self._type, StructType):
                if self.is_tmp:
                    return ADDR_SIZE
                return self._type.get_size()
            elif self._type == 'int':
                return INT_SIZE
            elif self._type == 'char':
                return CHAR_SIZE
            elif self._type == 'float':
                return FLOAT_SIZE
            elif self._type == 'void':
                return 0
            else:
                raise Exception(f'Invalid type {self._type}')

    def get_ref_size(self):
        if not self.is_array():
            return VarType(self.ref_count - 1, self._type).get_size()
        else:
            return self.get_array_element_type().get_size()

    def is_pointer(self):
        return self.ref_count > 0
    
    def is_array(self):
        if self.arr_offset is None:
            return False
        return len(self.arr_offset) > 0
    
    def get_array_len(self):
        assert(self.is_array())
        return int(self.arr_offset[0].const)

    def get_array_element_type(self):
        assert(self.is_array())
        # return type of element after applying array access operator
        if len(self.arr_offset) > 1:
            return VarType(self.ref_count, self._type, self.arr_offset[1:])
        else:
            return VarType(self.ref_count-1, self._type, self.arr_offset[1:])

    def basic_type(self):
        return self._type
    
    def is_struct_type(self):
        # print(not self.is_pointer(), type(self._type))
        return (not self.is_pointer()) and isinstance(self._type, StructType)

    def castable_to(self, other):
        if self.is_pointer():
            return other.is_pointer() or other.basic_type() in ['int', 'char']
        elif self.basic_type() in ['int', 'char']:
            return other.is_pointer() or other.basic_type() in ['int', 'char', 'float']
        elif self.basic_type() in ['float']:
            return (not other.is_pointer()) and other.basic_type() in ['int', 'char', 'float']
        else:
            return self == other

    def get_caste_type(self, other):
        
        if self == other:
            return copy.deepcopy(self)
        
        if self.is_pointer():
            if self == other:
                return copy.deepcopy(self)
            else:
                return None
    
        elif self.basic_type() in ['int', 'char']:
            if other.is_pointer():
                return None
            elif other.basic_type() in ['int', 'float']:
                return copy.deepcopy(other)
            elif other.basic_type() == 'char':
                return copy.deepcopy(self)
            else:
                return None
        
        elif self.basic_type() == 'float':
            if other.is_pointer():
                return None
            elif other.basic_type() in ['int', 'char', 'float']:
                return copy.deepcopy(self)
            else:
                return None
        else:
            return None

    def __str__(self):
        # add representation of array with offsets
        if isinstance(self._type, str):
            type_string = self._type
        else:
            type_string = str(self._type)
        return type_string + ((" " + "*" * self.ref_count) if self.ref_count>0 else "")
    
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
        self.bool = False
        self.attr_ignore.append('t_name')
        self.attr_ignore.append('bool')

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

    def gen(self):

        # in case of constant we store the trimmed constant
        # val as the place
        self.place = '$'+self.const
        
        if getattr(self, 'bool', False):
            self.truelist = [tac.nextquad()]
            self.falselist = [tac.nextquad() + 1]
            tac.emit(f"ifnz {self.place} goto ")
            tac.emit(f"goto ")

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
    "Class for storing the Variable Identifier"
    def __init__(self, name: str):
        super().__init__("Identifier")
        self.name = name
        self.get_type()
    
    def gen(self):
        if self.expr_type.is_struct_type() or self.expr_type.is_array():
            # store starting addr of struct/array
            self.place = tac.newtmp()
            symtable.add_var(self.place, self.expr_type)
            tac.emit(f"{self.place} = & {self.name}")
        else:
            self.place = self.name # resolved using symtable during code generation

        if getattr(self, 'bool', False):
            self.truelist = [tac.nextquad()]
            tac.emit(f"ifnz {self.place} goto ")
            self.falselist = [tac.nextquad()]
            tac.emit(f"goto ")

    def get_type(self):
        _var = symtable.lookup_var(self.name)
        if _var is None:
            parser_error(f'Undeclared Variable {self.name}')
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
        # self.emit()

    def gen(self):
        self.place = tac.newtmp()
        symtable.add_var(self.place, self.expr_type)
        self.nextlist = []
        if self.ops == '||':
            self.lhs.bool = True

            self.rhs.bool = True

            self.lhs.gen()
            tac.backpatch(getattr(self.lhs, 'falselist', []), tac.nextquad())
            self.rhs.gen()
            self.truelist = self.lhs.truelist + self.rhs.truelist
            self.falselist = self.rhs.falselist

        elif self.ops == '&&':
            
            self.lhs.bool = True

            self.rhs.bool = True

            self.lhs.gen()
            tac.backpatch(getattr(self.lhs, 'truelist', []), tac.nextquad())
            self.rhs.gen()
            self.truelist = self.lhs.truelist
            self.falselist = self.lhs.falselist + self.rhs.falselist
        
        else:
            self.lhs.gen()
            tac.backpatch(getattr(self.lhs, 'nextlist', []), tac.nextquad())
            self.rhs.gen()

            if self.expr_type.basic_type() == 'float' and not self.expr_type.is_pointer():
                operator = 'float' + self.ops
            elif self.ops in ['<<', '>>', '|', '&', '%']:
                operator = self.ops
            else:
                operator = 'int' + self.ops

            if self.lhs.expr_type.is_pointer() and not self.rhs.expr_type.is_pointer():
                tmpvar = tac.newtmp()
                symtable.add_var(tmpvar, self.rhs.expr_type)
                tac.emit(f"{tmpvar} = {self.rhs.place} int* ${self.lhs.expr_type.get_ref_size()}")
                tac.emit(f"{self.place} = {self.lhs.place} {operator} {tmpvar}")
            elif not self.lhs.expr_type.is_pointer() and self.rhs.expr_type.is_pointer():
                tmpvar = tac.newtmp()
                symtable.add_var(tmpvar, self.lhs.expr_type)
                tac.emit(f"{tmpvar} = {self.lhs.place} int* ${self.rhs.expr_type.get_ref_size()}")
                tac.emit(f"{self.place} = {tmpvar} {operator} {self.rhs.place}")
            elif self.lhs.expr_type.is_pointer():
                tmpvar = tac.newtmp()
                symtable.add_var(tmpvar, VarType(0, 'int'))
                tac.emit(f"{tmpvar} = {self.lhs.place} {operator} {self.rhs.place}")
                tac.emit(f"{self.place} = {tmpvar} int/ {self.rhs.expr_type.get_ref_size()}")
            else:
                tac.emit("{} = {} {} {}".format(self.place, self.lhs.place, operator, self.rhs.place))

            if getattr(self, 'bool', False):
                self.truelist = [tac.nextquad()]
                self.falselist = [tac.nextquad()+1]
                tac.emit(f"ifnz {self.place} goto ")
                tac.emit(f"goto ")
        
        if not getattr(self, 'bool', False) and self.ops in ['||', '&&']:
            self.nextlist = [tac.nextquad() + 1]
            
            tac.backpatch(self.truelist, tac.nextquad())
            tac.emit(f'{self.place} = 1')
            tac.emit(f'goto ')

            tac.backpatch(self.falselist, tac.nextquad())
            tac.emit(f'{self.place} = 0')
        
        self.nextlist += getattr(self.rhs, 'nextlist', [])

    def get_type(self):
        
        ref_count = 0
        inferred_type = 'int'

        if (
            self.lhs.expr_type._type not in self.ops_type[self.ops] and
            self.rhs.expr_type._type not in self.ops_type[self.ops]
        ):
            parser_error(f'Invalid operands to ops {self.ops} (have `{self.lhs.expr_type}` and `{self.rhs.expr_type}`)')

        if self.ops in ['>', '>=', '<', '<=']:
            if self.lhs.expr_type.get_caste_type(self.rhs.expr_type):
                self.expr_type = VarType(0, 'int')
                return
            else:
                parser_error(f'Type not compatible with ops {self.ops}')
                return
        elif self.ops in ['||', '&&']:
            if self.lhs.expr_type.is_struct_type() or self.rhs.expr_type.is_struct_type():
                parser_error(f'Type not compatible with ops {self.ops}')
                return
            else:
                self.expr_type = VarType(0, 'int')
                return

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
        self.ops_type['++'] = ['int', 'char', 'float']
        self.ops_type['--'] = ['int', 'char', 'float']
        super().__init__(None, ops, rhs)
        self.get_type()

    def gen(self, is_lhs=False):
        self.place = tac.newtmp()
        
        # if self.expr_type.is_struct_type():
        #     # value of struct in 3ac == addr of starting position of struct
        #     symtable.add_var(self.place, VarType(1, self.expr_type._type))
        # else:
        symtable.add_var(self.place, self.expr_type)

        if self.ops == 'sizeof':
            tac.emit(f"{self.place} = {self.rhs.get_size()}")
        elif self.ops == '++':
            self.rhs.gen()
            tac.backpatch(getattr(self.rhs, 'nextlist', []), tac.nextquad())

            tac.emit(f"{self.place} = {self.rhs.place}")
            tac.emit(f"{self.rhs.place} = {self.rhs.place} + 1")
        elif self.ops == '--':
            self.rhs.gen()
            tac.backpatch(getattr(self.rhs, 'nextlist', []), tac.nextquad())

            tac.emit(f"{self.place} = {self.rhs.place}")
            tac.emit(f"{self.rhs.place} = {self.rhs.place} - 1")
        elif self.ops in ['&', '*', '-', '~']:
            if self.ops == '&' and (not isinstance(self.rhs, Identifier)):
                if isinstance(self.rhs, PostfixExpr):
                    self.rhs.gen(is_lhs=True)
                elif isinstance(self.rhs, UnaryExpr):
                    self.rhs.gen(is_lhs=True)
                else:
                    raise Exception("Invalid class {}", type(self.rhs))
                tac.emit(f"{self.place} = {self.rhs.place}")
                return
            self.rhs.gen()
            tac.backpatch(getattr(self.rhs, 'nextlist', []), tac.nextquad())
            if self.ops == '-':
                # TODO: in semantics, negation of pointer is syntax error
                self.ops = self.expr_type.basic_type() + self.ops
            
            if self.rhs.expr_type.is_struct_type() and self.ops == '&':
                # address of struct == addr of starting position of struct
                tac.emit(f"{self.place} = {self.rhs.place}")
            elif self.expr_type.is_struct_type() and self.ops == '*':
                # value of struct == addr of starting position of struct == address of struct
                tac.emit(f"{self.place} = {self.rhs.place}")
            else:
                if is_lhs and self.ops == '*':
                    tac.emit(f"{self.place} = {self.rhs.place}")
                else:
                    tac.emit("{} = {} {}".format(self.place, self.ops, self.rhs.place))
        elif self.ops == '+':
            self.rhs.gen()
            tac.backpatch(getattr(self.rhs, 'nextlist', []), tac.nextquad())

            tac.emit(f"{self.place} = {self.rhs.place}")
        elif self.ops == '!':
            
            self.rhs.bool = True
            self.rhs.gen()
            
            self.truelist = self.rhs.falselist
            self.falselist = self.rhs.truelist

            if not getattr(self, 'bool', False):
                tac.backpatch(getattr(self, 'truelist', []), tac.nextquad())
                tac.emit(f'{self.place} = 1')

                self.nextlist = getattr(self, 'nextlist', []) + [tac.nextquad()]
                tac.emit(f'goto ')

                tac.backpatch(getattr(self, 'falselist', []), tac.nextquad())
                tac.emit(f'{self.place} = 0')


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
            if not isinstance(self.rhs, Identifier) and \
                (not (isinstance(self.rhs, PostfixExpr) and self.rhs.ops in ['.', '->'])) and \
                (not (isinstance(self.rhs, UnaryExpr) and self.rhs.ops in ['*'])):
                compilation_err.append('RHS should be an indentifier / postfix . or -> / unary *')
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

    def gen(self, is_lhs=False):
        self.place = '#'
        # populate self.place when it is not void
        if self.expr_type != VarType(0, 'void'):
            self.place = tac.newtmp()
            # if self.expr_type.is_struct_type() or is_lhs:
                # tac variables of struct points to the starting of struct
            if is_lhs:
                symtable.add_var(self.place, VarType(1 + self.expr_type.ref_count, self.expr_type._type, self.expr_type.arr_offset))
            else:
                symtable.add_var(self.place, self.expr_type)

        if self.ops == '++':
            self.lhs.gen()
            tac.backpatch(getattr(self.lhs, 'nextlist', []), tac.nextquad())
            
            tac.emit(f"{self.lhs.place} = {self.lhs.place} int+ $1")
            tac.emit(f"{self.place} = {self.lhs.place}")
        elif self.ops == '--':
            self.lhs.gen()
            tac.backpatch(getattr(self.lhs, 'nextlist', []), tac.nextquad())
            
            tac.emit(f"{self.lhs.place} = {self.lhs.place} int- $1")
            tac.emit(f"{self.place} = {self.lhs.place}")
        elif self.ops == '[':
            self.lhs.gen()
            tac.backpatch(getattr(self.lhs, 'nextlist', []), tac.nextquad())
            
            self.rhs.gen()
            tac.backpatch(getattr(self.rhs, 'nextlist', []), tac.nextquad())
            
            tmpvar = tac.newtmp()
            symtable.add_var(tmpvar, self.rhs.expr_type)
            tac.emit(f"{tmpvar} = {self.rhs.place} int* ${self.lhs.expr_type.get_ref_size()}")

            tac.emit(f"{self.place} = {self.lhs.place} [ {tmpvar} ]")
        elif self.ops == '(':
            # stdio function (special as it contain variable number of args)
            if self.lhs.name in ['printf', 'scanf']:

                # generate code for parameters other than first one
                for param in self.rhs[1:]:
                    param.gen()
                    tac.backpatch(getattr(param, 'nextlist', []), tac.nextquad())

                args_size = 0

                # push parameters other than the first one
                for param in reversed(self.rhs[1:]):
                    args_size += param.expr_type.get_size()
                    tac.emit(f"param {param.place}")

                # add 4bytes for fmt_string
                args_size += 4
                fmt_sym = tac.fmt_string()
                symtable.add_fmt(fmt_sym, self.rhs[0].const)
                tac.emit(f'param ${fmt_sym}')

                # call the function
                tac.emit(f"{self.lhs.name} {args_size} {self.place}")
            
            # standard function call
            else:
                args = [] if self.rhs is None else self.rhs

                # generate code for parameters
                for param in args:
                    param.gen()
                    tac.backpatch(getattr(param, 'nextlist', []), tac.nextquad())

                # push parameters 
                for param in reversed(args):
                    tac.emit(f"param {param.place}")

                # call the function
                tac.emit(f"call {self.lhs.name} {self.place}")
        elif self.ops in ['.', '->']:
            self.lhs.gen()
            tac.backpatch(getattr(self.lhs, 'nextlist', []), tac.nextquad())

            offset = self.lhs.expr_type._type.get_offset(self.rhs)
            
            var_type = self.lhs.expr_type._type.variables[self.rhs]

            if var_type.is_struct_type() or var_type.is_array():
                # store only addr of struct
                tac.emit(f"{self.place} = {self.lhs.place} int+ ${offset}")
            else:
                if is_lhs:
                    tac.emit(f"{self.place} = {self.lhs.place} int+ ${offset}")
                else:
                    var_addr = tac.newtmp()
                    symtable.add_var(var_addr, VarType(1 + var_type.ref_count, var_type._type, var_type.arr_offset))

                    tac.emit(f"{var_addr} = {self.lhs.place} int+ ${offset}")
                    tac.emit(f"{self.place} = * {var_addr}")

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

            _var = symtable.lookup_func(self.lhs)
            if isinstance(_var, Function):
                func = self.lhs = _var
                if func is None:
                    compilation_err.append('{} is not callable'.format(self.lhs))
                    parser.error = compilation_err[-1]
                    parser_error()

                if func.name in ['printf', 'scanf']:
                    if len(arg_list) < 1:
                        parser_error('too few/many arguments to function {}'.format(func.name))
                    # check if first arg is list
                    elif isinstance(arg_list[0], Const) and arg_list[0].expr_type == VarType(1, 'char'):
                        inferred_type = func.ret_type._type
                        ref_count = func.ret_type.ref_count
                    else:
                        parser_error(f'expected string as first arguments to function {func.name}')
                elif len(arg_list) == len(func.args):
                    inferred_type = func.ret_type._type
                    ref_count = func.ret_type.ref_count
                    # TODO: add argument checking logic and typecasting it!
                else:
                    compilation_err.append('too few/many arguments to function {}'.format(func.name))
                    parser.error = compilation_err[-1]
                    parser_error()
            else:
                parser_error(f'called object {self.lhs} is not a function')


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
    
    def gen(self):
        
        self.expr.gen()
        tac.backpatch(getattr(self.expr, 'nextlist', []), tac.nextquad())
        
        self.place = tac.newtmp()
        symtable.add_var(self.place, self.expr_type)

        if self.expr.expr_type.is_pointer():
            if self.expr_type.is_pointer() or self.expr_type.basic_type() == 'int':
                tac.emit(f"{self.place} = {self.expr.place}") # type of self.place and self.expr.place is different
            else:
                tac.emit(f"{self.place} = int2{self.expr_type.basic_type()} {self.expr.place}")
        else:
            if self.expr_type.is_pointer() or self.expr_type.basic_type() == 'int':
                if self.expr.expr_type.basic_type() == 'int':
                    tac.emit(f"{self.place} = {self.expr.place}")
                else:
                    tac.emit(f"{self.place} = {self.expr.expr_type.basic_type()}2int {self.expr.place}")
            else:
                if self.expr.expr_type.basic_type() == 'float':
                    tac.emit(f"{self.place} = {self.expr.place}")
                else:
                    tac.emit(f"{self.place} = {self.expr.expr_type.basic_type()}2float {self.expr.place}")

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

    def gen(self):

        self.place = tac.newtmp()
        symtable.add_var(self.place, self.expr_type)

        if isinstance(self.lhs, UnaryExpr) and self.lhs.ops == '*':
            self.lhs.rhs.gen()
            tac.backpatch(getattr(self.lhs.rhs, 'nextlist', []), tac.nextquad())
            
            self.rhs.gen()
            tac.backpatch(getattr(self.rhs, 'nextlist', []), tac.nextquad())
            
            tac.emit(f"* {self.lhs.rhs.place} = {self.rhs.place}")
        elif isinstance(self.lhs, PostfixExpr) and self.lhs.ops == '[':
            self.lhs.lhs.gen()
            tac.backpatch(getattr(self.lhs.lhs, 'nextlist', []), tac.nextquad())
            
            self.lhs.rhs.gen()
            tac.backpatch(getattr(self.lhs.rhs, 'nextlist', []), tac.nextquad())

            self.rhs.gen()
            tac.backpatch(getattr(self.rhs, 'nextlist', []), tac.nextquad())
            
            tmpvar = tac.newtmp()
            symtable.add_var(tmpvar, self.lhs.rhs.expr_type)
            tac.emit(f"{tmpvar} = {self.lhs.rhs.place} int* ${self.lhs.lhs.expr_type.get_ref_size()}")
            
            tac.emit(f"{self.lhs.lhs.place} [ {tmpvar} ] = {self.rhs.place}")
        elif isinstance(self.lhs, PostfixExpr) and self.lhs.ops in ['.', '->']:
            # we need self.lhs as lhs of '=' => it should be addr of some memory location which 
            # '=' will update
            self.lhs.gen(is_lhs=True)
            tac.backpatch(getattr(self.lhs, 'nextlist', []), tac.nextquad())

            self.rhs.gen()
            tac.backpatch(getattr(self.rhs, 'nextlist', []), tac.nextquad())

            tac.emit(f"* {self.lhs.place} = {self.rhs.place}")
        else:
            self.lhs.gen()
            tac.backpatch(getattr(self.lhs, 'nextlist', []), tac.nextquad())
            
            self.rhs.gen()
            tac.backpatch(getattr(self.rhs, 'nextlist', []), tac.nextquad())
            
            tac.emit(f"{self.lhs.place} = {self.rhs.place}")
        
        tac.emit(f"{self.place} = {self.rhs.place}")

    def get_type(self):
        
        # compatability is checked in CastExpr
        self.rhs = CastExpr(self.lhs.expr_type, self.rhs)
        self.expr_type = self.lhs.expr_type

class CondExpr(BaseExpr):
    def __init__(self, cond, if_expr, else_expr):
        super().__init__("Conditional Expr")
        self.cond = cond
        self.if_expr = if_expr
        self.else_expr = else_expr
    
    def gen(self):

        self.cond.bool = True

        self.cond.gen()
        
        tac.backpatch(getattr(self.cond, 'truelist', []), tac.nextquad())
        
        self.place = tac.newtmp()
        symtable.add_var(self.place, self.expr_type)
        
        self.if_expr.gen()
        tac.backpatch(getattr(self.if_expr, 'nextlist', []), tac.nextquad())

        tac.emit(f"{self.place} = {self.if_expr.place}")

        self.nextlist = [tac.nextquad()]
        tac.emit(f"goto ")
        tac.backpatch(getattr(self.cond, 'falselist', []), tac.nextquad())
        
        self.else_expr.gen()
        tac.backpatch(getattr(self.else_expr, 'nextlist', []), tac.nextquad())
        
        tac.emit(f"{self.place} = {self.else_expr.place}")

    def get_type(self, ):
        # check type mismatch between if_expr and else_expr
        self.expr_type = self.if_expr.expr_type.get_caste_type(self.else_expr)
        if self.expr_type is None:
            parser_error("Types not compatible with ternary operator")

class CommaExpr(BaseExpr):
    def __init__(self, *expr):
        super().__init__("Comma Expression")
        self.expr_list = expr
        self.get_type()

    def add_expr(self, expr):
        self.expr_list.append(expr)

    def gen(self):
        for expr in self.expr_list:
            expr.gen()
            tac.backpatch(getattr(expr, 'nextlist', []), tac.nextquad())
        
        self.place = tac.newtmp()
        symtable.add_var(self.place, self.expr_type)
        tac.emit(f"{self.place} = {self.expr_list[-1].place}")

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
            parser_error('can not initialize typedef {}', self.declarator.name)

        if self.initializer is not None:
            
            if isinstance(self.initializer, Initializers):
                self.initializer.compatible_with(self.expr_type, error=True)
                return
            
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
        # dot: print only if initializer is not empty

    def gen(self):
        if self.initializer is not None:
            if isinstance(self.initializer, Initializers):
                addr = tac.newtmp()
                if self.expr_type.is_array() or self.expr_type.is_struct_type():
                    symtable.add_var(addr, self.expr_type)
                else:
                    symtable.add_var(addr, VarType(1+self.expr_type.ref_count, self.expr_type._type, self.expr_type.arr_offset))
                tac.emit(f"{addr} = & {self.declarator.name}")
                self.initializer.gen_init(addr, self.expr_type)
                self.nextlist = getattr(self.initializer, 'nextlist', [])
            else:
                self.initializer.gen()
                tac.backpatch(getattr(self.initializer, 'nextlist', []), tac.nextquad())

                tac.emit(f"{self.declarator.name} = {self.initializer.place}")
        else:
            pass

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

        # lambda structs => give name as None in StructType
        elif self.decls_list is not None and self.name is None:
            struct_type = StructType(None, self.variables)

        # ony name given => try lookup struct in symtable, if not
        # found then give only name in hope it gets resolved later 
        # (case of LinkedList struct!)
        elif self.decls_list is None and self.name is not None:
            lookup_type = symtable.lookup_struct(self.name)
            if lookup_type is None:
                struct_type = StructType(self.name, None)
            else:
                struct_type = lookup_type
            
        self.struct_type = struct_type

    def compute_variables(self):
        self.variables = OrderedDict()
        
        for declaration in self.decls_list:
      
            d_spec = declaration.specifier
            d_decl_list = declaration.init_list
            d_type = d_spec.type_spec 
            
            is_void = d_type == 'void'
            is_struct = d_type is StructType  
            
            for decl in d_decl_list:

                vartype = VarType(decl.ref_count, d_type, decl.arr_offset)

                # Sanity checking of arr offset
                if not all(map(lambda x: isinstance(x, Const) and x.dvalue=='int', decl.arr_offset)):
                    parser_error('Size of array ‘{}’ has non-integer type'.format(decl.name))

                # void declaration checking
                if is_void and vartype.ref_count==0:
                    parser_error('Variable `{}` declared void inside struct'.format(decl.name))
                
                # struct declaration checking
                if is_struct and not d_type.is_defined() and vartype.ref_count==0:
                    parser_error('Storage of struct named `{}` not avaiable'.format(d_type.name))

                # Add declaration in variables
                if decl.name in self.variables:
                    parser_error('Redeclaration of variable named `{}` inside struct'.format(decl.name))

                self.variables[decl.name] = vartype
    
    def get_struct_type(self):
        return self.struct_type
    
    def gen(self):
        pass

class DeclarationSpecifier(Specifier):
    def __init__(
        self, 
        storage_type_spec, 
        type_spec: Union[str, StructUnionSpecifier]
    ):
        super().__init__("Declaration Specifier")
        self.storage_type_spec = storage_type_spec
        self.type_spec = type_spec
        self.is_typedef = (storage_type_spec == 'typedef')
        self.is_static = (storage_type_spec == 'static')
        self.type = type_spec

        if isinstance(self.type_spec, StructUnionSpecifier):
            self.type_spec = self.type_spec.struct_type

    def gen(self):
        pass

class StructDeclaration(_BaseDecl):
    def __init__(
        self, 
        specifier: DeclarationSpecifier, 
        init_list: List[InitDeclarator] = []
    ): 
        super().__init__('TODO')
        self.specifier = specifier
        self.init_list = init_list
    
    def gen(self):
        # TODO: allow initialization with expr (`int x: 2` in struct declaration)
        pass

class Declarator(_BaseDecl):
    def __init__(self, ref_count, name, arr_offset):
        super().__init__('TODO')

        # NOTE: don't add symtab function here as
        # this is used in function parameter_list
        # where symtab addition is not required

        self.ref_count = ref_count
        self.name = name
        self.arr_offset = arr_offset
    
    def gen(self):
        pass

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
        self.arr_offset = None

    def gen(self):
        pass

class Declaration(_BaseDecl):
    def __init__(
        self, 
        specifier: DeclarationSpecifier, 
        init_list: List[InitDeclarator] = []
    ):
        super().__init__('TODO')
        self.specifier = specifier
        self.init_list = init_list

        self._type = self.specifier.type_spec

        self.is_static = self.specifier.is_static
        self.is_typedef = self.specifier.is_typedef
        self.is_void = self._type == 'void'
        self.is_struct = isinstance(self._type, StructType)

        # storing aliases
        if self.is_typedef:
            for init_decl in self.init_list:
                decl = init_decl.declarator

                # Function declaration !
                if isinstance(decl, FuncDirectDecl):    
                    parser_error('Function typedefs not supported')
                    continue

                vartype = VarType(decl.ref_count, self._type, decl.arr_offset)

                # Sanity checking of arr offset
                if not all(map(lambda x: isinstance(x, Const) and x.dvalue=='int', decl.arr_offset)):
                    parser_error('Size of array `{}` has non-integer type'.format(decl.name))

                # TODO: this is valid `typedef void mytype;`
                # if self.is_void and vartype.ref_count==0:
                #     compilation_err.append('Variable `{}` declared void'.format(decl.name))
                #     parser.error = compilation_err[-1]
                #     parser_error()
                
                # # struct declaration checking
                # if self.is_struct and not self._type.is_defined() and vartype.ref_count==0:
                #     compilation_err.append('storage of struct named {} not avaiable'.format(self._type.name))
                #     parser.error = compilation_err[-1]
                #     parser_error()

                # Add declaration in symtab
                symtable.add_typedef(decl.name, vartype)

        else:

            for init_decl in self.init_list:

                decl = init_decl.declarator

                # Function declaration !
                if isinstance(decl, FuncDirectDecl):    
                    vartype = VarType(decl.ref_count, self._type)
                    symtable.add_func(Function(vartype, decl.name, decl.param_list))
                    continue

                vartype = VarType(decl.ref_count, self._type, decl.arr_offset)

                # Sanity checking of arr offset
                if not all(map(lambda x: isinstance(x, Const) and x.dvalue=='int', decl.arr_offset)):
                    parser_error('Size of array `{}` has non-integer type'.format(decl.name))

                # Sanity checking of void declartion
                if self.is_void and vartype.ref_count==0:
                    parser_error('Variable `{}` declared void'.format(decl.name))
                
                # struct declaration checking
                if self.is_struct and not self._type.is_defined() and vartype.ref_count==0:
                    parser_error('storage of struct named `{}` not avaiable'.format(self._type.name))

                # Add declaration in symtab
                symtable.add_var(decl.name, vartype, self.is_static)

    def gen(self):
        for idx, init in enumerate(self.init_list):
            init.gen()
            tac.backpatch(getattr(init, 'nextlist', []), tac.nextquad())
        
        if len(self.init_list) > 0:
            self.nextlist = getattr(self.init_list[-1], 'nextlist', [])
        else:
            self.nextlist = []
    

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

    def gen(self):
        for init in self.init_list:
            init.gen()
            tac.backpatch(getattr(init, 'nextlist', []), tac.nextquad())
    
    def compatible_with(self, vartype : VarType, error=False):
        
        if vartype.is_array():
            # lhs is array
            if len(self.init_list) > vartype.get_array_len():
                if error:
                    parser_error(f"too many initializers")
                return False
            
            if not self.check_array_init(vartype, error=error):
                return False
        
        elif vartype.is_struct_type():
            # lhs is struct
            structtype = vartype._type

            if len(self.init_list) > len(structtype.variables):
                if error:
                    parser_error(f"too many initializers")
                return False
            
            if not self.check_struct_init(structtype, error=error):
                return
        
        else:
            # lhs is of a basic type
            if len(self.init_list) != 1:
                if error:
                    parser_error(f"too many/few initializers")
                return False
            
            if not isinstance(self.init_list[0], BaseExpr):
                if error:
                    parser_error(f"too many braces around scalar initializer for type {vartype}")
                return False
            
            if not self.check_basic_init(self.init_list[0].expr_type, vartype, error=error):
                return False
        
        return True
            
    def check_array_init(self, vartype, error=False):
        for init_idx, init in enumerate(self.init_list):
            if isinstance(init, Initializers):
                if not init.compatible_with(vartype.get_array_element_type(), error=error):
                    return False
            else:
                # init is an expression
                element_type = vartype.get_array_element_type()
                if not self.check_basic_init(init.expr_type, element_type, error=error):
                    return False
                else:
                    self.init_list[init_idx] = CastExpr(element_type, init)
        return True

    def check_struct_init(self, structtype, error=False):
        for init_idx, (vname, vartype) in enumerate(structtype.variables.items()):
            if init_idx >= len(self.init_list):
                return True
            init = self.init_list[init_idx]
            if isinstance(init, Initializers):
                if not init.compatible_with(vartype, error=error):
                    return False
            else:
                # init is an expression
                element_type = vartype
                if not self.check_basic_init(init.expr_type, element_type, error=error):
                    return False
                else:
                    self.init_list[init_idx] = CastExpr(vartype, init)
        return True

    def check_basic_init(self, init : VarType, element_type : VarType, error=False):
        while(element_type.is_array() or element_type.is_struct_type()):
            if element_type.is_array():
                # type of first element of array
                element_type = element_type.get_array_element_type()
            elif element_type.is_struct_type():
                # type of first element of struct
                element_type = element_type._type.get_first_element_type()
        if not init.castable_to(element_type):
            if error:
                parser_error(f"Can not caste {init} into {element_type}")
            return False

    def gen_init(self, name, vartype : VarType):
        if vartype.is_array():
            self.gen_array_init(name, vartype)
        
        elif vartype.is_struct_type():
            # lhs is struct
            structtype = vartype._type

            self.gen_struct_init(name, structtype)
        
        else:
            # lhs is of a basic type
            self.gen_basic_init(self.init_list[0], name, vartype)
        
        return True
            
    def gen_array_init(self, arr_addr, vartype):
        init_len = len(self.init_list)
        for init_idx, init in enumerate(self.init_list):
            element_type = vartype.get_array_element_type()

            tmpvar = tac.newtmp()
            if element_type.is_array() or element_type.is_struct_type():
                symtable.add_var(tmpvar, element_type)
            else:
                symtable.add_var(tmpvar, VarType(1 + element_type.ref_count, element_type._type, element_type.arr_offset))
            
            tac.emit(f"{tmpvar} = {arr_addr} int+ ${init_idx * vartype.get_ref_size()}")
            
            if isinstance(init, Initializers):    
                init.gen_init(tmpvar, element_type)
            else:
                self.gen_basic_init(init, tmpvar, element_type)
                    
            if init_idx < init_len-1:
                tac.backpatch(getattr(init, 'nextlist', []), tac.nextquad())
            else:
                self.nextlist = getattr(init, 'nextlist', [])

    def gen_struct_init(self, struct_addr, structtype):
        init_len = len(self.init_list)
        for init_idx, (vname, vartype) in enumerate(structtype.variables.items()):
            
            if init_idx >= len(self.init_list):
                return
            
            tmpvar = tac.newtmp()
            if vartype.is_struct_type() or vartype.is_array():
                # addr == object
                symtable.add_var(tmpvar, vartype)
            else:
                symtable.add_var(tmpvar, VarType(1 + vartype.ref_count, vartype._type, vartype.arr_offset))

            tac.emit(f"{tmpvar} = {struct_addr} int+ ${structtype.get_offset(vname)}")
            init = self.init_list[init_idx]
            
            if isinstance(init, Initializers):
                init.gen_init(tmpvar, vartype)
            else:
                self.gen_basic_init(init, tmpvar, vartype)
            
            if init_idx < init_len-1:
                tac.backpatch(getattr(init, 'nextlist', []), tac.nextquad())
            else:
                self.nextlist = getattr(init, 'nextlist', [])
                

    def gen_basic_init(self, init, addr, element_type):
        # no need for while loop as addr is already addr of first element
        
        init.gen()
        tac.backpatch(getattr(init, 'nextlist', []), tac.nextquad())

        while(element_type.is_array() or element_type.is_struct_type()):
            if element_type.is_array():
                # type of first element of array
                element_type = element_type.get_array_element_type()
            elif element_type.is_struct_type():
                # type of first element of struct
                element_type = element_type._type.get_first_element_type()
        
        ref_type = VarType(1 + element_type.ref_count, element_type._type, element_type.arr_offset)
        symtable.cur_scope().variables[addr]['type'] = ref_type
        
        tac.emit(f"* {addr} = {init.place}")
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

        if not symtable.check_case_scope():
            parser_error('`{}` label not within a switch statement'.format(self.case[0]))

    def gen(self):
        self.stmt.gen()
        self.breaklist = getattr(self.stmt, 'breaklist', [])
        self.nextlist = getattr(self.stmt, 'nextlist', [])
        self.returnlist = getattr(self.stmt, 'returnlist', [])

class CompoundStmt(Statement):
    def __init__(
        self, 
        decls: List[Declaration], 
        stmts: List[Statement]
    ):
        super().__init__("Compound Statment")
        self.decl_list = decls
        self.stmt_list = stmts

    def gen(self):
        symtable.push_scope(exists=True)
        if self.decl_list:
            for decl in self.decl_list:
                decl.gen()
                tac.backpatch(getattr(decl, 'nextlist', []), tac.nextquad())
        
        self.breaklist = []
        self.continuelist = []
        self.returnlist = []

        if self.stmt_list:
            for idx, stmt in enumerate(self.stmt_list):
                stmt.gen()
                tac.backpatch(getattr(stmt, 'nextlist', []), tac.nextquad())

                self.breaklist += getattr(stmt, 'breaklist', [])
                self.continuelist += getattr(stmt, 'continuelist', [])
                self.returnlist += getattr(stmt, 'returnlist', [])

            if self.stmt_list == []:
                self.nextlist = []
            else:
                self.nextlist = getattr(self.stmt_list[-1], 'nextlist', [])
        
        symtable.update_scope_size()
    
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
    
    def gen(self):
        if self.expr:
            self.expr.gen()
            self.nextlist = getattr(self.expr, 'nextlist', [])

class SelectionStmt(Statement):
    def __init__(self, select_type, select_expr, if_stmt, else_stmt=None):
        super().__init__("Selection Statement")
        self.select_type = select_type
        self.select_expr = select_expr
        self.if_stmt = if_stmt
        self.else_stmt = else_stmt
    
    def gen(self):

        if self.select_type == 'if':
            # if else statment
            if self.else_stmt:
                self.select_expr.bool = True

                self.select_expr.gen()
                tac.backpatch(getattr(self.select_expr, 'truelist', []), tac.nextquad())

                self.if_stmt.gen()

                self.nextlist = [tac.nextquad()]
                tac.emit(f'goto ')

                tac.backpatch(getattr(self.select_expr, 'falselist', []), tac.nextquad())
                self.else_stmt.gen()

                self.nextlist += getattr(self.if_stmt, 'nextlist', []) + getattr(self.else_stmt, 'nextlist', [])
                self.returnlist += getattr(self.if_stmt, 'returnlist', []) + getattr(self.else_stmt, 'returnlist', [])
            # if statement
            else:
                self.select_expr.bool = True

                self.select_expr.gen()
                tac.backpatch(getattr(self.select_expr, 'truelist', []), tac.nextquad())

                self.if_stmt.gen()

                self.nextlist = getattr(self.if_stmt, 'nextlist', []) + getattr(self.select_expr, 'falselist', [])
                self.returnlist = getattr(self.if_stmt, 'returnlist', []) + getattr(self.select_expr, 'returnlist', [])
        # switch
        else:
            self.select_expr.gen()
            tac.backpatch(getattr(self.select_expr, 'nextlist', []), tac.nextquad())
            
            case_list = []
            case_stmts = self.if_stmt.stmt_list
            
            testlist = [tac.nextquad()]
            tac.emit(f'goto ')

            case_labels = []
            case_labels.append(tac.nextquad())
            self.breaklist = []
            self.returnlist = []

            for idx, case_stmt in enumerate(case_stmts):
                case_stmt.breaklabel = self.nextlist
                if idx < len(case_stmts) - 1:
                    case_stmt.gen()
                    tac.backpatch(getattr(case_stmt, 'nextlist', []), tac.nextquad())
                    case_labels.append(tac.nextquad())
                else:
                    case_stmt.gen()
                    self.nextlist = [tac.nextquad()]
                    tac.emit(f'goto ')
                    
                self.breaklist += getattr(case_stmt, 'breaklist', [])
                self.returnlist += getattr(case_stmt, 'returnlist', [])

                case_list.append(case_stmt.case)
            
            tac.backpatch(testlist, tac.nextquad())
            for idx, case in enumerate(case_list):
                if isinstance(case, tuple):
                    case[1].gen()
                    tac.backpatch(getattr(case[1], 'nextlist', []), tac.nextquad())

                    tac.emit(f'ifeq {self.select_expr.place} {case[1].place} goto {case_labels[idx]}')
                else:
                    tac.emit(f'goto {case_labels[idx]}')
            
            tac.backpatch(self.breaklist, tac.nextquad()) # can be shifted to upper productions


class IterStmt(Statement):
    def __init__(self, iter_type, iter_expr, stmt):
        super().__init__("Iteration Statement")
        self.iter_type = iter_type
        self.iter_expr = iter_expr
        self.stmt = stmt
    
    def gen(self):

        # `while` loop
        if self.iter_type == 'while':
            
            begin = tac.nextquad()

            self.iter_expr.bool = True
            
            self.iter_expr.gen()
            tac.backpatch(getattr(self.iter_expr, 'truelist', []), tac.nextquad())
            self.stmt.gen()
            tac.emit(f'goto {begin}')

            tac.backpatch(getattr(self.stmt, 'nextlist', []) + getattr(self.stmt, 'continuelist', []), begin)

            self.nextlist = getattr(self.iter_expr, 'falselist', []) + getattr(self.stmt, 'breaklist', [])

        # `for` loop
        else:
            e1, e2, e3 = self.iter_expr
            
            e1.gen()
            tac.backpatch(getattr(e1, 'nextlist', []), tac.nextquad())

            # if `e3` is None then it is equiv to `while` loop
            if e3 is None:
                self.iter_type = 'while'
                self.iter_expr = e2
                self.gen()
            else:
                begin = tac.nextquad()
            
                e2.bool = True

                e2.gen()
                tac.backpatch(getattr(e2, 'truelist', []), tac.nextquad())
                self.stmt.gen()
                
                tac.backpatch(getattr(self.stmt, 'nextlist', []), tac.nextquad())

                e3.gen()
                tac.backpatch(getattr(e3, 'nextlist', []), begin)

                tac.backpatch(getattr(e3, 'continuelist', []) + getattr(self.stmt, 'continuelist', []), begin)

                self.nextlist = getattr(e3, 'breaklist', []) + getattr(self.stmt, 'breaklist', []) + getattr(e2, 'falselist', [])

                tac.emit(f'goto {begin}')

        # return list 
        self.returnlist = getattr(self.stmt, 'returnlist', [])
            

class JumpStmt(Statement):
    def __init__(self, jump_type, expr=None):
        super().__init__("Jump Statement")
        self.jump_type = jump_type
        self.expr = expr
        if self.jump_type == 'break':
            if not symtable.check_break_scope():
                parser_error('`break` statement not within loop or switch')
        elif self.jump_type == 'continue':
            if not symtable.check_continue_scope():
                parser_error('`continue` statement not within a loop')
        # elif self.jump_type == 'return':
        #     if self.expr.expr_type != (function_type):
        #         parser_error('')
        # # check the return type with function scope
        # i


    def gen(self):
        if self.jump_type == 'continue':
            self.continuelist = [tac.nextquad()]
            tac.emit(f'goto ')
        elif self.jump_type == 'break':
            self.breaklist = [tac.nextquad()]
            tac.emit(f'goto ')
        elif self.jump_type == 'return':
            if self.expr:
                self.expr.gen()
                tac.backpatch(getattr(self.expr, 'nextlist', []), tac.nextquad())
            
            # only generate return stmt when there is expr to return
            if self.expr is not None:
                tac.emit(f'return {self.expr.place}')
            
            self.returnlist = [tac.nextquad()]
            # in all return stmt, goto the end of function for call seq cleanup
            tac.emit(f'goto ')


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
    
    def gen(self, ):
        for unit in self.units:
            unit.gen()
            tac.backpatch(getattr(unit, 'nextlist', []), tac.nextquad())

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
    ):
        super().__init__('Function Definition')
        self.specifier = specifier
        self.ref_count = ref_count
        self.name = name
        self.param_list = param_list
        self.stmt = stmt
        self.vartype = VarType(self.ref_count, self.specifier.type_spec)
        symtable.add_func(Function(self.vartype, self.name, self.param_list, is_declared=True))

    def gen(self):
        tac.push_func_code()
        tac.emit(f'FuncBegin {self.name}')
        self.stmt.gen()
        self.nextlist = getattr(self.stmt, 'nextlist', [])
        tac.backpatch(getattr(self.stmt, 'returnlist', []), tac.nextquad())
        tac.emit(f'FuncEnd {self.name}')


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
