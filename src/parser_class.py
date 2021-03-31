import pydot

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
                
                graph.add_edge(pydot.Edge(node_idx, cur_idx+1))
                cur_idx = _BASENODE._gen_dot(graph, child, cur_idx+1)                

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

                cur_idx = _BASENODE._gen_dot(graph, child, cur_idx+1)                
                
        return cur_idx

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
        self.init_list = init_list
        # dot file: print only init_list

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
    def __init__(self, struct_union, name=None, struct_decls_list=None):
        super().__init__("Struct or Union Specifier")
        self.struct_union = struct_union
        self.name = name
        self.struct_decls_list = struct_decls_list

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

    def gen_dot(self, graph, node_idx=0):
        """Get a list of node and edge declarations."""
        _BASENODE._gen_dot(graph, self, node_idx)
        print('Dot graph generated')

class FuncDef(Node):
    def __init__(self, specifiers, declarator, stmt):
        super().__init__('Function Definition')
        self.specifiers = specifiers
        self.declarator = declarator
        self.stmt = stmt
        # self.dot_attr = {'Function Def': [self.specifiers, ]}

