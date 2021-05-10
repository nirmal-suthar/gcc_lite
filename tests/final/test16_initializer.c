// #include<stdio.h>

struct inode{
    int a;
    float b;
};

struct node{
    float x;
    int y[2];
    struct inode z;
};

int main(){
    // int b[2][3];
    // int b[2][3] = {{3, 1}, {5, 2, {8}}};
    float d = 5.98;
    struct node a = {1.23, {34.5, 3}, {4, d}};
    struct node * c = &(a);
    // struct node a = {{1}, 2};
    // int c = {4};
    // printf("%d %d %d %d %d %d\n", b[0][0], b[0][1], b[0][2], b[1][0], b[1][1], b[1][2]);
    printf("%f %d %d %d %f\n", a.x, a.y[0], a.y[1], a.z.a, a.z.b);
    // printf("%d %d %d %d\n", a.y[0], a.y[1], a.z.a, a.z.b);
    printf("%f %d\n", c->x, (c->y)[0]);
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