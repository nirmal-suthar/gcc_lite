
class SymbolTable:
    def __init__(self,parent=None, type_ = None):
        self.table = {}
        self.parent = parent
        self.type_ = type_
        self.metadata = {}
        self.metadata['name'] = 'global'

    def lookUp(self, id):
        return (id in self.table)
    
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

