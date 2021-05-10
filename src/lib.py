
stdlib = '''
int printf(char *s);
int scanf(char *s);
void strcpy(char *d, char *s);

// TODO: add malloc, free and math function

// Extra functions

void prints(char* s){
    printf("%s", s);
}

void printn(int n){
    printf("%d", n);
}

int scanint(){
    int tmp;
    scanf("%d", &tmp);
    return tmp;
}

'''
