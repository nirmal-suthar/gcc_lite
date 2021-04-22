
reg_no = {'ebx':0,'ecx':1, 'esi':2,  'edi':3, 'eax':4, 'edx':5}
reg_name =  {value:key for key, value in reg_no.items()}
neg_relop = {"==":"!=", "!=":"==", "<=": ">", "<": ">=", ">=": "<", ">=": "<"}
allocated = [0]*6
reloplatest=0 #used to store info for compare and jump
curr_procedure = ['empty','main']

def spillbeforecall():
    for q in range(6):
        if(regalloc[q]!=0) and not "temp" in regalloc[q]:
        #Search for the function where the variable in that register was defined
            #check its offset
            offset = 0#TODO symtable.function[curr_procedure[0]]['variables'][str(regalloc[q])]['offset']
            if(offset<0):
                print('\tmov '+ '[ebp+' + str(abs(offset)) + ']' + ' , ' + reg_name[q])
            else:
                print('\tmov '+ '[ebp-' + str(offset) + ']' + ' , ' + reg_name[q])
        regalloc[q] = 0

def isAssigned(var):
    for i in range(0,6):
        if(regalloc[i]==var):
            return i
    return 0

def loadreg(a, var):
    offset = 0#TODO get offset of var symtable.function[curr_procedure[0]]['variables'][str(regalloc[q])]['offset']
    if(offset<0):
        print('\tmov '+ reg_name[a] + ' , ' + '[ebp+' + str(abs(offset)) + ']')
    else:
        print('\tmov '+ reg_name[a] + ' , ' + '[ebp-' + str(offset) + ']' )

def printins(ins,op1,op2='0'):
    if ins == 'MOV':
        if op1 != op2:
            print('\tmov '+ op2 +' , '+op1)
    elif ins == 'A':
        print('\tadd '+op2+' , '+op1)
    elif ins == 'S':
        print('\tsub '+op2+' , '+op1)
    elif ins == "MUL":
        print('\timul '+ op1)
    elif ins == "P":
        print('\tpush ' +op1)
    elif ins=="neg":
        print('\tneg '+op1)
    elif ins=="AND":
        print('\tand '+op1 + ' , '+op2)
    elif ins == "DIV":
        print('\tdiv '+op1)

    elif ins == "C":
        print('\tcmp '+op2+' , '+op1)
    elif ins == ">=":
        spillbeforecall()
        print('\tjge '+op1)
    elif ins == ">":
        spillbeforecall()
        print('\tjg '+op1)
    elif ins == "<=":
        spillbeforecall()
        print('\tjle '+op1)
    elif ins == "<":
        spillbeforecall()
        print('\tjl '+op1)
    elif ins == "==":
        spillbeforecall()
        print('\tje '+op1)
    elif ins == "!=":
        spillbeforecall()
        print('\tjne '+op1)
  
    elif ins == "GOTO":
         # will be called if tac code is 'goto : '
        spillbeforecall()
        print('\tjmp '+op1)
    elif ins == "LAB":
        # will be called if tac code is 'label : '
        spillbeforecall()
        print('\n'+op1+':')
        allocated = [0]*6

# This function should return a register after allocationg
def getreg(i):

    for q in range(6):
        if regalloc[q] == 0:
            return q
   
    # Register Spilling

def regs(i, var, load=0, lhs=0):
    
    tmp=isAssigned(var)
    #import pdb; pdb.set_trace()

    if(tmp!=0):
        a=reg_name[tmp]
    else:
        a=getreg(i)
        if load == 1:
            loadreg(a, var)
        regalloc[a] = var
        a = reg_name[a]
    if lhs == 1:
        if "temp" == tac.code[i][1][0:4] and tac.code[i][1] != tac.code[i][0]:
            for x in range(0,6):
                if(regalloc[x]==tac.code[i][1]):
                    q = x
                    regalloc[x] = 0
                    break

        if "temp" == tac.code[i][2][0:4] and tac.code[i][2] != tac.code[i][0]:
            for x in range(0,6):
                if(regalloc[x]==tac.code[i][2]):
                    q = x
                    regalloc[x] = 0
                    break
    return a

def ADDSUB(quad,isadd=1):
    #TODO
    #if both const, call regs for op1, then printins("MOV") and then printins("A/S")
    #otherwise store regs for all ops, then printins("MOV") and then printins("A/S")

def MUL(quad):
    #TODO

def DIV(quad):
    #TODO

def COMPARE(quad):
    #TODO

def EQUAL(quad):
    #TODO

def IFGOTO(quad):
    #TODO


#Converts every instruction to corresponding assembly code
def generate():
    flag_for_pop=0
    fgl =0
    print("section .text")
    print("\tglobal main")
    print("\textern printInt1")
    print("\textern scanInt0")
    print("\textern printString1")
    print("\textern scanString0")
    print("\textern fcreate1")
    print("\textern fwrite2")
    print("\textern fclose1")
    print("\textern fopen1")
    print("\textern fread2")
    print("\textern append2")
    print("\textern val1")
    print("\textern next1")

    for i in range(len(tac.code)):
       if(tac.code[i][3]=='+'):
            #import pdb; pdb.set_trace()
            ADDSUB(i)
        elif(tac.code[i][3]=='-'):
            ADDSUB(i,0)
        elif(tac.code[i][3]=='*'):
            MUL(i)
        elif(tac.code[i][3]=="/"):
            DIV(i)
        elif(tac.code[i][3]=='='):
            #import pdb; pdb.set_trace()
            EQUAL(i)
        elif(tac.code[i][0]=='goto'):
            printins("J",tac.code[i][3])
        elif(tac.code[i][0]=='label :'):
            printins("L", tac.code[i][3])
        elif(tac.code[i][0]=="ifgoto"):
            IFGOTO(i)
        elif(tac.code[i][3]=='||' or tac.code[i][3]=='&&'):
            pass
        elif(tac.code[i][3]=='<'or tac.code[i][3]=='<='or tac.code[i][3]=='>'or tac.code[i][3]=='>='or tac.code[i][3]=='=='or tac.code[i][3]=='!='):
            COMPARE(i)

        ## CASES for function, return, call , push , pop

    print("\n\tmov eax , 1")
    print("\tmov ebx , 0")
    print("\tint 0x80")
