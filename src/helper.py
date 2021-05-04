import csv
from parser import parser_error
import re

stdlib = '''
int printf(char *s);
int scanf(char *s);

// TODO: add malloc, free and math function
'''

# def parser_error(error_str=None):
#     parser.compilation_err = True
#     print(bcolors.BOLD+'{}:{}:'.format(lexer.filename,lexer.lineno)+bcolors.ENDC,end='')
#     print(bcolors.FAIL+' SyntaxError: '+bcolors.ENDC,parser.error)
#     print('     {} |{}'.format(lexer.lineno,lexer.lines[lexer.lineno - 1]))
ADDR_SIZE = 4

class ScopeTable:
    def __init__(self, scope_depth=0, parent=None, scope_id=0, scope_type='Other'):
        self.scope_id = scope_id        # scope id
        self.scope_depth = scope_depth  # scope depth
        self.parent = parent            # parent scopeTable
        self.variables = {}             # for identifiers
        self.aliases = {}               # for typedefs
        self.structs = {}               # for structs and union
        self.metadata = scope_type      # will include function, loop or ifelse
        self.size = 0
        self.child_max_size = 0
        self.param_size = 0


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
    
    def add_var(self, name, vtype, is_param=False):
        offset = 0
        if self.metadata == 'Global':
            # global variables will be stored in .data section
            offset = 0

        elif self.metadata == 'Function':
            if is_param:

                offset = self.param_size + 2*ADDR_SIZE + vtype.get_size() # 2 ADDR_SIZE for return addr and rbp
                self.param_size += vtype.get_size()
            else:
                offset = -(vtype.get_size() + self.size)
                self.size = -offset

        else:
            offset = -(self.parent.size + self.size + vtype.get_size())
            self.size = self.size + vtype.get_size()
            self.parent.child_max_size = max(self.parent.child_max_size, self.size)

        self.variables[name] = {'name': name, 'type': vtype, 'offset': offset, 'scope_id': self.scope_id}
    
    def lookup_info(self, name):
        scope = self
        while scope:
            if scope.lookup_var(name):
                return scope.variables[name]
            scope = scope.parent
        return None
        
class SymbolTable():
    def __init__(self):

        self.function = {} # for function (func can only be declared in global mode)
        self.global_scope = ScopeTable()
        self.global_scope.metadata = 'Global'
        self.all_scope = [self.global_scope]

        self.scope_stack = [self.global_scope]
        self.tmp_cnt = 0 #for three address code temp variables
        self.tac_scope_idx = 0 # for changing scope while 3ac generation
        self.fmt_var = {} # stores the fmt strings used in printf, scanf

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
    
    def check_case_scope(self):
        # if immediate scope is Switch case then good,
        # else throw error
        if self.cur_scope().metadata in ['Switch']:
            return True
        return False

    def push_scope(self, scope_type='Other', exists=False) -> None:
        if exists:
            self.scope_stack.append(self.all_scope[self.tac_scope_idx + 1])
            self.tac_scope_idx += 1
            return
        new_scope = ScopeTable(self.cur_depth(), self.scope_stack[-1], len(self.all_scope), scope_type)
        self.all_scope.append(new_scope)
        self.scope_stack.append(new_scope)

    def pop_scope(self) -> None:
        scope = self.cur_scope() 
        if scope.metadata != 'Global':
            scope.parent.child_max_size = max(scope.parent.child_max_size, scope.size+scope.child_max_size)
        self.scope_stack.pop()

    def lookup_var(self, name):
        scope = self.cur_scope()
        while scope:
            if scope.lookup_var(name):
                return scope.variables[name]['type']
            scope = scope.parent
        return None

    def lookup_struct(self, name):
        scope = self.cur_scope()
        while scope:
            if scope.lookup_struct(name):
                return scope.structs[name]
            scope = scope.parent
        return None

    def lookup_alias(self, name):
        scope = self.cur_scope()
        while scope:
            if scope.lookup_alias(name):
                return scope.aliases[name]
            scope = scope.parent
        return None
        # return self.cur_scope().lookup_alias(id)

    def lookup_func(self, name):
        if name in self.function:
            return self.function[name]
        return None

    def get_size(self, dtype):
        raise Exception('TODO')

    def add_var(self, name, vtype, is_static = False, is_param=False):
        scope = self.global_scope if is_static else self.cur_scope()
        if scope.lookup_var(name):
            parser_error('Redeclaration of variable named `{}`'.format(name))
            return

        scope.add_var(name, vtype, is_param=is_param)
        # scope.variables[name] = {'type': vtype, 'offset': offset}

    def add_struct(self, name, struct_type):
        if self.cur_scope().lookup_struct(name):
            parser_error('Redeclaration of struct named `{}`'.format(name))
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
            parser_error('Redeclaration of type/alias named {}'.format(alias))
        
    def add_func(self, func) -> None:
        if func.name in self.function:
            func_ = self.function[func.name]

            if func_.is_declared == func.is_declared == 1:
                parser_error('Redefinition of function named `{}`'.format(func.name))
                return

            if func_.ret_type == func.ret_type and func_.args == func.args:
                return

            parser_error('Redeclaration of function named {}'.format(func.name))
            return

        self.function[func.name] = func

    # for enabling printf and scanf
    def add_fmt(self, label, fmt_str):
        self.fmt_var[label] = fmt_str

    #this will give a temp for three address code
    def get_temp_for_ir(self):
        self.tmp_cnt = self.tmp_cnt + 1
        name = 'temp' + str(self.tmp_cnt)
        return  name
    
    def dump_csv(self, filename):
        with open(filename, 'w', newline='') as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(['Table Id', 'Parent Id', 'Table Type', 'Symbol Id', 'Symbol Name', 'Symbol Type', 'Symbol Other Information'])
            writer.writerow(['======','======','======','======','======','======','======'])
            
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
                if scope_id != len(self.all_scope):
                    # writer.writerow(['','','','','','',''])
                    writer.writerow(['======','======','======','======','======','======','======'])
                    # writer.writerow(['','','','','','',''])

