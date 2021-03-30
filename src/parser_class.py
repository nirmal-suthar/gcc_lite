# #############################################################################
# Expressions            
# #############################################################################

class BaseExpr:
    def __init__(self, t_name):
        self.t_name = t_name

class Const(BaseExpr):
    def __init__(self, const, dvalue):
        super().__init__("Constant")
        self.const = const
        self.dvalue = dvalue

class OpExpr(BaseExpr):
    def __init__(self, lhs, ops, rhs):
        super().__init__("Expression")
        self.lhs = lhs
        self.ops = ops
        self.rhs = rhs

class UnaryExpr(OpExpr):
    def __init__(self, ops, rhs):
        super().__init__(None, ops, rhs)
        pass


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

class Declaration():
    def __init__(self, specifier, init_list):
        self.specifier = specifier
        self.init_list = init_list

class InitDeclaratorList():
    def __init__(self, *init_expr):
        self.init_list = init_expr

    def add_init_expr(self, expr):
        self.init_list.append(expr)

class InitDeclarator():
    def __init__(self, declarator, initializer=None):
        self.declarator = declarator
        self.initializer = initializer

class Specifier():
    def __init__(self, specifier_name):
        self.specifier_name = specifier_name

class DeclarationSpecifier(Specifier):
    def __init__(self, type_spec, storage_type_spec=None):
        super().__init__("Declaration Specifier")
        self.type_spec = type_spec
        self.storage_type_spec = storage_type_spec

class StorageSpecifier(Specifier):
    def __init__(self, spec):
        super().__init__("Storage Specifier")
        self.spec = spec

class TypeSpecifier(Specifier):
    def __init__(self, type_name):
        super().__init__("Type Specifier")
        self.type_name = type_name # type_name can be a Struct Union Specifier

class StructUnionSpecifier(Specifier):
    def __init__(self, struct_union, name=None, struct_decls_list=None):
        super().__init__("Struct Union Specifier")
        self.struct_union = struct_union
        self.name = name
        self.struct_decls_list = struct_decls_list

class StructDeclaration(Declaration):
    def __init__(self, spec, init_list):
        super().__init__(spec, init_list)

class StructDeclarationList():
    def __init__(self, *decls):
        self.decls = decls

    def add_decls(self, expr):
        self.decls.append(expr)

class StructDeclarator():
    def __init__(self, declarator, expr):
        self.declarator = declarator
        self.expr =- expr
# #############################################################################
# Statements            
# #############################################################################

class Stmt():
    def __init__(self, name):
        self.name

class LabeledStmt(Stmt):
    def __init__(self, case, stmt):
        super().__init__("Labeled Statement")
        self.case = case
        self.stmt = stmt

class CompoundStmt(Stmt):
    def __init__(self, decls, stmts):
        super().__init__("Compound Statment")
        self.decl_list = decls
        self.stmt_list = stmts

class ExprStmt(Stmt):
    def __init__(self, expr):
        super().__init__("Expression Statement")
        self.expr = expr
    def __call__(self):
        return self.expr

class SelectionStmt(Stmt):
    def __init__(self, select_type, select_expr, if_stmt, else_stmt=None):
        super().__init__("Selection Statement")
        self.select_type = select_type
        self.select_expr = select_expr
        self.if_stmt = if_stmt
        self.else_stmt = else_stmt

class IterStmt(Stmt):
    def __init__(self, iter_type, iter_expr, stmt):
        super().__init__("Iteration Statement")
        self.iter_type = iter_type
        self.iter_expr = iter_expr
        self.stmt = stmt

class JumpStmt(Stmt):
    def __init__(self, jump_type, expr=None):
        super().__init__("Jump Statement")
        self.jump_type = jump_type
        self.expr = expr

# #############################################################################
# External declaration and function definitions            
# #############################################################################

class Node():
    def __init__(self, t_name):
        self.t_name

class Start(Node):
    def __init__(self):
        super.__init__("Start")

class TranslationUnits(Node):
    def __init__(self, *units):
        super().__init__("Translation Unit")
        self.unit_list = units
    
    def add_unit(self, unit):
        self.unit_list.append(unit)


class FuncDef(Node):
    def __init__(self, specifiers, declarator, stmt):
        super().__init__('Function Definition')
        self.specifiers = specifiers
        self.declarator = declarator
        self.stmt = stmt
