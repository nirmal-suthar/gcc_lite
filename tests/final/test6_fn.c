
int f10(int a, int b, int c, int d, int e,
    int f, int g, int h, int i, int j) {
  return a+b+c+d+e+f+g+h+i+j;
}

int f9(int a, int b, int c, int d,
    int e, int f, int g, int h, int i) {
  return a+b+c+d+e+f+g+h+i;
}

int f8(int a, int b, int c, int d,
    int e, int f, int g, int h) {
  return a+b+c+d+e+f+g+h;
}

int main() {
  printf("f8(1,2,3,4,5,6,7,8) = ");
  printf("%d",f8(1,2,3,4,5,6,7,8));
  printf("\nf9(1,2,3,4,5,6,7,8,9) = ");
  printf("%d",f9(1,2,3,4,5,6,7,8,9));
  printf("\nf10(1,2,3,4,5,6,7,8,9,10) = ");
  printf("%d",f10(1,2,3,4,5,6,7,8,9,10));
  printf("\n");
  return 0;
}