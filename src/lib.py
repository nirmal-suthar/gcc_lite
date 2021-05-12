
stdlib = '''
int printf(char *s);
int scanf(char *s);
void strcpy(char *d, char *s);
void* memcpy(void* d, void* s, int cnt);

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

void * bufcpy(void * dest, void* src, int cnt){
    return memcpy(dest, src, cnt);
}
'''
