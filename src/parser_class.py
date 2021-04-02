import typing
import pydot
symtable = SymbolTable()
compilation_err = []


# #############################################################################
# Misc.            
# #############################################################################

class StructType:
    def __init__(self, struct_name, struct_decl):
        self.struct_name = struct_name
        self.struct_decl = self.struct_decl
        # TODO 
    
    def _get_size(self):
        raise Exception('TODO')

class variable:
    def __init__(self, name, ref_count, _type):
        self.name = name
        self.ref_count = ref_count
        self.type = _type

class ScopeTable:
    def __init__(self, scope_depth=0, parent=None):
        self.scope_depth = scope_depth # scope depth
        self.parent = parent # parent scopeTable
        self.variables = {} # for identifiers
        self.aliases = {} # for typedefs
        self.structs = {} # for structs and union
        self.metadata = 'TODO' # will include function, loop or ifelse

    def lookup_var(self, name):
        if name in self.variables:
            return True
        else:
            return False
        # return self.parent.lookup_var(name) if self.parent is not None else False
    
    def lookup_struct(self, name):
        if name in self.structs:
            return True
        # return self.parent.lookup_struct(name) if self.parent is not None else False
    
    def lookup_alias(self, name):
        if name in self.aliases:
            return True
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
        # return self.cur_scope().lookup_var(name)        
        raise Exception('TODO')

    def lookup_struct(self, id):
        raise Exception('TODO')

    def lookup_alias(self, id):
        raise Exception('TODO')

    def lookup_func(self, id):
        raise Exception('TODO')

    def get_size(self, dtype):
        raise Exception('TODO')

    def add_var(self, id):
        raise Exception('TODO')

    def add_struct(self, type):
        raise Exception('TODO')

    def add_typedef(self, alias, actual):
        raise Exception('TODO')
        
    def add_func(self, func):
        raise Exception('TODO')

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

class ScopeName(_BASENODE):
    def __init__(self, name):
        self.name = name

# #############################################################################
# Expressions            
# #############################################################################

class BaseExpr(_BASENODE) :
    def __init__(self, t_name):
        super().__init__()
        self.t_name = t_name
        self.attr_ignore.append('t_name')

class Const(BaseExpr):
    def __init__(self, const, dvalue):
        super().__init__("Constant")
        self.const = const
        self.dvalue = dvalue

class Identifier(BaseExpr):
    def __init__(self, ident):
        super().__init__("Identifier")
        self.ident = ident

class OpExpr(BaseExpr):
    def __init__(self, lhs, ops, rhs):
        super().__init__("Expression")
        self.lhs = lhs
        self.ops = ops
        self.rhs = rhs

class UnaryExpr(OpExpr):
    def __init__(self, ops, rhs):
        super().__init__(None, ops, rhs)

class PostfixExpr(OpExpr):
    def __init__(self, lhs, *ops):
        super().__init__(lhs, ops, None)

class CastExpr(BaseExpr):
    def __init__(self, _type, Expr):
        super().__init__("Cast Expression")
        self.type = _type
        self.expr = Expr

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
    def __init__(self, specifier, init_list):
        super().__init__('TODO')
        self.specifier = specifier
        self.init_list = [] if init_list is None else init_list
        # dot file: print only init_list

        # FIXME: ignoring storage_class_speciier for now!
        for id in self.init_list:
            if symtable.lookup_var(id.decl):







# class InitDeclaratorList():
#     def __init__(self, *init_expr):
#         self.init_list = init_expr

#     def add_init_expr(self, expr):
#         self.init_list.append(expr)    
#     # dot print all

class InitDeclarator(_BaseDecl):
    def __init__(self, declarator, initializer=None):
        super().__init__('TODO')
        self.declarator = declarator
        self.initializer = initializer
    # dot: print only if initiaizer is not empty

class Specifier(_BaseDecl):
    def __init__(self, specifier_name):
        super().__init__("Specifier")
        self.specifier_name = specifier_name
        self.attr_ignore.append('specifier_name')

class DeclarationSpecifier(Specifier):
    def __init__(self, storage_type_spec, type_spec):
        super().__init__("Declaration Specifier")
        self.storage_type_spec = storage_type_spec
        self.type_spec = type_spec

# class StorageSpecifier(Specifier):
#     def __init__(self, spec):
#         super().__init__("Storage Specifier")
#         self.spec = spec
# 
# class TypeSpecifier(Specifier):
#     def __init__(self, type_name):
#         super().__init__("Type Specifier")
#         self.type_name = type_name # type_name can be a Struct Union Specifier

class StructUnionSpecifier(Specifier):
    def __init__(self, struct_union, name=None, decls_list=None):
        super().__init__("Struct or Union Specifier")
        self.struct_union = struct_union
        self.name = name
        self.decls_list = decls_list

class StructDeclaration(Declaration):
    def __init__(self, spec, init_list):
        super().__init__(spec, init_list)

# class StructDeclarationList():
#     def __init__(self, *decls):
#         self.decls = decls

#     def add_decls(self, expr):
#         self.decls.append(expr)

class StructDeclarator(_BaseDecl):
    def __init__(self, declarator, expr):
        super().__init__('TODO')
        self.declarator = declarator
        self.constexpr = expr

class Declarator(_BaseDecl):
    def __init__(self, ref_count, decl):
        super().__init__('TODO')
        self.ref_count = ref_count
        self.decl = decl

class DirectDecl(_BaseDecl):
    def __init__(self, directdecl, *args):
        super().__init__('TODO')
        self.directdecl = directdecl
        self.args = args

class ParamsDecl(_BaseDecl):
    def __init__(self, spec, decl=None):
        super().__init__('TODO')
        self.spec = spec
        self.decl = decl

class TypeName:
    def __init__(self, spec, abs_decl=None):
        super().__init__('TODO')
        self.spec = spec
        self.abs_decl = abs_decl

class AbsDecl(_BaseDecl):
    def __init__(self, ref_count=0, direct_abs_decl=None):
        super().__init__('TODO')
        self.ref_count = ref_count
        self.direct_abs_decl = direct_abs_decl

class DirectAbsDecl(_BaseDecl):
    def __init__(self, decl, abs_type, abs_args):
        super().__init__('TODO')
        self.decl = decl
        self.abs_type = abs_type
        self.abs_args = abs_args

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
    def __init__(self, specifiers, declarator, stmt):
        super().__init__('Function Definition')
        self.specifiers = specifiers
        self.declarator = declarator
        self.stmt = stmt
        # self.dot_attr = {'Function Def': [self.specifiers, ]}

