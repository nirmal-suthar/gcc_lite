
stdlib = '''
int printf(char *s);
int scanf(char *s);
void strcpy(char *d, char *s);
void* memcpy(void* d, void* s, int cnt);

float sinf(float x);
float cosf(float x);
float tanf(float x);
float asinf(float x);
float acosf(float x);
float atanf(float x);

float expf(float x);
float logf(float x);
float sqrtf(float x);
float powf(float base, float power);


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
    return sinf(x);
}

float fcos(float x){
    return cosf(x);
}

float ftan(float x){
    return tanf(x);
}

float fsininv(float x){
    return asinf(x);
}

float fcosinv(float x){
    return acosf(x);
}

float ftaninv(float x){
    return atanf(x);
}

float flog(float x){
    return logf(x);
}

float fexp(float x){
    return expf(x);
}

float fsqrt(float x){
    return sqrtf(x);
}

float fpow(float base, float power){
    return powf(base, power);
}
'''
