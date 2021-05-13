
int foo(char s[2][10]){
  printf("%s\n", s[0]);
  printf("%s\n", s[1]);
  // s = 1;
  // printf("%s %d\n", s);
}
int main(){
  char a[2][10] = {{'H', 'E', 'L', 'L', 'O', '\0'}, {'B', 'Y', 'E', '\0'}};
  // a[0] = 1;
  printf("%s\n", a[0]);
  printf("%s\n", a[1]);
    foo(a);
    return 0;
}