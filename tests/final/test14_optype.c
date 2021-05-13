int main(){
    int a, b, c;
    float x, y, z,b;
    char *c;

    a = -9;
    b = 10;
    x = -9.8;
    y = a * 1.4  + b * 7.5 - 24;
    printf("y - %f\n",y);
    c = a * b;
    c += a + b;
    c += a/b;
    c += a - b;
    printf("c - %d\n",c);

    z = x * y;
    z += x + y;
    z += x/y;
    z += x - y;
    
    printf("z - %f\n",z);
    z = a * y;
    z += a + y;
    z += a/y;
    z += a - y;

    printf("z - %f\n",z);
    // Operator type error
    // if(c<x){;}
    // if(c<a){;}
   
    return 0;
}