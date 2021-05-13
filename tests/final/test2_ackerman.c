
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
    printf("Input the number of cases : ");
    scanf("%d", &T);
    while(T){
       T = T-1;
       printf("Input m : ");
       scanf("%d",&m);
       printf("Input n : ");
       scanf("%d",&n);
       printf("The corrseponding ackermann value is : ");
       printf("%d\n",ackermann(m,n)); 
    }
    return 0;
}