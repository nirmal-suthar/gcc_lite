class ScopeTable:
    def __init__(self, scope_depth=0, parent=None):
        self.scope_depth = scope_depth  # scope depth
        self.parent = parent            # parent scopeTable
        self.variables = {}             # for identifiers
        self.aliases = {}               # for typedefs
        self.structs = {}               # for structs and union
        self.metadata = 'TODO'          # will include function, loop or ifelse

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

    def push_scope(self, scope_type='TODO') -> None:
        new_scope = ScopeTable(self.cur_depth(), self.scope_stack[-1])
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
            return

        scope.variables[name] = vtype

    def add_struct(self, name, struct_type):
        if self.cur_scope().lookup_struct(name):
            compilation_err.append('Redeclaration of struct named {}'.format(name))
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
        
    def add_func(self, func) -> None:
        if func.name in self.function:
            compilation_err.append('Redeclaration of function named {}'.format(func.name))
            return
                
        self.function[func.name] = func

symtable = SymbolTable()
compilation_err = []