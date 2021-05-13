int main(){
    int list[1000];
    int T ;
    int i,c,d,n,len,t,u,k=1;
    int d_lim, c_lim;
    printf("Enter the number of test cases : ");
    scanf("%d", &T);
    while(T){
	T = T-1;
	printf("Enter the length of the array (<=1000) : ");
        scanf("%d", &len);
        printf("Enter %d numbers: ", len);
        for(i=0;i<len;i=i+1){
            scanf("%d", &list[i]);
        }
	printf("Sorting the array............ \n");
  
	c_lim = len - 1;
        for(c =0;c< c_lim;c=c+1){
	   d_lim = c_lim - c;
           d=0;
            while(d<d_lim){
                k = d+1;
                   t = list[d];
		   u = list[k];
                if(t < u){
                   list[d] = u;
		   list[k] = t;
                }
               d = d+1;
       	   }
    	}
        for(i=0;i<len-1;i=i+1){
           printf("%d ",list[i]);
        }
        printf("%d",list[i]);
	printf("\n");
    }
    return 0;
}