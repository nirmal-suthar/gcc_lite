from os import removedirs
from typing import Union, List
import pydot
from parser import parser, parser_error
from helper import *
import copy

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

    def get_size(self):
        size = 0
        for var in self.variables:
            size += self.variables[var].get_size()
        return size

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
    def __init__(self, ret_type, name, args, is_ellipsis=False, is_declared=False):
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

    def get_size(self):
        if self.ref_count > 0:
            return ADDR_SIZE
        else:
            if isinstance(self._type, StructType):
                return self._type.get_size()
            elif self._type == 'int':
                return INT_SIZE
            elif self._type == 'char':
                return CHAR_SIZE
            elif self._type == 'float':
                return FLOAT_SIZE
            else:
                raise Exception("Invalid type")

    def get_ref_size(self):
        return VarType(self.ref_count - 1, self._type).get_size()

    def is_pointer(self):
        return self.ref_count > 0

    def basic_type(self):
        return self._type
    
    def is_struct_type(self):
        return (not self.is_pointer()) and isinstance(self, StructType)

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

    def gen(self):
        self.place = self.const

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
    
    def gen(self):
        self.place = self.name # resolved using symtable during code generation

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
        # self.emit()

    def gen(self):
        self.place = tac.newtmp()
        symtable.add_var(self.place, self.expr_type)

        if self.ops in ['||', '&&'] and not getattr(self, 'bool', False):
            self.true = tac.newlabel()
            self.false = tac.newlabel()

        if self.ops == '||':
            self.lhs.bool = True
            self.lhs.true = self.true
            self.lhs.false = tac.newlabel()

            self.rhs.bool = True
            self.rhs.true = self.true
            self.rhs.false = self.false

            self.lhs.gen()
            tac.emit(f'{self.lhs.false} :')
            self.rhs.gen()

        elif self.ops == '&&':
            
            self.lhs.bool = True
            self.lhs.true = tac.newlabel()
            self.lhs.false = self.false

            self.rhs.bool = True
            self.rhs.true = self.true
            self.rhs.false = self.false

            self.lhs.gen()
            tac.emit(f'{self.lhs.true} :')
            self.rhs.gen()
        
        else:
            if isinstance(self.lhs, Const) or isinstance(self.lhs, Identifier):
                self.lhs.gen()
            else:
                self.lhs.next = tac.newlabel()
                self.lhs.gen()
                tac.emit(f'{self.lhs.next} :')
            self.rhs.next = self.next
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
                tac.emit(f"{tmpvar} = {self.rhs.place} int* {self.lhs.expr_type.get_ref_size()}")
                tac.emit(f"{self.place} = {self.lhs.place} {operator} {tmpvar}")
            elif not self.lhs.expr_type.is_pointer() and self.rhs.expr_type.is_pointer():
                tmpvar = tac.newtmp()
                symtable.add_var(tmpvar, self.lhs.expr_type)
                tac.emit(f"{tmpvar} = {self.lhs.place} int* {self.rhs.expr_type.get_ref_size()}")
                tac.emit(f"{self.place} = {tmpvar} {operator} {self.rhs.place}")
            elif self.lhs.expr_type.is_pointer():
                tmpvar = tac.newtmp()
                symtable.add_var(tmpvar, VarType(0, 'int'))
                tac.emit(f"{tmpvar} = {self.lhs.place} {operator} {self.rhs.place}")
                tac.emit(f"{self.place} = {tmpvar} int/ {self.rhs.expr_type.get_ref_size()}")
            else:
                tac.emit("{} = {} {} {}".format(self.place, self.lhs.place, operator, self.rhs.place))

            if getattr(self, 'bool', False):
                tac.emit(f"ifnz {self.place} goto {self.true}")
                tac.emit(f"goto {self.false}")
        
        if not getattr(self, 'bool', False) and self.ops in ['||', '&&']:
            tac.emit(f'{self.true} :')
            tac.emit(f'{self.place} = 1')
            tac.emit(f'goto {self.next}')
            tac.emit(f'{self.false} :')
            tac.emit(f'{self.place} = 0')

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

    def gen(self):
        self.place = tac.newtmp()
        symtable.add_var(self.place, self.expr_type)

        if self.ops == 'sizeof':
            tac.emit(f"{self.place} = {self.rhs.get_size()}")
        elif self.ops == '++':
            if isinstance(self.rhs, Const) or isinstance(self.rhs, Identifier):
                self.rhs.gen()
            else:
                self.rhs.next = tac.newlabel()
                self.rhs.gen()
                tac.emit(f'{self.rhs.next} :')
            tac.emit(f"{self.place} = {self.rhs.place}")
            tac.emit(f"{self.rhs.place} = {self.rhs.place} + 1")
        elif self.ops == '--':
            if isinstance(self.rhs, Const) or isinstance(self.rhs, Identifier):
                self.rhs.gen()
            else:
                self.rhs.next = tac.newlabel()
                self.rhs.gen()
                tac.emit(f'{self.rhs.next} :')
            tac.emit(f"{self.place} = {self.rhs.place}")
            tac.emit(f"{self.rhs.place} = {self.rhs.place} - 1")
        elif self.ops in ['&', '*', '-', '~']:
            if isinstance(self.rhs, Const) or isinstance(self.rhs, Identifier):
                self.rhs.gen()
            else:
                self.rhs.next = tac.newlabel()
                self.rhs.gen()
                tac.emit(f'{self.rhs.next} :')
            tac.emit("{} = {}{}".format(self.place, self.ops, self.rhs.place))
        elif self.ops == '+':
            if isinstance(self.rhs, Const) or isinstance(self.rhs, Identifier):
                self.rhs.gen()
            else:
                self.rhs.next = tac.newlabel()
                self.rhs.gen()
                tac.emit(f'{self.rhs.next} :')
            tac.emit(f"{self.place} = {self.rhs.place}")
        elif self.ops == '!':
            self.rhs.next = self.next
            if not getattr(self, 'bool', False):
                self.true = tac.newlabel()
                self.false = tac.newlabel()
            self.rhs.true = self.false
            self.rhs.false = self.true
            self.rhs.bool = True
            self.rhs.gen()
            if not getattr(self, 'bool', False):
                tac.emit(f'{self.true} :')
                tac.emit(f'{self.place} = 1')
                tac.emit(f'goto {self.next}')
                tac.emit(f'{self.false} :')
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

    def gen(self):
        self.place = tac.newtmp()
        symtable.add_var(self.place, self.expr_type)

        if self.ops == '++':
            if isinstance(self.lhs, Const) or isinstance(self.lhs, Identifier):
                self.lhs.gen()
            else:
                self.lhs.next = tac.newlabel()
                self.lhs.gen()
                tac.emit(f'{self.lhs.next} :')
            tac.emit(f"{self.lhs.place} = {self.lhs.place} + 1")
            tac.emit(f"{self.place} = {self.lhs.place}")
        elif self.ops == '--':
            if isinstance(self.lhs, Const) or isinstance(self.lhs, Identifier):
                self.lhs.gen()
            else:
                self.lhs.next = tac.newlabel()
                self.lhs.gen()
                tac.emit(f'{self.lhs.next} :')
            tac.emit(f"{self.lhs.place} = {self.lhs.place} - 1")
            tac.emit(f"{self.place} = {self.lhs.place}")
        elif self.ops == '[':
            if isinstance(self.lhs, Const) or isinstance(self.lhs, Identifier):
                self.lhs.gen()
            else:
                self.lhs.next = tac.newlabel()
                self.lhs.gen()
                tac.emit(f'{self.lhs.next} :')
            tac.emit(f"{self.lhs.place} [ {self.rhs.place} ]")
        elif self.ops == '(':
            if self.rhs == None:
                self.lhs.gen()
                tac.emit(f"call {self.lhs.place}")
            else:
                self.lhs.gen()

                # generate code for parameters
                for param in self.rhs:
                    param.gen()

                # push parameters 
                for param in self.rhs:
                    tac.emit(f"param {param.place}")

                # call the function
                tac.emit(f"call {self.lhs.place}")

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
    
    def gen(self):
        
        if isinstance(self.expr, Const) or isinstance(self.expr, Identifier):
            self.expr.gen()
        else:
            self.expr.next = tac.newlabel()
            self.expr.gen()
            tac.emit(f'{self.expr.next} :')
        self.place = tac.newtmp()
        symtable.add_var(self.place, self.expr_type)

        if self.expr.expr_type.is_pointer():
            if self.expr_type.is_pointer():
                tac.emit(f"{self.place} = {self.expr.place}") # type of self.place and self.expr.place is different
            else:
                tac.emit(f"{self.place} = pointer2{self.expr_type.basic_type()} {self.expr.place}")
        else:
            if self.expr_type.is_pointer():
                tac.emit(f"{self.place} = {self.expr.expr_type.basic_type()}2pointer {self.expr.place}")
            else:
                tac.emit(f"{self.place} = {self.expr.expr_type.basic_type()}2{self.expr_type.basic_type()} {self.expr.place}")

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
            if isinstance(self.lhs.rhs, Const) or isinstance(self.lhs.rhs, Identifier):
                self.lhs.rhs.gen()
            else:
                self.lhs.rhs.next = tac.newlabel()
                self.lhs.rhs.gen()
                tac.emit(f'{self.lhs.rhs.next} :')
            
            if isinstance(self.rhs, Const) or isinstance(self.rhs, Identifier):
                self.rhs.gen()
            else:
                self.rhs.next = tac.newlabel()
                self.rhs.gen()
                tac.emit(f'{self.rhs.next} :')
            
            tac.emit(f"*{self.lhs.rhs.place} = {self.rhs.place}")
        elif isinstance(self.lhs, PostfixExpr) and self.lhs.ops == '[':
            
            if isinstance(self.lhs.lhs, Const) or isinstance(self.lhs.lhs, Identifier):
                self.lhs.lhs.gen()
            else:
                self.lhs.lhs.next = tac.newlabel()
                self.lhs.lhs.gen()
                tac.emit(f'{self.lhs.lhs.next} :')
            
            if isinstance(self.rhs, Const) or isinstance(self.rhs, Identifier):
                self.rhs.gen()
            else:
                self.rhs.next = tac.newlabel()
                self.rhs.gen()
                tac.emit(f'{self.rhs.next} :')
            
            tac.emit(f"{self.lhs.lhs.place} [ {self.lhs.rhs.place} ] = {self.rhs.place}")
        else:
            if isinstance(self.lhs, Const) or isinstance(self.lhs, Identifier):
                self.lhs.gen()
            else:
                self.lhs.next = tac.newlabel()
                self.lhs.gen()
                tac.emit(f'{self.lhs.next} :')

            if isinstance(self.rhs, Const) or isinstance(self.rhs, Identifier):
                self.rhs.gen()
            else:
                self.rhs.next = tac.newlabel()
                self.rhs.gen()
                tac.emit(f'{self.rhs.next} :')
        
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

        self.cond.true = tac.newlabel()
        self.cond.false = tac.newlabel()
        self.cond.bool = True

        self.cond.gen()
        
        tac.emit(f"{self.cond.true} :")
        
        self.place = tac.newtmp()
        symtable.add_var(self.place, self.expr_type)
        
        if isinstance(self.if_expr, Const) or isinstance(self.if_expr, Identifier):
            self.if_expr.gen()
        else:
            self.if_expr.next = tac.newlabel()
            self.if_expr.gen()
            tac.emit(f'{self.if_expr.next} :')

        tac.emit(f"{self.place} = {self.if_expr.place}")

        tac.emit(f"goto {self.next}")
        tac.emit(f"{self.cond.false} :")
        
        if isinstance(self.else_expr, Const) or isinstance(self.else_expr, Identifier):
            self.else_expr.gen()
        else:
            self.else_expr.next = tac.newlabel()
            self.else_expr.gen()
            tac.emit(f'{self.else_expr.next} :')
        
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
            if isinstance(expr, Const) or isinstance(expr, Identifier):
                expr.gen()
            else:
                expr.next = tac.newlabel()
                expr.gen()
                tac.emit(f'{expr.next} :')
        
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
        # dot: print only if initializer is not empty

    def gen(self):
        if self.initializer is not None:
            self.initializer.gen()
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

