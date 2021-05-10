// #include<stdio.h>

struct inode{
    int a;
    char b;
};

struct node{
    float x;
    char y[2];
    struct inode z;
};

int main(){
    // int b[2][3];
    // int b[2][3] = {{3, 1}, {5, 2, {8}}};
    int d = 5.234;
    // struct node a = {1.23};
    struct node a = {1.23, {97, 'b' + 2}, {'Z', 10}};
    struct node * c = &(a);
    char s[10] = "Helo\n";
    // struct node a = {{1}, 2};
    s[3] = 'l';
    // int c = {4};
    // printf("%d %d %d %d %d %d\n", b[0][0], b[0][1], b[0][2], b[1][0], b[1][1], b[1][2]);
    printf("%f %c %c %d %c\n", a.x, a.y[0], a.y[1], a.z.a, a.z.b);
    printf("%f %d %d %c %d\n", a.x, a.y[0], a.y[1], a.z.a, a.z.b);
    printf("%d %d %d %d\n", a.y[0], a.y[1], a.z.a, a.z.b);
    printf("%f %d %s\n", c->x, (c->y)[0], s);
    printf("%f %d %s\n", a.x, (c->y)[0], s);
    // printf("%f %d %s\n", a.x, (c->y)[0], s);
    // int i, j;
    // for(i=0;i < 2; i++){
    //     for(j=0; j < 3; j++){
    //         printf("%d ", b[i][j]);
    //     }
    //     printf("\n");
    // }
    // printf("%d %d\n", b[0], b[1]);
    return 0;
}