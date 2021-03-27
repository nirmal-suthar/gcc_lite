
class SymbolTable:
    def __init__(self,parent=None, type_ = None):
        self.table = {}
        self.parent = parent
        self.type_ = type_
        self.typeDefs = {} # this is a dictionary of dictionary, in which each type name is key
                           # for each key, all the declarations are key in the new dict, with type, size tuple
                           # In this dictionary we will also store the total size
        self.metadata = {}
        self.metadata['name'] = 'global'

    def lookUp(self, id):
        return (id in self.table)
    
    def lookUpType(self,id):
        return (id in self.typeDefs)

    def delete(self, name):
        (self.table).pop(name, None)

    def getArg(self, id):
        if(self.lookUp(id)):
            return (self.table)[id]

        return None

    #inserts if not present before
    def insert(self, name, value):
        if (not self.lookUp(name)):
            (self.table)[name] = value
            return True
        else:
            return False
        

    def update(self, id, value):
        try:
            (self.table)[id] = value
            return True
        except KeyError:
            return False

 
    def getDetail(self, name):
        if(self.lookUp(name)):
            return self.table[name]
        else:
            return None

    def setParent(self, parent):
        self.parent = parent

    def updateMetadata(self,id,value):
        self.metadata[id]=value


class Node:
    def __init__(self):
        self.data = {}
        self.code = []
        self.placeList = ["NOP",None]
        self.name = name
        self.extra = {}
        self.parse


class SymbolTableHelper:
    def __init__(self):
        self.varCount = 0 #cnt
        self.labelCount = 0
        self.labeldict = {}
        self.scope = 0
        self.scopeStack = [] 
        self.offsetStack = [] #offsetList
        self.symbolTables = [] #scopeTableList
        self.lastScope = 0 #currScopeTable

    #getnewvar
    def newVar(self, type_, size_):
        var = 't' + str(self.varCount)
        self.symbolTables[self.getScope()].insert(var, type_)
        self.symbolTables[self.getScope()].update(var, 'size', size_)
        self.symbolTables[self.getScope()].update(var, 'offset', self.getOffset())
        self.updateOffset(size_)
        self.varCount += 1
        return var

    #getnewlabel
    def newLabel(self,s="label"):
        self.labeldict[s] = self.labeldict[s]+1 if s in self.labeldict.keys() else 0
        label = s + "#" + str(labeldict[s])
        return label

    #pushOffSet
    def newOffset(self):
        self.offsetStack.append(0)
        return

    #get_offset
    def getOffset(self):
        return self.offsetStack[-1]

    #popOffSet
    def popOffset(self):
        return self.offsetStack.pop()

    def updateOffset(self, size):
        self.offsetStack[-1] += size

    def newScope(self, parent=None):
        newTable = SymbolTable(parent)
        newTable.updateMetadata('scopeNo', self.scope)
        self.symbolTables.append(newTable)
        self.scopeStack.append(self.scope)
        self.newOffset()
        self.scope += 1

    def getScope(self):
        return self.scopeStack[-1]

    def endScope(self):
        self.lastScope = self.scopeStack.pop()
        self.popOffset()

    #checkVar
    def checkId(self,identifier, type_='default'):
        if type_ == 'global':
            if self.symbolTables[0].lookUp(identifier) is True:
                return True
            return False
        
        if type_ == "current":
            if self.symbolTables[self.getScope()].lookUp(identifier) is True:
                return True
            return False

        # Default case
        for scope in self.scopeStack[::-1]:
            if self.symbolTables[scope].lookUp(identifier) is True:
                return True
        return False

    def checkType(self, identifier, type_='default'):
        if type_ == 'global':
            if self.symbolTables[0].lookUpType(identifier) is True:
                return True
            return False
        
        if type_ == 'current':
            if self.symbolTables[self.getScope()].lookUpType(identifier) is True:
                return True
            return False

        # Default case
        for scope in self.scopeStack[::-1]:
            if self.symbolTables[scope].lookUpType(identifier) is True:
                return True
        return False

    def findInfo(self, identifier, type_='default'):
        if type_ == 'global':
            if self.symbolTables[0].getArg(identifier) is not None:
                return self.symbolTables[0].getArg(identifier)
        
        else:
            for scope in self.scopeStack[::-1]:
                if self.symbolTables[scope].getArg(identifier) is not None:
                    return self.symbolTables[scope].getArg(identifier)

            for scope in self.scopeStack[::-1]:
                if self.symbolTables[scope].typeDefs.getArg(identifier) is not None:
                    return self.symbolTables[scope].typeDefs.getArg(identifier)
        return None

    def findScope(self, identifier):
        for scope in self.scopeStack[::-1]:
                if self.symbolTables[scope].getArg(identifier) is not None:
                    return scope

    #getParentScope
    def getNearest(self, type_):
        # return nearest parent scope with name = type_(func, for), -1 if no such scope exist
        for scope in self.scopeStack[::-1]:
            if self.symbolTables[scope].metadata['name'] == type_:
                return scope
        return -1

   