class StructDeclarator(_BaseDecl):
    def __init__(self, declarator, expr=None):
        super().__init__('TODO')
        self.declarator = declarator
        # FIXME: const expr set to None for simpler behaviour
        self.constexpr = None
        # self.constexpr = expr
    
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

    def gen(self):
        for idx, init in enumerate(self.init_list):
            init.gen()
            # if isinstance(init, Const) or isinstance(init, Identifier):
            #     init.gen()
            # elif idx == len(self.init_list):
            #     init.next = self.next
            #     init.gen()
            # else:
            #     init.next = tac.newlabel()
            #     init.gen()
            #     tac.emit(f'{init.next} :')
    

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
        raise Exception("Not supported")

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
    
    def gen(self):
        self.stmt.next = self.next
        self.stmt.breaklabel = self.breaklabel
        self.stmt.gen()

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
        
        if self.stmt_list:
            for idx, stmt in enumerate(self.stmt_list):
                stmt.breaklabel = getattr(self, 'breaklabel', None)
                stmt.continuelabel = getattr(self, 'continuelabel', None)

                if idx < len(self.stmt_list)-1:
                    stmt.next = tac.newlabel()
                    stmt.gen()
                    tac.emit(f'{stmt.next} :')
                else:
                    stmt.next = self.next
                    stmt.gen()
    
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
            self.expr.next = self.next
            self.expr.gen()

