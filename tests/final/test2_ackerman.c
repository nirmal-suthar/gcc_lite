
int ackermann(int a,int l)
{
    if(a == 0)
      return l+1;
    if((a>0) && (l == 0))
      return ackermann(a-1,1);
    if( a>0 && l>0){ 
      int k = ackermann(a,l-1);
      return ackermann(a-1,k);}
      return 1;
}

int main(){
    int T,m,n;
    prints("Input the number of cases : ");
    T = scanint();
    while(T){
       T = T-1;
       prints("Input m : ");
       m = scanint();
       prints("Input n : ");
       n = scanint();
       prints("The corrseponding ackermann value is : ");
       printn(ackermann(m,n)); 
       prints("\n");
    }
    return 0;
}