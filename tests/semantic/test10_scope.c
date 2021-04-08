int sum(int a, int b){
    if(a==b) return a*2;
    else return a+b;
}
void main(){
    int a = 3;
    int b = 2;
    int c = 99;

    switch(a) 
    {
        case 1:
            if(b == 0) 
                printf("%d",&c);
        case 2:
            if(b==1) a = 10;
        case 3:
            if(b==2){
                int x = 10;
                while(x>1)
                {
                    x--;
                    for( a = 0; a < 5; a++){
                        int l = sum(x,a);
                    }
                    // printf("%d",&l);//error line
                }
                a = x*a;
            }
        default:
            a--;
            break;
    }
}