class SelectionStmt(Statement):
    def __init__(self, select_type, select_expr, if_stmt, else_stmt=None):
        super().__init__("Selection Statement")
        self.select_type = select_type
        self.select_expr = select_expr
        self.if_stmt = if_stmt
        self.else_stmt = else_stmt
    
    def gen(self):
        if self.select_type == 'if':
            if self.else_stmt:
                self.select_expr.bool = True
                self.select_expr.true = tac.newlabel()
                self.select_expr.false = tac.newlabel()

                self.if_stmt.next = self.next
                self.else_stmt.next = self.next

                self.select_expr.gen()
                tac.emit(f'{self.select_expr.true} :')
                self.if_stmt.gen()
                tac.emit(f'goto {self.next}')
                tac.emit(f'{self.select_expr.false} :')
                self.else_stmt.gen()
            else:
                self.select_expr.bool = True
                self.select_expr.true = tac.newlabel()
                self.select_expr.false = self.next

                self.if_stmt.next = self.next

                self.select_expr.gen()
                tac.emit(f'{self.select_expr.true} :')
                self.if_stmt.gen()
        else:
            if isinstance(init, Const) or isinstance(init, Identifier):
                self.select_expr.gen()
            else:
                self.select_expr.next = tac.newlabel()
                self.select_expr.gen()
                tac.emit(f'{self.select_expr.next} :')
            case_list = []
            case_stmts = self.if_stmt.stmt_list
            test_label = tac.newlabel()
            tac.emit(f'goto {test_label}')
            case_labels = []
            case_labels.append(tac.newlabel())
            tac.emit(f'{case_labels[-1]} :')
            for idx, case_stmt in enumerate(case_stmts):
                case_stmt.breaklabel = self.next
                if idx < len(case_stmt) - 1:
                    case_stmt.next = tac.newlabel()
                    case_stmt.gen()
                    tac.emit(f'{case_stmt.next} :')
                    case_labels.append(case_stmt.next)
                else:
                    case_stmt.gen()
                    tac.emit(f'goto {self.next}')
                    tac.emit(f'{test_label} :')    
                case_list.append(case_stmt.case)
            
            for idx, case in enumerate(case_list):
                if isinstance(case, tuple):
                    case[1].gen()
                    tac.emit(f'ifeq {self.select_expr.place} {case[1].place} goto {case_labels[idx]}')
                else:
                    tac.emit(f'goto {case_labels[idx]}')


