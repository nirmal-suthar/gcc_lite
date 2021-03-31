import pydot

# #############################################################################
# Misc.            
# #############################################################################

class _BASENODE():
    def __init__(self):
        pass
        # self.dot_attr = None

    # def _gen_dot_single(self, graph, key, obj, node_idx):

    #     if isinstance(obj, (str, int, float, tuple)):
    #         graph.add_node(pydot.Node(node_idx, label=repr(obj), shape='house', style='filled', color='yellowgreen'))
    #         return node_idx
    #     elif isinstance(obj, list):
    #         graph.add_node(pydot.Node(node_idx, label=key, shape='egg'))
    #         cur_idx = node_idx
    #         for child in obj:
    #             if child == []:
    #                 continue
    #             graph.add_edge(pydot.Edge(node_idx, cur_idx+1))
    #             cur_idx = child._gen_dot(graph, cur_idx+1)
    #         return cur_idx
    #     elif isinstance(obj, _BASENODE):
    #         graph.add_node(pydot.Node(node_idx, label=key, shape='egg'))
    #         graph.add_edge(pydot.Edge(node_idx, node_idx+1))
    #         return obj._gen_dot(graph, node_idx+1)
    #     elif obj is None:
    #         # pass
    #         return node_idx
    #         # raise Exception('None please check')
    #     else:
    #         raise Exception('Invalid type {}'.format(type(obj)))
            
            
    # def _gen_dot(self, graph, node_idx=0):

    #     # graph.add_node(pydot.Node(node_idx, label=self.__dict__['t_name'], shape='egg'))
    #     graph.add_node(pydot.Node(node_idx, label='TODO', shape='egg'))
    #     cur_idx = node_idx
    #     for key in filter(lambda x: x!='t_name', self.__dict__.keys()):
    #         child = self.__dict__[key]
    #         graph.add_edge(pydot.Edge(node_idx, cur_idx+1))
    #         cur_idx = self._gen_dot_single(graph, key, child, cur_idx+1)
    #     return cur_idx

    @staticmethod
    def _gen_dot_single(graph, key, obj, node_idx):

        if isinstance(obj, (str, int, float, tuple)):
            graph.add_node(pydot.Node(node_idx, label=repr(obj), shape='house', style='filled', color='yellowgreen'))
            return node_idx
        elif isinstance(obj, list):
            graph.add_node(pydot.Node(node_idx, label=key, shape='egg'))
            cur_idx = node_idx
            for child in obj:
                if child == []:
                    continue
                graph.add_edge(pydot.Edge(node_idx, cur_idx+1))
                cur_idx = _BASENODE._gen_dot_single(graph, key, child, cur_idx+1)
            return cur_idx
        elif isinstance(obj, _BASENODE):
            graph.add_node(pydot.Node(node_idx, label=key, shape='egg'))
            graph.add_edge(pydot.Edge(node_idx, node_idx+1))
            return obj._gen_dot(graph, node_idx+1)
        elif obj is None:
            # pass
            return node_idx
            # raise Exception('None please check')
        else:
            raise Exception('Invalid type {}'.format(type(obj)))
            
            
    def _gen_dot(self, graph, node_idx=0):

        # graph.add_node(pydot.Node(node_idx, label=self.__dict__['t_name'], shape='egg'))
        graph.add_node(pydot.Node(node_idx, label=self.__class__.__name__, shape='egg'))
        cur_idx = node_idx
        for attr in self.__dict__:
            print(attr)
            child = getattr(self, attr)

            if( child is None
                or child == ''
                or child == []
                or attr == 't_name'
            ):
                continue

            graph.add_edge(pydot.Edge(node_idx, cur_idx+1))
            cur_idx = self._gen_dot_single(graph, attr, child, cur_idx+1)

        return cur_idx


# #############################################################################
# Expressions            
# #############################################################################

