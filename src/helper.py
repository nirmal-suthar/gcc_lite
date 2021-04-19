import csv
from parser import parser_error

# def parser_error(error_str=None):
#     parser.compilation_err = True
#     print(bcolors.BOLD+'{}:{}:'.format(lexer.filename,lexer.lineno)+bcolors.ENDC,end='')
#     print(bcolors.FAIL+' SyntaxError: '+bcolors.ENDC,parser.error)
#     print('     {} |{}'.format(lexer.lineno,lexer.lines[lexer.lineno - 1]))


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
        self.tmp_cnt = 0 #for three address code temp variables
    
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

    def add_var(self, name, vtype, is_static = False):
        scope = self.global_scope if is_static else self.cur_scope()
        if scope.lookup_var(name):
            parser_error('Redeclaration of variable named {}'.format(name))
            return

        scope.variables[name] = vtype

    def add_struct(self, name, struct_type):
        if self.cur_scope().lookup_struct(name):
            parser_error('Redeclaration of struct named {}'.format(name))
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
            if func_.ret_type == func.ret_type and func_.args == func.args and func_.is_ellipsis == func.is_ellipsis:
                return
            parser_error('Redeclaration of function named {}'.format(func.name))
            return
                
        self.function[func.name] = func

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

class IRHelper:

    def __init__(self):
        self.tmpCount = 0
        self.lebelCount = 0
        self.code = []

    def newtmp(self):
        #get a new symtable temporary, may put in symbol table
        tmp = "t" + str(self.tmpCount)
        self.tmpCount += 1
        return tmp
    
    def newlabel(self):
        label = "L" + str(self.labelCount)
        self.labelCount += 1
        return label

    def emit(self, code):
        self.code.append(code)

    def backpatch(self,st_list,target_label):
        #set the target label for the statements in the list
        for x in st_list:
            self.code[x][3] = target_label

tac = IRHelper()

compilation_err = []