int absolute(int x){
 if(x < 0) return -x;
 return x;
}
// int odd(int number){}
// int even(int number){}
int odd(int number);
int even(int number);


int main() {
  int T; 
  T = scanint();
  while (T) {
    int n; 
    T = T-1;
    n = scanint();
    prints("odd: ");
    printn(odd(n));
    prints("\neven: ");
    printn(even(n));
    prints("\n");
  }
  return 0;
}

int even(int number) {    
  if (number == 0)
    return 1;
  else
    return odd(absolute(number)-1);
}

int odd(int number) {
  if (number == 0)
    return 0;
  else
    return even(absolute(number)-1);
}