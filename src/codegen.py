from parser import symtable
import re

from parser_class import Function, VarType

def binary(num):
    return ''.join('{:0>8b}'.format(c) for c in struct.pack('!f', num))

class AssemblyGen:
    def __init__(self, func_code):
        self.func_code = func_code
        self.reg_no = {'ebx':0, 'ecx':1, 'esi':2, 'edi':3, 'eax':4, 'edx':5}
        self.reg_name =  {value:key for key, value in self.reg_no.items()}
        self.num_reg = len(self.reg_no)
        self.tie_reg = 0 # register to be spilled if all registers are full
        self.reg_d = [None] * self.num_reg
        self.addr_d = {}
        self.assembly = []
        self.cur_instr = None
    
    def code_idx(self):
        return len(self.assembly)
    
    def add(self, instr):
        self.assembly.append(instr)

    def getreg(self):
        for i in range(self.num_reg):
            if self.reg_d[i] is None:
                return i
        
        # all registers are full
        self.spillreg(self.tie_reg)
        reg = self.tie_reg
        self.tie_reg = (reg + 1)%self.num_reg
        return reg
    
    def spillreg(self, reg, need=True):
        if self.reg_d[reg] != None:
            if need:
                self.add(f"mov %{self.reg_name[reg]}, {self.get_addr(self.reg_d[reg])}")
                # TODO: dev can addr_d be scope dependent?
                self.addr_d.pop(self.reg_d[reg])
            self.reg_d[reg] = None
    
    def spillallregs(self, need=True): #need implies if we may need to store or just empty it
        for reg in range(self.num_reg):
            self.spillreg(reg, need)
    
    def get_info(self, name):
        """ Get symbol table information related to name symbol """
        # print(f'{self.cur_instr}, {self.cur_instr.scope.scope_id}, {self.cur_instr.scope.lookup_info(name)}, {name}')
        return self.cur_instr.scope.lookup_info(name)

    def is_char(self, name) -> bool:
        var = self.cur_instr.scope.lookup_info(name)
        if var is None:
            return True
        return not var['type'].is_pointer and (var['type'].basic_type() == 'char')

    def get_addr(self, name_info, displ=False):
        """ get memory address of name """

        if re.fullmatch('\$.*', name_info):
            return name_info
        elif isinstance(name_info, str):
            # if argument is name of symbol then get info from scope/symbol table
            name = name_info
            name_info = self.get_info(name_info)
            if name_info == None: # possibly constant value
                # return '$' + name
                raise Exception(f'hii {name}')

        if name_info['scope_id'] == 0:
            # global variables are stored in .data section
            return '$' + name_info['name']
        else:
            if displ:
                return hex(name_info['offset'])
            else:
                return f'{hex(name_info["offset"])}(%ebp)'
    
    def loadreg(self, reg, name):
        if self.reg_d[reg] != None:
            self.addr_d.pop(self.reg_d[reg])
        if name in self.addr_d:
            self.add(f"mov {self.get_symbol(name)}, %{self.reg_name[reg]}")
        else:
            self.add(f"mov {self.get_addr(name)}, %{self.reg_name[reg]}")
        
        if self.get_info(name) == None:
            # constant value
            return
        self.addr_d[name] = reg
        self.reg_d[reg] = name
    
    def get_symbol(self, name, reg=False, float=False): # TODO: think of some good name for this function !!
        """ returns register / memory where symbol name is stored """
        if name in self.addr_d:
            return '%' + self.reg_name[self.addr_d[name]]
        else:
            if reg:
                r = self.getreg()
                self.loadreg(r, name)
                return '%' + self.reg_name[r]
            else:
                return self.get_addr(name)

    def gen_assembly(self, ):
        self.add('.data')
        
        # dump global symtable into .data section
        for keys, value in symtable.global_scope.variables.items():
            self.add(f'{value["name"]}:')
            self.add(f'.zero {value["type"].get_size()}')
        
        # .text section
        self.add('.text')
        self.add('.global main')

        # #For file io fns from fileio.s file
        # self.add("\textern fcreate1")
        # self.add("\textern fwrite2")
        # self.add("\textern fclose1")
        # self.add("\textern fopen1")
        # self.add("\textern fread2")

        # add fmt string info
        for (label, fmt_str) in symtable.fmt_var.items():
            self.add(f'{label}:')
            self.add (f'.string {fmt_str}')

        # start traversing the IR (one function at a time!)
        for fidx, codes in enumerate(self.func_code):

            # compute the labels info and store in relevant places
            labels = []
            for code in codes:
                if hasattr(code, 'label'):
                    labels.append(code.label)
            
            self.labels = {label: f"label_{fidx}_{id}" for id, label in enumerate(labels)}

            for idx, code in enumerate(codes):
                self.cur_instr = code

                # if cur code is part of new label => create it
                if str(idx) in self.labels:
                    self.add(f'{self.labels[str(idx)]}:')
                
                self.add(f'// {code}')
                # gen it!
                self.gen_instr(code)

            # FIXME: don't know what it is for
            if str(len(codes)) in self.labels:
                self.add(f'{self.labels[str(len(codes))]}:')
            
            self.spillallregs(need=False)
        
    def gen_instr(self, code):
        """ generate x86 from 3AC instr """
        if code.instr == 'ifnz':
            self.add(f'cmp $0, {self.get_symbol(code.e1)}')
            self.add(f'jne {self.labels[code.label]}')

        elif code.instr == 'goto':
            self.add(f'jmp {self.labels[code.label]}')

        elif code.instr == 'binop':
            self.binary_op_assembly(code)

        elif code.instr == 'mov':
            # check if instruction is 1byte aligned
            if self.is_char(code.e2):
                self.spillreg(self.reg_no['eax'])
                self.loadreg(self.reg_no['eax'], code.e1)
                self.add(f'movb %al, {self.get_addr(code.e2)}')
            else:
                # mov e1, e2
                # Forcing e2 to be a register
                r2 = self.get_symbol(code.e2, reg=True)
                r1 = self.get_symbol(code.e1)
                self.add(f'mov {r1}, {r2}')

        elif code.instr == 'unaryop':
            self.unary_op_assembly(code)

        elif code.instr == 'array access':
            # mov e1[e2], e3
            # e1[e2] is memory so e3 is required to be in register

            r = self.get_symbol(code.e3, reg=True)

            displ = self.get_addr(code.e1, displ=True) # need only offset/displacement of e1 not entier address
            if self.get_info(code.e3)['type'].is_array():
                instr = 'lea'
            else:
                instr = 'mov'

            if displ[0] == '$':
                # e1 is global
                self.add(f'{instr} {displ}(, {self.get_symbol(code.e2, reg=True)}, {self.get_info(code.e1)["type"].get_ref_size()}), {r}')
            else:
                self.add(f'{instr} {displ}(%ebp , {self.get_symbol(code.e2, reg=True)}, {self.get_info(code.e1)["type"].get_ref_size()}), {r}')

        elif code.instr == 'call':

            self.spillreg(self.reg_no['eax'])

            # assuming label for the function is same as name of the function
            self.add(f'call {code.e1}')

            FuncType = symtable.lookup_func(code.e1)
            if FuncType is None:
                raise Exception(f'functype is none {code.e1}')

            self.add(f'add ${FuncType.param_size()}, %esp')

            if code.e2 != '#':
                self.reg_d[self.reg_no['eax']] = code.e2
                self.addr_d[code.e2] = self.reg_no['eax']

        elif code.instr in ['printf', 'scanf']:

            self.spillreg(self.reg_no['eax'])

            # assuming label for the function is same as name of the function
            self.add(f'call {code.instr}')

            self.add(f'add ${code.e1}, %esp')

            if code.e2 != '#':
                self.reg_d[self.reg_no['eax']] = code.e2
                self.addr_d[code.e2] = self.reg_no['eax']
        
        elif code.instr == 'push param':
            self.add(f'push {self.get_symbol(code.e1)}')

        elif code.instr == 'memory update':

            # mov e1, (e2)
            # (e2) is memory location so e1 is required to be in register

            self.add(f'mov {self.get_symbol(code.e1, reg=True)}, ({self.get_symbol(code.e2, reg=True)})')

        elif code.instr == 'array update':

            # mov e1, e2[e3]
            # e2[e3] is memory location so e1 is required to be in register
            
            r = self.get_symbol(code.e1, reg=True)

            displ = self.get_addr(code.e3, displ=True) # need only offset/displacement of e3 not entier address
            if displ[0] == '$':
                # e3 is global
                self.add(f'mov {r}, {displ}(, {self.get_symbol(code.e2, reg=True)}, {self.get_info(code.e3)["type"].get_ref_size()})')
            else:
                self.add(f'mov {r}, {displ}(%ebp , {self.get_symbol(code.e2, reg=True)}, {self.get_info(code.e3)["type"].get_ref_size()})')

        elif code.instr == 'ifeq':
            if code.e1 in self.addr_d:
                r1 = '%' + self.reg_name[self.addr_d[code.e1]]
                r2 = self.get_symbol(code.e2)
            elif code.e2 in self.addr_d:
                r2 = '%' + self.reg_name[self.addr_d[code.e2]]
                r1 = self.get_symbol(code.e1)
            else:
                # at least one register required for cmp
                r = self.getreg()
                self.loadreg(r, code.e1)
                r1 = '%' + self.reg_name[r]
                r2 = self.get_symbol(code.e2)

            self.add(f'cmp {r1}, {r2}')
            self.add(f'je {self.labels[code.label]}')

        elif code.instr == 'return':
            
            self.spillreg(self.reg_no['eax'])
            self.loadreg(self.reg_no['eax'], code.e1)
            
        elif code.instr == 'FuncBegin':
            self.add(f'{code.e1}:')
            self.add(f'push %ebp')
            self.add(f'mov %esp, %ebp')
            func = symtable.lookup_func(code.e1)
            scope = symtable.all_scope[func.scope_id]
            self.add(f'sub ${hex(scope.size + scope.child_max_size)}, %esp')
            self.add(f'push %ebx')
            self.add(f'push %ecx')
            self.add(f'push %edx')
            self.add(f'push %esi')
            self.add(f'push %edi')
            
        elif code.instr == 'FuncEnd':
            self.add(f'pop %edi')
            self.add(f'pop %esi')
            self.add(f'pop %edx')
            self.add(f'pop %ecx')
            self.add(f'pop %ebx')
            self.add(f'mov %ebp, %esp')
            self.add(f'pop %ebp')
            self.add(f'ret ')  
        else:
            raise Exception(f'Invalid code instr = {code.instr}')


    def unary_op_assembly(self, code):
        if code.op == '&':
            # lea (e1), e2
            # e2 requires to be in register
            self.add(f'lea {self.get_addr(code.e1)}, {self.get_symbol(code.e2, reg=True)}')
        elif code.op == '*':
            # mov (e1), e2
            # e2 requires to be in register
            self.add(f'mov {self.get_addr(code.e1)}, {self.get_symbol(code.e2, reg=True)}')
        elif code.op == '~':
            # not e1
            r = self.get_symbol(code.e2, reg=True)
            if code.e1 in self.addr_d:
                self.add(f'mov {self.get_symbol(code.e1)}, {r}')
            else:
                self.add(f'mov {self.get_addr(code.e1)}, {r}')
            self.add(f'not {r}')
        elif code.op == 'int-':
            # neg e1
            r = self.get_symbol(code.e2, reg=True)
            if code.e1 in self.addr_d:
                self.add(f'mov {self.get_symbol(code.e1)}, {r}')
            else:
                self.add(f'mov {self.get_addr(code.e1)}, {r}')
            self.add(f'neg {r}')
        elif code.op == 'float-':
            # 
            # r = self.get_symbol(code.e2, reg=True, float=True)
            
            binaryCode = binary(float(0.0))
            #get a free reg to store 0.0 and then subtract e1 from it?
            self.add(f'mov {r}, 0b' + str(binaryCode))
            self.add(f'sub edi {self.get_addr(code.e1)}' )
            # unar
            # TODO:
            raise Exception('floats are not handled')
        elif code.op == 'int2float':
            # TODO:
            raise Exception('floats are not handled')
        elif code.op == 'float2int':
            # TODO:
            raise Exception('floats are not handled')
        elif code.op == 'int2char':
            self.spillreg(self.reg_no['eax'])
            self.loadreg(self.reg_no['eax'], code.e1)
            self.add(f'movb %al, {self.get_addr(code.e2)}')
        elif code.op == 'char2int':
            self.add(f'movzbl {self.get_addr(code.e1)}, {self.get_symbol(code.e2, reg=True)}')
        elif code.op == 'float2char':
            # float => int => char
            raise Exception('not handled')
        elif code.op == 'char2float':
            # char => int => float
            raise Exception('not handled')
        else:
            raise Exception(f'Invalid code.op = {code.op}')
    
    def binary_op_assembly(self, code):
        """
        binary ops: +, -, *, /, %, <<, >>, |, &, ^, >, >=, <, <=, ==, !=
        """
        if code.op == 'int+':
            # add e1, e2
            r2 = self.get_symbol(code.e3, reg=True)
            
            # copy e2 into e3
            self.add(f'mov {self.get_symbol(code.e2)}, {r2}')

            self.add(f'add {self.get_symbol(code.e1)}, {r2}')
        elif code.op == 'int-':
            # sub e2, e1
            r2 = self.get_symbol(code.e3, reg=True)
            
            # copy e1 into e3
            self.add(f'mov {self.get_symbol(code.e1)}, {r2}')

            self.add(f'sub {self.get_symbol(code.e2)}, {r2}')
        elif code.op == 'int*':
            # imul e1, e2
            r2 = self.get_symbol(code.e3, reg=True)
            
            # copy e2 into e3
            self.add(f'mov {self.get_symbol(code.e2)}, {r2}')

            self.add(f'imul {self.get_symbol(code.e1)}, {r2}')
        elif code.op == 'int/':
            # idiv e2
            # store e1 in edx:eax, eax will have quotient and edx will have remainder
            self.spillreg(self.reg_no['edx'])
            self.spillreg(self.reg_no['eax'])
            
            self.add(f'mov $0, %edx')
            self.add(f'mov {self.get_symbol(code.e1)}, %eax')
            
            self.add(f'idiv {self.get_symbol(code.e2)}')
            self.reg_d[self.reg_no['eax']] = code.e3
            self.addr_d[code.e3] = self.reg_no['eax']
        elif code.op == '%':
            # idiv e2
            # store e1 in edx:eax, eax will have quotient and edx will have remainder
            self.spillreg(self.reg_no['edx'])
            self.spillreg(self.reg_no['eax'])
            
            self.add(f'mov $0, %edx')
            self.add(f'mov {self.get_symbol(code.e1)}, %eax')
            
            self.add(f'idiv {self.get_symbol(code.e2)}')
            self.reg_d[self.reg_no['edx']] = code.e3
            self.addr_d[code.e3] = self.reg_no['edx']
        elif code.op == '<<':
            # shl e2, e1
            # e2 can either be constant or %cl (lower 8 bits of %ecx) register
            self.spillreg(self.reg_no['ecx'])
            self.add(f"mov {self.get_symbol(code.e2)}, %cl")
            
            r = self.get_symbol(code.e3, reg=True)
            self.add(f'mov {self.get_symbol(code.e1)}, {r}') # store e1 in e3

            self.add(f'shl %cl, {r}')
        elif code.op == '>>':
            # shr e2, e1
            # e2 can either be constant or %cl (lower 8 bits of %ecx) register
            self.spillreg(self.reg_no['ecx'])
            self.add(f"mov {self.get_symbol(code.e2)}, %cl")
            
            r = self.get_symbol(code.e3, reg=True)
            self.add(f'mov {self.get_symbol(code.e1)}, {r}') # store e1 in e3

            self.add(f'shr %cl, {r}')
        elif code.op == '|':
            # or e1, e2
            r2 = self.get_symbol(code.e3, reg=True)
            
            # copy e2 into e3
            self.add(f'mov {self.get_symbol(code.e2)}, {r2}')

            self.add(f'or {self.get_symbol(code.e1)}, {r2}')
        elif code.op == '&':
            # and e1, e2
            r2 = self.get_symbol(code.e3, reg=True)
            
            # copy e2 into e3
            self.add(f'mov {self.get_symbol(code.e2)}, {r2}')

            self.add(f'and {self.get_symbol(code.e1)}, {r2}')
        elif code.op == '^':
            # xor e1, e2
            r2 = self.get_symbol(code.e3, reg=True)
            
            # copy e2 into e3
            self.add(f'mov {self.get_symbol(code.e2)}, {r2}')

            self.add(f'xor {self.get_symbol(code.e1)}, {r2}')
        elif code.op == 'int==':
            # cmp e1 e2
            # at least one should be register, let r2 is register
            r2 = self.get_symbol(code.e2, reg=True)

            self.add(f'cmp {self.get_symbol(code.e1)}, {r2}')
            self.spillreg(self.reg_no['eax'])
            self.add(f'sete %al')
            self.add(f'movzbl %al, %eax')
            self.reg_d[self.reg_no['eax']] = code.e3
            self.addr_d[code.e3] = self.reg_no['eax']
        elif code.op == 'int!=':
            # cmp e1 e2
            # at least one should be register, let r2 is register
            r2 = self.get_symbol(code.e2, reg=True)

            self.add(f'cmp {self.get_symbol(code.e1)}, {r2}')
            self.spillreg(self.reg_no['eax'])
            self.add(f'setne %al')
            self.add(f'movzbl %al, %eax')
            self.reg_d[self.reg_no['eax']] = code.e3
            self.addr_d[code.e3] = self.reg_no['eax']
        elif code.op == 'int<':
            # cmp e1 e2
            # at least one should be register, let r2 is register
            r2 = self.get_symbol(code.e2, reg=True)

            self.add(f'cmp {self.get_symbol(code.e1)}, {r2}')
            self.spillreg(self.reg_no['eax'])
            self.add(f'setl %al')
            self.add(f'movzbl %al, %eax')
            self.reg_d[self.reg_no['eax']] = code.e3
            self.addr_d[code.e3] = self.reg_no['eax']
        elif code.op == 'int<=':
            # cmp e1 e2
            # at least one should be register, let r2 is register
            r2 = self.get_symbol(code.e2, reg=True)

            self.add(f'cmp {self.get_symbol(code.e1)}, {r2}')
            self.spillreg(self.reg_no['eax'])
            self.add(f'setle %al')
            self.add(f'movzbl %al, %eax')
            self.reg_d[self.reg_no['eax']] = code.e3
            self.addr_d[code.e3] = self.reg_no['eax']
        elif code.op == 'int>':
            # cmp e1 e2
            # at least one should be register, let r2 is register
            r2 = self.get_symbol(code.e2, reg=True)

            self.add(f'cmp {self.get_symbol(code.e1)}, {r2}')
            self.spillreg(self.reg_no['eax'])
            self.add(f'setg %al')
            self.add(f'movzbl %al, %eax')
            self.reg_d[self.reg_no['eax']] = code.e3
            self.addr_d[code.e3] = self.reg_no['eax']
        elif code.op == 'int>=':
            # cmp e1 e2
            # at least one should be register, let r2 is register
            r2 = self.get_symbol(code.e2, reg=True)

            self.add(f'cmp {self.get_symbol(code.e1)}, {r2}')
            self.spillreg(self.reg_no['eax'])
            self.add(f'setge %al')
            self.add(f'movzbl %al, %eax')
            self.reg_d[self.reg_no['eax']] = code.e3
            self.addr_d[code.e3] = self.reg_no['eax']
        elif code.op == "float+":
            # fadd e1, e2
            r2 = self.get_symbol(code.e3, reg=True, float = True)
            
            # copy e2 into e3
            self.add(f'mov {self.get_symbol(code.e2)}, {r2}')

            self.add(f'fadd {self.get_symbol(code.e1)}, {r2}')
        elif code.op == "float-":
            # fsub e1, e2
            r2 = self.get_symbol(code.e3, reg=True, float = True)
            
            # copy e2 into e3
            self.add(f'mov {self.get_symbol(code.e2)}, {r2}')

            self.add(f'fsub {self.get_symbol(code.e1)}, {r2}')
        
        elif code.op == "float*":
            # fmul e1, e2
            r2 = self.get_symbol(code.e3, reg=True, float = True)
            
            # copy e2 into e3
            self.add(f'mov {self.get_symbol(code.e2)}, {r2}')

            self.add(f'fmul {self.get_symbol(code.e1)}, {r2}')

        elif code.op == "float/":
            # fdiv e1, e2
            r2 = self.get_symbol(code.e3, reg=True, float = True)
            
            # copy e2 into e3
            self.add(f'mov {self.get_symbol(code.e2)}, {r2}')

            self.add(f'fdiv {self.get_symbol(code.e1)}, {r2}')
        elif code.op == 'float==':
            # cmp e1 e2
            # at least one should be register, let r2 is register
            r2 = self.get_symbol(code.e2, reg=True, float = True)

            self.add(f'fcomip {self.get_symbol(code.e1)}, {r2}')
            self.spillreg(self.reg_no['eax'])
            self.add(f'sete %al')
            self.add(f'movzbl %al, %eax')
            self.reg_d[self.reg_no['eax']] = code.e3
            self.addr_d[code.e3] = self.reg_no['eax']
        elif code.op == 'float!=':
            # cmp e1 e2
            # at least one should be register, let r2 is register
            r2 = self.get_symbol(code.e2, reg=True, float = True)

            self.add(f'fcomip {self.get_symbol(code.e1)}, {r2}')
            self.spillreg(self.reg_no['eax'])
            self.add(f'setne %al')
            self.add(f'movzbl %al, %eax')
            self.reg_d[self.reg_no['eax']] = code.e3
            self.addr_d[code.e3] = self.reg_no['eax']
        elif code.op == 'float<':
            # cmp e1 e2
            # at least one should be register, let r2 is register
            r2 = self.get_symbol(code.e2, reg=True, float = True)

            self.add(f'fcomip {self.get_symbol(code.e1)}, {r2}')
            self.spillreg(self.reg_no['eax'])
            self.add(f'setb %al')
            self.add(f'movzbl %al, %eax')
            self.reg_d[self.reg_no['eax']] = code.e3
            self.addr_d[code.e3] = self.reg_no['eax']
        elif code.op == 'float<=':
            # cmp e1 e2
            # at least one should be register, let r2 is register
            r2 = self.get_symbol(code.e2, reg=True, float = True)

            self.add(f'fcomip {self.get_symbol(code.e1)}, {r2}')
            self.spillreg(self.reg_no['eax'])
            self.add(f'setbe %al')
            self.add(f'movzbl %al, %eax')
            self.reg_d[self.reg_no['eax']] = code.e3
            self.addr_d[code.e3] = self.reg_no['eax']

        elif code.op == 'float>':
            # fcmip e1 e2
            # at least one should be register, let r2 is register
            r2 = self.get_symbol(code.e2, reg=True, float = True)

            self.add(f'fcomip {self.get_symbol(code.e1)}, {r2}')
            self.spillreg(self.reg_no['eax'])
            self.add(f'seta %al')
            self.add(f'movzbl %al, %eax')
            self.reg_d[self.reg_no['eax']] = code.e3
            self.addr_d[code.e3] = self.reg_no['eax']
        elif code.op == 'float>=':
            # cmp e1 e2
            # at least one should be register, let r2 is register
            r2 = self.get_symbol(code.e2, reg=True, float = True)

            self.add(f'fcomip {self.get_symbol(code.e1)}, {r2}')
            self.spillreg(self.reg_no['eax'])
            self.add(f'setae %al')
            self.add(f'movzbl %al, %eax')
            self.reg_d[self.reg_no['eax']] = code.e3
            self.addr_d[code.e3] = self.reg_no['eax']
        else:
            raise Exception(f'float is not handled {code.op}')
    
    def dump_code(self, filename):
        with open(filename, 'w') as f:
            for idx, instr in enumerate(self.assembly):
                if instr[-1] == ':':
                    f.write("" + instr + "\n")
                else:
                    f.write("\t" + instr + "\n")



reg_no = {'ebx':0,'ecx':1, 'esi':2,  'edi':3, 'eax':4, 'edx':5}
reg_name =  {value:key for key, value in reg_no.items()}
neg_relop = {"==":"!=", "!=":"==", "<=": ">", "<": ">=", ">=": "<", ">=": "<"}
allocated = [0]*6
reloplatest=0 #used to store info for compare and jump
curr_procedure = ['empty','main']