class IterStmt(Statement):
    def __init__(self, iter_type, iter_expr, stmt):
        super().__init__("Iteration Statement")
        self.iter_type = iter_type
        self.iter_expr = iter_expr
        self.stmt = stmt
    
    def gen(self):
        if self.iter_type == 'while':
            begin = tac.newlabel()
            
            self.iter_expr.bool = True
            self.iter_expr.true = tac.newlabel()
            self.iter_expr.false = self.next
            
            self.stmt.next = begin
            self.stmt.continuelabel = begin
            self.stmt.breaklabel = self.next

            tac.emit(f'{begin} :')
            self.iter_expr.gen()
            tac.emit(f'{self.iter_expr.true} :')
            self.stmt.gen()
            tac.emit(f'goto {begin}')
        else:
            e1, e2, e3 = iter_expr
            
            e1.next = tac.newlabel()
            e1.gen()
            tac.emit(f'{e1.next} :')

            if e3 is None:
                self.iter_type = 'while'
                self.iter_expr = e2
                self.gen()
            else:
                begin = tac.newlabel()
            
                e2.bool = True
                e2.true = tac.newlabel()
                e2.false = self.next
                
                self.stmt.next = tac.newlabel()
                self.stmt.continuelabel = begin
                self.stmt.breaklabel = self.next

                tac.emit(f'{begin} :')
                e2.gen()
                tac.emit(f'{e2.true} :')
                self.stmt.gen()
                tac.emit(f'{self.stmt.next} :')

                e3.next = begin
                e3.gen()
                tac.emit(f'goto {begin}')

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
    
    def gen(self):
        if self.jump_type == 'continue':
            tac.emit(f'goto {self.continuelabel}')
        elif self.jump_type == 'break':
            tac.emit(f'goto {self.breaklabel}')
        elif self.jump_type == 'return':
            if self.expr:
                self.expr.next = self.next
            tac.emit(f'return')


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
            unit.next = None
            unit.gen()

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

    def gen(self):
        self.stmt.next = self.next
        self.stmt.gen()

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
