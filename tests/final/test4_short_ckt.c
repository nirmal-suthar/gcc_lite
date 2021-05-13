int main() {
  int *a;
  int b =1;
  int c = 0;
  if (b || (b/0)) {
    printf("Test 1: (1 || (1/0)) => passed\n");
  }
  if (c && (b/c)) { }
  else {
    printf("Test 2: (0 && (1/0)) => passed\n");
  }
  return 0;
}