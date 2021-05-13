typedef struct node{
  int a;
  int b;
} node;


node foo(int c, node d){
  // return 0;
  struct node a = {d.b + c, d.a};
  return a;
}



int main(){
    struct node b = {1, 2};
    int c;
    node d;
    c = foo(2, b).a;
    d = foo(1, b);
    // return 0;
    printf("%d %d\n", b.a, b.b);
    printf("%d %d\n", d.a, d.b);
    // printf("%d %d\n", c.a, c.b);
    return 0;
}