class BaseExpr(_BASENODE) :
    def __init__(self, t_name):
        self.t_name = t_name

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
    def __init__(self):
        self.t_name = 'TODO'
    
class Declaration(_BaseDecl):
    def __init__(self, specifier, init_list):
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
        self.declarator = declarator
        self.initializer = initializer
    # dot: print only if initiaizer is not empty

class Specifier(_BaseDecl):
    def __init__(self, specifier_name):
        self.specifier_name = specifier_name

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
        self.declarator = declarator
        self.constexpr = expr

class Declarator(_BaseDecl):
    def __init__(self, ref_count, decl):
        self.ref_count = ref_count
        self.decl = decl

class DirectDecl(_BaseDecl):
    def __init__(self, directdecl, *args):
        self.directdecl = directdecl
        self.args = args

class ParamsDecl(_BaseDecl):
    def __init__(self, spec, decl=None):
        self.spec = spec
        self.decl = decl

class TypeName:
    def __init__(self, spec, abs_decl=None):
        self.spec = spec
        self.abs_decl = abs_decl

class AbsDecl(_BaseDecl):
    def __init__(self, ref_count=0, direct_abs_decl=None):
        self.ref_count = ref_count
        self.direct_abs_decl = direct_abs_decl

class DirectAbsDecl(_BaseDecl):
    def __init__(self, decl, abs_type, abs_args):
        self.decl = decl
        self.abs_type = abs_type
        self.abs_args = abs_args
# #############################################################################
# Initializers            
# #############################################################################

class Initializers(_BASENODE):
    def __init__(self, init_list):
        self.init_list = init_list


# #############################################################################
# Statements            
# #############################################################################

class Statement(_BASENODE):
    def __init__(self, name):
        self.name = name

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
        self.t_name = t_name
    
    # def _gen_dot_single(self, graph, key, obj, node_idx):

    #     if isinstance(obj, (str, int, float)):
    #         graph.add_node(pydot.Node(node_idx, label=repr(obj), shape='house', style='filled', color='yellowgreen'))
    #         return node_idx
    #     elif isinstance(obj, list):
    #         graph.add_node(pydot.Node(node_idx, label=key, shape='egg'))
    #         cur_idx = node_idx
    #         for child in obj:
    #             if child == []:
    #                 continue
    #             graph.add_edge(pydot.Edge(node_idx, cur_idx+1))
    #             cur_idx = child._gen_dot(graph, cur_idx+1)
    #         return cur_idx
    #     elif isinstance(obj, _BASENODE):
    #         graph.add_node(pydot.Node(node_idx, label=key, shape='egg'))
    #         graph.add_edge(pydot.Edge(node_idx, node_idx+1))
    #         return obj._gen_dot(graph, node_idx+1)
    #     # elif isinstance(obj, NoneType):
    #     #     raise Exception('None please check')
    #     else:
    #         raise Exception('Invalid type {}'.format(type(obj)))
            
            
    # def _gen_dot(self, graph, node_idx=0):

    #     graph.add_node(pydot.Node(node_idx, label=self.__dict__['t_name'], shape='egg'))
    #     cur_idx = node_idx
    #     for key in filter(lambda x: x!='t_name', self.__dict__.keys()):
    #         child = self.__dict__[key]
    #         cur_idx = self._gen_dot_single(graph, key, child, cur_idx+1)
    #     return cur_idx

class Start(Node):
    def __init__(self, units):
        super().__init__("Start")
        self.units = units
        # self.dot_attr = {'Start': self.units}

# class TranslationUnits(Node):
#     def __init__(self, *units):
#         super().__init__("Translation Unit")
#         self.unit_list = units
    
#     def add_unit(self, unit):
#         self.unit_list.append(unit)

class FuncDef(Node):
    def __init__(self, specifiers, declarator, stmt):
        super().__init__('Function Definition')
        self.specifiers = specifiers
        self.declarator = declarator
        self.stmt = stmt
        # self.dot_attr = {'Function Def': [self.specifiers, ]}

