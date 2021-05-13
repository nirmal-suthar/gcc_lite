stdlib = '''
int printf(char *s);
int scanf(char *s);
void strcpy(char *d, char *s);
void* memcpy(void* d, void* s, int cnt);

int open(char* filename, int flags);
int close(int fd);
int read(int fd, char* buf, int size);
int write(int fd, char* buf, int size);

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

void* malloc(int size);
void free(void *ptr);

int strlen(char *s);
'''