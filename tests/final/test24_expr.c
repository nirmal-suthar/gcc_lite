int b, a;
float d, c;
int main(){
    char s[10] = "HELL\n";
  c = 1.2e1;
  d = 2.59e-1;
  a = 2;
  b = 3;
  printf("sum %d\n", a + b);
  printf("diff %d\n", a - b);
  printf("mul %d\n", a * b);
  printf("div %d\n", a / b);
  printf("mod %d\n", a % b);
  printf("rshift %d\n", a >> b);
  printf("lshift %d\n", a << b);
  printf("or %d\n", a | b);
  printf("and %d\n", a & b);
  printf("xor %d\n", a ^ b);

  printf("sum %f\n", c + d);
  printf("diff %f\n", c - d);
  printf("mul %f\n", c * d);
  printf("div %f\n", c / d);
    return 0;
}