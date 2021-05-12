
stdlib = '''
int printf(char *s);
int scanf(char *s);
void strcpy(char *d, char *s);
void* memcpy(void* d, void* s, int cnt);

float fsin(float x);
float fcos(float x);
float ftan(float x);
float fsininv(float x);
float fcosinv(float x);
float ftaninv(float x);

float fexp(float x);
float flog(float x);
float fsqrt(float x);
float fpow(float base, float power);

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

float fsin(float x){
    return sinf(x)
}

float fcos(float x){
    return cosf(x)
}

float ftan(float x){
    return tanf(x)
}

float fsininv(float x){
    return asinf(x)
}

float fcosinv(float x){
    return acosf(x)
}

float ftaninv(float x){
    return atanf(x)
}

float flog(float x){
    return logf(x)
}

float fexp(float x){
    return expf(x)
}

float fsqrt(float x){
    return sqrtf(x)
}

float fpow(float base, float power){
    return powf(base, power)
}
'''
