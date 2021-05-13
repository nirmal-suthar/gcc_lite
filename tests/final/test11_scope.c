int a;

void f(){
  a=10;
}

int g(int b,int c){
  return a++;
}

int main()
{
  int a=10;
  int b;
  int k;
  int f1;
  int q[10];
  // int a;
  b--;
  k =(int) a;

  f();
  f1 = g(a,b);
  q[1] = a;
  a = k<2 ? 4: 6 ;
  printf("k = %d\n",k);
  printf("q[1] = %d\n",q[1]);
  }  