symtable = SymbolTable()

class Instr:
    def __init__(self, code):
        self.code = code
        self.parse_instr(self.code)

    def parse_instr(self, code):
        self.scope = symtable.cur_scope()
        if m := re.fullmatch('ifnz (?P<e1>[^ ]*) goto (?P<label>[^ ]*)', code):
            self.instr = 'ifnz'
            self.e1 = m.group('e1')
            self.label = m.group('label')

        elif m := re.fullmatch('goto (?P<label>[^ ]*)', code):
            self.instr = 'goto'
            self.label = m.group('label')

        elif m := re.fullmatch('(?P<e3>[^ ]*) = (?P<e1>[^ ]*) (?P<op>[^ ]*) (?P<e2>[^ ]*)', code):
            self.instr = 'binop'
            self.e1 = m.group('e1')
            self.e2 = m.group('e2')
            self.e3 = m.group('e3')
            self.op = m.group('op')

        elif m := re.fullmatch('(?P<e2>[^ ]*) = (?P<e1>[^ ]*)', code):
            self.instr = 'mov'
            self.e1 = m.group('e1')
            self.e2 = m.group('e2')

        elif m := re.fullmatch('(?P<e2>[^ ]*) = (?P<op>[^ ]*) (?P<e1>[^ ]*)', code):
            self.instr = 'unaryop'
            self.e1 = m.group('e1')
            self.e2 = m.group('e2')
            self.op = m.group('op')

        elif m := re.fullmatch('(?P<e3>[^ ]*) = (?P<e1>[^ ]*) \[ (?P<e2>[^ ]*) \]', code):
            self.instr = 'array access'
            self.e1 = m.group('e1')
            self.e2 = m.group('e2')
            self.e3 = m.group('e3')

        elif m := re.fullmatch('call (?P<e1>[^ ]*) (?P<e2>[^ ]*)', code):
            self.instr = 'call'
            self.e1 = m.group('e1')
            self.e2 = m.group('e2')

        elif m := re.fullmatch('param (?P<e1>[^ ]*)', code):
            self.instr = 'push param'
            self.e1 = m.group('e1')

        elif m := re.fullmatch('\* (?P<e2>[^ ]*) = (?P<e1>[^ ]*)', code):
            self.instr = 'memory update'
            self.e1 = m.group('e1')
            self.e2 = m.group('e2')

        elif m := re.fullmatch('(?P<e3>[^ ]*) \[ (?P<e2>[^ ]*) \] = (?P<e1>[^ ]*)', code):
            self.instr = 'array update'
            self.e1 = m.group('e1')
            self.e2 = m.group('e2')
            self.e3 = m.group('e3')

        elif m := re.fullmatch('ifeq (?P<e1>[^ ]*) (?P<e2>[^ ]*) goto (?P<label>[^ ]*)', code):
            self.instr = 'ifeq'
            self.e1 = m.group('e1')
            self.e2 = m.group('e2')
            self.label = m.group('label')

        elif m := re.fullmatch('return (?P<e1>[^ ]*)', code):
            self.instr = 'return'
            self.e1 = m.group('e1')
        
        elif m := re.fullmatch('FuncBegin (?P<e1>[^ ]*)', code):
            self.instr = 'FuncBegin'
            self.e1 = m.group('e1')
        
        elif m := re.fullmatch('FuncEnd (?P<e1>[^ ]*)', code):
            self.instr = 'FuncEnd'
            self.e1 = m.group('e1')

        elif m := re.fullmatch('printf (?P<e1>[^ ]*) (?P<e2>[^ ]*)', code):
            self.instr = 'printf'
            self.e1 = m.group('e1')
            self.e2 = m.group('e2')

        elif m := re.fullmatch('scanf (?P<e1>[^ ]*) (?P<e2>[^ ]*)', code):
            self.instr = 'scanf'
            self.e1 = m.group('e1')
            self.e2 = m.group('e2')
        else:
            raise Exception(f'regex not handled! {code}')
    
    def __str__(self):
        return self.code

class IRHelper:

    def __init__(self):
        self.tmpCount = 0
        self.labelCount = 0
        self.code = []
        self.func_code = None
        self.fmtCount = 0

    def fmt_string(self,):
        label = f'FMT{self.fmtCount}'
        self.fmtCount += 1
        return label

    def push_func_code(self):
        self.code = []
        if self.func_code is None:
            self.func_code = [self.code]
        else:
            self.func_code.append(self.code)
        self.tmpCount = 0

    def newtmp(self):
        #get a new symtable temporary, may put in symbol table
        tmp = "t#" + str(self.tmpCount)
        self.tmpCount += 1
        return tmp
    
    def newlabel(self):
        label = "L" + str(self.labelCount)
        self.labelCount += 1
        return label

    def emit(self, code):
        self.code.append(Instr(code))
        # print(len(self.code))

    def backpatch(self,st_list,target_label):
        #set the target label for the statements in the list
        for x in st_list:
            if self.code[x].label == '':
                self.code[x].label = str(target_label)
                self.code[x].code += str(target_label)
    
    def nextquad(self):
        return len(self.code)

    def dump_code(self, filename):
        with open(filename, 'w') as f:
            for func in self.func_code:
                for idx, instr in enumerate(func):
                    f.write(str(idx) + "\t" + str(instr) + "\n")
                f.write('\n')

tac = IRHelper()

compilation_err = []