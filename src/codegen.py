from parser import symtable
import re

from parser_class import Function, VarType
import struct

INT_MAX = 2**31 - 1
INT_MIN = -2**31

def binary(num):
    return hex(struct.unpack('<I', struct.pack('<f', num))[0])
    # return ''.join('{:0>8b}'.format(c) for c in struct.pack('!f', num))

def binary2float(b):
    return struct.unpack('>f', struct.pack('>I', int(b, 16)))[0]

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

    def is_byte_reg(self, reg):
        return self.reg_name[reg] in ["eax", "ebx", "ecx", "edx"]
    
    def getreg(self, byte_reg=False):
        available_regs = self.get_available_regs(byte_reg=byte_reg)

        assert(len(available_regs) > 0)

        for i in available_regs:
            if self.reg_d[i] is None:
                return i
        
        # all registers are full
        self.spillreg(available_regs[0])
        return available_regs[0]
        # for i in range(self.num_reg):
        #     if byte_reg and (not self.is_byte_reg(i)):
        #         continue
        #     if self.reg_d[i] is None:
        #         return i
        
        # # all registers are full
        # self.spillreg(self.tie_reg)
        # reg = self.tie_reg
        # self.tie_reg = (reg + 1)%self.num_reg
        # if byte_reg and not self.is_byte_reg(reg):
        #     return self.getreg(byte_reg=True)
        # return reg
    
    def spillreg(self, reg, need=True):
        if self.reg_d[reg] != None:
            if not self.is_in_scope(self.reg_d[reg]):
                # variable stored in reg is out of scope so we don't need its value
                need = False
            if need:
                if self.is_char(self.reg_d[reg]):
                    if not self.is_byte_reg(reg):
                        old_reg = reg
                        name = self.reg_d[reg]
                        self.spillreg(old_reg, need=False) # clear the old reg

                        reg = self.getreg(byte_reg=True) # get a byte reg [eax, ebx, ecx, edx]

                        self.loadreg(reg, name, need=False) # load the reg

                        self.add(f"mov %{self.reg_name[old_reg]}, %{self.reg_name[reg]}") # move value from old reg

                    self.add(f'movb %{self.reg_name[reg][1]}l, {self.get_addr(self.reg_d[reg])}') # move char from reg to memory
                else:
                    self.add(f"mov %{self.reg_name[reg]}, {self.get_addr(self.reg_d[reg])}")
            # TODO: dev can addr_d be scope dependent?
            self.addr_d.pop(self.reg_d[reg], None) # None to prevent KeyError
            self.reg_d[reg] = None
    
    def spillallregs(self, need=True): #need implies if we may need to store or just empty it
        for reg in range(self.num_reg):
            self.spillreg(reg, need)
    
    def get_info(self, name):
        """ Get symbol table information related to name symbol """
        # print(f'{self.cur_instr}, {self.cur_instr.scope.scope_id}, {self.cur_instr.scope.lookup_info(name)}, {name}')
        return self.cur_instr.scope.lookup_info(name)

    def is_in_scope(self, name):
        # check by looking up in current instruction scope
        return self.cur_instr.scope.lookup_info(name) != None

    def is_char(self, name) -> bool:
        var = self.cur_instr.scope.lookup_info(name)
        if var is None:
            return True
        return not var['type'].is_pointer() and (var['type'].basic_type() == 'char')
    
    def is_in_reg(self, name):
        return name in self.addr_d
    
    def get_reg_by_symbol(self, name):
        return self.addr_d[name]
    
    def get_all_regs(self):
        return list(range(self.num_reg))

    def get_active_regs(self):
        regs = []
        for attr in ['e1', 'e2', 'e3']:
            if e := getattr(self.cur_instr, attr, False):
                if self.is_in_reg(e):
                    regs.append(self.get_reg_by_symbol(e))
        return regs
    
    def get_available_regs(self, byte_reg=False):
        restricted_regs = self.get_active_regs()
        if byte_reg:
            # add esi, edi to restricted reg
            for reg in [self.reg_no['esi'], self.reg_no['edi']]:
                if reg not in restricted_regs:
                    restricted_regs.append(reg)
        
        # create list of regs other than restricted regs
        available_regs = []
        for reg in self.get_all_regs():
            if reg not in restricted_regs:
                available_regs.append(reg)
        return available_regs

    def get_addr(self, name_info, displ=False, need=False):
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
        if need:
            # update memory with latest value if need=True
            if self.is_in_reg(name_info['name']):
                self.spillreg(self.get_reg_by_symbol(name_info['name']), need=need)

        if name_info['scope_id'] == 0:
            # global variables are stored in .data section
            return '$' + name_info['name']
        else:
            if displ:
                return hex(name_info['offset'])
            else:
                return f'{hex(name_info["offset"])}(%ebp)'
    
    def loadreg(self, reg, name, need=True):
        if self.reg_d[reg] != None:
            self.addr_d.pop(self.reg_d[reg], None)
            self.reg_d[reg] = None
        if need:
            if name in self.addr_d:
                self.add(f"mov {self.get_symbol(name)}, %{self.reg_name[reg]}")
            else:
                if self.is_char(name) and (not self.is_const(name)):
                    # if not self.is_byte_reg(reg):
                    #     reg = self.getreg(byte_reg=True)
                        # no need to spill old reg as it was already empty
                    # print(self.reg_name[reg])
                    # self.add(f"movb {self.get_addr(name)}, %{self.reg_name[reg][1]}l")
                    # self.add(f'movzbl %{self.reg_name[reg][1]}l, %{self.reg_name[reg]}')
                    self.add(f'movzbl {self.get_addr(name)}, %{self.reg_name[reg]}')
                else:
                    self.add(f"mov {self.get_addr(name)}, %{self.reg_name[reg]}")
        
        if self.get_info(name) == None:
            # constant value
            return
        self.addr_d[name] = reg
        self.reg_d[reg] = name
    
    def get_symbol(self, name, reg=False, byte_reg=False, float=False, need=True): # TODO: think of some good name for this function !!
        """ returns register / memory where symbol name is stored """
        
        if name in self.addr_d:
            if byte_reg and not self.is_byte_reg(self.addr_d[name]):
                # name in non byte register [esi, edi]
                old_r = self.addr_d[name]
                self.spillreg(old_r, need=False)
                r = self.getreg(byte_reg=True)
                self.loadreg(r, name, need=False)
                if need:
                    self.add(f'mov %{self.reg_name[old_r]}, %{self.reg_name[r]}')
            return '%' + self.reg_name[self.addr_d[name]]
        else:
            if byte_reg:
                #  name in memory
                r = self.getreg(byte_reg=True)
                self.loadreg(r, name, need=False)
                if need:
                    # self.add(f'movb {self.get_addr(name)}, %{self.reg_name[r][1]}l')
                    # self.add(f'movzbl %{self.reg_name[r][1]}l, %{self.reg_name[r]}')
                    if self.is_const(name):
                        self.add(f'movl {self.get_addr(name)}, %{self.reg_name[r]}')
                    else:
                        self.add(f'movzbl {self.get_addr(name)}, %{self.reg_name[r]}')
                return '%' + self.reg_name[r]
            elif reg:
                r = self.getreg()
                self.loadreg(r, name, need=need)
                return '%' + self.reg_name[r]
            else:
                return self.get_addr(name)

    def gen_assembly(self, ):
        self.add('.data')
        
        # dump global symtable into .data section
        for keys, value in symtable.global_scope.variables.items():
            self.add(f'{value["name"]}:')
            self.add(f'.zero {value["type"].get_size()}')
        
        # add fmt string info
        for (label, fmt_str) in symtable.fmt_var.items():
            self.add(f'{label}:')
            self.add (f'.string {fmt_str}')

        # .text section
        self.add('.text')
        self.add('.global main')

        # #For file io fns from fileio.s file
        # self.add("\textern fcreate1")
        # self.add("\textern fwrite2")
        # self.add("\textern fclose1")
        # self.add("\textern fopen1")
        # self.add("\textern fread2")

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
                    self.spillallregs() # spill registers before jump / labelled instruction for consistency
                    self.add(f'{self.labels[str(idx)]}:')
                
                self.add(f'\n // {code} \n // {self.reg_no} \n // {self.addr_d} \n // {self.reg_d}')
                # gen it!
                self.gen_instr(code)

            # FIXME: don't know what it is for
            if str(len(codes)) in self.labels:
                self.add(f'{self.labels[str(len(codes))]}:')
            
            self.spillallregs(need=False)
        
    def gen_instr(self, code):
        """ generate x86 from 3AC instr """
        if code.instr == 'ifnz':
            if self.is_float(code.e1):
                if code.e1 in self.addr_d:
                    self.spillreg(self.addr_d[code.e1])
                self.add(f'fldz')
                self.add(f'fld {self.get_addr(code.e1)}')
                self.add(f'fcomip')
                self.add(f'fstp %st(0)')
            else:
                self.add(f'cmp $0, {self.get_symbol(code.e1)}')
            
            self.spillallregs() # spill registers before jumps / labelled statements for consistency
            self.add(f'jne {self.labels[code.label]}')

        elif code.instr == 'goto':
            self.spillallregs() # spill registers before jumps / labelled statements for consistency
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


            # displ = self.get_addr(code.e1, displ=True) # need only offset/displacement of e1 not entier address
            r1 = self.get_symbol(code.e1, reg=True) # need only offset/displacement of e1 not entier address

            if self.get_info(code.e3)['type'].is_array():
                instr = 'lea'
                byte_reg = False
            else:
                if self.is_char(code.e3):
                    instr = 'movb'
                    byte_reg = True
                else:
                    byte_reg = False
                    instr = 'mov'
            r3 = self.get_symbol(code.e3, reg=True, byte_reg=byte_reg)

            # if displ[0] == '$':
            #     # e1 is global
            #     self.add(f'{instr} ({r1}, {self.get_symbol(code.e2, reg=True)}, {self.get_info(code.e1)["type"].get_ref_size()}), {r}')
            # else:
            if instr == 'movb':
                self.add(f'{instr} ({r1} , {self.get_symbol(code.e2, reg=True)}, 1), %{r3[2]}l')
            else:
                self.add(f'{instr} ({r1} , {self.get_symbol(code.e2, reg=True)}, 1), {r3}')

            if self.is_char(code.e3):
                r3 = self.reg_no[r3[1:]]
                if not self.is_byte_reg(r3):
                    old_reg = r3
                    self.spillreg(old_reg, need=False)

                    r3 = self.getreg(byte_reg=True)
                    self.loadreg(r3, code.e3, need=False)

                    self.add(f"mov %{self.reg_name[old_reg]}, %{self.reg_name[r3]}")
                self.add(f"movzbl %{self.reg_name[r3][1]}l, %{self.reg_name[r3]}")

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
            if self.is_float(code.e1):
                if code.e1 in self.addr_d:
                    self.spillreg(self.addr_d[code.e1])
                self.add(f'lea -0x8(%esp), %esp')
                self.add(f'fld {self.get_addr(code.e1)}')
                self.add(f'fstpl (%esp)')
            elif self.is_char(code.e1) and (not self.is_const(code.e1)):

                self.add(f'push {self.get_symbol(code.e1, reg=True, byte_reg=True)}')
                # self.add(f'push {self.get_symbol(code.e1)}')
            else:
                self.add(f'push {self.get_symbol(code.e1)}')

        elif code.instr == 'memory update':

            # mov e1, (e2)
            # (e2) is memory location so e1 is required to be in register

            info = self.get_info(code.e2)
            if info['type'].get_ref_type().is_char():
                if code.e1 in self.addr_d and self.is_byte_reg(self.addr_d[code.e1]):
                    # e1 in byte register [eax, ebx, ecx, edx]
                    r = self.addr_d[code.e1]
                    self.add(f'movb %{self.reg_name[r][1]}l, ({self.get_symbol(code.e2, reg=True)})')
                else:
                    if code.e1 in self.addr_d:
                        # e1 in non byte register [esi, edi]
                        old_r = self.addr_d[code.e1]
                        self.spillreg(self.addr_d[code.e1], need=False)
                        r = self.getreg(byte_reg=True)
                        self.loadreg(r, code.e1, need=False)
                        self.add(f'mov %{self.reg_name[old_r]}, %{self.reg_name[r]}')
                    else:
                        #  e1 in memory
                        r = self.getreg(byte_reg=True)
                        # print(self.reg_name[r])
                        self.loadreg(r, code.e1, need=False)
                        self.add(f'movb {self.get_addr(code.e1)}, %{self.reg_name[r][1]}l')
                        self.add(f'movzbl %{self.reg_name[r][1]}l, %{self.reg_name[r]}')
                    self.add(f'movb %{self.reg_name[r][1]}l, ({self.get_symbol(code.e2, reg=True)})')
            else:
                self.add(f'mov {self.get_symbol(code.e1, reg=True)}, ({self.get_symbol(code.e2, reg=True)})')

        elif code.instr == 'array update':

            # mov e1, e3[e2]
            # e3[e2] is memory location so e1 is required to be in register
            info = self.get_info(code.e3)
            if info['type'].get_ref_type().is_char():
                byte_reg = True
                instr = 'movb'
            else:
                byte_reg = False
                instr = 'mov'
            r1 = self.get_symbol(code.e1, reg=True, byte_reg=byte_reg)

            r3 = self.get_symbol(code.e3, reg=True) 
            r2 = self.get_symbol(code.e2, reg=True)

            if instr == 'movb':
                self.add(f'{instr} %{r1[2]}l, ({r3} , {r2}, 1)')
            else:
                self.add(f'{instr} {r1}, ({r3} , {r2}, 1)')

        elif code.instr == 'ifeq':
            r1 = self.get_symbol(code.e1, reg=True)
            r2 = self.get_symbol(code.e2)

            self.add(f'cmp {r2}, {r1}')
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
        
        elif code.instr == 'spill all':
            self.spillallregs()
        else:
            raise Exception(f'Invalid code instr = {code.instr}')

    def is_const(self, e):
        return e[0] == '$'
    
    def is_float(self, e):
        return self.get_info(e) and self.get_info(e)['type'].is_float()

    def unary_op_assembly(self, code):
        if code.op == '&':
            # lea (e1), e2
            # e2 requires to be in register
            self.add(f'lea {self.get_addr(code.e1, need=True)}, {self.get_symbol(code.e2, reg=True)}')
        elif code.op == '*':
            # mov (e1), e2
            # e2 requires to be in register
            if self.is_char(code.e2):
                # read 1 byte from (e1) into register e2
                r2 = self.get_symbol(code.e2, byte_reg=True)
                self.add(f'movb ({self.get_symbol(code.e1, reg=True)}), %{r2[2]}l')
                self.add(f'movzbl %{r2[2]}l, {r2}')
            else:
                self.add(f'mov ({self.get_symbol(code.e1, reg=True)}), {self.get_symbol(code.e2, reg=True)}')
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
            
            if code.e1 in self.addr_d:
                self.spillreg(self.addr_d[code.e1])

            if code.e2 in self.addr_d:
                self.spillreg(self.addr_d[code.e2])
            
            self.add(f'fldz') # pushes 0.0 on stack
            self.add(f'fsub {self.get_addr(code.e1)}')
            self.add(f'fstp {self.get_addr(code.e2)}')

        elif code.op == 'int2float':
            if code.e1 in self.addr_d:
                # update memory with actual value of e1
                self.spillreg(self.addr_d[code.e1])
            
            if code.e2 in self.addr_d:
                # update memory with actual value of e2
                self.spillreg(self.addr_d[code.e2])            
            
            if self.is_const(code.e1):
                val = float(code.e1[1:])
                self.add(f'movl ${binary(val)}, {self.get_addr(code.e2)}')
            else:
                self.add(f'fild {self.get_addr(code.e1)}')
                self.add(f'fstp {self.get_addr(code.e2)}')

        elif code.op == 'float2int':
            if code.e1 in self.addr_d:
                # update memory with actual value of e1
                self.spillreg(self.addr_d[code.e1])
            
            if code.e2 in self.addr_d:
                # update memory with actual value of e2
                self.spillreg(self.addr_d[code.e2])            
            
            if self.is_const(code.e1):
                val = int(binary2float(code.e1[1:]))
                # print(code.e1[1:])
                self.add(f'movl ${hex(val)}, {self.get_addr(code.e2)}')
            else:
                self.add(f'fld {self.get_addr(code.e1)}')
                # fistp rounds off the float rather than truncating
                # to change this behaviour we need to change control word
                # using fnstcw, fldcw, etc instructions
                self.add(f'fistpl {self.get_addr(code.e2)}')

        elif code.op == 'int2char':

            # load e1 in byte register
            r = self.get_symbol(code.e1, byte_reg=True)

            #  and save in e2 as integer
            self.add(f'movb %{r[2]}l, {self.get_addr(code.e2)}')

        elif code.op == 'char2int':

            # char2int only required when reading char from memory
            if code.e1 in self.addr_d:
                # read char from register and copy into register of e2
                r = self.get_symbol(code.e1)
                self.add(f'mov {r}, {self.get_symbol(code.e2)}')
            else:
                # read char from memory
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
            
            if self.is_const(code.e2):
                self.add(f'idiv {self.get_symbol(code.e2, reg=True)}')
            else:
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
        elif code.op[3:] in ['==', '!=', '<', '<=', '>', '>='] and code.op[:3] == 'int':
            # cmp e1 e2
            # at least one should be register, let r2 is register
            r1 = self.get_symbol(code.e1, reg=True)
            # self.add(f'cmp {r2}, {self.get_symbol(code.e1)}')
            self.add(f'cmp {self.get_symbol(code.e2)}, {r1}')

            r = self.get_symbol(code.e3, need=False, byte_reg=True)
            self.comparator_assembly(code.op[3:], r)

        elif code.op == "float+":
            if code.e1 in self.addr_d:
                self.spillreg(self.addr_d[code.e1])

            if code.e2 in self.addr_d:
                self.spillreg(self.addr_d[code.e2])
            
            if code.e3 in self.addr_d:
                self.spillreg(self.addr_d[code.e3])

            self.add(f'fld {self.get_addr(code.e1)}')
            self.add(f'fadd {self.get_symbol(code.e2)}')
            self.add(f'fstp {self.get_symbol(code.e3)}')

        elif code.op == "float-":
            if code.e1 in self.addr_d:
                self.spillreg(self.addr_d[code.e1])

            if code.e2 in self.addr_d:
                self.spillreg(self.addr_d[code.e2])
            
            if code.e3 in self.addr_d:
                self.spillreg(self.addr_d[code.e3])

            self.add(f'fld {self.get_addr(code.e1)}')
            self.add(f'fsub {self.get_symbol(code.e2)}')
            self.add(f'fstp {self.get_symbol(code.e3)}')

        elif code.op == "float*":
            if code.e1 in self.addr_d:
                self.spillreg(self.addr_d[code.e1])

            if code.e2 in self.addr_d:
                self.spillreg(self.addr_d[code.e2])
            
            if code.e3 in self.addr_d:
                self.spillreg(self.addr_d[code.e3])

            self.add(f'fld {self.get_addr(code.e1)}')
            self.add(f'fmul {self.get_symbol(code.e2)}')
            self.add(f'fstp {self.get_symbol(code.e3)}')
            
        elif code.op == "float/":
            if code.e1 in self.addr_d:
                self.spillreg(self.addr_d[code.e1])

            if code.e2 in self.addr_d:
                self.spillreg(self.addr_d[code.e2])
            
            if code.e3 in self.addr_d:
                self.spillreg(self.addr_d[code.e3])

            self.add(f'fld {self.get_addr(code.e1)}')
            self.add(f'fdiv {self.get_symbol(code.e2)}')
            self.add(f'fstp {self.get_symbol(code.e3)}')
            # # fdiv e1, e2
            # r2 = self.get_symbol(code.e3, reg=True, float = True)
            
            # # copy e2 into e3
            # self.add(f'mov {self.get_symbol(code.e2)}, {r2}')

            # self.add(f'fdiv {self.get_symbol(code.e1)}, {r2}')
        elif code.op[5:] in ['==', '!=', '<', '<=', '>', '>='] and code.op[:5] == 'float':
            if code.e1 in self.addr_d:
                self.spillreg(self.addr_d[code.e1])

            if code.e2 in self.addr_d:
                self.spillreg(self.addr_d[code.e2])
            
            self.add(f'fld {self.get_addr(code.e1)}')
            self.add(f'fld {self.get_addr(code.e2)}')
            self.add(f'fcomip')
            self.add(f'fstp %st(0)')
            r = self.get_symbol(code.e3, need=False, byte_reg=True)
            self.comparator_assembly(code.op[5:], r)
        else:
            raise Exception(f'float is not handled {code.op}')
    
    def comparator_assembly(self, op, r):
        if op == '==':
            self.add(f'sete %{r[2]}l')
            self.add(f'movzbl %{r[2]}l, {r}')
        elif op == '!=':
            self.add(f'setne %{r[2]}l')
            self.add(f'movzbl %{r[2]}l, {r}')
        elif op == '<':
            self.add(f'setb %{r[2]}l')
            self.add(f'movzbl %{r[2]}l, {r}')
        elif op == '<=':
            self.add(f'setbe %{r[2]}l')
            self.add(f'movzbl %{r[2]}l, {r}')
        elif op == '>':
            self.add(f'seta %{r[2]}l')
            self.add(f'movzbl %{r[2]}l, {r}')

        elif op == '>=':
            self.add(f'setae %{r[2]}l')
            self.add(f'movzbl %{r[2]}l, {r}')
        else:
            raise Exception(f'Unkown comparator {op}')
    
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
