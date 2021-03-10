/* ---------------- //  **/
//   /* 


union lex_0_{
    short int v;
    long double si[3];
};

/*
*/  // 

int main(){
    union lex_0_ lex1, lex2, *lex3;
    lex1.si[2] = lex2.v = 0;
    lex1.v = ~lex2.v;
    switch (lex2.v = (lex1.v))
    {
    case 1:
        *lex3 = lex2;
        break;
    case '\'':
        lex3 = &lex1; 
    default:
        1 ==++lex1.v;
        break;
    }
    return 0;
}