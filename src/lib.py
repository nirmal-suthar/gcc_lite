stdlib = '''
int printf(char *s);
int scanf(char *s);

void* memcpy(void* d, void* s, int cnt);

void strcpy(char *d, char *s);
int strlen(char *s);

int open(char* filename, int flags);
int close(int fd);
int read(int fd, char* buf, int size);
int write(int fd, char* buf, int size);

float sin(float x);
float cos(float x);
float tan(float x);
float asin(float x);
float acos(float x);
float atan(float x);

float exp(float x);
float log(float x);
float sqrt(float x);
float pow(float base, float power);

void* malloc(int size);
void free(void *ptr);

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

void* bufcpy(void * d, void* s, int cnt){
    return memcpy(d, s, cnt);
}

void* malloc(int size);
void free(void *ptr);
'''
